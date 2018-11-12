#!/usr/bin/python
import sys, pygame, pyaudio, wave, audioop, math
from pygame.locals import *
import opc

# set up a bunch of constants
BGCOLOR = (0, 0, 0)
WINDOWWIDTH = 130
WINDOWHEIGHT = 500
PeakL = 0
PeakR = 0

# fadecandy variables
numLEDs = 64
maxLEDs = numLEDs / 2
maxBars = 40
client = opc.Client('localhost:7890')
pixels = [(0, 0, 0)] * numLEDs
brightness = 255
y_pos = 20
r_pos = 30

def led_on(led_index, Red, Green, Blue):
    # all_lights_off()
    pixels[led_index] = (Red, Green, Blue)
    client.put_pixels(pixels)

def leds_off():
    for i in range(numLEDs):
        pixels[i] = (0, 0, 0)
        client.put_pixels(pixels)

# setup code
pygame.init()
pygame.mixer.quit()  # stops unwanted audio output on some computers
DISPLAYSURF = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT), HWSURFACE)
pygame.display.set_caption('VU Meter')
fontSmall = pygame.font.Font('freesansbold.ttf', 12)
pa = pyaudio.PyAudio()

info = pa.get_default_input_device_info()
RATE = int(info['defaultSampleRate'])

# open stream
stream = pa.open(format=pyaudio.paInt16,
                 channels=2,
                 rate=RATE,
                 input=True,
                 frames_per_buffer=1024)

while True:  # main application loop
    # event handling loop for quit events
    for event in pygame.event.get():
        if event.type == QUIT or (event.type == KEYUP and event.key == K_ESCAPE):
            pygame.quit()
            sys.exit()

    # Read the data and calcualte the left and right levels
    data = stream.read(1024)
    ldata = audioop.tomono(data, 2, 1, 0)
    amplitudel = ((audioop.max(ldata, 2)) / 32767)
    LevelL = (int(maxBars + (20 * (math.log10(amplitudel + (1e-40)))))) # changed 41 to 32
    rdata = audioop.tomono(data, 2, 0, 1)
    amplituder = ((audioop.max(rdata, 2)) / 32767)
    LevelR = (int(maxBars + (20 * (math.log10(amplituder + (1e-40))))))

    # Use the levels to set the peaks
    if LevelL > PeakL:
        PeakL = LevelL
        brightness = 255
    elif PeakL > 0:
        PeakL = PeakL - 0.2
        brightness = brightness - (brightness * 0.023)
    if LevelR > PeakR:
        PeakR = LevelR
    elif PeakR > 0:
        PeakR = PeakR - 0.2

    # Fill the screen to draw from a blank state and draw the clock face
    DISPLAYSURF.fill(BGCOLOR)

    # Write the scale and draw in the lines
    for dB in range(0, 60, 4):
        number = str(dB)
        text = fontSmall.render("-" + number, 1, (255, 255, 255))
        textpos = text.get_rect()
        DISPLAYSURF.blit(text, (55, (12 * dB)))
        pygame.draw.line(DISPLAYSURF, (255, 255, 255), (40, 5 + (12 * dB)), (50, 5 + (12 * dB)), 1)
        pygame.draw.line(DISPLAYSURF, (255, 255, 255), (80, 5 + (12 * dB)), (90, 5 + (12 * dB)), 1)

    leds_off()
    # Draw the boxes
    for i in range(0, LevelL):
        if i < y_pos:
            pygame.draw.rect(DISPLAYSURF, (0, 192, 0), (10, (475 - i * 12), 30, 10))
        elif i >= y_pos and i < r_pos:
            pygame.draw.rect(DISPLAYSURF, (255, 255, 0), (10, (475 - i * 12), 30, 10))
        else:
            pygame.draw.rect(DISPLAYSURF, (255, 0, 0), (10, (475 - i * 12), 30, 10))
    for i in range(0, LevelR):
        if i < y_pos:
            pygame.draw.rect(DISPLAYSURF, (0, 192, 0), (90, (475 - i * 12), 30, 10))
        elif i >= y_pos and i < r_pos:
            pygame.draw.rect(DISPLAYSURF, (255, 255, 0), (90, (475 - i * 12), 30, 10))
        else:
            pygame.draw.rect(DISPLAYSURF, (255, 0, 0), (90, (475 - i * 12), 30, 10))
    # Draw the LEDs
    LedMultiplier = (maxLEDs / maxBars)
    LedLevelL = int(LedMultiplier * LevelL)
    LedLevelR = int(LedMultiplier * LevelR)
    LedY_pos = int(y_pos * LedMultiplier)
    LedR_pos = int(r_pos * LedMultiplier)
    for i in range(0, LedLevelL):
        if i < LedY_pos:
            led_on(i, 0, 127, 0)
        elif i >= LedY_pos and i < LedR_pos:
            led_on(i, 255, 255, 0)
        else:
            led_on(i, 255, 0, 0)
    neg_start = numLEDs - 1
    for i in range(0, LedLevelR):
        if i < LedY_pos:
            led_on(neg_start - i, 0, 192, 0)
        elif i >= LedY_pos and i < LedR_pos:
            led_on(neg_start - i, 255, 255, 0)
        else:
            led_on(neg_start - i, 255, 0, 0)
    # Draw the peak bars
    pygame.draw.rect(DISPLAYSURF, (255, 255, 255), (10, (485 - int(PeakL) * 12), 30, 2))
    led_on(int(PeakL * LedMultiplier), brightness, brightness, brightness)
    pygame.draw.rect(DISPLAYSURF, (255, 255, 255), (90, (485 - int(PeakR) * 12), 30, 2))
    led_on(neg_start - int(PeakR * LedMultiplier), brightness, brightness, brightness)
    pygame.display.update()