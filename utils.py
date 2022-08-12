DIRECTIONS = {
    0: (-1, 0), 1: (0, 1), 2: (1, 0), 3: (0, -1)
    # up right down left
}

def inside_borders(pos, board_size):
    row, col = pos
    M, N = board_size
    return 0 <= row < M and 0 <= col < N