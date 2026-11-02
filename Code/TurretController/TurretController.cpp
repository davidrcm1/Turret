#include "TurretController.h"

#include <math.h>


void TurretController::initializeEnablePins(){
    digitalWrite(PAN_ENABLE, HIGH);
    digitalWrite(TILT_ENABLE, HIGH);

    pinMode(PAN_ENABLE, OUTPUT);
    pinMode(TILT_ENABLE, OUTPUT);
}

void TurretController::initializeSerial(){
    Serial.begin(115200);
    usbCommand.reserve(96);
}

bool TurretController::configurationConfirmed(){
    return HARDWARE_CONFIRMED && LIMITS_CONFIRMED;
}

bool TurretController::initializeMotors(){
    engine.init();

    pan = engine.stepperConnectToPin(PAN_STEP);
    tilt = engine.stepperConnectToPin(TILT_STEP);

    if(!pan || !tilt){
        disableMotors();
        return false;
    }

    configureMotor(pan, PAN_DIR, PAN_ENABLE, PAN_REVERSED, PAN_SPEED, PAN_ACCELERATION, PAN_STEPS_PER_DEGREE);
    configureMotor(tilt, TILT_DIR, TILT_ENABLE, TILT_REVERSED, TILT_SPEED, TILT_ACCELERATION, TILT_STEPS_PER_DEGREE);

    motorsReady = true;
    return true;
}


void TurretController::printStartupMessage() {
    Serial.println("Initialized; w motors disabled");
    Serial.println("Commands: STATUS, ZERO, STOP, DISABLE");

    if (USE_ETHERNET){
        Serial.println("ETHERNET  ((req implementation))");

    }

}

void TurretController::readUsbCommands(){

    for (int count = 0; count < 64 && Serial.available(); ++count){
        processUsbCharacter(static_cast<char>(Serial.read()));
    }
}

void TurretController::processUsbCharacter(char c) {
    if (c == '\r') {
        return;
    }

    if (c == '\n') {
        if (usbLineTooLong) {
            Serial.println("ERROR: Command too long.");
        } else {
            executeUsbCommand();
        }

        usbCommand = "";
        usbLineTooLong = false;
        return;
    }

    if (usbLineTooLong) {
        return;
    }

    if (usbCommand.length() < 95) {
        usbCommand += c;
    } else {
        usbLineTooLong = true;
    }
}

void TurretController::executeUsbCommand() {
    usbCommand.trim();
    usbCommand.toUpperCase();

    if (usbCommand == "STATUS") {
        showStatus(Serial);
    } else if (usbCommand == "ZERO") {
        zeroPosition(Serial);
    } else if (usbCommand == "STOP") {
        stopMotors();
        Serial.println("OK: Stop requested.");
    } else if (usbCommand == "DISABLE") {
        disableMotors();
        Serial.println("OK: Disabled.");
    } else if (usbCommand.length() != 0) {
        Serial.println("ERROR: Unknown command.");
    }
}

void TurretController::checkConnectionTimeout() {
    if (!connectionActive) {
        return;
    }

    if (millis() - lastHeartbeat >= CONNECTION_TIMEOUT_MS) {
        disableMotors();
        Serial.println(
            "ERROR: Connection timed out; motors disabled.");
    }
}

void TurretController::updateStoppingState() {
    if (stopping && !isMoving()) {
        stopping = false;
    }
}

void TurretController::configureMotor(
    FastAccelStepper* motor,
    int directionPin,
    int enablePin,
    bool reversed,
    double speed,
    double acceleration,
    double stepsPerDegree) {

    motor->setDirectionPin(directionPin, !reversed);
    motor->setEnablePin(enablePin);
    motor->setAutoEnable(false);

    motor->setSpeedInHz(
        static_cast<uint32_t>(round(speed * stepsPerDegree)));

    motor->setAcceleration(
        static_cast<uint32_t>(
            round(acceleration * stepsPerDegree)));
}



void TurretController::begin() {
    initializeEnablePins();
    initializeSerial();

    if (!configurationConfirmed()) {
        Serial.println(
            "Motor initialization blocked: check BoardConfig.h.");
        return;
    }

    if (!initializeMotors()) {
        Serial.println("ERROR: Stepper initialization failed.");
        return;
    }

    disableMotors();
    printStartupMessage();
}

void TurretController::update() {
    readUsbCommands();
    checkConnectionTimeout();
    updateStoppingState();
}

bool TurreController::isMoving() {
    if (!motorsReady || pan == nullptr || tilt = nullptr){
        return false
    }

    return pan->isRunning()|| tilt->isRunning()
}


void TurretController::stopMoving(){
    if(!motorsReady || pan == nullptr || tilt == nullptr){
        return;
    
    }
    pan->stopMove();
    tilt->stopMove();

    stopping = true;

}

void TurretController::disableMotors(){
    if (pan != nullptr){
        pan->forceStopAndNewPosition(pan->getCurretnPosition());
        pan->disableOutputs();

    }
    if (tilt != nullptr){
        tilt->forceStopAndNewPosition(tilt->getCurrentPosition());
        tilt->disableOutputs();
    }
}


void TurretController::showStatus(Print& reply){
        reply.print("READY=");
    reply.print(motorsReady);

    reply.print(" ENABLED=");
    reply.print(motorsEnabled);

    reply.print(" ZEROED=");
    reply.print(positionKnown);

    reply.print(" MOVING=");
    reply.print(isMoving());

    reply.print(" STOPPING=");
    reply.print(stopping);

    reply.print(" CONNECTION_ACTIVE=");
    reply.print(connectionActive);

    reply.print(" ETHERNET_READY=");
    reply.print(ethernetReady);

    if (motorsReady && pan != nullptr && tilt != nullptr) {
        // These are estimates derived from generated steps,
        // not measurements from position sensors.
        reply.print(" PAN_EST_DEG=");
        reply.print(
            pan->getCurrentPosition() / PAN_STEPS_PER_DEGREE,
            3);

        reply.print(" TILT_EST_DEG=");
        reply.print(
            tilt->getCurrentPosition() / TILT_STEPS_PER_DEGREE,
            3);
    }

    reply.println();
}

void TurretController::zeroPosition(Print& reply){
     if (!motorsReady || pan == nullptr || tilt == nullptr) {
        reply.println("ERROR: Motors not initialized.");
        return;
    }

    if (motorsEnabled || isMoving()) {
        reply.println(
            "ERROR: Disable motors and place at origin first.");
        return;
    }

    // The operator must physically place both axes at origin.
    // This records that position; it does not home the motors.
    pan->setCurrentPosition(0);
    tilt->setCurrentPosition(0);

    positionKnown = true;
    stopping = false;

    reply.println("OK: Manual zero set.");
}
