#include "TurretController.h"

TurretController turret;

void setup() {
    turret.begin();
}

void loop() {
    turret.update();
}
