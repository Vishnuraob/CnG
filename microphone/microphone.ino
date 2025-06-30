#include <Arduino.h>
#include <SD.h>
#include <SPI.h>
#include "driver/i2s.h"

// === I2S MIC PIN CONFIGURATION ===
#define I2S_WS      25  // LRCLK
#define I2S_SCK     26  // BCLK
#define I2S_SD      22  // DOUT (Data from mic)

#define SD_CS       4   // Change to your SD card CS pin

// === WAV SETTINGS ===
#define SAMPLE_RATE     16000
#define BITS_PER_SAMPLE 16
#define CHANNELS        1
#define RECORD_TIME     10  // seconds

// === BUFFER CONFIG ===
#define BUFFER_SIZE     1024

File audioFile;

// === I2S Configuration ===
i2s_config_t i2s_config = {
  .mode = i2s_mode_t(I2S_MODE_MASTER | I2S_MODE_RX),
  .sample_rate = SAMPLE_RATE,
  .bits_per_sample = i2s_bits_per_sample_t(BITS_PER_SAMPLE),
  .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
  .communication_format = I2S_COMM_FORMAT_I2S_MSB,
  .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
  .dma_buf_count = 4,
  .dma_buf_len = 1024,
  .use_apll = false,
  .tx_desc_auto_clear = false,
  .fixed_mclk = 0
};

i2s_pin_config_t pin_config = {
  .bck_io_num = I2S_SCK,
  .ws_io_num = I2S_WS,
  .data_out_num = I2S_PIN_NO_CHANGE, // Not used for mic
  .data_in_num = I2S_SD
};

// === WAV Header Generator ===
void writeWavHeader(File file, uint32_t sampleRate, uint16_t bitsPerSample, uint16_t channels, uint32_t dataLength) {
  file.seek(0);
  file.write((const uint8_t*)"RIFF", 4);
  uint32_t chunkSize = 36 + dataLength;
  file.write((uint8_t*)&chunkSize, 4);
  file.write((const uint8_t*)"WAVE", 4);
  file.write((const uint8_t*)"fmt ", 4);

  uint32_t subchunk1Size = 16;
  uint16_t audioFormat = 1;

  file.write((uint8_t*)&subchunk1Size, 4);
  file.write((uint8_t*)&audioFormat, 2);
  file.write((uint8_t*)&channels, 2);
  file.write((uint8_t*)&sampleRate, 4);

  uint32_t byteRate = sampleRate * channels * bitsPerSample / 8;
  uint16_t blockAlign = channels * bitsPerSample / 8;

  file.write((uint8_t*)&byteRate, 4);
  file.write((uint8_t*)&blockAlign, 2);
  file.write((uint8_t*)&bitsPerSample, 2);

  file.write((const uint8_t*)"data", 4);
  file.write((uint8_t*)&dataLength, 4);
}

void setup() {
  Serial.begin(115200);

  // Initialize SD card
  if (!SD.begin(SD_CS)) {
    Serial.println("SD card initialization failed!");
    while (true);
  }
  Serial.println("SD card initialized.");

  // Create audio file
  audioFile = SD.open("/record.wav", FILE_WRITE);
  if (!audioFile) {
    Serial.println("Failed to create file");
    while (true);
  }

  // Reserve space for WAV header (will overwrite after recording)
  for (int i = 0; i < 44; i++) audioFile.write((byte)0);

  // Initialize I2S
  i2s_driver_install(I2S_NUM_0, &i2s_config, 0, NULL);
  i2s_set_pin(I2S_NUM_0, &pin_config);
  i2s_zero_dma_buffer(I2S_NUM_0);

  Serial.println("Recording...");

  // Start recording
  size_t bytesWritten;
  uint8_t buffer[BUFFER_SIZE];
  uint32_t totalBytes = 0;
  unsigned long startTime = millis();

  while ((millis() - startTime) < RECORD_TIME * 1000) {
    i2s_read(I2S_NUM_0, &buffer, BUFFER_SIZE, &bytesWritten, portMAX_DELAY);
    audioFile.write(buffer, bytesWritten);
    totalBytes += bytesWritten;
  }

  // Finish recording
  Serial.println("Recording finished.");
  i2s_driver_uninstall(I2S_NUM_0);

  // Update WAV header
  writeWavHeader(audioFile, SAMPLE_RATE, BITS_PER_SAMPLE, CHANNELS, totalBytes);
  audioFile.close();

  Serial.println("WAV file saved to SD card.");
}

void loop() {

}