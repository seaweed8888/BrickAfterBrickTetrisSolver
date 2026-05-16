import tkinter as tk
import sys
import queue

CELL_SIZE = 20
ROWS = 20
COLS = 10

class StdoutRedirector:
    def __init__(self, original_stdout):
        self.original_stdout = original_stdout
        self.queue = queue.Queue()

    def write(self, string):
        self.original_stdout.write(string)
        self.queue.put(string)

    def flush(self):
        self.original_stdout.flush()

class DebugHUD:
    def __init__(self, root, bot_state):
        self.root = root
        self.bot_state = bot_state
        self.root.title("Bot HUD")
        self.root.attributes('-topmost', True)
        self.root.configure(bg='black')
        self.root.minsize(550, 650) 
        
        self.create_ui()
        self.redirector = StdoutRedirector(sys.stdout)
        sys.stdout = self.redirector
        self.update_ui()

    def create_ui(self):
        self.left_frame = tk.Frame(self.root, bg='black', width=220)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=10, pady=10)
        self.left_frame.pack_propagate(False) 
        
        self.terminal_text = tk.Text(self.left_frame, bg='black', fg='white', font=('Courier', 8), wrap=tk.WORD, borderwidth=0, highlightthickness=0)
        self.terminal_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.terminal_text.config(state=tk.DISABLED)

        self.right_frame = tk.Frame(self.root, bg='black', width=280)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)
        
        self.dash_frame = tk.Frame(self.right_frame, bg='white', width=280, height=150)
        self.dash_frame.pack(fill=tk.X)
        self.dash_frame.pack_propagate(False) 
        
        self.info_frame = tk.Frame(self.dash_frame, bg='white')
        self.info_frame.pack(side=tk.LEFT, padx=10, pady=5)
        
        self.status_label = tk.Label(self.info_frame, text="STATE: WAITING", fg='blue', bg='white', font=('Arial', 10, 'bold'))
        self.status_label.pack(anchor='w')
        self.current_label = tk.Label(self.info_frame, text="CURR: NONE", fg='black', bg='white', font=('Arial', 10))
        self.current_label.pack(anchor='w')
        self.next_label = tk.Label(self.info_frame, text="NEXT: NONE", fg='black', bg='white', font=('Arial', 10))
        self.next_label.pack(anchor='w')
        self.holes_label = tk.Label(self.info_frame, text="HOLES: 0", fg='purple', bg='white', font=('Arial', 10, 'bold'))
        self.holes_label.pack(anchor='w')
        
        self.start_btn = tk.Label(self.info_frame, text="WAITING FOR F8", bg='lightgray', font=('Arial', 8, 'bold'))
        self.start_btn.pack(pady=2, anchor='w')

        self.arrow_frame = tk.Frame(self.dash_frame, bg='white')
        self.arrow_frame.pack(side=tk.RIGHT, padx=10, pady=5)
        self.arrows = {
            'up': tk.Label(self.arrow_frame, text=" 🡅 ", bg='white', fg='black', font=('Arial', 12, 'bold')),
            'left': tk.Label(self.arrow_frame, text=" 🡄 ", bg='white', fg='black', font=('Arial', 12, 'bold')),
            'down': tk.Label(self.arrow_frame, text=" 🡇 ", bg='white', fg='black', font=('Arial', 12, 'bold')),
            'right': tk.Label(self.arrow_frame, text=" 🡆 ", bg='white', fg='black', font=('Arial', 12, 'bold')),
            'space': tk.Label(self.arrow_frame, text=" DROP ", bg='white', fg='black', font=('Arial', 8, 'bold'))
        }
        self.arrows['up'].grid(row=0, column=1)
        self.arrows['left'].grid(row=1, column=0)
        self.arrows['down'].grid(row=1, column=1)
        self.arrows['right'].grid(row=1, column=2)
        self.arrows['space'].grid(row=2, column=0, columnspan=3, pady=2)

        self.canvas = tk.Canvas(self.right_frame, width=COLS*CELL_SIZE, height=ROWS*CELL_SIZE, bg='black', highlightthickness=1)
        self.canvas.pack(pady=10)

    def update_ui(self):
        try:
            while not self.redirector.queue.empty():
                msg = self.redirector.queue.get_nowait()
                self.terminal_text.config(state=tk.NORMAL)
                self.terminal_text.insert(tk.END, msg)
                
                # --- MEMORY LEAK FIX ---
                # Forces the terminal to only keep the most recent 150 lines
                lines = int(self.terminal_text.index('end-1c').split('.')[0])
                if lines > 150:
                    self.terminal_text.delete('1.0', f'{lines - 150}.0')
                # -----------------------
                
                self.terminal_text.see(tk.END) 
                self.terminal_text.config(state=tk.DISABLED)
        except queue.Empty:
            pass

        if self.bot_state.status == "RUNNING":
            self.start_btn.configure(text="RUNNING", bg='green', fg='white')
        
        for k in self.arrows:
            self.arrows[k].configure(bg='white', fg='black')
            
        active = self.bot_state.active_key
        if active in self.arrows:
            self.arrows[active].configure(bg='darkgray', fg='white')

        game_state = self.bot_state.game_state
        if game_state:
            phase = game_state['phase']
            
            if phase == "GAMEPLAY":
                self.status_label.configure(text=f"STATE: {phase}", fg='green')
            else:
                self.status_label.configure(text=f"STATE: {phase}", fg='red')
                
            loc = game_state['current_piece_location']
            l_str = f" @ {loc}" if loc else ""
            self.current_label.configure(text=f"CURR: {game_state['current_piece_name']}{l_str}")
            self.next_label.configure(text=f"NEXT: {game_state['next_piece_name']}")
            
            if phase == "GAMEPLAY":
                h_count = self.draw_grid(
                    game_state['board_grid'], 
                    game_state.get('active_blocks', []), 
                    self.bot_state.target_blocks
                )
                self.holes_label.configure(text=f"HOLES: {h_count}")
            else:
                self.canvas.delete("all")
                self.holes_label.configure(text=f"HOLES: 0")

        self.root.after(50, self.update_ui)

    def draw_grid(self, grid, active_blocks, target_blocks):
        self.canvas.delete("all")
        surf = [ROWS] * COLS
        holes = 0
        
        for c in range(COLS):
            for r in range(ROWS):
                if grid[r][c] == 1 and (r, c) not in active_blocks:
                    surf[c] = r
                    break
                    
        for r in range(ROWS):
            for c in range(COLS):
                x1, y1 = c*CELL_SIZE, r*CELL_SIZE
                x2, y2 = x1+CELL_SIZE, y1+CELL_SIZE
                
                if grid[r][c] == 1:
                    if (r, c) in active_blocks:
                        self.canvas.create_rectangle(x1, y1, x2, y2, fill='cyan', outline='black')
                    else:
                        self.canvas.create_rectangle(x1, y1, x2, y2, fill='gray', outline='black')
                elif r > surf[c]:
                    self.canvas.create_rectangle(x1, y1, x2, y2, outline='purple', width=2)
                    holes += 1
                else:
                    self.canvas.create_rectangle(x1, y1, x2, y2, outline='#222222')

        if target_blocks:
            for r, c in target_blocks:
                x1, y1 = c*CELL_SIZE, r*CELL_SIZE
                x2, y2 = x1+CELL_SIZE, y1+CELL_SIZE
                self.canvas.create_rectangle(x1, y1, x2, y2, fill='#003300', outline='#00FF00', width=2)
                    
        for c in range(COLS):
            y_land = surf[c] * CELL_SIZE
            x_left = c * CELL_SIZE
            x_right = x_left + CELL_SIZE
            self.canvas.create_line(x_left, y_land, x_right, y_land, fill='red', width=3)
            
            if c < COLS - 1:
                next_y_land = surf[c + 1] * CELL_SIZE
                self.canvas.create_line(x_right, y_land, x_right, next_y_land, fill='red', width=3)

        return holes