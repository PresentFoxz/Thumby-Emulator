import sys
sys.path.append("/Games/Beyond")
from thumbyGrayscale import Sprite

Tiles = [
    None,
    
    Sprite(
        8, 8,
        (
            bytearray([250,240,132,241,232,224,241,252]),
            bytearray([7,31,255,31,31,127,15,135])
        ),
        0, 0
    ),
    
    Sprite(
        8, 8,
        (
            bytearray([255,123,255,255,255,255,255,247]),
            bytearray([0,132,128,0,0,2,136,8])
        ),
        0, 0
    ),
    
    Sprite(
        8, 8,
        (
          bytearray([0,126,126,102,102,126,126,0]),
          bytearray([0,0,0,0,0,0,0,0])
        ),
        0, 0
    )
]