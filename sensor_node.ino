#include <OneWire.h>
#include <DallasTemperature.h>
#include <EEPROM.h>

#define ONE_WIRE_BUS 2

int phPin = A0;
int turbPin = A1;

// ================== TEMPERATURE ==================
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

// ================== CALIBRATION ==================
struct CalibData {
  float ph4;
  float ph7;
  float ph10;
  float turbClean;
  float turbDirty;
};

CalibData calib;

// ================== SETTINGS ==================
const int SAMPLES = 20;

// ================== EEPROM LOAD ==================
void loadCalibration() {
  EEPROM.get(0, calib);

  if (isnan(calib.ph7) || calib.ph7 == 0) {
    calib.ph4 = 320;
    calib.ph7 = 380;
    calib.ph10 = 420;
    calib.turbClean = 975;
    calib.turbDirty = 150;
  }
}

void saveCalibration() {
  EEPROM.put(0, calib);
}

// ================== FILTER ==================
float readAvg(int pin) {
  long sum = 0;
  for (int i = 0; i < SAMPLES; i++) {
    sum += analogRead(pin);
    delay(10);
  }
  return sum / (float)SAMPLES;
}

// ================== pH ==================
float calcPH(float raw) {
  float slope = (7.0 - 4.0) / (calib.ph7 - calib.ph4);
  float ph = 7.0 + (raw - calib.ph7) * slope;

  if (ph < 0) ph = 0;
  if (ph > 14) ph = 14;

  return ph;
}

// ================== TURBIDITY (LIMITED TO 0–100) ==================
float calcTurb(float raw) {
  float ntu = (calib.turbClean - raw) *
              (100.0 / (calib.turbClean - calib.turbDirty));

  if (ntu < 0) ntu = 0;
  if (ntu > 100) ntu = 100;

  return ntu;
}

// ================== SERIAL COMMANDS ==================
void checkSerial() {
  if (!Serial.available()) return;

  String cmd = Serial.readStringUntil('\n');
  cmd.trim();

  if (cmd == "CAL_PH7") {
    calib.ph7 = readAvg(phPin);
    Serial.println("OK PH7");
  }

  else if (cmd == "CAL_CLEAN") {
    calib.turbClean = readAvg(turbPin);
    Serial.println("OK CLEAN");
  }

  else if (cmd == "CAL_DIRTY") {
    calib.turbDirty = readAvg(turbPin);
    Serial.println("OK DIRTY");
  }

  else if (cmd == "SAVE") {
    saveCalibration();
    Serial.println("SAVED");
  }
}

// ================== SETUP ==================
void setup() {
  Serial.begin(115200);
  sensors.begin();
  loadCalibration();
}

// ================== LOOP ==================
void loop() {

  checkSerial();

  sensors.requestTemperatures();
  float temp = sensors.getTempCByIndex(0);
  if (temp == -127.0) temp = 0;

  float phRaw = readAvg(phPin);
  float turbRaw = readAvg(turbPin);

  float ph = calcPH(phRaw);
  float turb = calcTurb(turbRaw);

  Serial.print("ph:");
  Serial.print(ph, 2);

  Serial.print(",temp:");
  Serial.print(temp, 1);

  Serial.print(",turb:");
  Serial.println(turb, 0);

  delay(1000);
}
