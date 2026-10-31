#include "TurretFunctions.h"
#include "BoardConfig.h"
#include <Arduino.h>
#include <Ethernet.h>
#include <FastAccelStepper.h>
#include <SPI.h>
#include <limits.h>
#include <math.h>
#include <stdio.h>


FastAccelStepperEngine engine;
FastAccelStepper *pan = nullptr;
FastAccelStepper *tilt = nullptr;

bool motorsReady = false;
bool motorsEnabled = false;
bool positionKnown = false;
bool stopping = false;
bool connectionActive = false;
unsigned long lastHeartbeat = 0;

EthernetServer server(TCP_PORT);
EthernetClient pc;
bool ethernetReady = false;


String usbCommand;
String ethernetCommand;
bool usbLineTooLong = false;
bool ethernetLineTooLong = false;

bool isMoving() {
    if (!motorsReady) {
        return false;
    }
    return pan->isRunning() || tilt->isRunning();
}

void stopMotors() {
    if (motorsReady) {
        pan->stopMove();
        tilt->stopMove();
        stopping = true;
    }
}

void disableMotors() {
    if (pan) {
        pan->forceStopAndNewPosition(pan->getCurrentPosition());
        pan->disableOutputs();
    }
    if (tilt) {
        tilt->forceStopAndNewPosition(tilt->getCurrentPosition());
        tilt->disableOutputs();
    }
    digitalWrite(PAN_ENABLE, HIGH);
    digitalWrite(TILT_ENABLE, HIGH);
    motorsEnabled = false;
    positionKnown = false;
    connectionActive = false;
    stopping = false;
}

void showStatus(Print &reply) {
    reply.print("READY=");
    reply.print(motorsReady);
    reply.print(" ENABLED=");
    reply.print(motorsEnabled);
    reply.print(" ZEROED=");
    reply.print(positionKnown);
    reply.print(" MOVING=");
    reply.print(isMoving());
    reply.print(" CONNECTION_ACTIVE=");
    reply.print(connectionActive);
    if (motorsReady) {
        reply.print(" PAN_EST_DEG=");
        reply.print(pan->getCurrentPosition() / PAN_STEPS_PER_DEGREE, 3);
        reply.print(" TILT_EST_DEG=");
        reply.print(tilt->getCurrentPosition() / TILT_STEPS_PER_DEGREE, 3);
    }
    reply.println();
}

void zeroPosition(Print &reply) {
    if (motorsEnabled || isMoving()) {
        reply.println("ERROR: Disable motors and place at origin first.");
        return;
    }
    pan->setCurrentPosition(0);
    tilt->setCurrentPosition(0);
    positionKnown = true;
    stopping = false;
    reply.println("OK: Manual zero set.");
}
