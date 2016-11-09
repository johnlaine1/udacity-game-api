import json

import endpoints
from protorpc import message_types
from protorpc import messages
from protorpc import remote
from google.appengine.ext import ndb

from models import User, Game, Score
from models import StringMessage, CreateGameForm, GameStateForm, GuessLetterForm
from models import GameStateForms, ScoreForm, ScoreForms, CreateUserForm
from models import RankingForms, GameHistoryForms
from models import GET_GAME_REQUEST, GUESS_LETTER_REQUEST, USER_SCORE_REQUEST
from models import GET_SCORES_REQUEST, GET_USER_GAMES_REQUEST, GUESS_WORD_REQUEST
from utils import get_by_urlsafe


##### GAME API #####
@endpoints.api(name='hangman', version = 'v1')
class HangmanAPI(remote.Service):
    """Hangman Game API"""

    @endpoints.method(request_message = CreateUserForm,
                      response_message = StringMessage,
                      path = 'user',
                      name = 'create_user',
                      http_method = 'POST')
    def create_user(self, request):
        """Create a user"""
        # Check if the user user already exists
        if User.query(User.user_name == request.user_name).get():
            raise endpoints.ConflictException(
                'Sorry, that username already exists')
        # Create the user and store in the database
        user = User(user_name=request.user_name,
                    email=request.email)
        user.put()
        return StringMessage(message = 'User {} has been created'.format(
            request.user_name))


    @endpoints.method(request_message=CreateGameForm,
                      response_message=GameStateForm,
                      path='game',
                      name='create_game',
                      http_method='POST')
    def create_game(self, request):
        """Create a game"""
        user = User.get_user(request.user_name)
        game = Game.create_game(user.key, request.misses_allowed)
        return game.game_state('A new game of Hangman has been created!')


    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameStateForm,
                      path='game/{urlsafe_game_key}',
                      name='get_game',
                      http_method='GET')
    def get_game(self, request):
        """Return a game state"""
        game = Game.get_game(request.urlsafe_game_key)
        return game.game_state("Here's the game you requested")


    @endpoints.method(request_message=GUESS_LETTER_REQUEST,
                      response_message=GameStateForm,
                      path='game/{urlsafe_game_key}/guess/letter',
                      name='guess_letter',
                      http_method='PUT')
    def guess_letter(self, request):
        """Guess a letter in a game. Returns the state of the game"""
        game = Game.get_game(request.urlsafe_game_key)
        return game.letter_guess(request.letter_guess.upper())


    @endpoints.method(request_message=GUESS_WORD_REQUEST,
                      response_message=GameStateForm,
                      path='game/{urlsafe_game_key}/guess/word',
                      name='guess_word',
                      http_method='PUT')
    def guess_word(self, request):
        """Guess the secret word in a game"""
        game = Game.get_game(request.urlsafe_game_key)
        return game.guess_word(request.word_guess.upper())


    @endpoints.method(response_message=ScoreForms,
                      path='scores',
                      name='get_scores',
                      http_method='GET')
    def get_scores(self, request):
        """Return all scores"""
        return ScoreForms(items=[score.create_form() for score in Score.query()])

    @endpoints.method(request_message=USER_SCORE_REQUEST,
                      response_message=ScoreForms,
                      path='scores/user/{user_name}',
                      name='get_user_scores',
                      http_method='GET')
    def get_user_scores(self, request):
        """Return all scores of a user"""
        user = User.get_user(request.user_name)
        scores = Score.query(Score.user == user.key)
        return ScoreForms(items=[score.create_form() for score in scores])


    @endpoints.method(request_message=GET_USER_GAMES_REQUEST,
                      response_message=GameStateForms,
                      path='games/user/{user_name}',
                      name='get_user_games',
                      http_method='GET')
    def get_user_games(self, request):
        """Return all games of a user"""
        user = User.get_user(request.user_name)
        games = Game.query(ancestor=user.key)
        return GameStateForms(items=[game.game_state() for game in games])


    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameStateForm,
                      path='game/{urlsafe_game_key}/cancel',
                      name='cancel_game',
                      http_method='PUT')
    def cancel_game(self, request):
        """Cancel a game"""
        game = Game.get_game(request.urlsafe_game_key)
        msg = 'The game has been cancelled'

        # If the requested game is already over.
        if game.game_over:
            raise endpoints.BadRequestException('This game is already over')

        # If the requested game has already been cancelled.
        if game.game_cancelled:
            raise endpoints.BadRequestException('This game has already been cancelled')

        game.game_cancelled = True
        game.update_history(guess='', result='Game Cancelled')
        game.put()
        return game.game_state(msg)


    @endpoints.method(request_message=GET_SCORES_REQUEST,
                      response_message=ScoreForms,
                      path='scores/high',
                      name='get_high_scores',
                      http_method='GET')
    def get_high_scores(self, request):
        """Returns a list of high scores"""
        scores = Score.query().order(-Score.score)
        if request.number_of_results:
            scores = scores.fetch(int(request.number_of_results))
        return ScoreForms(items=[score.create_form() for score in scores])


    @endpoints.method(response_message=RankingForms,
                      path='user/ranking',
                      name='get_user_rankings',
                      http_method='GET')
    def get_user_rankings(self, request):
        """Returns a list of users with the highest scores"""
        users = User.query().order(-User.score)
        return RankingForms(items=[user.create_ranking_form() for user in users])


    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameHistoryForms,
                      path='game/{urlsafe_game_key}/history',
                      name='get_game_history',
                      http_method='GET')
    def get_game_history(self, request):
        """Get the history of a game"""
        game = Game.get_game(request.urlsafe_game_key)
        return game.create_history_form()


api = endpoints.api_server([HangmanAPI])