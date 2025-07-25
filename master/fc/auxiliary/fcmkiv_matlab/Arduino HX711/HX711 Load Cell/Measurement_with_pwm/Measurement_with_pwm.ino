/*
 Example using the SparkFun HX711 breakout board with a scale
 By: Nathan Seidle
 SparkFun Electronics
 Date: November 19th, 2014
 License: This code is public domain but you buy me a beer if you use this and we meet someday (Beerware license).

 This example demonstrates basic scale output. See the calibration sketch to get the calibration_factor for your
 specific load cell setup.

 This example code uses bogde's excellent library: https://github.com/bogde/HX711
 bogde's library is released under a GNU GENERAL PUBLIC LICENSE

 The HX711 does one thing well: read load cells. The breakout board is compatible with any wheat-stone bridge
 based load cell which should allow a user to measure everything from a few grams to tens of tons.
 Arduino pin 2 -> HX711 CLK
 3 -> DAT
 5V -> VCC
 GND -> GND

 The HX711 board can be powered from 2.7V to 5V so the Arduino 5V power should be fine.

*/

#include "HX711.h"

#define calibration_factor -2720050.0 //This value is obtained using the SparkFun_HX711_Calibration sketch

#define DOUT  11
#define CLK  12
 int s=250;
 int num=0;
 int startdelay=300;       //roughly s*10
HX711 scale(DOUT, CLK);

void setup() {
  Serial.begin(9600);
  //Serial.println("HX711 scale demo");

  scale.set_scale(calibration_factor); //This value is obtained by using the SparkFun_HX711_Calibration sketch
 scale.tare(); //Assuming there is no weight on the scale at start up, reset the scale to 0

 // Serial.println("Readings:");

 for ( int n=2; n<11; n++) {
  pinMode(n,OUTPUT);
 }

}

void loop() {

for ( int n=2; n<11; n++) {
  analogWrite(n,s);
}
  
  //Serial.print("Reading: ");
  Serial.print(scale.get_units()*1000, 6); //scale.get_units() returns a float
  Serial.print(" g"); //You can change this to kg but you'll need to refactor the calibration_factor
  Serial.println();
 
    Serial.print(s,1); //scale.get_units() returns a float 
    Serial.print(" PWM");
    
    Serial.println();

    if ( num % 10 == 0 && num > startdelay )
    {
         s=s-1;
    }
num=num+1;
}

