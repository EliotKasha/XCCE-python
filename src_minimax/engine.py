import chess
from evaluator import get_eval, PIECE_VALUES
from transposition_table import TranspositionTable
from book import OpeningBook
import math
import time
import settings

class Engine:
    def __init__(self):
        self.tt = TranspositionTable()
        self.book = OpeningBook()
        self.nodes_searched = 0
        self.quiescence_cap = 10  # Cut off quiescence at 10 moves
        self.killer_moves = {}
        self.starting_depth = 0

    def use_nmp(self):
        return False

    # Returns eval + best move
    def minimax(self, board, depth, alpha, beta, maximizing):
        self.nodes_searched += 1
        hash = board.board_fen().__hash__()  # Board hash via fen for tt

        tt_score, tt_move = self.tt.lookup(hash, depth)
        if tt_score is not None:
            return tt_score, tt_move

        # Game over
        if board.is_checkmate():
            if board.turn == chess.WHITE:
                score = -99999 - depth
            else:
                score = 99999 + depth
            self.tt.store(hash, depth, score)
            return score, None

        if board.is_stalemate() or board.is_insufficient_material():
            self.tt.store(hash, depth, 0)
            return 0, None

        # Max depth
        if depth <= 0:
            return self.quiescence(board, alpha, beta, maximizing, 0)

        # Null move pruning
        if self.use_nmp() and (self.starting_depth - depth) >= 2 and not board.is_check() and self.has_non_pawn_material(board, board.turn):
            r = 2

            # Play null
            board.push(chess.Move.null())

            null_score, _ = self.minimax(board, depth - 1 - r, -beta, -alpha, not maximizing)
            null_score = -null_score

            board.pop()

            if null_score >= beta:
                return beta, None


        best_move = None

        # Move ordering
        moves = list(board.legal_moves)
        ordered_moves = self.order_moves(board, moves, tt_move, depth)

        if maximizing:
            best_score = -math.inf
            for move in ordered_moves:
                board.push(move)
                score, _ = self.minimax(board, depth - 1, alpha, beta, False)
                board.pop()

                if score > best_score:
                    best_score = score
                    best_move = move

                alpha = max(alpha, best_score)
                if beta <= alpha:
                    # Killers
                    if not board.is_capture(move) and not move.promotion:
                        self.add_killer(move, depth)
                    break

            self.tt.store(hash, depth, best_score, best_move)

            return best_score, best_move

        else:
            best_score = math.inf
            for move in ordered_moves:
                board.push(move)
                score, _ = self.minimax(board, depth - 1, alpha, beta, True)
                board.pop()

                if score < best_score:
                    best_score = score
                    best_move = move

                beta = min(beta, best_score)
                if beta <= alpha:
                    # Killers
                    if not board.is_capture(move) and not move.promotion:
                        self.add_killer(move, depth)
                    break

            self.tt.store(hash, depth, best_score, best_move)

            return best_score, best_move

    # Continue to explore noisy moves past default depth cap
    def quiescence(self, board, alpha, beta, maximizing, quiescence_depth):
        self.nodes_searched += 1

        if quiescence_depth >= self.quiescence_cap:
            return get_eval(board), None

        stand_pat = get_eval(board)
        best_score = stand_pat
        best_move = None

        # Delta pruning
        big_delta = 900

        if maximizing:
            if stand_pat >= beta:
                return beta, None

            if stand_pat + big_delta < alpha:
                return alpha, None

            if stand_pat > alpha:
                alpha = stand_pat

        else:
            if stand_pat <= alpha:
                return alpha, None

            if stand_pat - big_delta > beta:
                return beta, None

            if stand_pat < beta:
                beta = stand_pat

        noisy_moves = self.get_noisy_moves(board)

        if not noisy_moves:
            return stand_pat, None

        ordered_noisy_moves = self.order_moves(board, noisy_moves, None, 0)

        if maximizing:
            for move in ordered_noisy_moves:
                board.push(move)
                score, _ = self.quiescence(board, alpha, beta, False, quiescence_depth+1)
                board.pop()

                if score > best_score:
                    best_score = score
                    best_move = move

                alpha = max(alpha, best_score)
                if beta <= alpha:
                    break

            return best_score, best_move

        else:
            for move in ordered_noisy_moves:
                board.push(move)
                score, _ = self.quiescence(board, alpha, beta, True, quiescence_depth+1)
                board.pop()

                if score < best_score:
                    best_score = score
                    best_move = move

                beta = min(beta, best_score)
                if beta <= alpha:
                    break

            return best_score, best_move

    # Returns all noisy moves (checks captures promotions)
    def get_noisy_moves(self, board):
        noisy_moves = []

        for move in board.legal_moves:
            if board.is_capture(move):
                noisy_moves.append(move)

            elif move.promotion:
                noisy_moves.append(move)

        return noisy_moves

    def add_killer(self, move, depth):
        if depth not in self.killer_moves:
            self.killer_moves[depth] = []

        if move in self.killer_moves[depth]:
            return

        # Pop oldest if more than 2 killers in a given depth
        self.killer_moves[depth].insert(0, move)
        if len(self.killer_moves[depth]) > 2:
            self.killer_moves[depth].pop()

    def get_killer_score(self, move, depth):
        if depth not in self.killer_moves:
            return 0

        if move in self.killer_moves[depth]:
            # First killer move gets better score
            i = self.killer_moves[depth].index(move)
            return 70000 - (i * 1000)

        return 0

    def order_moves(self, board, moves, tt_move, depth=0):

        def move_score(move):
            score = 0

            # 1st tt
            if move == tt_move:
                return 1000000

            # 2nd captures (mvv lva)
            if board.is_capture(move):
                victim = board.piece_at(move.to_square)
                attacker = board.piece_at(move.from_square)

                if victim and attacker:
                    victim_score = PIECE_VALUES[victim.piece_type] // 100
                    attacker_score = PIECE_VALUES[attacker.piece_type] // 100

                    mvv_lva_score = victim_score * 10 - attacker_score
                    score += 100000 + mvv_lva_score

            # 3rd promotions
            elif move.promotion == chess.QUEEN:
                score += 90000
            elif move.promotion:
                score += 80000

            else:
                score += self.get_killer_score(move, depth)

            return score

        return sorted(moves, key=move_score, reverse=True)



    '''
    # Move ordering
    def order_moves(self, board, moves, tt_move):
        ordered_moves = []

        # 1st transposition table moves
        if tt_move and tt_move in moves:
            ordered_moves.append(tt_move)

        # 2nd captures
        captures = [move for move in moves if move != tt_move and board.is_capture(move)]
        ordered_captures = self.order_captures(board, captures)
        ordered_moves.extend(ordered_captures)

        # 3rd checks and promotions
        for move in moves:
            if (move != tt_move and not board.is_capture(move) and
                (move.promotion)):
                ordered_moves.append(move)

        # Rest
        for move in moves:
            if (move != tt_move and not board.is_capture(move) and
                not move.promotion):
                ordered_moves.append(move)

        return ordered_moves
    '''

    def get_pv(self, board, depth):
        pv = []
        temp_board = board.copy()

        for i in range(depth):
            hash = temp_board.board_fen().__hash__()
            _, tt_move = self.tt.lookup(hash, 0)

            if tt_move is None or tt_move not in temp_board.legal_moves:
                break

            pv.append(tt_move)
            temp_board.push(tt_move)

            if temp_board.is_game_over():
                break

        return pv

    def has_non_pawn_material(self, board, color):
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece and piece.color == color and piece.piece_type not in [chess.PAWN, chess.KING]:
                return True

        return False

    # ID best move
    def get_best_move(self, board, max_depth):
        print(f"FEN: {board.board_fen()} - " + ("White" if board.turn == chess.WHITE else "Black") + " to move")
        if settings.USE_BOOK:
            b = self.book.lookup(board.board_fen().__hash__())
            if b:
                return b

        best_move = None
        self.tt.clear()
        self.killer_moves = {}
        maximizing = (board.turn == chess.WHITE)

        for depth in range(1, max_depth + 1):
            self.starting_depth = depth
            self.nodes_searched = 0
            start_time = time.time()

            # Actual call
            score, move = self.minimax(board, depth, -math.inf, math.inf, maximizing)
            best_move = move

            depth_time = time.time() - start_time

            pv = self.get_pv(board, depth)
            pv_str = " ".join(str(m) for m in pv)

            # Notes
            print(f"{depth}: {move} ({score/100:+.2f}) - {self.nodes_searched} nodes @ {self.nodes_searched / depth_time / 1000:.2f} kn/s - pv {pv_str}")

            # Early stopping if mate found
            if score >= 99999 or score <= -99999:
                print(f"Mate found, stopping at depth {depth}")
                return best_move

        if best_move is None:
            return list(board.legal_moves)[0]

        return best_move