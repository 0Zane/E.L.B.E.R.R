"""Background UART communication with the ESP32."""

from __future__ import annotations

import json
import os
import queue
import re
import threading
import time
from concurrent.futures import Future
from dataclasses import dataclass
from enum import IntEnum
from typing import Any

import serial


BAUD_RATE = 115_200
DEFAULT_PORT = "/dev/serial0"
RESPONSE_TIMEOUT = 8.0
RECONNECT_DELAY = 2.0
MAX_PENDING_REQUESTS = 16


class UARTCommand(IntEnum):
    """Numeric commands shared with the ESP32 firmware."""

    INITIALIZE = 0
    SYSTEM_DIAGNOSIS = 1
    SKULL_STATE = 2
    TEMPERATURE = 3
    WIFI_COUNT = 4


# Edit these phrases to match the vocabulary used by the speech recognizer.
VOICE_COMMANDS = {
    "system diagnosis": UARTCommand.SYSTEM_DIAGNOSIS,
    "diagnosis": UARTCommand.SYSTEM_DIAGNOSIS,
    "diagnose": UARTCommand.SYSTEM_DIAGNOSIS,
    "skull state": UARTCommand.SKULL_STATE,
    "skull": UARTCommand.SKULL_STATE,
    "temperature": UARTCommand.TEMPERATURE,
    "wifi count": UARTCommand.WIFI_COUNT,
    "wifi": UARTCommand.WIFI_COUNT,
    "wi fi": UARTCommand.WIFI_COUNT,
}


@dataclass
class _Request:
    command: UARTCommand
    future: Future[dict[str, object]]


def commands_for_utterance(text: str) -> tuple[UARTCommand, ...]:
    """Return requested commands, combining multiple requests into a diagnosis."""
    normalized_text = re.sub(r"[^a-z0-9]+", " ", text.casefold()).strip()
    padded_text = f" {normalized_text} "
    matches: list[UARTCommand] = []

    for phrase, command in sorted(
        VOICE_COMMANDS.items(), key=lambda item: len(item[0]), reverse=True
    ):
        normalized_phrase = re.sub(r"[^a-z0-9]+", " ", phrase.casefold()).strip()
        if f" {normalized_phrase} " in padded_text and command not in matches:
            matches.append(command)

    if UARTCommand.SYSTEM_DIAGNOSIS in matches or len(matches) > 1:
        return (UARTCommand.SYSTEM_DIAGNOSIS,)
    return tuple(matches)


class Esp32UART:
    """Own the serial link and receive replies without blocking speech capture."""

    def __init__(
        self,
        port: str | None = None,
        baud_rate: int = BAUD_RATE,
        response_timeout: float = RESPONSE_TIMEOUT,
    ) -> None:
        self.port = port or os.environ.get("ELBERR_UART_PORT", DEFAULT_PORT)
        self.baud_rate = baud_rate
        self.response_timeout = response_timeout

        self._requests: queue.Queue[_Request] = queue.Queue(
            maxsize=MAX_PENDING_REQUESTS
        )
        self._stop_event = threading.Event()
        self._state_lock = threading.Lock()
        self._snapshot: dict[str, object] = {"connected": False}
        self._connected = False
        self._worker: threading.Thread | None = None

    @property
    def connected(self) -> bool:
        with self._state_lock:
            return self._connected

    def snapshot(self) -> dict[str, object]:
        with self._state_lock:
            return dict(self._snapshot)

    def start(self) -> None:
        """Start receiving and send the initialize command on each connection."""
        if self._worker is not None and self._worker.is_alive():
            return
        self._stop_event.clear()
        self._worker = threading.Thread(
            target=self._run,
            name="esp32-uart",
            daemon=True,
        )
        self._worker.start()

    def close(self) -> None:
        self._stop_event.set()
        if self._worker is not None:
            self._worker.join(timeout=1.0)
        self._fail_queued(RuntimeError("ESP32 UART has been stopped"))

    def request(self, command: UARTCommand) -> Future[dict[str, object]]:
        """Queue one command and return a future resolved by the reader thread."""
        if not isinstance(command, UARTCommand):
            raise ValueError(f"Unsupported ESP32 command: {command!r}")
        if self._worker is None or not self._worker.is_alive():
            raise RuntimeError("ESP32 UART is not running")
        if not self.connected:
            raise RuntimeError("ESP32 UART is not connected")

        future: Future[dict[str, object]] = Future()
        try:
            self._requests.put_nowait(_Request(command, future))
        except queue.Full as exc:
            raise RuntimeError("ESP32 UART request queue is full") from exc
        return future

    def request_diagnosis(self) -> Future[dict[str, object]]:
        return self.request(UARTCommand.SYSTEM_DIAGNOSIS)

    def get_skull_state(self) -> Future[dict[str, object]]:
        return self.request(UARTCommand.SKULL_STATE)

    def get_temperature(self) -> Future[dict[str, object]]:
        return self.request(UARTCommand.TEMPERATURE)

    def get_wifi_count(self) -> Future[dict[str, object]]:
        return self.request(UARTCommand.WIFI_COUNT)

    def _run(self) -> None:
        connection: Any = None
        pending: _Request | None = None
        last_connection_error: str | None = None

        while not self._stop_event.is_set():
            if connection is None:
                try:
                    connection = serial.Serial(
                        self.port,
                        self.baud_rate,
                        timeout=0.1,
                        write_timeout=0.5,
                    )
                except (serial.SerialException, OSError, ValueError) as exc:
                    self._set_connected(False)
                    message = str(exc)
                    if message != last_connection_error:
                        print(f"[uart] cannot open {self.port}: {message}", flush=True)
                        last_connection_error = message
                    self._stop_event.wait(RECONNECT_DELAY)
                    continue

                print(
                    f"[uart] connected to {self.port} at {self.baud_rate} baud",
                    flush=True,
                )
                last_connection_error = None

            pending = _Request(UARTCommand.INITIALIZE, Future())

            try:
                deadline = self._send(connection, pending)
                while not self._stop_event.is_set():
                    line = connection.read_until(expected=b"\n", size=512)
                    if line:
                        response = self._parse_response(line)
                        if response is not None:
                            response_command = response["cmd"]
                            if response_command == int(pending.command):
                                self._update_snapshot(response, pending.command)
                                if not pending.future.done():
                                    pending.future.set_result(response)
                                if (
                                    pending.command == UARTCommand.INITIALIZE
                                    and response["ok"] is not True
                                ):
                                    raise serial.SerialException(
                                        "ESP32 rejected the initialize command"
                                    )
                                pending = None
                            else:
                                print(
                                    "[uart] ignoring response for command "
                                    f"{response_command}; waiting for "
                                    f"{int(pending.command)}",
                                    flush=True,
                                )

                    if pending is None:
                        try:
                            pending = self._requests.get_nowait()
                        except queue.Empty:
                            continue
                        deadline = self._send(connection, pending)

                    if time.monotonic() >= deadline:
                        message = (
                            f"no reply for ESP32 command {int(pending.command)} "
                            f"within {self.response_timeout:.1f}s"
                        )
                        if not pending.future.done():
                            pending.future.set_exception(TimeoutError(message))
                        pending = None
                        raise serial.SerialException(message)
            except (serial.SerialException, OSError, ValueError) as exc:
                self._set_connected(False)
                if pending is not None and not pending.future.done():
                    pending.future.set_exception(RuntimeError(str(exc)))
                print(f"[uart] connection lost: {exc}", flush=True)
                try:
                    connection.close()
                except (serial.SerialException, OSError) as close_error:
                    print(f"[uart] error closing serial port: {close_error}", flush=True)
                connection = None

        if pending is not None and not pending.future.done():
            pending.future.set_exception(RuntimeError("ESP32 UART has been stopped"))
        if connection is not None:
            try:
                connection.close()
            except (serial.SerialException, OSError) as exc:
                print(f"[uart] error closing serial port: {exc}", flush=True)
        self._set_connected(False)

    def _send(self, connection: Any, request: _Request) -> float:
        if request.future.cancelled():
            return time.monotonic()
        payload = f"{int(request.command)}\n".encode("ascii")
        connection.write(payload)
        connection.flush()
        return time.monotonic() + self.response_timeout

    @staticmethod
    def _parse_response(line: bytes) -> dict[str, object] | None:
        try:
            response = json.loads(line.decode("utf-8").strip())
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            print(f"[uart] invalid response: {exc}", flush=True)
            return None

        if (
            not isinstance(response, dict)
            or not isinstance(response.get("cmd"), int)
            or not isinstance(response.get("ok"), bool)
        ):
            print("[uart] response must contain integer 'cmd' and boolean 'ok'", flush=True)
            return None
        return response

    def _update_snapshot(
        self, response: dict[str, object], command: UARTCommand
    ) -> None:
        with self._state_lock:
            if command == UARTCommand.INITIALIZE:
                self._connected = response["ok"] is True
                self._snapshot["connected"] = self._connected
            if response["ok"] is True:
                for key in ("skull_state", "temperature_c", "wifi_count"):
                    if key in response:
                        self._snapshot[key] = response[key]
            self._snapshot["last_command"] = int(command)
            self._snapshot["last_ok"] = response["ok"]

    def _set_connected(self, connected: bool) -> None:
        with self._state_lock:
            self._connected = connected
            self._snapshot["connected"] = connected

    def _fail_queued(self, error: Exception) -> None:
        while True:
            try:
                request = self._requests.get_nowait()
            except queue.Empty:
                return
            if not request.future.done():
                request.future.set_exception(error)
