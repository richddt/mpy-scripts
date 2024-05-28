from micropython import const
import time

# codec ES8316
# everything here copied verbatim from the vendor reference code

STATEconfirm = const(0x4F)

NORMAL_I2S = const(0x00)
NORMAL_LJ = const(0x01)
NORMAL_DSPA = const(0x03)
NORMAL_DSPB = const(0x23)
Format_Len24 = const(0x00)
Format_Len20 = const(0x01)
Format_Len18 = const(0x02)
Format_Len16 = const(0x03)
Format_Len32 = const(0x04)
VDDA_3V3 = const(0x00)
VDDA_1V8 = const(0x01)

# Product master/slave mode selection: default 0 for SlaveMode, set to 1 for
# MasterMode
MSMode_MasterSelOn = const(0)

# Actual Ratio = MCLK/LRCK ratio, needs to match the actual clock proportion
Ratio = const(256)
Format = NORMAL_I2S
Format_Len = Format_Len16

# SCLK division selection: (range 1~18), SCLK = MCLK/SCLK_DIV, specific
# correspondence beyond this range is detailed in the DS
SCLK_DIV = const(4)
# SCLK_DIV = const(8)

# Default alignment method is on the falling edge, 1 for rising edge alignment,
# needs to match the actual timing
SCLK_INV = const(0)

# Single-channel ADC input channel selection between CH1 (MIC1P/1N) or CH2
# (MIC2P/2N)
ADC_MIC1P_MIC1N = const(0)
ADC_MIC2P_MIC2N = const(1)
ADC_MIC1P_DF2SE = const(2)
ADC_MIC2P_DF2SE = const(3)

ADC_Mic = ADC_MIC1P_DF2SE
ADC_AuxIn = ADC_MIC2P_DF2SE

ADCChannelSel = ADC_AuxIn

# Analog voltage selection between 3V3 or 1V8, needs to match the actual
# hardware
VDDA_VOLTAGE = VDDA_3V3

# ADC analog fixed 15dB gain: default off 0, set to 1 to turn on
ADC_PGA_DF2SE_15DB = const(0)

# ADC analog gain: (range 0~10), see DS for specific correspondences
ADC_PGA_GAIN = const(0)

# ADC digital gain: (range 0~192), 0: 0DB, -0.5dB/Step
ADC_Volume = const(0)

# DAC digital gain: (range 0~192), 0: 0DB, -0.5dB/Step
DAC_Volume = const(0)

# DMIC selection: default off 0, set to 1 for stereo, for mono select 2 for H,
# 3 for L
Dmic_Selon = const(0)

I2C_ADDR = const(0x11)


def init(i2c, format_len=Format_Len16, adc_input=ADC_AuxIn):

    i2c.writeto(I2C_ADDR, bytearray([0x00, 0x7F]))
    time.sleep_ms(5)
    i2c.writeto(I2C_ADDR, bytearray([0x00, 0x00]))
    i2c.writeto(I2C_ADDR, bytearray([0x0C, 0xFF]))

    time.sleep_ms(50)

    i2c.writeto(I2C_ADDR, bytearray([0x02, 0x08]))
    i2c.writeto(I2C_ADDR, bytearray([0x03, 0x20]))
    i2c.writeto(I2C_ADDR, bytearray([0x04, 0x11]))
    i2c.writeto(I2C_ADDR, bytearray([0x05, 0x00]))
    i2c.writeto(I2C_ADDR, bytearray([0x06, 0x11]))
    i2c.writeto(I2C_ADDR, bytearray([0x07, 0x00]))
    i2c.writeto(I2C_ADDR, bytearray([0x08, 0x00]))
    i2c.writeto(
        I2C_ADDR,
        bytearray([0x09, (MSMode_MasterSelOn << 7) + (SCLK_INV << 5) + SCLK_DIV]),
    )
    i2c.writeto(I2C_ADDR, bytearray([0x01, 0x7F]))

    i2c.writeto(I2C_ADDR, bytearray([0x1C, 0x0F]))
    i2c.writeto(I2C_ADDR, bytearray([0x1E, 0x90]))
    i2c.writeto(I2C_ADDR, bytearray([0x1F, 0x90]))
    i2c.writeto(I2C_ADDR, bytearray([0x27, ADC_Volume]))
    i2c.writeto(I2C_ADDR, bytearray([0x22, (adc_input << 4)]))
    i2c.writeto(I2C_ADDR, bytearray([0x23, (ADC_PGA_GAIN << 4)]))
    i2c.writeto(I2C_ADDR, bytearray([0x24, ADC_PGA_DF2SE_15DB]))
    i2c.writeto(I2C_ADDR, bytearray([0x25, 0x08 + Dmic_Selon]))
    i2c.writeto(I2C_ADDR, bytearray([0x31, 0x00]))
    i2c.writeto(I2C_ADDR, bytearray([0x32, 0x00]))
    i2c.writeto(I2C_ADDR, bytearray([0x33, DAC_Volume]))
    i2c.writeto(I2C_ADDR, bytearray([0x34, DAC_Volume]))

    i2c.writeto(I2C_ADDR, bytearray([0x0A, Format + (format_len << 2)]))
    i2c.writeto(I2C_ADDR, bytearray([0x0B, Format + (format_len << 2)]))
    i2c.writeto(
        I2C_ADDR, bytearray([0x10, 0x12 + (0x0C * VDDA_VOLTAGE) - VDDA_VOLTAGE])
    )
    i2c.writeto(I2C_ADDR, bytearray([0x11, 0xFC]))
    i2c.writeto(I2C_ADDR, bytearray([0x12, 0x28]))
    i2c.writeto(I2C_ADDR, bytearray([0x0E, 0x04]))
    i2c.writeto(I2C_ADDR, bytearray([0x0F, 0x0C]))
    i2c.writeto(I2C_ADDR, bytearray([0x0F, 0x00]))

    i2c.writeto(I2C_ADDR, bytearray([0x2F, 0x00]))
    i2c.writeto(I2C_ADDR, bytearray([0x13, 0x00]))
    i2c.writeto(I2C_ADDR, bytearray([0x14, 0x88]))
    i2c.writeto(I2C_ADDR, bytearray([0x15, 0x44]))
    i2c.writeto(I2C_ADDR, bytearray([0x16, 0xBB]))
    i2c.writeto(I2C_ADDR, bytearray([0x1A, 0x10]))
    i2c.writeto(I2C_ADDR, bytearray([0x1B, 0x30]))
    i2c.writeto(I2C_ADDR, bytearray([0x19, 0x00]))
    i2c.writeto(I2C_ADDR, bytearray([0x18, 0x00]))
    i2c.writeto(I2C_ADDR, bytearray([0x4D, 0x00]))
    i2c.writeto(I2C_ADDR, bytearray([0x4E, 0x02]))
    i2c.writeto(I2C_ADDR, bytearray([0x50, 0xA0]))
    i2c.writeto(I2C_ADDR, bytearray([0x51, 0x00]))
    i2c.writeto(I2C_ADDR, bytearray([0x52, 0x00]))
    i2c.writeto(I2C_ADDR, bytearray([0x0D, 0x00]))
    i2c.writeto(I2C_ADDR, bytearray([0x00, 0xC0]))

    time.sleep_ms(100)

    i2c.writeto(I2C_ADDR, bytearray([0x17, 0x66]))

    # I'm not sure why, but this seems to resolve the
    # issue with the codec randomly not initing properly.
    # I guess we can't send I2S data for a bit after config
    time.sleep_ms(500)


def dumpregisters(i2c):
    # registers = i2c.readfrom_mem(I2C_ADDR, 0x00, 0x50)
    for i in range(0x50):
        res = i2c.readfrom_mem(I2C_ADDR, i, 1)
        print("0x%02X: 0x%s" % (i, res.hex()))
