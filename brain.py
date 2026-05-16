import numpy as np
from numba import jit

SHAPES = {
    'I': [
        np.array([[1, 1, 1, 1]], dtype=np.int32), 
        np.array([[1], [1], [1], [1]], dtype=np.int32)
    ],
    'O': [
        np.array([[1, 1], [1, 1]], dtype=np.int32)
    ],
    'T': [
        np.array([[0, 1, 0], [1, 1, 1]], dtype=np.int32),
        np.array([[0, 1], [1, 1], [0, 1]], dtype=np.int32),
        np.array([[1, 1, 1], [0, 1, 0]], dtype=np.int32),
        np.array([[1, 0], [1, 1], [1, 0]], dtype=np.int32)
    ],
    'S': [
        np.array([[0, 1, 1], [1, 1, 0]], dtype=np.int32),
        np.array([[1, 0], [1, 1], [0, 1]], dtype=np.int32)
    ],
    'Z': [
        np.array([[1, 1, 0], [0, 1, 1]], dtype=np.int32),
        np.array([[0, 1], [1, 1], [1, 0]], dtype=np.int32)
    ],
    'J': [
        np.array([[1, 0, 0], [1, 1, 1]], dtype=np.int32),
        np.array([[0, 1], [0, 1], [1, 1]], dtype=np.int32),
        np.array([[1, 1, 1], [0, 0, 1]], dtype=np.int32),
        np.array([[1, 1], [1, 0], [1, 0]], dtype=np.int32)
    ],
    'L': [
        np.array([[0, 0, 1], [1, 1, 1]], dtype=np.int32),
        np.array([[1, 1], [0, 1], [0, 1]], dtype=np.int32),
        np.array([[1, 1, 1], [1, 0, 0]], dtype=np.int32),
        np.array([[1, 0], [1, 0], [1, 1]], dtype=np.int32)
    ]
}

@jit(nopython=True)
def fast_drop_row(board, piece, col):
    piece_h = piece.shape[0]
    piece_w = piece.shape[1]
    for r in range(24 - piece_h + 1):
        collision = False
        for i in range(piece_h):
            for j in range(piece_w):
                if piece[i, j] and board[r + i, col + j]:
                    collision = True
                    break
            if collision:
                break
        if collision:
            return r - 1
    return 24 - piece_h

@jit(nopython=True)
def fast_evaluate(board, drop_r, col, piece):
    piece_h = piece.shape[0]
    piece_w = piece.shape[1]

    sim_board = np.copy(board)
    for i in range(piece_h):
        for j in range(piece_w):
            if piece[i, j]:
                sim_board[drop_r + i, col + j] = 1

    clears = 0
    cleared_board = np.zeros((24, 10), dtype=np.int32)
    write_row = 23
    for r in range(23, -1, -1):
        is_full = True
        for c in range(10):
            if sim_board[r, c] == 0:
                is_full = False
                break
        if is_full:
            if r >= 4:
                clears += 1
        else:
            for c in range(10):
                cleared_board[write_row, c] = sim_board[r, c]
            write_row -= 1

    column_heights = np.zeros(10, dtype=np.int32)
    blank_cnt = 0
    blank_depth = 0
    almost_full_score = 0.0

    for c in range(10):
        found_block = False
        for r in range(24):
            if cleared_board[r, c] > 0:
                if not found_block:
                    column_heights[c] = 24 - r
                    found_block = True
            elif found_block and cleared_board[r, c] == 0:
                blank_cnt += 1
                blank_depth += (24 - r) - 1

    max_height = 0
    for c in range(10):
        if column_heights[c] > max_height:
            max_height = column_heights[c]

    for r in range(24):
        row_sum = 0
        for c in range(10):
            if cleared_board[r, c] > 0:
                row_sum += 1
        if row_sum == 9:
            almost_full_score += 2.0
        elif row_sum == 8:
            almost_full_score += 0.5

    hole_penalty = 0
    prev_h = 24 
    for c in range(1, 9):
        if (prev_h - 2 > column_heights[c]) and (column_heights[c] < column_heights[c+1] - 2):
            hole_penalty += 1
        prev_h = column_heights[c]

    score = 0.0
    score += almost_full_score

    if clears >= 4:
        score += 1000.0
        
    is_scared = max_height >= 13

    if is_scared:
        score += 10.0 * clears
        score -= max_height + (float(max_height) ** 1.4)
        return score, clears

    score -= blank_cnt * 10.0
    score -= blank_depth * 2.0

    if max_height > 7:
        score -= (float(max_height) ** 1.4)
        
    score -= hole_penalty * 10.0

    if blank_cnt > 0:
        score += 5.0 * clears
        return score, clears

    score -= 3.0 * clears
    if column_heights[9] != 0:
        score -= 10.0
        score -= column_heights[9]

    return score, clears

class ElTetrisBrain:
    def __init__(self):
        print("[Brain] Compiling AI heuristics with Sky Buffer...")
        dummy_board = np.zeros((24, 10), dtype=np.int32)
        dummy_piece = np.array([[1, 1, 1, 1]], dtype=np.int32)
        _ = fast_drop_row(dummy_board, dummy_piece, 0)
        _ = fast_evaluate(dummy_board, 23, 0, dummy_piece)
        print("[Brain] Compilation complete.")

    def get_best_move(self, board_grid, piece_name):
        if piece_name not in SHAPES:
            return None, None, [], 0

        original_board = np.array(board_grid, dtype=np.int32)
        padded_board = np.zeros((24, 10), dtype=np.int32)
        padded_board[4:24, :] = original_board
        
        best_score = -1e9
        best_rotation, best_column, best_drop_r, best_clears = 0, 0, 0, 0

        rotations = SHAPES[piece_name]

        for rot_index, piece_grid in enumerate(rotations):
            piece_w = piece_grid.shape[1]

            for col in range(10 - piece_w + 1):
                drop_r = fast_drop_row(padded_board, piece_grid, col)
                if drop_r < 0: continue 

                score, clears = fast_evaluate(padded_board, drop_r, col, piece_grid)

                if score > best_score:
                    best_score = score
                    best_rotation = rot_index
                    best_column = col
                    best_drop_r = drop_r
                    best_clears = clears

        target_blocks = []
        if best_score != -1e9:
            best_piece = SHAPES[piece_name][best_rotation]
            for i in range(best_piece.shape[0]):
                for j in range(best_piece.shape[1]):
                    if best_piece[i, j]:
                        target_blocks.append((best_drop_r + i - 4, best_column + j))

        return best_rotation, best_column, target_blocks, best_clears