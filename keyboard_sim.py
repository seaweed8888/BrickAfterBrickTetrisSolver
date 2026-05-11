# controller/keyboard_sim.py

import pyautogui
import time
import random
import keyboard

pyautogui.FAILSAFE = True

MIN_DELAY = 0.010
MAX_DELAY = 0.020

def _press_key(key_name):
    time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
    pyautogui.keyDown(key_name)
    time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
    pyautogui.keyUp(key_name)

def press_left():
    _press_key('left')

def press_right():
    _press_key('right')

def press_down():
    _press_key('down')

def press_rotate():
    _press_key('up')

def press_start():
    _press_key('space')

def press_reset():
    _press_key('r')

def test():
    press_start()
    time.sleep(0.5)
    
    for _ in range(4):
        press_rotate()
        time.sleep(0.5)
        
    press_left()
    time.sleep(0.5)
    
    press_right()
    time.sleep(0.5)
    
    press_left()
    time.sleep(0.5)
    
    for _ in range(5):
        pyautogui.keyDown('down')
        time.sleep(2)
    pyautogui.keyUp('down')
    time.sleep(0.5)
    
    press_reset()

if __name__ == "__main__":
    keyboard.wait('f8')
    test()