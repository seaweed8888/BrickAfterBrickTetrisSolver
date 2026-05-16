import pyautogui
import time
import keyboard

pyautogui.PAUSE = 0

def test_speed(press_time, cooldown_time, moves, test_num):
    print(f"\n--- Test {test_num} ---")
    print("Press 'T' to run this test...")
    keyboard.wait('t')
    
    # 0.5s delay so you can lift your finger off the key
    time.sleep(0.5) 
    
    print(f"Running... (Press: {press_time}s | Cooldown: {cooldown_time}s)")
    
    # Move Left
    for _ in range(moves):
        pyautogui.keyDown('left')
        time.sleep(press_time)
        pyautogui.keyUp('left')
        time.sleep(cooldown_time)
        
    # Move Right
    for _ in range(moves):
        pyautogui.keyDown('right')
        time.sleep(press_time)
        pyautogui.keyUp('right')
        time.sleep(cooldown_time)

def main():
    print("Switch to the Tetris game!")
    print("Make sure your piece has at least 5 empty spaces to its left!")
    
    # Test 1: The current speed (Safe)
    test_speed(0.015, 0.015, 5, 1)
    
    # Test 2: Pushing the Windows clock limit
    test_speed(0.010, 0.010, 5, 2)
    
    # Test 3: Sub-frame timings
    test_speed(0.005, 0.005, 5, 3)
    
    # Test 4: Zero cooldown (Instant machine-gunning)
    test_speed(0.002, 0.000, 5, 4)

    print("\nCalibration complete. Which test was the fastest one to move EXACTLY 5 spaces left AND 5 spaces right (ending up exactly where it started)?")

if __name__ == "__main__":
    main()