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
from models import GET_GAME_REQUEST, GUESS_LETTER_REQUEST, USER_SCORE_REQUEST,
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
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            return game.game_state("Here's the game you requested")
        else:
            raise endpoints.NotFoundException('No Game Found')


    @endpoints.method(request_message=GUESS_LETTER_REQUEST,
                      response_message=GameStateForm,
                      path='game/{urlsafe_game_key}/guess/letter',
                      name='guess_letter',
                      http_method='PUT')
    def guess_letter(self, request):
        """Guess a letter in a game. Returns the state of the game"""
        letter_guess = request.letter_guess.upper()
        game = get_by_urlsafe(request.urlsafe_game_key, Game)

        # If the game is already over
        if game.game_over:
            msg = 'Error, This game is already over.'
            raise endpoints.BadRequestException(msg)

        # If the game has been cancelled
        if game.game_cancelled:
            msg = 'Error, this game has been cancelled.'
            raise endpoints.BadRequestException(msg)

        # If more than one letter is submitted.
        if len(letter_guess) > 1:
            msg = 'Error, you can only choose one letter at a time.'
            raise endpoints.BadRequestException(msg)

        # If letter guess has already been tried.
        if game.letters_guessed and letter_guess in game.letters_guessed:
            msg = 'Sorry, you already tried that letter, please pick another.'
            return game.game_state(msg)

        # If letter guess is incorrect.
        if letter_guess not in game.secret_word:
            msg = 'Sorry, that is incorrect'
            game.decrement_misses_remaining()
            game.update_letters_guessed(letter_guess)
            game.update_history(guess=letter_guess, result='Incorrect')

            if game.misses_remaining < 1:
                game.end_game(False)
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
                game.end_game(True)
            else:
                game.update_score(letters=num_of_letters)
                msg = 'Nice Job, the letter {} is in the secret word'.format(letter_guess)

            game.put()
            return game.game_state(msg)


    @endpoints.method(request_message=GUESS_WORD_REQUEST,
                      response_message=GameStateForm,
                      path='game/{urlsafe_game_key}/guess/word',
                      name='guess_word',
                      http_method='PUT')
    def guess_word(self, request):
        """Guess the secret word in a game"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        word_guess = request.word_guess.upper()

        # If the game is already over
        if game.game_over:
            msg = 'Error, This game is already over.'
            raise endpoints.BadRequestException(msg)

        # If the game has been cancelled
        if game.game_cancelled:
            msg = 'Error, this game has been cancelled.'
            raise endpoints.BadRequestException(msg)

        # If the guess is incorrect
        if word_guess != game.secret_word:
            game.decrement_misses_remaining()
            game.update_history(guess=word_guess, result='Incorrect')
            if game.misses_remaining < 1:
                game.end_game(won=False)
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
            game.end_game(won=True)
            msg = 'Congratulations! you win!'

            game.put()
            return game.game_state(msg)


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
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        msg = 'The game has been cancelled'

        # If the requested game does not exist.
        if not game:
            raise endpoints.NotFoundException('No game found.')

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
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        return game.create_history_form()


api = endpoints.api_server([HangmanAPI])