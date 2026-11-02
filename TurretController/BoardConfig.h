#pragma once

constexpr bool HARDWARE_CONFIRMED = false;
constexpr bool LIMITS_CONFIRMED = false;
constexpr bool USE_ETHERNET = true;

constexpr int PAN_STEP = 2;
constexpr int PAN_DIR = 4;
constexpr int PAN_ENABLE = 6;
constexpr bool PAN_REVERSED = false;

constexpr int TILT_STEP = 16;
constexpr int TILT_DIR = 17;
constexpr int TILT_ENABLE = 18;
constexpr bool TILT_REVERSED = false;

constexpr int PAN_MICROSTEPS = 1;
constexpr int TILT_MICROSTEPS = 1;
constexpr double PAN_STEPS_PER_DEGREE = 1420.0 * PAN_MICROSTEPS / 360.0;
constexpr double TILT_STEPS_PER_DEGREE = 600.0 * TILT_MICROSTEPS / 360.0;

constexpr double PAN_MIN = -170.0;
constexpr double PAN_MAX = 170.0;
constexpr double TILT_MIN = -30.0;
constexpr double TILT_MAX = 60.0;

constexpr double PAN_SPEED = 10.0;
constexpr double PAN_ACCELERATION = 20.0;
constexpr double TILT_SPEED = 5.0;
constexpr double TILT_ACCELERATION = 10.0;

constexpr int ETH_SCK = 7;
constexpr int ETH_MOSI = 8;
constexpr int ETH_MISO = 9;
constexpr int ETH_CS = 10;
constexpr int ETH_RESET = 11;
constexpr int TCP_PORT = 5000;
constexpr unsigned long CONNECTION_TIMEOUT_MS = 2000;
