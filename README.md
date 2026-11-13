
# ESP32-S3 Vision Tracking Pan-Tilt Turret
<img width="1536" height="2048" alt="2f7d8cb3-8989-4bfb-986b-2ada7bba075c" src="https://github.com/user-attachments/assets/9dd3a10e-7bd3-417a-829a-4167d98ed782" />



A custom-built two-axis pan-and-tilt tracking platform combining mechanical design,
embedded motion control, Ethernet communication, and computer vision.

The system uses an ESP32-S3 to control two NEMA 17 stepper motors through A4988
stepper drivers. A PC performs camera-based target detection and tracking, then sends
movement commands to the ESP32 over Ethernet.

The mechanical system was designed in CAD and manufactured primarily using 3D-printed
components.

## Project Overview

The goal of this project is to develop a complete mechatronic tracking system covering:

- Mechanical and CAD design
- 3D printing and prototyping
- Stepper motor motion control
- ESP32-S3 embedded development
- Ethernet communication
- Computer vision and target tracking
- Closed-loop visual position correction

## System Architecture

![System Architecture](docs/images/system-architecture.png)

The system is divided into two main controllers:

**PC / Vision System**

Camera → Object Detection / Tracking → Position Error → Motion Command → Ethernet

**ESP32-S3 / Motion Controller**

Ethernet → Motion Command → Pan/Tilt Control → A4988 Drivers → NEMA 17 Motors

The PC performs the computationally intensive vision processing while the ESP32-S3
handles real-time motor control.

## Mechanical Design

![CAD Assembly](docs/images/cad-assembly.png)

The turret was designed as a two-axis pan-and-tilt mechanism.

### Pan Axis

- NEMA 17 stepper motor
- GT2 timing belt transmission
- 142-tooth driven pulley
- Bearing-supported rotating base
- 3D-printed structural components

### Tilt Axis

- NEMA 17 stepper motor
- GT2 timing belt transmission
- 60-tooth driven pulley
- 3D-printed camera/turret support structure

The pulley reductions increase positioning resolution while allowing the motors to be
mounted away from the rotational axes.

## Electronics

<img width="1447" height="1087" alt="4444" src="https://github.com/user-attachments/assets/1aee8d81-d0ab-4a54-bdd0-280e69a7c3cd" />


### Main Components

| Component | Description |
|---|---|
| ESP32-S3 | Main embedded motion controller |
| 2 × NEMA 17 | Pan and tilt actuators |
| 2 × A4988 | Stepper motor drivers |
| Mean Well LRS-75-12 | 12 V, 6.3 A power supply |
| Buck Converter | Low-voltage electronics supply |
| Camera | Target detection and tracking |
| Ethernet Interface | PC ↔ ESP32 communication |

The ESP32 generates step pulses and direction signals for each A4988 driver. The
drivers translate these logic-level commands into the phase currents required to
drive the stepper motors.

## Motion Control

Each axis is controlled using three primary signals:

- **STEP** – each pulse advances the motor by one step or microstep.
- **DIR** – determines the direction of rotation.
- **ENABLE** – enables or disables the A4988 output stage.

The controller converts requested turret movement into the required number and
frequency of step pulses while accounting for the mechanical transmission ratio.




