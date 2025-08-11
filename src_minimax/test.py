from engine import Engine
import chess

if __name__ == "__main__":
    board = chess.Board("r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 4 4")
    engine = Engine()

    move = engine.get_best_move(board, 99)
    print(move)

# Tests on: r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 4 4

# + killer moves
# 1: b1c3 (+0.20) - 145 nodes @ 1.63 kn/s
# 2: b1c3 (-0.10) - 1022 nodes @ 19.17 kn/s
# 3: b1c3 (+0.20) - 5293 nodes @ 21.54 kn/s
# 4: b1c3 (+0.00) - 46497 nodes @ 19.55 kn/s
# 5: b1c3 (+0.15) - 167215 nodes @ 21.15 kn/s

# killer moves + delta pruning
# 1: b1c3 (+0.20) - 145 nodes @ 1.60 kn/s
# 2: b1c3 (-0.10) - 1020 nodes @ 22.07 kn/s
# 3: b1c3 (+0.20) - 5293 nodes @ 29.80 kn/s
# 4: b1c3 (+0.00) - 46409 nodes @ 24.44 kn/s
# 5: b1c3 (+0.15) - 167143 nodes @ 31.00 kn/s


# ANOMALY: FEN: r1bqkb1r/2p2ppp/p1np1n2/1p2p3/B3P3/2NP1N2/PPP2PPP/R1BQK2R - White to move
# With tt
# 1: a4b3 (+0.30) - 103 nodes @ 1.30 kn/s
# 2: a4b3 (+0.15) - 290 nodes @ 24.23 kn/s
# 3: a4b3 (+0.30) - 3810 nodes @ 30.32 kn/s
# 4: e1g1 (+0.20) - 14999 nodes @ 26.24 kn/s
# 5: a4b3 (+0.20) - 143413 nodes @ 32.33 kn/s
# Without tt
# 1: a4b3 (+0.30) - 103 nodes @ 0.99 kn/s
# 2: a4b3 (+0.15) - 424 nodes @ 26.06 kn/s
# 3: a4b3 (+0.30) - 4617 nodes @ 28.32 kn/s
# 4: a4b3 (+0.15) - 18644 nodes @ 25.60 kn/s
# 5: a4b3 (+0.30) - 146779 nodes @ 32.76 kn/s

