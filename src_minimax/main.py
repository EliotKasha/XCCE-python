import berserk
import chess
import requests
import time
import settings
from engine import Engine

session = berserk.TokenSession(token=settings.API_KEY)
client = berserk.Client(session=session)
engine = Engine()

def send_challenge():
    challenge = client.challenges.create(
        username=settings.CHALLENGE_USER,
        rated=False,
        clock_limit=300,
        clock_increment=0,
        color="random",
        variant="standard"
    )

    print(f"---> Sent challenge to {settings.CHALLENGE_USER}")

    return challenge

# Handling state updates for game <game_id>
def play_game(game_id):
    board = chess.Board()
    bot_color = None
    last_move_count = 0

    # Event loop
    for event in client.bots.stream_game_state(game_id):

        # Start of game
        if event["type"] == "gameFull":
            state = event["state"]

            # Store bot color
            white_id = event["white"]["id"].lower()
            bot_id = client.account.get()["id"].lower()

            bot_color = "white" if white_id == bot_id else "black"

            # Custom fen handling
            initial_fen = event.get("initialFen")
            if initial_fen and initial_fen != "startpos":
                board = chess.Board(fen=initial_fen)

        # Ingame update (after move, etc.)
        elif event["type"] == "gameState":
            state = event

        moves = state.get("moves", "").split()  # Uci format

        # Check if lichess is being annoying w/ turns
        if last_move_count == len(moves) and len(moves) != 0:
            continue

        if hasattr(play_game, "initial_board"):
            board = play_game.initial_board.copy()
        else:
            play_game.initial_board = board.copy()

        # Replay all moves from the game from fresh position
        for move in moves:
            try:
                board.push_uci(move)
            except:
                pass  # Illegal move fallback

        # Only move if engine's turn
        if (board.turn == chess.WHITE and bot_color != "white") or (board.turn == chess.BLACK and bot_color != "black"):
            continue

        # Check game over
        status = state.get("status", "started")
        if status != "started":
            send_message(game_id, settings.END_MSG)
            print(f"--> Game Over: {status}")
            return

        # Make random move for now
        legal_moves = list(board.legal_moves)
        if legal_moves:
            move = engine.get_best_move(board, 3)
            print(f"--> Playing move <{move}>")
            client.bots.make_move(game_id, move)
            last_move_count = len(legal_moves) + 1
            time.sleep(0.5)  # Sry servers :(


# Sends some message <msg> to game <game_id>
def send_message(game_id, msg):
    url = f"https://lichess.org/api/bot/game/{game_id}/chat"
    headers = {
        "Authorization": f"Bearer {settings.API_KEY}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "room": "player",
        "text": msg
    }
    res = requests.post(url, headers=headers, data=data)
    if res.status_code != 200:
        print(f"Failed to send message: {res.status_code} - {res.text}")

# Listening loop
def listen():
    print("Awaiting...")

    for event in client.bots.stream_incoming_events():
        # On challenge
        if event["type"] == "challenge":

            challenge = event["challenge"]
            challenger = challenge["challenger"]["name"]
            print(f"Challenge received from account <{challenger}>")

            if challenge["speed"] in ["classical", "rapid", "blitz", "bullet"]:
                client.bots.accept_challenge(challenge["id"])
                print(f"--> Accepted challenge from <{challenger}>")

            else:
                print(challenge["speed"])
                client.bots.decline_challenge(challenge["id"], reason="timeControl")
                print(f"--> Declined challenge from <{challenger}>")

        # On game start
        elif event["type"] == "gameStart":
            print("--> Game started")
            game_id = event["game"]["id"]
            send_message(game_id, settings.WELCOME_MSG)

            # Loop
            try:
                play_game(game_id)

            except Exception as e:
                print(f"ERROR: {e}")


if __name__ == "__main__":
    if settings.AUTO_CHALLENGE:
        send_challenge()
    listen()
