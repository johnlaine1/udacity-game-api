import endpoints
from protorpc import message_types
from protorpc import messages
from protorpc import remote

from models import User
from models import Test, StringMessage

##### RESOURCE CONTAINERS #####
CREATE_USER_REQUEST = endpoints.ResourceContainer(
                      user_name = messages.StringField(1, required = True))
    
##### GAME API #####
@endpoints.api(name='hangman', version = 'v1')
class HangmanAPI(remote.Service):
    """Hangman Game API"""
    @endpoints.method(request_message = message_types.VoidMessage,
                      response_message = Test,
                      path = 'test',
                      http_method = 'GET',
                      name = 'test')
    def test(self, request):
        return Test(message = 'This is a test, this is only a test')
        
    
    @endpoints.method(request_message = CREATE_USER_REQUEST,
                      response_message = StringMessage,
                      path = 'user',
                      name = 'create_user',
                      http_method = 'POST')
    def create_user(self, request):
        """Create a user"""
        # Check if the user name already exists
        if User.query(User.name == request.user_name).get():
            raise endpoints.ConflictException(
                'Sorry, that username already exists')
        # Create the user and store in the database
        user = User(name = request.user_name)
        user.put()
        return StringMessage(message = 'User {} has been created'.format(
            request.user_name))
        
api = endpoints.api_server([HangmanAPI])