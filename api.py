import endpoints
from protorpc import message_types
from protorpc import messages
from protorpc import remote

from models import Test

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
        
    
api = endpoints.api_server([HangmanAPI])