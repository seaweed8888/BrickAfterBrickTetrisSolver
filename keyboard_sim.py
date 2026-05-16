import ctypes
import time

PUL = ctypes.POINTER(ctypes.c_ulong)

class KeyBdInput(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort),
                ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]

class HardwareInput(ctypes.Structure):
    _fields_ = [("uMsg", ctypes.c_ulong),
                ("wParamL", ctypes.c_short),
                ("wParamH", ctypes.c_ushort)]

class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]

class Input_I(ctypes.Union):
    _fields_ = [("ki", KeyBdInput),
                ("mi", MouseInput),
                ("hi", HardwareInput)]

class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong),
                ("ii", Input_I)]

# Virtual Key Codes
VK_KEYS = {'left': 0x25, 'up': 0x26, 'right': 0x27, 'space': 0x20, 'r': 0x52}

def PressKey(vkCode):
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.ki = KeyBdInput(vkCode, 0, 0, 0, ctypes.pointer(extra))
    
    # We MUST store this in a variable (x) so Python doesn't garbage-collect 
    # the pointer before Windows reads it!
    x = Input(ctypes.c_ulong(1), ii_)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

def ReleaseKey(vkCode):
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.ki = KeyBdInput(vkCode, 0, 0x0002, 0, ctypes.pointer(extra))
    
    x = Input(ctypes.c_ulong(1), ii_)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

TAP_PRESS = 0.025    
TAP_COOLDOWN = 0.015 

def _tap(key_name):
    vk = VK_KEYS[key_name]
    PressKey(vk)
    time.sleep(TAP_PRESS)
    ReleaseKey(vk)
    time.sleep(TAP_COOLDOWN)

def nudge_left(): _tap('left')
def nudge_right(): _tap('right')
def press_space(): _tap('space')

def execute_rotations(rot_count):
    for _ in range(rot_count):
        _tap('up')

def execute_moves(move_key, moves_count):
    if move_key and moves_count > 0:
        for _ in range(moves_count):
            _tap(move_key)

def set_speed(gear):
    pass