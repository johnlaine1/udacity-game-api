import endpoints

from utils import secret_word_generator

from models.user_model import User
from models.game_model import (
    Game,
    GameStateForm,
    GameStateForms,
    CreateGameForm,
    GuessLetterForm,
    GuessWordForm,
    GameHistoryForm,
    GameHistoryForms,
)

def create_game(user_name, misses_allowed):
    """Create a game"""
    user = User.get_by_name(user_name)
    secret_word = secret_word_generator()
    current_solution = ''.join(['_' for l in secret_word])

    # Check if misses_allowed exists and if so make sure it's a number
    if misses_allowed:
        if not misses_allowed.isnumeric():
            msg = 'Error, only numbers are allowed in misses_allowed'
            raise endpoints.BadRequestException(msg)
        else:
            misses_allowed = int(misses_allowed)

    else:
        misses_allowed = 5

    game = Game.create_game(user=user.key,
                            misses_allowed=misses_allowed,
                            secret_word=secret_word,
                            current_solution=current_solution)

    return game.game_state('A new game of Hangman has been created!')

def get_game():
    pass

def guess_letter():
    pass

def guess_word():
    pass

def get_game_history():
    pass

def get_user_games():
    pass

def cancel_game():
    pass