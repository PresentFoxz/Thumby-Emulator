import pygame
import thumbyLibrary as tLib

class thumbyButton:
    def __init__(self, key):
        self.key = key
        self._last = False

    def pressed(self):
        if isinstance(self.key, bool):
            return self.key
        
        keys = pygame.key.get_pressed()
        return bool(keys[self.key])

    def justPressed(self):
        current = self.pressed()
        result = current and not self._last
        self._last = current
        return result

buttonA = thumbyButton(tLib.buttonInputs[tLib.inputState][0])
buttonB = thumbyButton(tLib.buttonInputs[tLib.inputState][1])
buttonU = thumbyButton(tLib.buttonInputs[tLib.inputState][2])
buttonD = thumbyButton(tLib.buttonInputs[tLib.inputState][3])
buttonL = thumbyButton(tLib.buttonInputs[tLib.inputState][4])
buttonR = thumbyButton(tLib.buttonInputs[tLib.inputState][5])
