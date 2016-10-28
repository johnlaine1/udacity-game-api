import random
from protorpc import messages
from google.appengine.ext import ndb


##### DATABASE MODELS #####

class User(ndb.Model):
    """A User Profile object"""
    name = ndb.StringProperty(required=True)

class Game(ndb.Model):
    """A Game object"""
    user = ndb.KeyProperty(required=True, kind='User')
    attempts_allowed = ndb.IntegerProperty(required=True)
    attempts_remaining = ndb.IntegerProperty(required=True, default=5)
    game_over = ndb.BooleanProperty(required=True, default=False)
    secret_word = ndb.StringProperty(required=True)
    
    @classmethod
    def create_game(cls, user, attempts_allowed):
        """Creates and returns a new game"""
        secret_word = cls.secret_word_generator()
        game = Game(user=user,
                    attempts_allowed=attempts_allowed,
                    secret_word=secret_word)
        game.put()
        return game
        
    def game_state(self, message):
        """Returns the state of a game"""
        state = GameState()
        state.urlsafe_game_key = self.key.urlsafe()
        state.user_name = self.user.get().name
        state.attempts_remaining = self.attempts_remaining
        state.message = message
        return state
    
    @staticmethod
    def secret_word_generator():
        """Returns a random word from a list of words"""
        words = [
            'cat',
            'dog',
            'house',
            'tree']
        return random.choice(words)
        
##### MESSAGES #####
class StringMessage(messages.Message):
    """A generic outbound string message"""
    message = messages.StringField(1, required=True)
    
class CreateGameForm(messages.Message):
    """Inbound, used to create a new game"""
    user_name = messages.StringField(1, required=True)
    attempts_allowed = messages.IntegerField(2, default=5)
    
class GameState(messages.Message):
    """Outbound game state information"""
    urlsafe_game_key = messages.StringField(1, required=True)
    user_name = messages.StringField(2, required=True)
    attempts_remaining = messages.IntegerField(3, required=True)
    message = messages.StringField(4, required=True)
    
    