import pygame
import os
from thumbySprite import Sprite

class display:
    WIDTH = 72
    HEIGHT = 40

    def __init__(self):
        self.scale = 8
        self.buffer = bytearray(360)

        pygame.init()

        self.screen = pygame.display.set_mode(
            (self.WIDTH * self.scale, self.HEIGHT * self.scale)
        )

        self.clock = pygame.time.Clock()
        self.fps = 30

        self.width = self.WIDTH
        self.height = self.HEIGHT
        self.max_x = self.width - 1
        self.max_y = self.height - 1

        self.frameRate = 0
        self.lastUpdateEnd = 0

        self.setFont("lib/font5x7.bin", 5, 7, 1)

        self.fill(0)

    def setFont(self, fontFile, width, height, space):
        self.textBitmapSource = fontFile
        self.textBitmapFile = open(fontFile, "rb")

        self.textWidth = width
        self.textHeight = height
        self.textSpaceWidth = space

        self.textBitmap = bytearray(self.textWidth)

        self.textCharCount = (
            os.stat(fontFile).st_size // self.textWidth
        )
    
    def drawText(self, stringToPrint, x, y, color):
        for char in str(stringToPrint):
            char_index = ord(char) - 0x20

            if char_index < 0:
                continue

            offset = char_index * self.textWidth

            self.textBitmapFile.seek(offset)
            glyph = self.textBitmapFile.read(self.textWidth)

            for gx in range(self.textWidth):
                column = glyph[gx]

                for gy in range(self.textHeight):
                    if column & (1 << gy):
                        self.setPixel(x + gx, y + gy, color)

            x += self.textWidth + self.textSpaceWidth

    def setFPS(self, fps):
        self.fps = fps

    def fill(self, color):
        v = 255 if color else 0
        for i in range(360):
            self.buffer[i] = v

    def setPixel(self, x, y, c):
        if x < 0 or y < 0 or x >= self.WIDTH or y >= self.HEIGHT:
            return

        i = x + ((y >> 3) * self.WIDTH)
        m = 1 << (y & 7)

        if c:
            self.buffer[i] |= m
        else:
            self.buffer[i] &= (~m & 0xFF)
    
    def drawFilledRectangle(self, x, y, w, h, c):
        if x + w < 0 or y + h < 0 or x >= self.WIDTH or y >= self.HEIGHT:
            return

        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.WIDTH, x + w)
        y1 = min(self.HEIGHT, y + h)

        for yy in range(y0, y1):
            for xx in range(x0, x1):
                self.setPixel(xx, yy, c)
    
    def drawRectangle(self, x, y, w, h, c):
        if x + w < 0 or y + h < 0 or x >= self.WIDTH or y >= self.HEIGHT:
            return

        for xx in range(x, x + w):
            self.setPixel(xx, y, c)
            self.setPixel(xx, y + h - 1, c)

        for yy in range(y, y + h):
            self.setPixel(x, yy, c)
            self.setPixel(x + w - 1, yy, c)

    def update(self):

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                raise SystemExit

        self.screen.fill((0, 0, 0))

        s = self.scale

        for x in range(self.WIDTH):
            for y in range(self.HEIGHT):
                i = x + ((y >> 3) * self.WIDTH)
                if self.buffer[i] & (1 << (y & 7)):
                    pygame.draw.rect(
                        self.screen,
                        (255, 255, 255),
                        (x * s, y * s, s, s)
                    )

        pygame.display.flip()
        self.clock.tick(self.fps)

display = display()