import endpoints
from protorpc import remote
from hangman_api import HangmanAPI

from models.user_model import (
    RankingForm,
    RankingForms,
    UserMessage,
    CreateUserForm
)
import controllers.users_controller as users_ctrl

CREATE_USER_REQUEST = endpoints.ResourceContainer(CreateUserForm)


# API Endpoints
@HangmanAPI.api_class(resource_name='users')
class UsersEndpoints(remote.Service):

    @endpoints.method(request_message=CREATE_USER_REQUEST,
                      response_message=UserMessage,
                      path = 'users',
                      name = 'create_user',
                      http_method = 'POST')
    def create_user(self, request):
        """Create a user"""
        return users_ctrl.create_user(request.user_name, request.email)


    @endpoints.method(response_message=RankingForms,
                      path='users/ranking',
                      name='get_user_rankings',
                      http_method='GET')
    def get_user_rankings(self, request):
        """Returns a list of users with the highest scores"""
        return users_ctrl.get_user_rankings()
