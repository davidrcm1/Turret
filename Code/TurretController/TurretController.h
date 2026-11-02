#pragma once        

#include <Arduino.h>
#include <Ethernet.h>
#include <FastAccelStepper.h>
#include "BoardConfig.h"


AccelStepper pan{AccelStepper::DRIVER, PAN_STEP, PAN_DIR};
AccelStepper tilt{AccelStepper::DRIVER, TILT_STEP, TILT_DIR};

class TurretController {

public:
    void begin();
    void update();


private 
    FastAccelStepperEngine engine;
    FastAccelStepper* pan = nullptr;
    FastAccelStepper* tilt = nullptr;


    bool motorsReady = false;
    bool motorsEnabled = false;
    bool positionKnown = false;
    bool stopping = false;

    bool connectionActive = false;
    unsigned long lastHeartbeat = 0;

    EthernetServer server{TCP_PORT};
    EthernetClient pc;
    bool ethernetReady = false;

    String usbCommand;
    String ethernetCommand;
    bool usbLineTooLong = false;
    bool ethernetLineTooLong = false;

    bool isMoving();
    void stopMotors();
    void disableMotors();
    void showStatus(Print& reply);
    void zeroPosition(Print& reply);

    void initializeEnablePins();
    void initializeSerial();
    bool configurationConfirmed();
    bool initializeMotors();

    void configureMotor(
        FastAccelStepper* motor,
        int directionPin,
        int enablePin,
        bool reversed,
        double speed,
        double acceleration,
        double stepsPerDegree);

    void printStartupMessage();

    void readUsbCommands();
    void processUsbCharacter(char c);
    void executeUsbCommand();

    void checkConnectionTimeout();
    void updateStoppingState();
}