# 🤖 Animatronic

![Status](https://img.shields.io/badge/Status-Active-brightgreen)
![Platform](https://img.shields.io/badge/Platform-Embedded-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Language](https://img.shields.io/badge/Language-C%2B%2B-red)

> A sophisticated animatronic robot powered by cutting-edge embedded systems and professional PCB design.

---

## ⚙️ Brain Architecture

The Animatronic features a **dual-brain system** with specialized processors handling different subsystems:

### 🍓 Raspberry Pi 4
- **Role**: Main computational hub and orchestration
- **Responsibilities**:
  - High-level logic and AI processing
  - Vision and sensor data aggregation
  - Communication and networking
  - Coordinating overall robot behavior

### 🔧 ESP32-S3
- **Role**: Real-time motor and actuator control
- **Responsibilities**:
  - Low-latency motor control
  - Direct sensor interfacing
  - Real-time responses and safety protocols
  - Peripheral management

This distributed architecture ensures responsive real-time control while maintaining sophisticated decision-making capabilities.

---

## 🎨 PCB Design

The PCB for the Animatronic is designed using **KiCAD**, an open-source electronics design automation suite. This allows for professional-grade circuit board design with schematic capture and PCB layout.

---

## 📋 Project Structure

```
Vyke/
├── firmware/
│   ├── src/
│   │   └── main.cpp
│   ├── include/
│   │   ├── pins.h
│   │   └── readposition.h
│   ├── lib/
│   ├── test/
│   └── platformio.ini
├── hardware/
│   └── README.md
├── README.md
└── LICENSE
```

---

## 🛠️ Technologies Used

| Component | Technology |
|-----------|-----------|
| **Main Brain** | Raspberry Pi 4 |
| **Motor Control** | ESP32-S3 |
| **PCB Design** | KiCAD |
| **Firmware** | C++ |
| **Architecture** | Distributed/Dual-Core |

---

## 📝 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
