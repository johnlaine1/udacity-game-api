import endpoints
from protorpc import remote, messages
from utils import get_by_urlsafe
from hangman_api import HangmanAPI

from models.score_model import (
    Score,
    ScoreForm,
    ScoreForms,
)

######### RESOURCE CONTAINERS ##########

# GET_GAME_REQUEST     = endpoints.ResourceContainer(
#     urlsafe_game_key=messages.StringField(1))

# GUESS_LETTER_REQUEST = endpoints.ResourceContainer(
#     GuessLetterForm, urlsafe_game_key=messages.StringField(1))

# GUESS_WORD_REQUEST = endpoints.ResourceContainer(
#     GuessWordForm, urlsafe_game_key=messages.StringField(1))

USER_SCORE_REQUEST   = endpoints.ResourceContainer(
    user_name=messages.StringField(1))

# GET_USER_GAMES_REQUEST = endpoints.ResourceContainer(
#     user_name=messages.StringField(1))

GET_SCORES_REQUEST = endpoints.ResourceContainer(
    number_of_results=messages.StringField(1, required=False))

# CREATE_USER_REQUEST = endpoints.ResourceContainer(CreateUserForm)

# CREATE_GAME_REQUEST = endpoints.ResourceContainer(CreateGameForm)

@HangmanAPI.api_class(resource_name='score')
class ScoresEndpoints(remote.Service):

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
        user = users.get(request.user_name)
        scores = Score.query(Score.user == user.key)
        return ScoreForms(items=[score.create_form() for score in scores])


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