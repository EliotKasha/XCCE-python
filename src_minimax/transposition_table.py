import chess

class TranspositionTable:
    def __init__(self):
        self.table = {}

    def store(self, hash, depth, score, best_move=None):
        if hash in self.table:
            if depth < self.table[hash]["depth"]:  # Only add higher depth entries
                return

        self.table[hash] = {
            "depth": depth,
            "score": score,
            "best_move": best_move,
        }

    def lookup(self, hash, depth):
        if hash not in self.table:
            return None, None

        entry = self.table[hash]

        if entry["depth"] >= depth:
            return entry["score"], entry["best_move"]

        return None, entry["best_move"]

    def clear(self):
        self.table = {}