import chess
import random

class OpeningBook:
    def __init__(self):
        self.book = {}
        self.construct()

    def add_entry(self, board, next_move):
        hash = board.board_fen().__hash__()

        if hash in self.book:
            if next_move not in self.book[hash]:
                self.book[hash].append(next_move)

        else:
            self.book[hash] = [next_move]

    def lookup(self, hash):
        if hash in self.book:
            return random.choice(self.book[hash])

        return None

    def construct(self):
        openings = [
            # Sveshnikov Sicilian
            ["e2e4", "c7c5", "g1f3", "b8c6", "d2d4", "c5d4", "f3d4", "g8f6", "b1c3", "e7e5", "d4b5", "d7d6"],

            # Nimzo
            ["d2d4", "g8f6", "c2c4", "e7e6", "b1c3", "f8b4", "g1f3", "e8g8"],

            # Ruy
            ["e2e4", "e7e5", "g1f3", "b8c6", "f1b5", "a7a6"]
        ]

        for opening in openings:
            board = chess.Board()
            for i in range(len(opening)):
                self.add_entry(board, opening[i])
                board.push(chess.Move.from_uci(opening[i]))


if __name__ == "__main__":
    book = OpeningBook()
    print(book.book)