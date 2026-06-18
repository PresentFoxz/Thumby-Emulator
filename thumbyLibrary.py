import pygame
import threading
import time
from array import array

class Ptr8:
    def __init__(self, data):
        self.data = data

    def __getitem__(self, i):
        return self.data[i]

    def __setitem__(self, i, v):
        self.data[i] = v & 0xFF


def ptr8(obj):
    return Ptr8(obj)

inputState = 0
buttonInputs = [
    [
        pygame.K_s,
        pygame.K_a,
        pygame.K_UP,
        pygame.K_DOWN,
        pygame.K_LEFT,
        pygame.K_RIGHT
    ],

    [
        pygame.K_w,
        pygame.K_q,
        pygame.K_u,
        pygame.K_j,
        pygame.K_h,
        pygame.K_k
    ],

    [
        False,
        False,
        False,
        False,
        False,
        False
    ]
]

inputSeries = []
def createInputSeries(file_name):
    global inputSeries
    inputSeries = []

    with open(file_name, "r") as f:
        lines = f.readlines()

    current_start = 0
    current_end = 0

    for line in lines:
        line = line.strip()
        if not line:
            continue

        parts = line.split()
        cmd = parts[0]

        if cmd == "f":
            current_start = int(parts[1])
            current_end = int(parts[2])

            # ensure list is big enough
            while len(inputSeries) < current_end:
                inputSeries.append(None)

        elif cmd == "i":
            inputs = [
                bool(int(parts[1])),
                bool(int(parts[2])),
                bool(int(parts[3])),
                bool(int(parts[4])),
                bool(int(parts[5])),
                bool(int(parts[6])),
            ]

            for frame in range(current_start, current_end):
                inputSeries[frame] = inputs

    for _, inp in enumerate(inputSeries):
        print(f"Frame {_} has inputs {inp}")

pygame.mixer.init()

def ticks_ms():
    return int(time.perf_counter() * 1000)

def ticks_diff(new, old):
    return new - old

class Timer:
    ONE_SHOT = 0

    def init(self, period, mode, callback):
        threading.Timer(period / 1000.0, callback).start()

pygame.mixer.init(frequency=44100, size=-16, channels=1)

class PWM:
    def __init__(self):
        self._freq = 440
        self._channel = None
        self._sound = None

    def freq(self, freq):
        self._freq = freq

    def _make_square_wave(self, freq, duration_ms=1000):
        sample_rate = 44100
        samples = int(sample_rate * duration_ms / 1000)

        period = sample_rate / freq
        amplitude = 32767 // 2

        buf = array('h')

        for i in range(samples):
            if (i % period) < (period / 2):
                buf.append(amplitude)
            else:
                buf.append(-amplitude)

        return pygame.mixer.Sound(buffer=buf)

    def duty_u16(self, value):
        if value == 0:
            if self._channel:
                self._channel.stop()
            return

        if self._channel:
            self._channel.stop()

        self._sound = self._make_square_wave(self._freq)
        self._channel = self._sound.play(-1)


swBuzzer = PWM()