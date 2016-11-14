import endpoints
from hangman_api import HangmanAPI
from api_endpoints.games_endpoints import GamesEndpoints
from api_endpoints.users_endpoints import UsersEndpoints
from api_endpoints.scores_endpoints import ScoresEndpoints
api = endpoints.api_server([HangmanAPI])

