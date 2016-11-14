import endpoints
from protorpc import remote, messages
from hangman_api import HangmanAPI

import controllers.scores_controller as scores_ctrl
from models.score_model import (
    Score,
    ScoreForm,
    ScoreForms,
)

######### RESOURCE CONTAINERS ##########

USER_SCORE_REQUEST   = endpoints.ResourceContainer(
    user_name=messages.StringField(1))

GET_SCORES_REQUEST = endpoints.ResourceContainer(
    number_of_results=messages.StringField(1, required=False))


@HangmanAPI.api_class(resource_name='scores')
class ScoresEndpoints(remote.Service):

    @endpoints.method(response_message=ScoreForms,
                      path='scores',
                      name='get_scores',
                      http_method='GET')
    def get_scores(self, request):
        """Return all scores"""
        return scores_ctrl.get_scores()

    @endpoints.method(request_message=USER_SCORE_REQUEST,
                      response_message=ScoreForms,
                      path='scores/user/{user_name}',
                      name='get_user_scores',
                      http_method='GET')
    def get_user_scores(self, request):
        """Return all scores of a user"""
        return scores_ctrl.get_user_scores(request.user_name)


    @endpoints.method(request_message=GET_SCORES_REQUEST,
                      response_message=ScoreForms,
                      path='scores/high',
                      name='get_high_scores',
                      http_method='GET')
    def get_high_scores(self, request):
        """Returns a list of high scores"""
        return scores_ctrl.get_high_scores(request.number_of_results)
