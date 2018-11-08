#!/usr/bin/env python
from websocket import create_connection

import time
import struct
import collections
import opc

import numpy as np
import pyaudio

# opc
numLEDs = 20
client = opc.Client('localhost:7890')
pixels = [(0, 0, 0)] * numLEDs


lastChange = time.time()
chan = 1
reset_count = 0
trigger = False
nFFT = 512
BUF_SIZE = 4 * nFFT
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
max_bar_length = 1

blub = list()
peak_buffer = collections.deque(16 * [0], 16)

def bar_lights_on(qty_on):
    for i in range(qty_on):
        pixels[i] = (255, 0, 0)
        client.put_pixels(pixels)


def all_lights_off():
    for i in range(numLEDs):
        pixels[i] = (0, 0, 0)
        client.put_pixels(pixels)


def one_light_on(led_index, Red, Green, Blue):
    all_lights_off()
    pixels[led_index] = (255, 0, 0)
    client.put_pixels(pixels)


def animate(stream, MAX_y):
    global trigger
    global chan
    global maxi
    global lastChange
    global max_bar_length
    global reset_count
    N = max(stream.get_read_available() / nFFT, 1) * nFFT
    data = stream.read(int(N))
    # Unpack data, LRLRLR...
    y = np.array(struct.unpack("%dh" % (N * CHANNELS), data)) / MAX_y
    y_L = y[::2]
    Y_L = np.fft.fft(y_L, nFFT)
    test = np.abs(Y_L)
    peak_buffer.appendleft(min(255, int((test[0]/128)*255)))
    # peak_buffer.appendleft(min(255, int((test[1]/128)*255)))
    #print(str(sum(peak_buffer)) + ' : ' + str(len(peak_buffer)))
    # col1 = int(sum(peak_buffer) / len(peak_buffer)) # find average of
    bar_length = int(sum(peak_buffer)/2)
    col1 = bar_length
    if bar_length > max_bar_length:
        max_bar_length = bar_length
    g_percent = 0.0  # %
    y_percent = 0.5  # %
    r_percent = 0.9  # %
    if max_bar_length == 0:
        all_lights_off()
    else:
        led_length = int((bar_length / max_bar_length) * numLEDs)
        all_lights_off()
        bar_lights_on(led_length)
    # print(bar_length)
    # print(max_bar_length)
    g_start = round(g_percent * max_bar_length)
    y_start = round(y_percent * max_bar_length)
    r_start = round(r_percent * max_bar_length)
    if bar_length > y_start:
        g_length = round(bar_length - y_start)
    else:
        g_length = bar_length
    g_value = '\033[92mG' * g_length
    if bar_length > r_start:
        r_length = round(bar_length - r_start)
        r_value = 'R' * r_length
    else:
        r_length = 0
        r_value = ""
    if bar_length > y_start:
        y_length = round(g_length - r_length)
        y_value = "Y" * y_length
    else:
        y_length = 0
        y_value = ""

    bar = g_value + y_value + r_value
    peak_length = max_bar_length - len(bar)
    peak_pad = ' ' * peak_length
    bar_print = bar + peak_pad + "#"
    reset_count += 1
    # if reset_count == 500:
    #    reset_count = 0
    #    max_bar_length = bar_length
    # print(bar_print)

#    if (col1 > 90 and not trigger and (time.time() - lastChange) > 0.5 or (time.time() - lastChange > 5)):
#        lastChange = time.time()
#        trigger = True
#        chan = chan +1
#        if chan > 7:
#            chan = 1
#    if (col1 < 80 and trigger):
#        trigger = False

#   frame = bytearray()
#    chred = col1 if (chan & (1 << 0)) else 0x00
#    chgreen = col1 if (chan & (1 << 1)) else 0x00
#    chblue = col1 if (chan & (1 << 2)) else 0x00
#    r_value = chred
#    g_value = chgreen
#    b_value = chblue
#    mycmd = '{"color":['+str(r_value)+','+str(g_value)+','+str(b_value)+'],"command":"color","priority":100}'
    # print(mycmd)
    # result = send_to_hyperion(mycmd)
    #print(str([chred, chgreen, chblue]))



def main():
    p = pyaudio.PyAudio()
    SPEAKERS = p.get_default_output_device_info()["hostApi"]
  # Used for normalizing signal. If use paFloat32, then it's already -1..1.
  # Because of saving wave, paInt16 will be easier.
    MAX_y = 2.0 ** (p.get_sample_size(FORMAT) * 8 - 1)
    print(MAX_y)
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    output_device_index=2,
                    input=True,
                    frames_per_buffer=BUF_SIZE,
                    input_host_api_specific_stream_info=SPEAKERS)

    while True:
        animate(stream,MAX_y)
        time.sleep(0.01)
        #time.sleep(0.5)
    stream.stop_stream()
    stream.close()
    p.terminate()

if __name__ == '__main__':
    main()
