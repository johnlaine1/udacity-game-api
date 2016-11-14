import endpoints
from datetime import date

from utils import secret_word_generator

from models.user_model import User
from models.score_model import Score
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

def get_game(urlsafe_game_key):
    """Get a game"""
    game = Game.get_game(urlsafe_game_key)
    return game.game_state("Here's the game you requested")

def guess_letter(urlsafe_game_key, letter_guess):
    """Make a letter guess in a game"""
    letter_guess = letter_guess.upper()
    game = Game.get_game(urlsafe_game_key)

    # If the game is already over
    if game.game_over:
        msg = 'Error, This game is already over.'
        raise endpoints.BadRequestException(msg)

    # If the game has been cancelled
    if game.game_cancelled:
        msg = 'Error, this game has been cancelled.'
        raise endpoints.BadRequestException(msg)

    # Check for illegal characters
    if not letter_guess.isalpha():
        msg = 'Error, only letters from a-z are accepted'
        raise endpoints.BadRequestException(msg)

    # If more than one letter is submitted.
    if len(letter_guess) > 1:
        msg = 'Error, you can only choose one letter at a time.'
        raise endpoints.BadRequestException(msg)

    # If letter guess has already been tried.
    if game.letters_guessed and letter_guess in game.letters_guessed:
        msg = 'Sorry, you already tried that letter, please pick another.'
        raise endpoints.BadRequestException(msg)

    # If letter guess is incorrect.
    if letter_guess not in game.secret_word:
        msg = 'Sorry, that is incorrect'
        game.decrement_misses_remaining()
        game.update_letters_guessed(letter_guess)
        game.update_history(guess=letter_guess, result='Incorrect')

        if game.misses_remaining < 1:
            end_game(game, False)
            game.put()
            msg = 'Sorry, that is incorrect and the game is now over.'
            return game.game_state(msg)

        game.put()
        return game.game_state(msg)

    # If letter guess is correct
    if letter_guess in game.secret_word:
        num_of_letters = game.secret_word.count(letter_guess)
        game_won = game.update_current_solution(letter_guess)
        game.update_letters_guessed(letter_guess)
        game.update_history(guess=letter_guess, result='Correct')

        if game_won:
            msg = "Great Job, you won the game!"
            game.update_score(letters=num_of_letters, words=1)
            end_game(gaem, True)
        else:
            game.update_score(letters=num_of_letters)
            msg = 'Nice Job, the letter {} is in the secret word'.format(letter_guess)

        game.put()
        return game.game_state(msg)

def guess_word(urlsafe_game_key, word_guess):
    """Make a word guess in a game"""
    word_guess = word_guess.upper()
    game = Game.get_game(urlsafe_game_key)

    # If the game is already over
    if game.game_over:
        msg = 'Error, This game is already over.'
        raise endpoints.BadRequestException(msg)

    # If the game has been cancelled
    if game.game_cancelled:
        msg = 'Error, this game has been cancelled.'
        raise endpoints.BadRequestException(msg)

    # Check for illegal characters
    if not word_guess.isalpha():
        msg = 'Error, only letters from a-z are accepted'
        raise endpoints.BadRequestException(msg)

    # If the guess is incorrect
    if word_guess != game.secret_word:
        game.decrement_misses_remaining()
        game.update_history(guess=word_guess, result='Incorrect')
        if game.misses_remaining < 1:
            end_game(game, False)
            game.update_history(guess='', result='Game Lost')
            msg = 'Sorry, that was the wrong answer and the game is over'
        else:
            msg = 'Sorry, that was not the correct answer'

        game.put()
        return game.game_state(msg)

    # If the guess is correct
    if word_guess == game.secret_word:
        blanks = game.current_solution.count('_')
        game.update_score(blanks=blanks, words=1)
        game.update_history(guess=word_guess, result='Correct')
        end_game(game, True)
        msg = 'Congratulations! you win!'

        game.put()
        return game.game_state(msg)

def get_game_history(urlsafe_game_key):
    """Get a games history"""
    game = Game.get_game(urlsafe_game_key)
    return game.create_history_form()

def get_user_games(user_name):
    """Get a user's games"""
    user = User.get_by_name(user_name)
    games = Game.query(ancestor=user.key)
    games = games.filter(Game.game_cancelled == False,
                         Game.game_over == False)
    return GameStateForms(items=[game.game_state() for game in games])

def cancel_game(urlsafe_game_key):
    """Cancels a game"""
    game = Game.get_game(urlsafe_game_key)
    msg = 'The game has been cancelled'

    # If the requested game is already over.
    if game.game_over:
        msg = 'This game is already over'
        raise endpoints.BadRequestException(msg)

    # If the requested game has already been cancelled.
    if game.game_cancelled:
        msg = 'This game has already been cancelled'
        raise endpoints.BadRequestException(msg)

    game.game_cancelled = True
    game.update_history(guess='', result='Game Cancelled')
    game.put()
    return game.game_state(msg)

def end_game(game, won=False):
    """Ends a game"""
    game.game_over = True

    if won:
        game.update_history(guess='', result='Game Won')
        game.current_solution = game.secret_word
        user = game.user.get()
        user.score += game.score
        user.put()
        score = Score(
            user=game.user,
            date=date.today(),
            won=won,
            score=game.score)
        score.put()
    else:
        game.update_history(guess='', result='Game Lost')