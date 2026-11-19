"""Single-player Connect 4. Run with python3 connect4.py (requires Tkinter)."""

import random

ROWS, COLS = 6, 7
COLOURS = ("#172247", "#ff786f", "#ffcb57")


class Game:
    def __init__(self):
        self.board = [[0] * COLS for _ in range(ROWS)]
        self.player = 1
        self.winning = set()
        self.moves = 0

    @property
    def finished(self):
        return bool(self.winning) or self.moves == ROWS * COLS

    def drop(self, col):
        if self.finished or not 0 <= col < COLS or self.board[0][col]:
            return False
        row = next(r for r in reversed(range(ROWS)) if not self.board[r][col])
        self.board[row][col] = self.player
        self.moves += 1
        for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
            line = {(row, col)}
            for sign in (-1, 1):
                r, c = row + sign * dr, col + sign * dc
                while 0 <= r < ROWS and 0 <= c < COLS and self.board[r][c] == self.player:
                    line.add((r, c))
                    r, c = r + sign * dr, c + sign * dc
            if len(line) >= 4:
                self.winning.update(line)
        if not self.finished:
            self.player = 3 - self.player
        return True


ORDER = (3, 2, 4, 1, 5, 0, 6)


def four(bits):
    for step in (1, 7, 6, 8):
        pair = bits & (bits >> step)
        if pair & (pair >> (2 * step)):
            return True
    return False


def computer_move(game, level):
    # Each column occupies six playable bits and one separator.
    pieces = [0, 0, 0]
    heights = [0] * COLS
    cells = [[1 << (7 * c + h) for h in range(ROWS)] for c in range(COLS)]
    for col in ORDER:
        for row in reversed(range(ROWS)):
            player = game.board[row][col]
            if player:
                pieces[player] |= cells[col][heights[col]]
                heights[col] += 1

    def legal():
        return [c for c in ORDER if heights[c] < ROWS]

    def bit(col):
        return cells[col][heights[col]]

    moves = legal()
    if level == "Easy":
        return random.choice(moves)

    def search(mine, theirs, depth, alpha, beta):
        replies = legal()
        if not replies:
            return 0
        if any(four(mine | bit(col)) for col in replies):
            return 1000 + depth
        blocks = [col for col in replies if four(theirs | bit(col))]
        if len(blocks) > 1:
            return -999 - depth
        if depth <= 0 and not blocks:
            return sum(
                (4 - abs(col - 3)) *
                ((mine & column_mask).bit_count() - (theirs & column_mask).bit_count())
                for col, column_mask in enumerate(column_masks)
            )
        best = -2000
        for col in blocks or replies:
            placed = mine | bit(col)
            heights[col] += 1
            best = max(best, -search(theirs, placed, depth - 1, -beta, -alpha))
            heights[col] -= 1
            alpha = max(alpha, best)
            if alpha >= beta:
                break
        return best

    column_masks = [sum(column) for column in cells]
    for col in moves:
        if four(pieces[2] | bit(col)):
            return col
    best, pick = -2000, moves[0]
    depth = 7 if level == "Hard" else 1
    for col in moves:
        placed = pieces[2] | bit(col)
        heights[col] += 1
        score = -search(pieces[1], placed, depth, -2000, -best)
        heights[col] -= 1
        if score > best:
            best, pick = score, col
    return pick


class Window:
    def __init__(self, root, tk):
        self.root = root
        self.pending = None
        self.level = tk.StringVar(value="Medium")
        root.title("Connect 4")
        root.configure(bg="#172247")
        tk.Label(root, text="Connect 4", font=("Helvetica", 32, "bold"),
                 bg="#172247", fg="white").pack(pady=(16, 4))
        tk.Label(root, text="You play coral. Click the board to drop a disc.",
                 bg="#172247", fg="white").pack()
        tk.OptionMenu(root, self.level, "Easy", "Medium", "Hard").pack(pady=6)
        self.canvas = tk.Canvas(root, width=420, height=360, bg="#3459be", highlightthickness=0)
        self.canvas.pack(padx=16)
        self.canvas.bind("<Button-1>", lambda event: self.play(event.x // 60))
        for col in range(COLS):
            root.bind(str(col + 1), lambda event, c=col: self.play(c))
        self.status = tk.Label(root, bg="#172247", fg="white", font=("Helvetica", 15))
        self.status.pack(pady=6)
        tk.Button(root, text="New game", command=self.reset).pack(pady=(0, 12))
        self.reset()

    def reset(self):
        if self.pending is not None:
            self.root.after_cancel(self.pending)
            self.pending = None
        self.game = Game()
        self.draw()

    def play(self, col):
        if self.game.player != 1 or self.game.finished:
            return
        if not self.game.drop(col):
            self.status.configure(text="That spot is full. Try another.")
            return
        self.draw()
        if not self.game.finished:
            self.pending = self.root.after(300, self.computer_turn)

    def computer_turn(self):
        self.pending = None
        self.game.drop(computer_move(self.game, self.level.get()))
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        for row, cells in enumerate(self.game.board):
            for col, value in enumerate(cells):
                x, y = col * 60 + 30, row * 60 + 30
                rim = "white" if (row, col) in self.game.winning else "#2a4892"
                self.canvas.create_oval(x-24, y-24, x+24, y+24,
                                        fill=COLOURS[value], outline=rim, width=3)
        if self.game.winning:
            message = "You win!" if self.game.player == 1 else "Computer wins."
        elif self.game.finished:
            message = "It's a draw!"
        else:
            message = "Your turn" if self.game.player == 1 else "Computer is thinking…"
        self.status.configure(text=message)


if __name__ == "__main__":
    import tkinter as tk
    root = tk.Tk()
    Window(root, tk)
    root.mainloop()
