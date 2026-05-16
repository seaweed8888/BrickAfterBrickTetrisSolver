import time
import keyboard
import tkinter as tk
import threading
import gc
from screen_reader import VisionSystem
from brain import ElTetrisBrain
import keyboard_sim
from debug_hud import DebugHUD

class BotState:
    def __init__(self):
        self.game_state = None
        self.target_blocks = []
        self.active_key = None
        self.status = "WAITING FOR F8"

def run_bot(bot_state):
    vision = VisionSystem()
    brain = ElTetrisBrain()

    print("Press F8 to start. (Verify-Before-Drop Mode)")
    keyboard.wait('f8')
    bot_state.status = "RUNNING"

    just_dropped = False
    expected_piece = None
    drop_time = 0 
    pieces_dropped = 0 
    suicide_triggered = False

    try:
        while True:
            # Memory dump trigger for Chrome freeze at 4200
            if pieces_dropped > 4200:
                if not suicide_triggered:
                    bot_state.status = "TOPPING OUT"
                    vision.stop()
                    gc.collect()
                    suicide_triggered = True
                keyboard_sim.press_space()
                time.sleep(0.08)
                continue

            state = vision.get_game_state()
            bot_state.game_state = state
            
            if state is None:
                time.sleep(0.002)
                continue

            if state['phase'] == 'GAME_OVER':
                print(f"\n=== GAME OVER ===\nFinal Count: {pieces_dropped}")
                return

            piece_name = state['current_piece_name']
            loc = state['current_piece_location']

            if just_dropped:
                bot_state.target_blocks = [] 
                if time.time() - drop_time > 0.18:
                    just_dropped = False
                    continue
                time.sleep(0.002)
                continue

            if piece_name == 'NONE' or piece_name == 'UNKNOWN' or loc is None:
                time.sleep(0.002)
                continue

            # 1. Spawn Wait (Let the piece fully enter the board)
            time.sleep(0.030)

            state = vision.get_game_state()
            if state is None or state['current_piece_location'] is None:
                continue
            loc = state['current_piece_location']

            # 2. Brain Calculation
            best_rot, best_col, target_blocks, _ = brain.get_best_move(state['board_grid'], piece_name)
            bot_state.target_blocks = target_blocks
            
            if best_rot is None or best_col is None:
                time.sleep(0.002)
                continue

            current_col = loc[0]

            # 3. Universal SRS Pivot Math Fix 
            # (Gets us 99% there before we run the vision check)
            if piece_name != "O" and best_rot == 1:
                current_col += 1

            estimated_moves = best_col - current_col
            move_key = 'left' if estimated_moves < 0 else 'right'
            moves_count = abs(estimated_moves)
            
            # 4. Fast Hardware Execution
            if best_rot > 0:
                keyboard_sim.execute_rotations(best_rot)
                time.sleep(0.015) 

            if moves_count > 0:
                keyboard_sim.execute_moves(move_key, moves_count)

            # --- 5. CHECK BEFORE DROP (VISUAL VERIFICATION) ---
            retries = 0
            while retries < 3:
                # Give the browser 25ms to render the fast moves
                time.sleep(0.025)
                
                verify_state = vision.get_game_state()
                if not verify_state or not verify_state.get('current_piece_location'):
                    break # If we lose track of the piece, break out and drop
                
                actual_col = verify_state['current_piece_location'][0]
                error = best_col - actual_col
                
                # If the piece is exactly where the brain wants it, break the loop!
                if error == 0:
                    break 
                    
                # If we are off, nudge the piece into the correct slot
                if error < 0:
                    for _ in range(abs(error)):
                        keyboard_sim.nudge_left()
                elif error > 0:
                    for _ in range(error):
                        keyboard_sim.nudge_right()
                        
                retries += 1

            # 6. Settle Frame & Drop
            # Wait 25ms to ensure the final nudge is processed before hitting spacebar
            time.sleep(0.025) 
            keyboard_sim.press_space() 

            just_dropped = True
            expected_piece = state['next_piece_name']
            drop_time = time.time()
            pieces_dropped += 1

            if pieces_dropped >= 3900 and pieces_dropped % 50 == 0:
                print(f"[PROGRESS] {pieces_dropped} pieces dropped...")

            if pieces_dropped % 25 == 0:
                gc.collect()

    except Exception as e:
        print(f"Bot stopped: {e}")
    finally:
        vision.stop()

def main():
    root = tk.Tk()
    bot_state = BotState()
    hud = DebugHUD(root, bot_state)
    bot_thread = threading.Thread(target=run_bot, args=(bot_state,), daemon=True)
    bot_thread.start()
    root.mainloop()

if __name__ == "__main__":
    main()