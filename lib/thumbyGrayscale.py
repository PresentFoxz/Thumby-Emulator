import pygame
import os

GRAY = [0, 255, 85, 170]

class Sprite:
    def __init__(self, width, height, bitmap, x, y):
        self.width = width
        self.height = height

        self.x = x
        self.y = y

        self.bitmap = bitmap

        self.frameCount = 1
        self.currentFrame = 0

    def getFrame(self):
        return self.currentFrame

    def setFrame(self, frame):
        if self.frameCount <= 1:
            return

        frame %= self.frameCount
        if frame == self.currentFrame:
            return

        self.currentFrame = frame
        
        bytes_per_frame = len(self.bitmapSource) // self.frameCount
        start = frame * bytes_per_frame
        end = start + bytes_per_frame

        self.bitmap = self.bitmapSource[start:end]


class display:
    WIDTH = 72
    HEIGHT = 40

    def __init__(self):
        self.scale = 8

        self.buffer = bytearray(360)
        self.shading = bytearray(360)
        
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
        color &= 0b11

        b0 = 0xFF if (color & 1) else 0x00
        b1 = 0xFF if (color & 2) else 0x00

        for i in range(len(self.buffer)):
            self.buffer[i] = b0
            self.shading[i] = b1

    def setPixel(self, x, y, c):
        if x < 0 or y < 0 or x >= self.WIDTH or y >= self.HEIGHT:
            return

        i = x + ((y >> 3) * self.WIDTH)
        bit = 1 << (y & 7)

        if c & 1:
            self.buffer[i] |= bit
        else:
            self.buffer[i] &= ~bit
        
        if c & 2:
            self.shading[i] |= bit
        else:
            self.shading[i] &= ~bit

    def drawFilledRectangle(self, x, y, w, h, c):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.WIDTH, x + w)
        y1 = min(self.HEIGHT, y + h)

        for yy in range(y0, y1):
            for xx in range(x0, x1):
                self.setPixel(xx, yy, c)

    def drawRectangle(self, x, y, w, h, c):
        for xx in range(x, x + w):
            self.setPixel(xx, y, c)
            self.setPixel(xx, y + h - 1, c)

        for yy in range(y, y + h):
            self.setPixel(x, yy, c)
            self.setPixel(x + w - 1, yy, c)

    def drawSprite(self, sprite):
        p0 = sprite.bitmap[0]
        p1 = sprite.bitmap[1]

        for y in range(sprite.height):
            for x in range(sprite.width):

                byte_index = x + ((y >> 3) * sprite.width)
                bit = 1 << (y & 7)

                buf = (p0[byte_index] & bit) != 0
                sha = (p1[byte_index] & bit) != 0

                if buf and sha:
                    v = 3
                elif buf:
                    v = 1
                elif sha:
                    v = 2
                else:
                    continue

                self.setPixel(sprite.x + x, sprite.y + y, v)

    def update(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                raise SystemExit

        self.screen.fill((0, 0, 0))
        s = self.scale

        for x in range(self.WIDTH):
            for y in range(self.HEIGHT):

                i = x + ((y >> 3) * self.WIDTH)
                bit = 1 << (y & 7)

                v = 0
                if self.buffer[i] & bit:
                    v |= 1
                if self.shading[i] & bit:
                    v |= 2

                if v:
                    g = GRAY[v]
                    pygame.draw.rect(
                        self.screen,
                        (g, g, g),
                        (x * s, y * s, s, s)
                    )

        pygame.display.flip()
        self.clock.tick(self.fps)

display = display()