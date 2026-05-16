import cv2
import dxcam
import numpy as np
import time

blockTolerance = 15   

BOARD_TL = (753, 225)
BOARD_BR = (984, 679)
NEXT_PIECE_TL = (1033, 615)
NEXT_PIECE_BR = (1125, 663)

BG_HEX = "#f3f3f3"
blockIHex = "#565656"
blockOHex = "#393939"
blockTHex = "#d42618"
blockSHex = "#9c443d"
blockZHex = "#4c120d"
blockJHex = "#eddbcb"
blockLHex = "#c8b49a"

GAME_ROWS = 20
GAME_COLS = 10
NEXT_PIECE_ROWS = 2
NEXT_PIECE_COLS = 4

class VisionSystem:
    def __init__(self):
        self.camera = dxcam.create()
        self.camera.start(target_fps=60)
        self.bg_color_1 = self._hex_to_rgb(BG_HEX)
        self.running = True
        
        self.shape_colors = {
            "I": self._hex_to_rgb(blockIHex),
            "O": self._hex_to_rgb(blockOHex),
            "T": self._hex_to_rgb(blockTHex),
            "S": self._hex_to_rgb(blockSHex),
            "Z": self._hex_to_rgb(blockZHex),
            "J": self._hex_to_rgb(blockJHex),
            "L": self._hex_to_rgb(blockLHex)
        }

    def _hex_to_rgb(self, hex_str):
        hex_str = hex_str.lstrip('#')
        return np.array([int(hex_str[i:i+2], 16) for i in (0, 2, 4)])

    def check_game_over(self, n_crop):
        height, width = n_crop.shape[:2]
        cols, rows = NEXT_PIECE_COLS, NEXT_PIECE_ROWS
        gap_x, gap_y = 1, 6
        
        cell_width = (width - (gap_x * (cols - 1))) / cols
        cell_height = (height - (gap_y * (rows - 1))) / rows
        
        valid_block_found = False
        
        for r in range(rows):
            for c in range(cols):
                cx = int(c * (cell_width + gap_x) + (cell_width / 2))
                cy = int(r * (cell_height + gap_y) + (cell_height / 2))
                
                if cy < height and cx < width:
                    pixel = n_crop[cy, cx].astype(int)
                    
                    for color in self.shape_colors.values():
                        if np.linalg.norm(pixel - color) < blockTolerance:
                            valid_block_found = True
                            break
                    
                    if not valid_block_found:
                        if pixel[0] > 180 and 80 < pixel[1] < 160 and pixel[2] < 60:
                            valid_block_found = True
                
                if valid_block_found: break
            if valid_block_found: break
                            
        return not valid_block_found

    def _is_block(self, pixel):
        pixel = pixel.astype(int)
        dist_bg = np.linalg.norm(pixel - self.bg_color_1)
        if dist_bg < blockTolerance:
            return False
        return True

    def _extract_grid(self, image_crop, rows, cols, gap_x=0, gap_y=0):
        height, width = image_crop.shape[:2]
        cell_width = (width - (gap_x * (cols - 1))) / cols
        cell_height = (height - (gap_y * (rows - 1))) / rows
        grid = np.zeros((rows, cols), dtype=int)
        for r in range(rows):
            for c in range(cols):
                cx = int(c * (cell_width + gap_x) + (cell_width / 2))
                cy = int(r * (cell_height + gap_y) + (cell_height / 2))
                if cy < height and cx < width:
                    if self._is_block(image_crop[cy, cx]):
                        grid[r][c] = 1
        return grid

    def get_active_piece(self, board_grid, board_crop):
        start_r, start_c = -1, -1
        for r in range(GAME_ROWS):
            for c in range(GAME_COLS):
                if board_grid[r][c] == 1:
                    start_r, start_c = r, c
                    break
            if start_r != -1: break
        
        if start_r == -1:
            return "NONE", None, []

        active_blocks = []
        queue = [(start_r, start_c)]
        visited = {(start_r, start_c)}
        
        while queue:
            r, c = queue.pop(0)
            active_blocks.append((r, c))
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr, nc = r+dr, c+dc
                if 0 <= nr < GAME_ROWS and 0 <= nc < GAME_COLS:
                    if nr <= start_r + 3: 
                        if board_grid[nr][nc] == 1 and (nr, nc) not in visited:
                            visited.add((nr, nc))
                            queue.append((nr, nc))

        # Rejects blobs that are not exactly 4 blocks
        if len(active_blocks) != 4:
            return "UNKNOWN", None, []

        # THE GROUND TOUCH FIX: If the 4 blocks are touching any other block on the board,
        # it is part of the ground stack, NOT an active falling piece.
        touching_stack = False
        for r, c in active_blocks:
            for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < GAME_ROWS and 0 <= nc < GAME_COLS:
                    if board_grid[nr][nc] == 1 and (nr, nc) not in visited:
                        touching_stack = True
                        break
            if touching_stack:
                break
                
        if touching_stack:
            return "UNKNOWN", None, []

        min_c = min(c for r, c in active_blocks)
        min_r = min(r for r, c in active_blocks)
        location = (min_c, min_r)

        max_r, max_c = max(r for r, c in active_blocks), max(c for r, c in active_blocks)
        shape_grid = np.zeros((max_r-min_r+1, max_c-min_c+1), dtype=int)
        for r, c in active_blocks:
            shape_grid[r-min_r][c-min_c] = 1
        
        shape_str = str(shape_grid.tolist())
        
        trimmed_shapes = {
            "[[1, 1, 1, 1]]": "I", "[[1], [1], [1], [1]]": "I",
            "[[1, 1], [1, 1]]": "O",
            "[[0, 1, 0], [1, 1, 1]]": "T", "[[1, 1, 1], [0, 1, 0]]": "T",
            "[[1, 0], [1, 1], [1, 0]]": "T", "[[0, 1], [1, 1], [0, 1]]": "T",
            "[[0, 1, 1], [1, 1, 0]]": "S", "[[1, 0], [1, 1], [0, 1]]": "S",
            "[[1, 1, 0], [0, 1, 1]]": "Z", "[[0, 1], [1, 1], [1, 0]]": "Z",
            "[[1, 0, 0], [1, 1, 1]]": "J", "[[1, 1, 1], [0, 0, 1]]": "J",
            "[[0, 1], [0, 1], [1, 1]]": "J", "[[1, 1], [1, 0], [1, 0]]": "J",
            "[[0, 0, 1], [1, 1, 1]]": "L", "[[1, 1, 1], [1, 0, 0]]": "L",
            "[[1, 1], [0, 1], [0, 1]]": "L", "[[1, 0], [1, 0], [1, 1]]": "L"
        }
        
        name = trimmed_shapes.get(shape_str, "UNKNOWN")
        
        if name == "UNKNOWN":
            return "UNKNOWN", None, []
            
        return name, location, active_blocks

    def classify_next_piece(self, grid):
        active_blocks = []
        for r in range(NEXT_PIECE_ROWS):
            for c in range(NEXT_PIECE_COLS):
                if grid[r][c] == 1:
                    active_blocks.append((r, c))
                    
        if len(active_blocks) == 0:
            return "UNKNOWN"
            
        min_r = min(r for r, c in active_blocks)
        max_r = max(r for r, c in active_blocks)
        min_c = min(c for r, c in active_blocks)
        max_c = max(c for r, c in active_blocks)
        
        shape_grid = np.zeros((max_r - min_r + 1, max_c - min_c + 1), dtype=int)
        for r, c in active_blocks:
            shape_grid[r - min_r][c - min_c] = 1
            
        shape_str = str(shape_grid.tolist())
        
        trimmed_shapes = {
            "[[1, 1, 1, 1]]": "I", "[[1], [1], [1], [1]]": "I",
            "[[1, 1], [1, 1]]": "O",
            "[[0, 1, 0], [1, 1, 1]]": "T", "[[1, 1, 1], [0, 1, 0]]": "T",
            "[[1, 0], [1, 1], [1, 0]]": "T", "[[0, 1], [1, 1], [0, 1]]": "T",
            "[[0, 1, 1], [1, 1, 0]]": "S", "[[1, 0], [1, 1], [0, 1]]": "S",
            "[[1, 1, 0], [0, 1, 1]]": "Z", "[[0, 1], [1, 1], [1, 0]]": "Z",
            "[[1, 0, 0], [1, 1, 1]]": "J", "[[1, 1, 1], [0, 0, 1]]": "J",
            "[[0, 1], [0, 1], [1, 1]]": "J", "[[1, 1], [1, 0], [1, 0]]": "J",
            "[[0, 0, 1], [1, 1, 1]]": "L", "[[1, 1, 1], [1, 0, 0]]": "L",
            "[[1, 1], [0, 1], [0, 1]]": "L", "[[1, 0], [1, 0], [1, 1]]": "L"
        }
        
        return trimmed_shapes.get(shape_str, "UNKNOWN")

    def get_game_state(self):
        f = self.camera.get_latest_frame()
        if f is None: return None

        b_crop = f[BOARD_TL[1]:BOARD_BR[1], BOARD_TL[0]:BOARD_BR[0]]
        n_crop = f[NEXT_PIECE_TL[1]:NEXT_PIECE_BR[1], NEXT_PIECE_TL[0]:NEXT_PIECE_BR[0]]
        
        if self.check_game_over(n_crop):
            empty_grid = np.zeros((GAME_ROWS, GAME_COLS), dtype=int)
            return {
                "phase": "GAME_OVER", "board_grid": empty_grid, "current_piece_name": "NONE",
                "current_piece_location": None, "next_piece_name": "UNKNOWN",
                "score": 0, "raw_board": b_crop, "active_blocks": []
            }

        b_grid = self._extract_grid(b_crop, GAME_ROWS, GAME_COLS, 2, 2)
        n_grid = self._extract_grid(n_crop, NEXT_PIECE_ROWS, NEXT_PIECE_COLS, 1, 6)
        
        name, loc, active_blocks = self.get_active_piece(b_grid, b_crop)
        next_name = self.classify_next_piece(n_grid)

        clean_grid = np.copy(b_grid)
        for r, c in active_blocks:
            clean_grid[r][c] = 0

        return {
            "phase": "GAMEPLAY", "board_grid": clean_grid, "current_piece_name": name,
            "current_piece_location": loc, "next_piece_name": next_name,
            "score": 0, "raw_board": b_crop,
            "active_blocks": active_blocks
        }

    def stop(self):
        self.running = False
        self.camera.stop()