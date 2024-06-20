from machine import SPI, I2C, Pin, I2S
import fern
import codec
import nfc
import asyncio
import espnow
import time
import network
import mixer
from tween import tween
from debounced_input import DebouncedInput

TAG_SCANNED_WINDOW = 3000  # 3 seconds
AUDIO_CROSSFADE_TIME = 0.5

# pixelblaze GPIO
PixelBlazePin1 = Pin(fern.D1, Pin.OUT)
PixelBlazePin2 = Pin(fern.D2, Pin.OUT)
PixelBlazePin3 = Pin(fern.D3, Pin.OUT)

PixelBlazePin1.value(0)
PixelBlazePin2.value(0)
PixelBlazePin3.value(0)

print("init D1 =", PixelBlazePin1.value())
print("init D2 =", PixelBlazePin2.value())
print("init D3 =", PixelBlazePin3.value())


# ----------------------------------------------------------------------------

# list of (combo, path, pixelblaze pattern)
# eg,: (set(["id1-greenGoal", "id2-blueFocus", "id3-goldLuck/Water"]), "path1", 1),

tag_combos = [
    (
        [
            ["2e8f3144080104e0", "808b3144080104e0", "6c773144080104e0"],
            ["afa83144080104e0", "0f633144080104e0", "6d541466080104e0"],
            [
                "d7f11366080104e0",
                "cc331466080104e0",
                "06e71366080104e0",
                "af1e1466080104e0",
                "20131466080104e0",
                "a3071466080104e0",
                "3a2a1466080104e0",
                "46dc3144080104e0",
                "13df3144080104e0",
            ],
        ],
        "/sd/1_DeepOcean.wav",
        1,
    ),
    (
        [
            ["2e8f3144080104e0", "808b3144080104e0", "6c773144080104e0"],
            ["88693144080104e0", "ed9b3144080104e0", "493f1466080104e0"],
            [
                "d7f11366080104e0",
                "cc331466080104e0",
                "06e71366080104e0",
                "af1e1466080104e0",
                "20131466080104e0",
                "a3071466080104e0",
                "3a2a1466080104e0",
                "46dc3144080104e0",
                "13df3144080104e0",
            ],
        ],
        "/sd/2_Crickets.wav",
        2,
    ),
    (
        [
            ["2e8f3144080104e0", "808b3144080104e0", "6c773144080104e0"],
            ["05953144080104e0", "d26a1466080104e0"],
            [
                "d7f11366080104e0",
                "cc331466080104e0",
                "06e71366080104e0",
                "af1e1466080104e0",
                "20131466080104e0",
                "a3071466080104e0",
                "3a2a1466080104e0",
                "46dc3144080104e0",
                "13df3144080104e0",
            ],
        ],
        "/sd/3_Rainy.wav",
        3,
    ),
    (
        [
            ["2e8f3144080104e0", "808b3144080104e0", "6c773144080104e0"],
            ["ea8d3144080104e0", "c5783144080104e0"],
            [
                "d7f11366080104e0",
                "cc331466080104e0",
                "06e71366080104e0",
                "af1e1466080104e0",
                "20131466080104e0",
                "a3071466080104e0",
                "3a2a1466080104e0",
                "46dc3144080104e0",
                "13df3144080104e0",
            ],
        ],
        "/sd/4_Coqui.wav",
        4,
    ),
    (
        [
            ["2e8f3144080104e0", "808b3144080104e0", "6c773144080104e0"],
            ["75803144080104e0", "9a863144080104e0"],
            [
                "d7f11366080104e0",
                "cc331466080104e0",
                "06e71366080104e0",
                "af1e1466080104e0",
                "20131466080104e0",
                "a3071466080104e0",
                "3a2a1466080104e0",
                "46dc3144080104e0",
                "13df3144080104e0",
            ],
        ],
        "/sd/5_Thunderstorm.wav",
        5,
    ),
    (
        [
            ["2e8f3144080104e0", "808b3144080104e0", "6c773144080104e0"],
            ["207f3144080104e0", "e3873144080104e0"],
            [
                "d7f11366080104e0",
                "cc331466080104e0",
                "06e71366080104e0",
                "af1e1466080104e0",
                "20131466080104e0",
                "a3071466080104e0",
                "3a2a1466080104e0",
                "46dc3144080104e0",
                "13df3144080104e0",
            ],
        ],
        "/sd/6_Wolf.wav",
        6,
    ),
    (
        [
            ["b7923144080104e0", "c86f3144080104e0", "3e963144080104e0"],
            ["afa83144080104e0", "0f633144080104e0", "6d541466080104e0"],
            [
                "d7f11366080104e0",
                "cc331466080104e0",
                "06e71366080104e0",
                "af1e1466080104e0",
                "20131466080104e0",
                "a3071466080104e0",
                "3a2a1466080104e0",
                "46dc3144080104e0",
                "13df3144080104e0",
            ],
        ],
        "/sd/7_Lush.wav",
        1,
    ),
    (
        [
            ["b7923144080104e0", "c86f3144080104e0", "3e963144080104e0"],
            ["88693144080104e0", "ed9b3144080104e0", "493f1466080104e0"],
            [
                "d7f11366080104e0",
                "cc331466080104e0",
                "06e71366080104e0",
                "af1e1466080104e0",
                "20131466080104e0",
                "a3071466080104e0",
                "3a2a1466080104e0",
                "46dc3144080104e0",
                "13df3144080104e0",
            ],
        ],
        "/sd/8_UnderTheSea.wav",
        2,
    ),
    (
        [
            ["b7923144080104e0", "c86f3144080104e0", "3e963144080104e0"],
            ["05953144080104e0", "d26a1466080104e0"],
            [
                "d7f11366080104e0",
                "cc331466080104e0",
                "06e71366080104e0",
                "af1e1466080104e0",
                "20131466080104e0",
                "a3071466080104e0",
                "3a2a1466080104e0",
                "46dc3144080104e0",
                "13df3144080104e0",
            ],
        ],
        "/sd/9_Aquarium.wav",
        3,
    ),
    (
        [
            ["b7923144080104e0", "c86f3144080104e0", "3e963144080104e0"],
            ["ea8d3144080104e0", "c5783144080104e0"],
            [
                "d7f11366080104e0",
                "cc331466080104e0",
                "06e71366080104e0",
                "af1e1466080104e0",
                "20131466080104e0",
                "a3071466080104e0",
                "3a2a1466080104e0",
                "46dc3144080104e0",
                "13df3144080104e0",
            ],
        ],
        "/sd/10_Idea.wav",
        4,
    ),
    (
        [
            ["b7923144080104e0", "c86f3144080104e0", "3e963144080104e0"],
            ["75803144080104e0", "9a863144080104e0"],
            [
                "d7f11366080104e0",
                "cc331466080104e0",
                "06e71366080104e0",
                "af1e1466080104e0",
                "20131466080104e0",
                "a3071466080104e0",
                "3a2a1466080104e0",
                "46dc3144080104e0",
                "13df3144080104e0",
            ],
        ],
        "/sd/11_WeWereInLove.wav",
        5,
    ),
    (
        [
            ["b7923144080104e0", "c86f3144080104e0", "3e963144080104e0"],
            ["207f3144080104e0", "e3873144080104e0"],
            [
                "d7f11366080104e0",
                "cc331466080104e0",
                "06e71366080104e0",
                "af1e1466080104e0",
                "20131466080104e0",
                "a3071466080104e0",
                "3a2a1466080104e0",
                "46dc3144080104e0",
                "13df3144080104e0",
            ],
        ],
        "/sd/12_Remnants.wav",
        6,
    ),
    (
        [
            ["aa993144080104e0", "69a23144080104e0", "0d611466080104e0"],
            ["afa83144080104e0", "0f633144080104e0", "6d541466080104e0"],
            [
                "d7f11366080104e0",
                "cc331466080104e0",
                "06e71366080104e0",
                "af1e1466080104e0",
                "20131466080104e0",
                "a3071466080104e0",
                "3a2a1466080104e0",
                "46dc3144080104e0",
                "13df3144080104e0",
            ],
        ],
        "/sd/13_Bassara.wav",
        1,
    ),
    (
        [
            ["aa993144080104e0", "69a23144080104e0", "0d611466080104e0"],
            ["88693144080104e0", "ed9b3144080104e0", "493f1466080104e0"],
            [
                "d7f11366080104e0",
                "cc331466080104e0",
                "06e71366080104e0",
                "af1e1466080104e0",
                "20131466080104e0",
                "a3071466080104e0",
                "3a2a1466080104e0",
                "46dc3144080104e0",
                "13df3144080104e0",
            ],
        ],
        "/sd/14_BlueArcher.wav",
        2,
    ),
    (
        [
            ["aa993144080104e0", "69a23144080104e0", "0d611466080104e0"],
            ["05953144080104e0", "d26a1466080104e0"],
            [
                "d7f11366080104e0",
                "cc331466080104e0",
                "06e71366080104e0",
                "af1e1466080104e0",
                "20131466080104e0",
                "a3071466080104e0",
                "3a2a1466080104e0",
                "46dc3144080104e0",
                "13df3144080104e0",
            ],
        ],
        "/sd/15_GoldenTriangle.wav",
        3,
    ),
    (
        [
            ["aa993144080104e0", "69a23144080104e0", "0d611466080104e0"],
            ["ea8d3144080104e0", "c5783144080104e0"],
            [
                "d7f11366080104e0",
                "cc331466080104e0",
                "06e71366080104e0",
                "af1e1466080104e0",
                "20131466080104e0",
                "a3071466080104e0",
                "3a2a1466080104e0",
                "46dc3144080104e0",
                "13df3144080104e0",
            ],
        ],
        "/sd/16_Bubbles.wav",
        4,
    ),
    (
        [
            ["aa993144080104e0", "69a23144080104e0", "0d611466080104e0"],
            ["75803144080104e0", "9a863144080104e0"],
            [
                "d7f11366080104e0",
                "cc331466080104e0",
                "06e71366080104e0",
                "af1e1466080104e0",
                "20131466080104e0",
                "a3071466080104e0",
                "3a2a1466080104e0",
                "46dc3144080104e0",
                "13df3144080104e0",
            ],
        ],
        "/sd/17_KoopIsland.wav",
        5,
    ),
    (
        [
            ["aa993144080104e0", "69a23144080104e0", "0d611466080104e0"],
            ["207f3144080104e0", "e3873144080104e0"],
            [
                "d7f11366080104e0",
                "cc331466080104e0",
                "06e71366080104e0",
                "af1e1466080104e0",
                "20131466080104e0",
                "a3071466080104e0",
                "3a2a1466080104e0",
                "46dc3144080104e0",
                "13df3144080104e0",
            ],
        ],
        "/sd/18_Bonus.wav",
        6,
    ),
    (
        [
            ["1a9d3144080104e0", "4ca03144080104e0", "be761466080104e0"],
            ["afa83144080104e0", "0f633144080104e0", "6d541466080104e0"],
            [
                "d7f11366080104e0",
                "cc331466080104e0",
                "06e71366080104e0",
                "af1e1466080104e0",
                "20131466080104e0",
                "a3071466080104e0",
                "3a2a1466080104e0",
                "46dc3144080104e0",
                "13df3144080104e0",
            ],
        ],
        "/sd/19_AqueousTrans.wav",
        1,
    ),
    (
        [
            ["1a9d3144080104e0", "4ca03144080104e0", "be761466080104e0"],
            ["88693144080104e0", "ed9b3144080104e0", "493f1466080104e0"],
            [
                "d7f11366080104e0",
                "cc331466080104e0",
                "06e71366080104e0",
                "af1e1466080104e0",
                "20131466080104e0",
                "a3071466080104e0",
                "3a2a1466080104e0",
                "46dc3144080104e0",
                "13df3144080104e0",
            ],
        ],
        "/sd/20_EthnoCut.wav",
        2,
    ),
    (
        [
            ["1a9d3144080104e0", "4ca03144080104e0", "be761466080104e0"],
            ["05953144080104e0", "d26a1466080104e0"],
            [
                "d7f11366080104e0",
                "cc331466080104e0",
                "06e71366080104e0",
                "af1e1466080104e0",
                "20131466080104e0",
                "a3071466080104e0",
                "3a2a1466080104e0",
                "46dc3144080104e0",
                "13df3144080104e0",
            ],
        ],
        "/sd/21_BeyondTheSea.wav",
        3,
    ),
    (
        [
            ["1a9d3144080104e0", "4ca03144080104e0", "be761466080104e0"],
            ["ea8d3144080104e0", "c5783144080104e0"],
            [
                "d7f11366080104e0",
                "cc331466080104e0",
                "06e71366080104e0",
                "af1e1466080104e0",
                "20131466080104e0",
                "a3071466080104e0",
                "3a2a1466080104e0",
                "46dc3144080104e0",
                "13df3144080104e0",
            ],
        ],
        "/sd/22_Floating.wav",
        4,
    ),
    (
        [
            ["1a9d3144080104e0", "4ca03144080104e0", "be761466080104e0"],
            ["75803144080104e0", "9a863144080104e0"],
            [
                "d7f11366080104e0",
                "cc331466080104e0",
                "06e71366080104e0",
                "af1e1466080104e0",
                "20131466080104e0",
                "a3071466080104e0",
                "3a2a1466080104e0",
                "46dc3144080104e0",
                "13df3144080104e0",
            ],
        ],
        "/sd/23_ToTheRiver.wav",
        5,
    ),
    (
        [
            ["1a9d3144080104e0", "4ca03144080104e0", "be761466080104e0"],
            ["207f3144080104e0", "e3873144080104e0"],
            [
                "d7f11366080104e0",
                "cc331466080104e0",
                "06e71366080104e0",
                "af1e1466080104e0",
                "20131466080104e0",
                "a3071466080104e0",
                "3a2a1466080104e0",
                "46dc3144080104e0",
                "13df3144080104e0",
            ],
        ],
        "/sd/24_CryMeARiver.wav",
        6,
    ),
    (
        [
            ["3b5b3144080104e0", "d6ae3144080104e0", "b2821466080104e0"],
            ["afa83144080104e0", "0f633144080104e0", "6d541466080104e0"],
            [
                "d7f11366080104e0",
                "cc331466080104e0",
                "06e71366080104e0",
                "af1e1466080104e0",
                "20131466080104e0",
                "a3071466080104e0",
                "3a2a1466080104e0",
                "46dc3144080104e0",
                "13df3144080104e0",
            ],
        ],
        "/sd/25_Blue.wav",
        1,
    ),
    (
        [
            ["3b5b3144080104e0", "d6ae3144080104e0", "b2821466080104e0"],
            ["88693144080104e0", "ed9b3144080104e0", "493f1466080104e0"],
            [
                "d7f11366080104e0",
                "cc331466080104e0",
                "06e71366080104e0",
                "af1e1466080104e0",
                "20131466080104e0",
                "a3071466080104e0",
                "3a2a1466080104e0",
                "46dc3144080104e0",
                "13df3144080104e0",
            ],
        ],
        "/sd/26_NotAshamed.wav",
        2,
    ),
    (
        [
            ["3b5b3144080104e0", "d6ae3144080104e0", "b2821466080104e0"],
            ["05953144080104e0", "d26a1466080104e0"],
            [
                "d7f11366080104e0",
                "cc331466080104e0",
                "06e71366080104e0",
                "af1e1466080104e0",
                "20131466080104e0",
                "a3071466080104e0",
                "3a2a1466080104e0",
                "46dc3144080104e0",
                "13df3144080104e0",
            ],
        ],
        "/sd/27_Superdream.wav",
        3,
    ),
    (
        [
            ["3b5b3144080104e0", "d6ae3144080104e0", "b2821466080104e0"],
            ["ea8d3144080104e0", "c5783144080104e0"],
            [
                "d7f11366080104e0",
                "cc331466080104e0",
                "06e71366080104e0",
                "af1e1466080104e0",
                "20131466080104e0",
                "a3071466080104e0",
                "3a2a1466080104e0",
                "46dc3144080104e0",
                "13df3144080104e0",
            ],
        ],
        "/sd/28_FloatOn.wav",
        4,
    ),
    (
        [
            ["3b5b3144080104e0", "d6ae3144080104e0", "b2821466080104e0"],
            ["75803144080104e0", "9a863144080104e0"],
            [
                "d7f11366080104e0",
                "cc331466080104e0",
                "06e71366080104e0",
                "af1e1466080104e0",
                "20131466080104e0",
                "a3071466080104e0",
                "3a2a1466080104e0",
                "46dc3144080104e0",
                "13df3144080104e0",
            ],
        ],
        "/sd/29_Asteroid.wav",
        5,
    ),
    (
        [
            ["3b5b3144080104e0", "d6ae3144080104e0", "b2821466080104e0"],
            ["207f3144080104e0", "e3873144080104e0"],
            [
                "d7f11366080104e0",
                "cc331466080104e0",
                "06e71366080104e0",
                "af1e1466080104e0",
                "20131466080104e0",
                "a3071466080104e0",
                "3a2a1466080104e0",
                "46dc3144080104e0",
                "13df3144080104e0",
            ],
        ],
        "/sd/30_Iron.wav",
        6,
    ),
    (
        [
            ["2e8f3144080104e0", "808b3144080104e0", "6c773144080104e0"],
            ["afa83144080104e0", "0f633144080104e0", "6d541466080104e0"],
            [
                "d8743144080104e0",
                "26843144080104e0",
                "4f6d3144080104e0",
                "cc5d3144080104e0",
                "9b653144080104e0",
                "947c3144080104e0",
                "d04a1466080104e0",
            ],
        ],
        "/sd/31_WaterPalace.wav",
        1,
    ),
    (
        [
            ["2e8f3144080104e0", "808b3144080104e0", "6c773144080104e0"],
            ["88693144080104e0", "ed9b3144080104e0", "493f1466080104e0"],
            [
                "d8743144080104e0",
                "26843144080104e0",
                "4f6d3144080104e0",
                "cc5d3144080104e0",
                "9b653144080104e0",
                "947c3144080104e0",
                "d04a1466080104e0",
            ],
        ],
        "/sd/32_Significance.wav",
        2,
    ),
    (
        [
            ["2e8f3144080104e0", "808b3144080104e0", "6c773144080104e0"],
            ["05953144080104e0", "d26a1466080104e0"],
            [
                "d8743144080104e0",
                "26843144080104e0",
                "4f6d3144080104e0",
                "cc5d3144080104e0",
                "9b653144080104e0",
                "947c3144080104e0",
                "d04a1466080104e0",
            ],
        ],
        "/sd/33_ImpossibleWorlds.wav",
        3,
    ),
    (
        [
            ["2e8f3144080104e0", "808b3144080104e0", "6c773144080104e0"],
            ["ea8d3144080104e0", "c5783144080104e0"],
            [
                "d8743144080104e0",
                "26843144080104e0",
                "4f6d3144080104e0",
                "cc5d3144080104e0",
                "9b653144080104e0",
                "947c3144080104e0",
                "d04a1466080104e0",
            ],
        ],
        "/sd/34_ForestKingdom.wav",
        4,
    ),
    (
        [
            ["2e8f3144080104e0", "808b3144080104e0", "6c773144080104e0"],
            ["75803144080104e0", "9a863144080104e0"],
            [
                "d8743144080104e0",
                "26843144080104e0",
                "4f6d3144080104e0",
                "cc5d3144080104e0",
                "9b653144080104e0",
                "947c3144080104e0",
                "d04a1466080104e0",
            ],
        ],
        "/sd/35_CityRuins.wav",
        5,
    ),
    (
        [
            ["2e8f3144080104e0", "808b3144080104e0", "6c773144080104e0"],
            ["207f3144080104e0", "e3873144080104e0"],
            [
                "d8743144080104e0",
                "26843144080104e0",
                "4f6d3144080104e0",
                "cc5d3144080104e0",
                "9b653144080104e0",
                "947c3144080104e0",
                "d04a1466080104e0",
            ],
        ],
        "/sd/36_FUYA.wav",
        6,
    ),
    (
        [
            ["b7923144080104e0", "c86f3144080104e0", "3e963144080104e0"],
            ["afa83144080104e0", "0f633144080104e0", "6d541466080104e0"],
            [
                "d8743144080104e0",
                "26843144080104e0",
                "4f6d3144080104e0",
                "cc5d3144080104e0",
                "9b653144080104e0",
                "947c3144080104e0",
                "d04a1466080104e0",
            ],
        ],
        "/sd/37_SimpleGifts.wav",
        1,
    ),
    (
        [
            ["b7923144080104e0", "c86f3144080104e0", "3e963144080104e0"],
            ["88693144080104e0", "ed9b3144080104e0", "493f1466080104e0"],
            [
                "d8743144080104e0",
                "26843144080104e0",
                "4f6d3144080104e0",
                "cc5d3144080104e0",
                "9b653144080104e0",
                "947c3144080104e0",
                "d04a1466080104e0",
            ],
        ],
        "/sd/38_CuteCircus.wav",
        2,
    ),
    (
        [
            ["b7923144080104e0", "c86f3144080104e0", "3e963144080104e0"],
            ["05953144080104e0", "d26a1466080104e0"],
            [
                "d8743144080104e0",
                "26843144080104e0",
                "4f6d3144080104e0",
                "cc5d3144080104e0",
                "9b653144080104e0",
                "947c3144080104e0",
                "d04a1466080104e0",
            ],
        ],
        "/sd/39_VicoNagori.wav",
        3,
    ),
    (
        [
            ["b7923144080104e0", "c86f3144080104e0", "3e963144080104e0"],
            ["ea8d3144080104e0", "c5783144080104e0"],
            [
                "d8743144080104e0",
                "26843144080104e0",
                "4f6d3144080104e0",
                "cc5d3144080104e0",
                "9b653144080104e0",
                "947c3144080104e0",
                "d04a1466080104e0",
            ],
        ],
        "/sd/40_SoulIsland.wav",
        4,
    ),
    (
        [
            ["b7923144080104e0", "c86f3144080104e0", "3e963144080104e0"],
            ["75803144080104e0", "9a863144080104e0"],
            [
                "d8743144080104e0",
                "26843144080104e0",
                "4f6d3144080104e0",
                "cc5d3144080104e0",
                "9b653144080104e0",
                "947c3144080104e0",
                "d04a1466080104e0",
            ],
        ],
        "/sd/41_Sweetwater.wav",
        5,
    ),
    (
        [
            ["b7923144080104e0", "c86f3144080104e0", "3e963144080104e0"],
            ["207f3144080104e0", "e3873144080104e0"],
            [
                "d8743144080104e0",
                "26843144080104e0",
                "4f6d3144080104e0",
                "cc5d3144080104e0",
                "9b653144080104e0",
                "947c3144080104e0",
                "d04a1466080104e0",
            ],
        ],
        "/sd/42_HowLong.wav",
        6,
    ),
    (
        [
            ["aa993144080104e0", "69a23144080104e0", "0d611466080104e0"],
            ["afa83144080104e0", "0f633144080104e0", "6d541466080104e0"],
            [
                "d8743144080104e0",
                "26843144080104e0",
                "4f6d3144080104e0",
                "cc5d3144080104e0",
                "9b653144080104e0",
                "947c3144080104e0",
                "d04a1466080104e0",
            ],
        ],
        "/sd/43_Shasha.wav",
        1,
    ),
    (
        [
            ["aa993144080104e0", "69a23144080104e0", "0d611466080104e0"],
            ["88693144080104e0", "ed9b3144080104e0", "493f1466080104e0"],
            [
                "d8743144080104e0",
                "26843144080104e0",
                "4f6d3144080104e0",
                "cc5d3144080104e0",
                "9b653144080104e0",
                "947c3144080104e0",
                "d04a1466080104e0",
            ],
        ],
        "/sd/44_StreamBeats.wav",
        2,
    ),
    (
        [
            ["aa993144080104e0", "69a23144080104e0", "0d611466080104e0"],
            ["05953144080104e0", "d26a1466080104e0"],
            [
                "d8743144080104e0",
                "26843144080104e0",
                "4f6d3144080104e0",
                "cc5d3144080104e0",
                "9b653144080104e0",
                "947c3144080104e0",
                "d04a1466080104e0",
            ],
        ],
        "/sd/45_Overhead.wav",
        3,
    ),
    (
        [
            ["aa993144080104e0", "69a23144080104e0", "0d611466080104e0"],
            ["ea8d3144080104e0", "c5783144080104e0"],
            [
                "d8743144080104e0",
                "26843144080104e0",
                "4f6d3144080104e0",
                "cc5d3144080104e0",
                "9b653144080104e0",
                "947c3144080104e0",
                "d04a1466080104e0",
            ],
        ],
        "/sd/46_Wriggle.wav",
        4,
    ),
    (
        [
            ["aa993144080104e0", "69a23144080104e0", "0d611466080104e0"],
            ["75803144080104e0", "9a863144080104e0"],
            [
                "d8743144080104e0",
                "26843144080104e0",
                "4f6d3144080104e0",
                "cc5d3144080104e0",
                "9b653144080104e0",
                "947c3144080104e0",
                "d04a1466080104e0",
            ],
        ],
        "/sd/47_Animals.wav",
        5,
    ),
    (
        [
            ["aa993144080104e0", "69a23144080104e0", "0d611466080104e0"],
            ["207f3144080104e0", "e3873144080104e0"],
            [
                "d8743144080104e0",
                "26843144080104e0",
                "4f6d3144080104e0",
                "cc5d3144080104e0",
                "9b653144080104e0",
                "947c3144080104e0",
                "d04a1466080104e0",
            ],
        ],
        "/sd/48_Sweat.wav",
        6,
    ),
    (
        [
            ["1a9d3144080104e0", "4ca03144080104e0", "be761466080104e0"],
            ["afa83144080104e0", "0f633144080104e0", "6d541466080104e0"],
            [
                "d8743144080104e0",
                "26843144080104e0",
                "4f6d3144080104e0",
                "cc5d3144080104e0",
                "9b653144080104e0",
                "947c3144080104e0",
                "d04a1466080104e0",
            ],
        ],
        "/sd/49_WickedWinds.wav",
        1,
    ),
    (
        [
            ["1a9d3144080104e0", "4ca03144080104e0", "be761466080104e0"],
            ["88693144080104e0", "ed9b3144080104e0", "493f1466080104e0"],
            [
                "d8743144080104e0",
                "26843144080104e0",
                "4f6d3144080104e0",
                "cc5d3144080104e0",
                "9b653144080104e0",
                "947c3144080104e0",
                "d04a1466080104e0",
            ],
        ],
        "/sd/50_Marrakech.wav",
        2,
    ),
    (
        [
            ["1a9d3144080104e0", "4ca03144080104e0", "be761466080104e0"],
            ["05953144080104e0", "d26a1466080104e0"],
            [
                "d8743144080104e0",
                "26843144080104e0",
                "4f6d3144080104e0",
                "cc5d3144080104e0",
                "9b653144080104e0",
                "947c3144080104e0",
                "d04a1466080104e0",
            ],
        ],
        "/sd/51_Infinite.wav",
        3,
    ),
    (
        [
            ["1a9d3144080104e0", "4ca03144080104e0", "be761466080104e0"],
            ["ea8d3144080104e0", "c5783144080104e0"],
            [
                "d8743144080104e0",
                "26843144080104e0",
                "4f6d3144080104e0",
                "cc5d3144080104e0",
                "9b653144080104e0",
                "947c3144080104e0",
                "d04a1466080104e0",
            ],
        ],
        "/sd/52_Phenomenal.wav",
        4,
    ),
    (
        [
            ["1a9d3144080104e0", "4ca03144080104e0", "be761466080104e0"],
            ["75803144080104e0", "9a863144080104e0"],
            [
                "d8743144080104e0",
                "26843144080104e0",
                "4f6d3144080104e0",
                "cc5d3144080104e0",
                "9b653144080104e0",
                "947c3144080104e0",
                "d04a1466080104e0",
            ],
        ],
        "/sd/53_Point.wav",
        5,
    ),
    (
        [
            ["1a9d3144080104e0", "4ca03144080104e0", "be761466080104e0"],
            ["207f3144080104e0", "e3873144080104e0"],
            [
                "d8743144080104e0",
                "26843144080104e0",
                "4f6d3144080104e0",
                "cc5d3144080104e0",
                "9b653144080104e0",
                "947c3144080104e0",
                "d04a1466080104e0",
            ],
        ],
        "/sd/54_ItsBecause.wav",
        6,
    ),
    (
        [
            ["3b5b3144080104e0", "d6ae3144080104e0", "b2821466080104e0"],
            ["afa83144080104e0", "0f633144080104e0", "6d541466080104e0"],
            [
                "d8743144080104e0",
                "26843144080104e0",
                "4f6d3144080104e0",
                "cc5d3144080104e0",
                "9b653144080104e0",
                "947c3144080104e0",
                "d04a1466080104e0",
            ],
        ],
        "/sd/55_StuckDream.wav",
        1,
    ),
    (
        [
            ["3b5b3144080104e0", "d6ae3144080104e0", "b2821466080104e0"],
            ["88693144080104e0", "ed9b3144080104e0", "493f1466080104e0"],
            [
                "d8743144080104e0",
                "26843144080104e0",
                "4f6d3144080104e0",
                "cc5d3144080104e0",
                "9b653144080104e0",
                "947c3144080104e0",
                "d04a1466080104e0",
            ],
        ],
        "/sd/56_Limitless.wav",
        2,
    ),
    (
        [
            ["3b5b3144080104e0", "d6ae3144080104e0", "b2821466080104e0"],
            ["05953144080104e0", "d26a1466080104e0"],
            [
                "d8743144080104e0",
                "26843144080104e0",
                "4f6d3144080104e0",
                "cc5d3144080104e0",
                "9b653144080104e0",
                "947c3144080104e0",
                "d04a1466080104e0",
            ],
        ],
        "/sd/57_SevenEleven.wav",
        3,
    ),
    (
        [
            ["3b5b3144080104e0", "d6ae3144080104e0", "b2821466080104e0"],
            ["ea8d3144080104e0", "c5783144080104e0"],
            [
                "d8743144080104e0",
                "26843144080104e0",
                "4f6d3144080104e0",
                "cc5d3144080104e0",
                "9b653144080104e0",
                "947c3144080104e0",
                "d04a1466080104e0",
            ],
        ],
        "/sd/58_Krane.wav",
        4,
    ),
    (
        [
            ["3b5b3144080104e0", "d6ae3144080104e0", "b2821466080104e0"],
            ["75803144080104e0", "9a863144080104e0"],
            [
                "d8743144080104e0",
                "26843144080104e0",
                "4f6d3144080104e0",
                "cc5d3144080104e0",
                "9b653144080104e0",
                "947c3144080104e0",
                "d04a1466080104e0",
            ],
        ],
        "/sd/59_MoonlightSonata.wav",
        5,
    ),
    (
        [
            ["3b5b3144080104e0", "d6ae3144080104e0", "b2821466080104e0"],
            ["207f3144080104e0", "e3873144080104e0"],
            [
                "d8743144080104e0",
                "26843144080104e0",
                "4f6d3144080104e0",
                "cc5d3144080104e0",
                "9b653144080104e0",
                "947c3144080104e0",
                "d04a1466080104e0",
            ],
        ],
        "/sd/60_LaZarra.wav",
        6,
    ),
    (
        [
            [
                "d8743144080104e0",
                "26843144080104e0",
                "4f6d3144080104e0",
                "cc5d3144080104e0",
                "9b653144080104e0",
                "947c3144080104e0",
                "d04a1466080104e0",
            ],
            [
                "d8743144080104e0",
                "26843144080104e0",
                "4f6d3144080104e0",
                "cc5d3144080104e0",
                "9b653144080104e0",
                "947c3144080104e0",
                "d04a1466080104e0",
            ],
            [
                "d8743144080104e0",
                "26843144080104e0",
                "4f6d3144080104e0",
                "cc5d3144080104e0",
                "9b653144080104e0",
                "947c3144080104e0",
                "d04a1466080104e0",
            ],
        ],
        "/sd/61_LuckyBastard.wav",
        6,
    ),
]


# ----------------------------------------------------------------------------

# keep track of tags from all controllers. dictionary keyed by controller id, value is tag id & timestamp
tags = {}

# our ESPNow broadcaster. We broadcast scanned tags to all listening controllers
broadcaster = espnow.ESPNow()
bcast = b"\xFF" * 6

audio_enabled = False

try:
    fern.mount_sdcard()
    m = mixer.Mixer()
    VoiceBG = mixer.Voice("/sd/0_JapGarden.wav")
    VoiceBG.loop = True
    audio_enabled = True
except Exception as e:
    print("No SD card found, no audio support on this device")

active_voice_path = None
VoiceActive = None
ActiveVolume = tween(0)


# set 3x PixelBlaze GPIO pins, based on 3-byte values (HIGH=1, LOW=0)
def play_pixelblaze_pattern(pattern):
    p1, p2, p3 = {
        0: (0, 0, 0),
        1: (0, 0, 1),
        2: (0, 1, 0),
        3: (0, 1, 1),
        4: (1, 0, 0),
        5: (1, 0, 1),
        6: (1, 1, 0),
        7: (1, 1, 1),
    }.get(pattern, (0, 0, 0))

    PixelBlazePin1.value(p1)
    PixelBlazePin2.value(p2)
    PixelBlazePin3.value(p3)

    # debug PIN values
    # print("D1 =", PixelBlazePin1.value())
    # print("D2 =", PixelBlazePin2.value())
    # print("D3 =", PixelBlazePin3.value())


def play_active_sound(path):
    if not audio_enabled:
        return

    global VoiceActive, active_voice_path

    if active_voice_path == path:
        return
    active_voice_path = path

    if VoiceActive:
        VoiceActive.stop()
    VoiceActive = mixer.Voice(path)
    VoiceActive.loop = True
    VoiceActive.volume = 0.0
    m.play(VoiceActive)

    # crossfade to active sound over 0.5 second
    ActiveVolume.tween(1.0, AUDIO_CROSSFADE_TIME)


# def is_match(tags, combo):
#     # tags is [1,2,3], combo is list where some items are also a list [1,2,[3,4]]
#     for tag in tags:
#         if not any([tag in c for c in combo]):
#             return False
#     return True


def is_match(tags, combo):
    found = set()
    # tags is [1,2,3], combo is list where some items are also a list [1,2,[3,4]]
    for tag in tags:
        is_this_tag_bueno = False
        for i, c in enumerate(combo):
            if tag in c:
                is_this_tag_bueno = True
                found.add(i)
        if not is_this_tag_bueno:
            return False

    # it's a match if the tags are in distinct groups
    return len(tags) == len(found)


# gets called when a tag is scanned locally, or remotely via ESPNow. Gets called with
# tag_id=None when a tag is lost
def tag_scanned(controller_id, tag_id):
    global active_voice_path

    if tag_id == "00":
        tag_id = None

    tags[controller_id] = (tag_id, time.ticks_ms())

    if tag_id is None:
        print("[{0}] Tag lost".format(controller_id))
    else:
        print("[{0}] Tag found {1}".format(controller_id, tag_id))

    # loop through the tags and determine if we have a match
    current_tags = [tag_id for tag_id, timestamp in tags.values() if tag_id is not None]
    if len(current_tags) == 3:
        print("Three tags scanned: ", current_tags)
        for combo, path, pattern in tag_combos:
            if is_match(current_tags, combo):
                # old code before we had duplicate tags to match against:
                #    if current_tags == combo:
                print(
                    "Found match! playing pattern {0} and sound {1}".format(
                        pattern, path
                    )
                )
                play_pixelblaze_pattern(pattern)
                play_active_sound(path)
                return

    # no match, just do background things
    play_pixelblaze_pattern(0)
    ActiveVolume.tween(0.0, AUDIO_CROSSFADE_TIME)
    active_voice_path = None


# local tag found
async def tag_found(reader):
    mac = network.WLAN(network.STA_IF).config("mac").hex()
    try:
        tag_scanned(mac, reader.tag.uid.hex())
        broadcaster.send(bcast, b"rich" + reader.tag.uid)

        while True:
            await asyncio.sleep(0.5)
    except asyncio.CancelledError:
        tag_scanned(mac, None)
        broadcaster.send(bcast, b"rich" + b"\x00")


# remote tag found
async def receiver_loop():
    while True:
        try:
            sender, tag_id = broadcaster.recv(0)
            if sender is not None and b"rich" in tag_id:
                tag_id = tag_id.replace(b"rich", b"")
                tag_scanned(sender.hex(), tag_id.hex() if tag_id is not None else None)
        except Exception as e:
            print("Error receiving tag: ", e)
        await asyncio.sleep(0.2)


async def play_audio_loop(audio_out):
    swriter = asyncio.StreamWriter(audio_out)
    wav_samples = bytearray(5120)
    # bytearray was originally 4096
    wav_samples_mv = memoryview(wav_samples)

    m.play(VoiceBG)

    while True:
        VoiceBG.volume = 1.0 - float(ActiveVolume)

        if VoiceActive and VoiceActive not in m.voices():
            m.play(VoiceActive)
        if VoiceActive:
            VoiceActive.volume = float(ActiveVolume)

        m.mixinto(wav_samples_mv)
        swriter.out_buf = wav_samples_mv[:]
        await swriter.drain()


def button_callback(btn):
    if btn.pressed():
        print("Button pressed")


async def main():
    print("Opening NFC reader")
    spi = SPI(
        1, baudrate=7000000, sck=fern.NFC_SCK, mosi=fern.NFC_MOSI, miso=fern.NFC_MISO
    )
    reader = nfc.NfcReader(spi, fern.NFC_NSS, fern.NFC_BUSY, fern.NFC_RST)
    reader.onTagFound(tag_found)
    try:
        await reader.start(verbose=False)
        asyncio.create_task(reader.loop())
    except Exception as e:
        print("No NFC reader found: ", e)

    print("Opening ESPNow")
    network.WLAN(network.STA_IF).active(True)
    broadcaster.active(True)
    broadcaster.add_peer(bcast)
    asyncio.create_task(receiver_loop())

    if audio_enabled:
        print("Starting audio")
        audio_out = I2S(
            0,
            sck=Pin(fern.I2S_BCK),
            ws=Pin(fern.I2S_WS),
            sd=Pin(fern.I2S_SDOUT),
            mck=Pin(fern.I2S_MCK),
            mode=I2S.TX,
            bits=16,
            format=I2S.STEREO,
            rate=44100,
            ibuf=10240,
            # rate was originally 16000
            # ibuf was originally 4000
        )

        i2c = I2C(0, scl=fern.I2C_SCL, sda=fern.I2C_SDA, freq=100000)
        i2c.scan()
        time.sleep_ms(100)
        codec.init(i2c)
        asyncio.create_task(play_audio_loop(audio_out))

    btn = DebouncedInput(fern.D8, button_callback, Pin.PULL_UP, False, 50)

    asyncio.get_event_loop().run_forever()


asyncio.run(main())
