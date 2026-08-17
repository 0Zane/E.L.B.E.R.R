"""Local LLM (Ollama) with sentence streaming for low-latency speech."""

from __future__ import annotations

import re
from typing import Iterator

# Only split once punctuation is followed by whitespace so streaming tokens
# like "E." in E.L.B.E.R.R. are not spoken one letter at a time.
_SENTENCE_END = re.compile(r"[.!?]+[\"')\]]*[ \t\n]+")
_FLUSH_CHARS = 110


def _chunk_text(chunk) -> str:
    if chunk is None:
        return ""
    if isinstance(chunk, str):
        return chunk
    message = getattr(chunk, "message", None)
    if message is not None:
        return getattr(message, "content", None) or ""
    if isinstance(chunk, dict):
        if "message" in chunk:
            return (chunk["message"] or {}).get("content") or ""
        return chunk.get("response") or ""
    return ""


def _pop_sentences(buf: str) -> tuple[list[str], str]:
    ready: list[str] = []
    while True:
        match = _SENTENCE_END.search(buf)
        if not match:
            break
        piece = buf[: match.end()].strip()
        buf = buf[match.end() :]
        if piece:
            ready.append(piece)
    return ready, buf


def _flush_long(buf: str) -> tuple[str | None, str]:
    if len(buf) < _FLUSH_CHARS:
        return None, buf
    split_at = buf.rfind(" ", 0, _FLUSH_CHARS)
    if split_at < 40:
        return None, buf
    return buf[:split_at].strip(), buf[split_at + 1 :]


def stream_sentences(client, model: str, messages: list[dict]) -> Iterator[str]:
    kwargs = {
        "model": model,
        "messages": messages,
        "stream": True,
        "keep_alive": "24h",
    }
    try:
        stream = client.chat(**kwargs, think=False)
    except TypeError:
        stream = client.chat(**kwargs)

    buf = ""
    for chunk in stream:
        buf += _chunk_text(chunk)
        sentences, buf = _pop_sentences(buf)
        for sentence in sentences:
            yield sentence
        piece, buf = _flush_long(buf)
        if piece:
            yield piece

    leftover = " ".join(buf.split()).strip()
    if leftover:
        yield leftover


def warmup(client, model: str) -> None:
    kwargs = {
        "model": model,
        "messages": [{"role": "user", "content": "."}],
        "keep_alive": "24h",
        "options": {"num_predict": 1},
    }
    try:
        client.chat(**kwargs, think=False)
    except TypeError:
        client.chat(**kwargs)
    except Exception as exc:
        print(f"[llm] warmup failed: {exc}", flush=True)
