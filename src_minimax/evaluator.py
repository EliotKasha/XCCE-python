import chess
from numba import njit
import numpy as np

PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 300,
    chess.BISHOP: 320,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0  # Can't capture
}

PAWN_TABLE = np.array([
    0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
     5,  5, 10, 25, 25, 10,  5,  5,
     0,  0,  0, 20, 20, 0,  0,  0,
     5, -5,-10,  0,  0,-10, -5,  5,
     5, 10, 10,-20,-20, 10, 10,  5,
     0,  0,  0,  0,  0,  0,  0,  0
], dtype=np.int32)

KNIGHT_TABLE = np.array([
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50
], dtype=np.int32)

BISHOP_TABLE = np.array([
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20
], dtype=np.int32)

ROOK_TABLE = np.array([
     0,  0,  0,  0,  0,  0,  0,  0,
     5, 10, 10, 10, 10, 10, 10,  5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
     0,  0,  0,  5,  5,  0,  0,  0
], dtype=np.int32)

QUEEN_TABLE = np.array([
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5,  5,  5,  5,  0,-10,
     -5,  0,  5,  5,  5,  5,  0, -5,
      0,  0,  5,  5,  5,  5,  0, -5,
    -10,  5,  5,  5,  5,  5,  0,-10,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20
], dtype=np.int32)

KING_TABLE = np.array([
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
     20, 20,  0,  0,  0,  0, 20, 20,
     20, 30, 10,  0,  0, 10, 30, 20
], dtype=np.int32)

PIECE_SQUARE_TABLES = np.array([
    np.zeros(64, dtype=np.int32),
    PAWN_TABLE.tolist(),
    KNIGHT_TABLE.tolist(),
    BISHOP_TABLE.tolist(),
    ROOK_TABLE.tolist(),
    QUEEN_TABLE.tolist(),
    KING_TABLE.tolist()
])

@njit
def get_piece_square_table_value(piece_type, square, is_white):
    if piece_type == 0 or piece_type > 6:
        return 0

    table = PIECE_SQUARE_TABLES[piece_type]

    if is_white:
        return table[square ^ 56]

    else:
        return table[square]

# Eval function in cp
def get_eval(board):
    score = 0

    # Piece-Square table and raw material
    for square in chess.SQUARES:
        piece = board.piece_at(square)

        if piece:

            material_score = PIECE_VALUES[piece.piece_type]
            pst_score = get_piece_square_table_value(piece.piece_type, square, piece.color == chess.WHITE)

            if piece.color == chess.WHITE:
                score += material_score + pst_score
            else:
                score -= material_score + pst_score

    # Mobility bonus
    # score += evaluate_mobility(board)

    # Pawn structure bonus
    score += evaluate_pawn_structure(board)

    # King safety bonus
    score += evaluate_king_safety(board)

    return score

def evaluate_mobility(board):
    score = 0

    current_mobility = len(list(board.legal_moves))

    temp_board = board.copy()
    temp_board.push(chess.Move.null())
    opponent_mobility = len(list(temp_board.legal_moves))

    if board.turn == chess.WHITE:
        score += (current_mobility - opponent_mobility) * 2
    else:
        score += (opponent_mobility - current_mobility) * 2

    return score

def evaluate_pawn_structure(board):
    white_pawns = board.pieces(chess.PAWN, chess.WHITE)
    black_pawns = board.pieces(chess.PAWN, chess.BLACK)

    if not (white_pawns or black_pawns):
        return 0

    score = 0

    # White pawns
    if white_pawns:
        file_counts = [0] * 8
        for square in white_pawns:
            file_counts[square & 7] += 1

        # Doubled pawns only
        for count in file_counts:
            if count > 1:
                score -= 15 * (count - 1)

        # Passed pawns only
        for square in white_pawns:
            file, rank = square & 7, square >> 3
            passed = True
            for enemy_sq in black_pawns:
                e_file, e_rank = enemy_sq & 7, enemy_sq >> 3
                if abs(e_file - file) <= 1 and e_rank > rank:
                    passed = False
                    break
            if passed:
                score += 15 + (7 - rank) * 5  # Simple distance bonus

    # Black pawns
    if black_pawns:
        file_counts = [0] * 8
        for square in black_pawns:
            file_counts[square & 7] += 1

        for count in file_counts:
            if count > 1:
                score += 15 * (count - 1)

        for square in black_pawns:
            file, rank = square & 7, square >> 3
            passed = True
            for enemy_sq in white_pawns:
                e_file, e_rank = enemy_sq & 7, enemy_sq >> 3
                if abs(e_file - file) <= 1 and e_rank < rank:
                    passed = False
                    break
            if passed:
                score -= 15 + rank * 5

    return score


def evaluate_king_safety(board):
    # Skip in endgame when king activity is more important than safety
    total_pieces = len(board.piece_map())
    if total_pieces <= 12:
        return 0

    score = 0
    white_king = board.king(chess.WHITE)
    black_king = board.king(chess.BLACK)

    if white_king is None or black_king is None:
        return 0

    white_pawns = board.pieces(chess.PAWN, chess.WHITE)
    black_pawns = board.pieces(chess.PAWN, chess.BLACK)

    # Evaluate both kings
    for king_sq, color, pawns, multiplier in [
        (white_king, chess.WHITE, white_pawns, 1),
        (black_king, chess.BLACK, black_pawns, -1)
    ]:
        king_file, king_rank = king_sq & 7, king_sq >> 3

        # Castling rights bonus
        if board.has_kingside_castling_rights(color):
            score += multiplier * 15
        if board.has_queenside_castling_rights(color):
            score += multiplier * 10

        # Pawn shelter - check king file and adjacent files
        for check_file in [king_file - 1, king_file, king_file + 1]:
            if 0 <= check_file <= 7:
                for pawn_sq in pawns:
                    pawn_file, pawn_rank = pawn_sq & 7, pawn_sq >> 3
                    if pawn_file == check_file:
                        # Good shelter ranks: 1-2 for white, 5-6 for black
                        if (color == chess.WHITE and 1 <= pawn_rank <= 2) or \
                                (color == chess.BLACK and 5 <= pawn_rank <= 6):
                            bonus = 12 if check_file == king_file else 8
                            score += multiplier * bonus
                            break

        # King exposure penalties
        if color == chess.WHITE and king_rank > 2:
            score += multiplier * (-(king_rank - 2) * 8)
        elif color == chess.BLACK and king_rank < 5:
            score += multiplier * (-(5 - king_rank) * 8)

        # Center file penalty
        if 2 <= king_file <= 5:
            score += multiplier * (-10)

    return score