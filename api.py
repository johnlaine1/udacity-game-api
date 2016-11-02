import endpoints
from protorpc import message_types
from protorpc import messages
from protorpc import remote

from models import User, Game, Score
from models import StringMessage, CreateGameForm, GameState, GuessLetterForm
from models import ScoreForm, ScoreForms

from utils import get_by_urlsafe

##### RESOURCE CONTAINERS #####
CREATE_USER_REQUEST  = endpoints.ResourceContainer(
                        user_name=messages.StringField(1, required = True),
                        email=messages.StringField(2))
GET_GAME_REQUEST     = endpoints.ResourceContainer(
                        urlsafe_game_key=messages.StringField(1))
GUESS_LETTER_REQUEST = endpoints.ResourceContainer(GuessLetterForm,
                        urlsafe_game_key=messages.StringField(1))
USER_SCORE_REQUEST   = endpoints.ResourceContainer(user_name=messages.StringField(1))

##### GAME API #####
@endpoints.api(name='hangman', version = 'v1')
class HangmanAPI(remote.Service):
    """Hangman Game API"""

    @endpoints.method(request_message = CREATE_USER_REQUEST,
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
                      response_message=GameState,
                      path='game',
                      name='create_game',
                      http_method='POST')
    def create_game(self, request):
        """Create a game"""
        user = User.query(User.user_name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                'A user with that name does not exist!')
        game = Game.create_game(user.key, request.misses_allowed)
        return game.game_state('A new game of Hangman has been created!')
                    
                    
    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameState,
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
                      response_message=GameState,
                      path='game/{urlsafe_game_key}',
                      name='guess_letter',
                      http_method='PUT')
    def guess_letter(self, request):
        """Guess a letter in a game. Returns the state of the game"""
        letter_guess = request.letter_guess.upper()
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        
        # If the game is already over
        if game.game_over:
            msg = 'Sorry, this game is already over.'
            return game.game_state(msg)
        
        # If more than one letter is submitted.
        if len(letter_guess) > 1:
            msg = 'Sorry, you can only choose one letter at a time.'
            return game.game_state(msg)

        # If letter guess has already been tried.
        if game.letters_guessed and letter_guess in game.letters_guessed:
            msg = 'Sorry, you already tried that letter, please pick another.'
            return game.game_state(msg)
        
        # If letter guess is incorrect.
        if letter_guess not in game.secret_word:
            msg = 'Sorry, that is incorrect'
            game.misses_remaining -=1
            game.letters_guessed = game.letters_guessed + letter_guess
            game.put()
            if game.misses_remaining < 1:
                game.end_game(False)
                msg = 'Sorry, that is incorrect and the game is now over.'
                return game.game_state(msg)
            return game.game_state(msg)
            
        # If letter guess is correct
        if letter_guess in game.secret_word:
            # Update the letters guessed property
            game.letters_guessed = game.letters_guessed + letter_guess
            game_won = game.update_current_solution(letter_guess)
            
            if game_won:
                msg = "Great Job, you won the game!"
                game.end_game(True)
            else:
                msg = 'Nice Job, the letter {} is in the secret word'.format(letter_guess)
            
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
        user = User.query(User.user_name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                'Sorry, that user does not exist')
        scores = Score.query(Score.user == user.key)
        return ScoreForms(items=[score.create_form() for score in scores])
    
    
    
api = endpoints.api_server([HangmanAPI])