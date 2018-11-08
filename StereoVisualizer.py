import pyaudio
import numpy as np
import opc

numLEDs = 20
client = opc.Client('localhost:7890')
pixels = [(0, 0, 0)] * numLEDs
g_percent = 0.0  # %
y_percent = 0.5  # %
r_percent = 0.9  # %
max_brightness = 255
fade_delay = 100

def led_on(led_index, Red, Green, Blue):
    # all_lights_off()
    pixels[led_index] = (Red, Green, Blue)
    client.put_pixels(pixels)

def all_lights_off():
    for i in range(numLEDs):
        pixels[i] = (0, 0, 0)
        client.put_pixels(pixels)

def get_vu_data():
    left_limit = 0
    left_fade = 0

    right_limit = 0
    right_fade = 0

    maxValue = 2**16
    bars = numLEDs
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=2,
                    rate=44100,
                    input=True,
                    frames_per_buffer=1024)
    while True:
        data = np.fromstring(stream.read(1024), dtype=np.int16)
        dataL = data[0::2]
        Lmax = np.max(dataL)
        Lmin = np.min(dataL)
        peakL = np.abs(Lmax - Lmin) / maxValue
        if (peakL >= left_limit) or (left_fade >= fade_delay):
            left_limit = peakL
            left_fade = 0
        else:
            left_fade += 1
        dataR = data[1::2]
        Rmax = np.max(dataR)
        Rmin = np.min(dataR)
        peakR = np.abs(Rmax - Rmin)/maxValue
        if (peakR > right_limit) or (right_fade >= fade_delay):
            right_limit = peakR
            right_fade = 0
        else:
            right_fade += 1
        lString = build_line(int(peakL*bars), int(left_limit*bars))
        led_bar(int(peakL*bars), int(left_limit*bars), left_fade)
        rString = build_line(int(peakR*bars), int(right_limit*bars))
        led_bar(int(peakR*bars), int(right_limit*bars), right_fade)
        print("L=[%s]\tR=[%s]" % (lString, rString))


def build_line(vu_level, max_level):
    g_start = 0
    if max_level > 1:
        y_start = int(y_percent * max_level)
    else:
        y_start = max_level + 100
    if max_level > 2:
        r_start = int(r_percent * max_level)
    else:
        r_start = max_level + 100

    if vu_level > y_start:
        g_length = int(y_start - g_start)
    else:
        if vu_level > g_start:
            g_length = vu_level
        else:
            g_length = 0
        y_length = 0
        r_length = 0
    g_value = 'G' * g_length

    if vu_level > r_start:
        y_length = int(r_start - y_start)
    else:
        if vu_level > y_start:
            y_length = int(vu_level - y_start)-1
        else:
            y_length = 0
        r_length = 0
    y_value = 'Y' * y_length

    if vu_level > r_start:
        r_length = int(vu_level - r_start)
    else:
        r_length = 0
    r_value = 'R' * r_length

    bar = g_value + y_value + r_value
    peak_length = max_level - len(bar)
    peak_pad = ' ' * peak_length
    bar_print = bar + peak_pad + "#"
    return bar_print


def led_bar(vu_level, max_level, fade_value):
    all_lights_off()
    g_start = 0
    if max_level > 1:
        y_start = int(y_percent * max_level)
    else:
        y_start = max_level + 100
    if max_level > 2:
        r_start = int(r_percent * max_level)
    else:
        r_start = max_level + 100

    if vu_level > y_start:
        g_length = int(y_start - g_start)
    else:
        if vu_level > g_start:
            g_length = vu_level
        else:
            g_length = 0
        y_length = 0
        r_length = 0
    for g_led in range(g_length):
        led_on(g_start + g_led, 0, max_brightness, 0)

    if vu_level > r_start:
        y_length = int(r_start - y_start)
    else:
        if vu_level > y_start:
            y_length = int(vu_level - y_start)-1
        else:
            y_length = 0
        r_length = 0
    for y_led in range(y_length):
        led_on(y_start + y_led, max_brightness, max_brightness, 0)

    if vu_level > r_start:
        r_length = int(vu_level - r_start)
    else:
        r_length = 0
    for r_led in range(r_length):
        led_on(r_start + r_led, max_brightness, 0, 0)

    fade_intensity = 255-(int((fade_value / fade_delay) * max_brightness))
    bar_len = g_length + y_length + r_length
    peak_length = max_level - bar_len
    led_on(peak_length + 1, fade_intensity, fade_intensity, fade_intensity)


get_vu_data()
