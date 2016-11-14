import endpoints
from protorpc import remote, messages
from utils import get_by_urlsafe
from hangman_api import HangmanAPI

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

import controllers.games_controller as games_ctrl

######### RESOURCE CONTAINERS ##########

GET_GAME_REQUEST     = endpoints.ResourceContainer(
    urlsafe_game_key=messages.StringField(1))

GUESS_LETTER_REQUEST = endpoints.ResourceContainer(
    GuessLetterForm, urlsafe_game_key=messages.StringField(1))

GUESS_WORD_REQUEST = endpoints.ResourceContainer(
    GuessWordForm, urlsafe_game_key=messages.StringField(1))

GET_USER_GAMES_REQUEST = endpoints.ResourceContainer(
    user_name=messages.StringField(1))

CREATE_GAME_REQUEST = endpoints.ResourceContainer(CreateGameForm)

@HangmanAPI.api_class(resource_name='game')
class GamesEndpoints(remote.Service):

    @endpoints.method(request_message=CREATE_GAME_REQUEST,
                      response_message=GameStateForm,
                      path='games',
                      name='create_game',
                      http_method='POST')
    def create_game(self, request):
        """Create a game"""
        return games_ctrl.create_game(user_name=request.user_name,
                                      misses_allowed=request.misses_allowed)


    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameStateForm,
                      path='games/{urlsafe_game_key}',
                      name='get_game',
                      http_method='GET')
    def get_game(self, request):
        """Return a game state"""
        game = Game.get_game(request.urlsafe_game_key)
        return game.game_state("Here's the game you requested")


    @endpoints.method(request_message=GUESS_LETTER_REQUEST,
                      response_message=GameStateForm,
                      path='games/{urlsafe_game_key}/guess/letter',
                      name='guess_letter',
                      http_method='PUT')
    def guess_letter(self, request):
        """Guess a letter in a game. Returns the state of the game"""
        letter_guess = request.letter_guess.upper()
        game = Game.get_game(request.urlsafe_game_key)

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

        return game.letter_guess(letter_guess)


    @endpoints.method(request_message=GUESS_WORD_REQUEST,
                      response_message=GameStateForm,
                      path='games/{urlsafe_game_key}/guess/word',
                      name='guess_word',
                      http_method='PUT')
    def guess_word(self, request):
        """Guess the secret word in a game"""
        word_guess = request.word_guess.upper()
        game = Game.get_game(request.urlsafe_game_key)

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

        return game.guess_word(word_guess)


    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameHistoryForms,
                      path='games/{urlsafe_game_key}/history',
                      name='get_game_history',
                      http_method='GET')
    def get_game_history(self, request):
        """Get the history of a game"""
        game = Game.get_game(request.urlsafe_game_key)
        return game.create_history_form()


    @endpoints.method(request_message=GET_USER_GAMES_REQUEST,
                      response_message=GameStateForms,
                      path='games/user/{user_name}',
                      name='get_user_games',
                      http_method='GET')
    def get_user_games(self, request):
        """Return all games of a user"""
        user = users.get(request.user_name)
        games = Game.query(ancestor=user.key)
        games = games.filter(Game.game_cancelled == False,
                             Game.game_over == False)
        return GameStateForms(items=[game.game_state() for game in games])


    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameStateForm,
                      path='games/{urlsafe_game_key}/cancel',
                      name='cancel_game',
                      http_method='PUT')
    def cancel_game(self, request):
        """Cancel a game"""
        game = Game.get_game(request.urlsafe_game_key)
        return game.cancel_game()