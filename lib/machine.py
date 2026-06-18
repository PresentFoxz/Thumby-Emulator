import time

class Timer:
    pass

def freq():
    return 125000000

def reset():
    raise SystemExit

def idle():
    pass

def ticks_ms():
    return int(time.time() * 1000)

def ticks_us():
    return int(time.time() * 1000000)