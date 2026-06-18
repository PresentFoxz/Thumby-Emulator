import pygame
import time
from thumbyLibrary import swBuzzer, Timer, ticks_ms, ticks_diff

class AudioClass:
    def __init__(self, pwm):
        self.timer = Timer()
        self.pwm = pwm
        self.enabled = 1
        self.dutyCycle = 0xFFFF // 2

    def setEnabled(self, setting=1):
        self.enabled = setting

        if self.enabled < 0:
            self.enabled = 0

        if self.enabled > 1:
            self.enabled = 1

    def stop(self, dummy=None):
        self.pwm.duty_u16(0)

    def set(self, freq):
        if self.enabled:
            self.pwm.freq(freq)
            self.pwm.duty_u16(self.dutyCycle)

    def play(self, freq, duration):
        if self.enabled:
            self.pwm.freq(freq)
            self.pwm.duty_u16(self.dutyCycle)

            self.timer.init(
                period=duration,
                mode=Timer.ONE_SHOT,
                callback=self.stop
            )

    def playBlocking(self, freq, duration):
        t0 = ticks_ms()

        if self.enabled:
            self.pwm.freq(freq)
            self.pwm.duty_u16(self.dutyCycle)

            while ticks_diff(ticks_ms(), t0) <= duration:
                pass

            self.stop()

        else:
            while ticks_diff(ticks_ms(), t0) <= duration:
                pass

audio = AudioClass(swBuzzer)