import os
import sys
import builtins
import importlib.util
import thumbyLibrary as library

builtins.ptr8 = library.ptr8

BASE = os.path.dirname(__file__)
LIB = os.path.join(BASE, "lib")
SAVES = os.path.join(BASE, "Saves")
GAMES_DIR = os.path.join(BASE, "Games")

_real_open = builtins.open

def thumby_open(path, *args, **kwargs):
    if isinstance(path, str):
        if path.startswith("/"):
            path = os.path.join(BASE, path.lstrip("/"))

    return _real_open(path, *args, **kwargs)

builtins.open = thumby_open

def get_games():
    games = []
    for folder in os.listdir(GAMES_DIR):
        game_path = os.path.join(GAMES_DIR, folder, folder + ".py")
        if os.path.exists(game_path):
            games.append(game_path)
    return games

def load_game(game_file, input_type):
    game_dir = os.path.dirname(game_file)

    library.inputState = input_type

    sys.path = [game_dir, LIB, SAVES] + sys.path

    spec = importlib.util.spec_from_file_location("game", game_file)
    module = importlib.util.module_from_spec(spec)

    spec.loader.exec_module(module)

    if hasattr(module, "main"):
        module.main()

while True:
    games = get_games()

    print("\nInstalled Games:\n")
    for i, g in enumerate(games):
        print(f"{i}: {os.path.basename(g)}")

    print("\nEnter -1 to exit")
    choice = int(input("Select Game: "))

    if choice == -1:
        break

    if choice < 0 or choice >= len(games):
        print("Invalid selection")
        continue

    print("\n0: Normal | Controler: 1 | Tas: 2")
    input_type = int(input("Input Mode: "))

    if input_type < 0 or input_type > 3:
        break

    load_game(os.path.abspath(games[choice]), input_type)