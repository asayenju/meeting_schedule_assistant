#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <WiFi.h>

// --- THESE ARE THE CORRECT AUDIO HEADERS ---
#include "AudioGeneratorMP3.h"
#include "AudioOutputI2S.h"
#include "AudioFileSourceHTTPStream.h"

// --- NEW HEADERS FOR RECORDING ---
#include "driver/i2s.h"      // For I2S-ADC
#include <HTTPClient.h>      // To send the audio

// --- AI SERVER URL ---
const char* AI_SERVER_URL = "http://:5000/transcribe";

// --- WIFI ---
const char* ssid = "Ashwin's iPhone";
const char* password = "12345678";

// --- Pin Definitions ---
#define POWER_BUTTON_PIN 4     // Your ONE momentary "release" button
#define PTT_BUTTON_PIN 12      // Your PTT button
#define MIC_ADC_PIN ADC1_CHANNEL_6 // This is GPIO 34

// --- Screen ---
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1

// --- Hardware Objects ---
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);
HTTPClient http;

// --- Audio Objects ---
AudioGeneratorMP3 *mp3;
AudioOutputI2S *out;
AudioFileSourceHTTPStream *file;

// --- Audio Recording Config ---
const i2s_port_t I2S_PORT_0 = I2S_NUM_0; 
const int SAMPLE_RATE = 16000;
const int BITS_PER_SAMPLE = 16;
const int READ_LEN = 1024;
char i2s_read_buff[READ_LEN];

// --- Global Variables ---
String yourName = "Hi Minh";
bool isBMOOn = false; 
bool screenNeedsUpdate = false; 

// --- Debounce Variables ---
int lastButtonState = HIGH; 
unsigned long lastDebounceTime = 0;
unsigned long debounceDelay = 50;

// =================================================================
// HELPER FUNCTIONS (OLED, FACE, TTS)
// =================================================================

void displayMessage(String line1, String line2 = "") {
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.println(line1);
  display.setCursor(0, 10);
  display.println(line2);
  display.display();
}

void drawBMOFace() {
  display.clearDisplay();
  display.fillCircle(44, 24, 8, SSD1306_WHITE); // Left eye
  display.fillCircle(84, 24, 8, SSD1306_WHITE); // Right eye
  display.drawLine(44, 45, 54, 50, SSD1306_WHITE);
  display.drawLine(54, 50, 74, 50, SSD1306_WHITE);
  display.drawLine(74, 50, 84, 45, SSD1306_WHITE);
  display.setTextSize(1);      
  display.setTextColor(SSD1306_WHITE); 
  display.setCursor(43, 56);
  display.print(yourName);     
  display.display();
}

void speakMessage(String text) {
  // Don't speak if BMO has been turned off
  if (!isBMOOn) return; 

  Serial.print("Attempting to say: ");
  Serial.println(text);

  out = new AudioOutputI2S(0, AudioOutputI2S::INTERNAL_DAC);
  out->SetGain(2.0);

  String fullUrl = "http://translate.google.com/translate_tts?ie=UTF-8&q=" + text + "&tl=en&client=tw-ob";
  fullUrl.replace(" ", "%20"); 

  file = new AudioFileSourceHTTPStream(fullUrl.c_str());
  mp3 = new AudioGeneratorMP3();

  if (mp3->begin(file, out)) {
    Serial.println("MP3->begin() successful.");
    while (mp3->loop()) { 
      // Check if power was cut mid-speech
      if (digitalRead(POWER_BUTTON_PIN) == LOW && (millis() - lastDebounceTime) > debounceDelay) {
        // This is a "hack" to catch a fast turn-off
        break;
      }
    }
    mp3->stop();
    Serial.println("TTS Finished.");
  } else {
    Serial.println("MP3->begin() failed. Check connection.");
  }

  delete mp3;
  delete file;
  delete out;
  out = NULL;
}

// =================================================================
// I2S-ADC (MICROPHONE) FUNCTIONS
// =================================================================

void i2s_adc_init() {
  i2s_config_t i2s_config = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX | I2S_MODE_ADC_BUILT_IN),
    .sample_rate = SAMPLE_RATE,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = I2S_COMM_FORMAT_STAND_I2S,
    .intr_alloc_flags = 0,
    .dma_buf_count = 8,
    .dma_buf_len = 64,
    .use_apll = false
  };

  i2s_driver_install(I2S_PORT_0, &i2s_config, 0, NULL);
  i2s_set_adc_mode(ADC_UNIT_1, MIC_ADC_PIN);
  i2s_set_clk(I2S_PORT_0, SAMPLE_RATE, I2S_BITS_PER_SAMPLE_16BIT, I2S_CHANNEL_MONO);
}

void recordAndStreamAudio() {
  if (!isBMOOn) return; 
  
  if (out) { delete out; out = NULL; }
  
  i2s_adc_init(); 
  i2s_adc_enable(I2S_PORT_0);
  displayMessage("Listening...", "(Hold PTT button)");
  Serial.println("Listening...");

  http.begin(AI_SERVER_URL);
  http.addHeader("Content-Type", "application/octet-stream");
  int httpResponseCode = http.sendRequest("POST", (uint8_t*)i2s_read_buff, 0); 

  size_t bytes_read = 0;
  while (digitalRead(PTT_BUTTON_PIN) == LOW) {
    // Check for power-off command while recording
    if (digitalRead(POWER_BUTTON_PIN) == LOW && (millis() - lastDebounceTime) > debounceDelay) {
        // This is a "hack" to catch a fast turn-off
        break;
    }
    
    esp_err_t err = i2s_read(I2S_PORT_0, (char*)i2s_read_buff, READ_LEN, &bytes_read, (100 / portTICK_RATE_MS));
    
    // --- THIS IS THE FIX ---
    if (err == ESP_OK && bytes_read > 0) { // Changed 'bytesRead' to 'bytes_read'
      http.getStream().write((uint8_t*)i2s_read_buff, bytes_read);
    }
  }

  i2s_adc_disable(I2S_PORT_0);
  i2s_driver_uninstall(I2S_PORT_0); 
  
  Serial.println("Stopped recording.");
  displayMessage("Sending...", "Please wait...");
  
  http.getStream().flush(); 
  http.end(); 

  String responseText = http.getString();
  Serial.print("Server said: ");
  Serial.println(responseText);

  if (responseText.length() > 0) {
    speakMessage(responseText);
  } else {
    speakMessage("I did not understand that.");
  }
}

// =================================================================
// SETUP & LOOP
// =================================================================

void setup() {
  Serial.begin(115200);
  // We only have TWO buttons now
  pinMode(POWER_BUTTON_PIN, INPUT_PULLUP); 
  pinMode(PTT_BUTTON_PIN, INPUT_PULLUP); 

  if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) { 
    Serial.println(F("SSD1306 allocation failed"));
  }
  
  display.clearDisplay();
  display.display();
  Serial.println("BMO is OFF. Press button to start.");
}

void loop() {
  // 1. Read the power button
  int buttonState = digitalRead(POWER_BUTTON_PIN);

  // 2. Check for a state change (the "click")
  if (buttonState != lastButtonState) {
    // Check if enough time has passed (debounce)
    if ((millis() - lastDebounceTime) > debounceDelay) {
      
      // Check if the button was just PRESSED (went from HIGH to LOW)
      if (buttonState == LOW) {
        Serial.println("Button Clicked!");
        // Toggle the state
        isBMOOn = !isBMOOn;
        screenNeedsUpdate = true; // Flag that we need to update
      }
      
      // Reset the debounce timer on ANY change (press or release)
      lastDebounceTime = millis(); 
    }
  }
  lastButtonState = buttonState; // Save the current state for next loop

  // 3. State Machine (runs once per click)
  if (screenNeedsUpdate) {
    if (isBMOOn) {
      // --- "BOOT UP" ---
      Serial.println("Turning ON...");
      displayMessage("Connecting to WiFi...");
      
      WiFi.begin(ssid, password);
      while (WiFi.status() != WL_CONNECTED) { 
          delay(100); 
          Serial.print("."); 
      }
      Serial.println("\nWiFi Connected!");

      drawBMOFace();
      speakMessage("Hello Minh. System online."); 
      drawBMOFace();
    } else {
      // --- "SHUT DOWN" ---
      Serial.println("Turning OFF...");
      WiFi.disconnect(true); 
      display.clearDisplay(); 
      display.display();
    }
    screenNeedsUpdate = false; // Done, wait for next click
  }

  // 4. This is your "gate" for all other functions
  if (isBMOOn) {
    // Check if the PTT button is pressed
    if (digitalRead(PTT_BUTTON_PIN) == LOW) {
      recordAndStreamAudio();
      
      // After speaking, redraw the face
      if (isBMOOn) {
        drawBMOFace();
      } else {
        // If power was clicked off mid-speech, shut down
        display.clearDisplay();
        display.display();
      }
    }
  }
}