import random
import json
from datetime import date
import endpoints
from protorpc import messages
from google.appengine.ext import ndb


##### DATABASE MODELS #####
class User(ndb.Model):
    """A User Profile object"""
    user_name = ndb.StringProperty(required=True)
    email     = ndb.StringProperty()
    score     = ndb.IntegerProperty(default=0)
    
    def create_ranking_form(self):
        return RankingForm(user_name=self.user_name,
                           score=self.score)


class Game(ndb.Model):
    """A Game object"""
    user = ndb.KeyProperty(required=True, kind='User')
    misses_allowed = ndb.IntegerProperty(required=True)
    misses_remaining = ndb.IntegerProperty(required=True)
    letters_guessed = ndb.StringProperty(default='')
    game_over = ndb.BooleanProperty(required=True, default=False)
    game_cancelled = ndb.BooleanProperty(required=True, default=False)
    secret_word = ndb.StringProperty(required=True)
    current_solution = ndb.StringProperty(required=True)
    score = ndb.IntegerProperty(required=True, default=0)
    history = ndb.JsonProperty(repeated=True)
    
    LETTER_POINT = 10
    WORD_POINT = 20
    BLANK_POINT = 20
    
    @classmethod
    def create_game(cls, user, misses_allowed=5):
        """Creates and returns a new game"""
        secret_word = cls.secret_word_generator()
        current_solution = ''.join(['_' for l in secret_word])
        game = Game(parent=user,
                    user=user,
                    misses_allowed=misses_allowed,
                    misses_remaining=misses_allowed,
                    secret_word=secret_word,
                    current_solution=current_solution)
        game.put()
        return game
        
        
    def game_state(self, message=''):
        """Returns the state of a game"""
        state = GameStateForm()
        state.urlsafe_game_key = self.key.urlsafe()
        state.user_name = self.user.get().user_name
        state.misses_remaining = self.misses_remaining
        state.message = message
        state.current_solution = list(self.current_solution)
        state.letters_guessed = list(self.letters_guessed)
        state.game_over = self.game_over
        state.game_cancelled = self.game_cancelled
        state.score = self.score
        return state
    
    @staticmethod
    def secret_word_generator():
        """Returns a random word from a list of words"""
        words = [
            'CAT',
            'DOG',
            'HOUSE',
            'TREE']
        return random.choice(words)
        
        
    def update_current_solution(self, letter):
            """Update the current solution."""
            # Get the indices of the letter matches
            matches = [i for i, x in enumerate(list(self.secret_word)) if x == letter]
            solution = list(self.current_solution)
            for match in matches:
                solution[match] = letter
            self.current_solution = ''.join(solution)
            if self.current_solution == self.secret_word:
                return True
            else:
                return False
                
                
    def decrement_misses_remaining(self):
        self.misses_remaining -=1
        
                
    def update_letters_guessed(self, letter):
        self.letters_guessed = self.letters_guessed + letter
        
        
    def end_game(self, won=False):
        """Ends the game"""
        self.game_over = True
        
        if won:
            self.update_history(guess='', result='Game Won')
            self.current_solution = self.secret_word
            user = self.user.get()
            user.score += self.score
            user.put()
        else:
            self.update_history(guess='', result='Game Lost')
            
        score = Score(user=self.user,
                      date=date.today(),
                      won=won,
                      score=self.score)
        score.put()
        
        
    def update_score(self, blanks=0, letters=0, words=0):
        points = 0
        points += letters * self.LETTER_POINT
        points += words * self.WORD_POINT
        points += blanks * self.BLANK_POINT
        self.score += points
        
        
    def update_history(self, guess='', result=''):
        item = json.dumps({'guess': guess, 'result': result})
        self.history.append(item)
        

    def create_history_form(self):
        history_items = [json.loads(item) for item in self.history]
                
        history_form_items = []         
        for item in history_items:
            history_form_items.append(GameHistoryForm(guess=item.get('guess'),
                                                      result=item.get('result')))
            
        return GameHistoryForms(history=history_form_items)
  

class Score(ndb.Model):
    """Score Object"""
    user = ndb.KeyProperty(required=True, kind='User')
    date = ndb.DateProperty(required=True)
    won = ndb.BooleanProperty(required=True)
    score = ndb.IntegerProperty(required=True)
    
    def create_form(self):
        return ScoreForm(user_name=self.user.get().user_name,
                         won=self.won,
                         date=str(self.date),
                         score=self.score)
                         
        
##### MESSAGES #####
class StringMessage(messages.Message):
    """A generic outbound string message"""
    message = messages.StringField(1, required=True)


class CreateGameForm(messages.Message):
    """Inbound, used to create a new game"""
    user_name = messages.StringField(1, required=True)
    misses_allowed = messages.IntegerField(2, default=5)

    
class GameStateForm(messages.Message):
    """Outbound game state information"""
    urlsafe_game_key = messages.StringField(1, required=True)
    user_name = messages.StringField(2, required=True)
    misses_remaining = messages.IntegerField(3, required=True)
    message = messages.StringField(4)
    current_solution = messages.StringField(5, repeated=True)
    letters_guessed = messages.StringField(6, repeated=True)
    game_over = messages.BooleanField(7)
    game_cancelled = messages.BooleanField(8)
    score = messages.IntegerField(9)

    
class GameStateForms(messages.Message):
    """Outbound, create multiple instances of GameStateForm"""
    items = messages.MessageField(GameStateForm, 1, repeated=True)

    
class GuessLetterForm(messages.Message):
    """Inbound, used to guess a letter in a game"""
    letter_guess = messages.StringField(1, required=True)

    
class GuessWordForm(messages.Message):
    """Inbound, used to guess the secret word in a game"""
    word_guess = messages.StringField(1, required=True)

    
class ScoreForm(messages.Message):
    """Outbound, score information"""
    user_name = messages.StringField(1, required=True)
    date = messages.StringField(2, required=True)
    won = messages.BooleanField(3, required=True)
    score = messages.IntegerField(4, required=True)

    
class ScoreForms(messages.Message):
    """Outbound, create multiple instances of ScoreForm"""
    items=messages.MessageField(ScoreForm, 1, repeated=True)

    
class RankingForm(messages.Message):
    """Outbound, user ranking information"""
    user_name = messages.StringField(1, required=True)
    score = messages.IntegerField(2, required=True)

    
class RankingForms(messages.Message):
    """Outbound, create mutiple instances of RankingForm"""
    items = messages.MessageField(RankingForm, 1, repeated=True)


class CreateUserForm(messages.Message):
    """Inbound: Used to create a new user"""
    user_name = messages.StringField(1, required = True)
    email = messages.StringField(2)
   

class GameHistoryForm(messages.Message):
    """Outbound, game history information"""
    guess = messages.StringField(1)
    result = messages.StringField(2)


class GameHistoryForms(messages.Message):
    """Outbound, create multiple instances of GameHistoryForm"""
    history = messages.MessageField(GameHistoryForm, 1, repeated=True)
    

##### RESOURCE CONTAINERS #####
GET_GAME_REQUEST     = endpoints.ResourceContainer(
    urlsafe_game_key=messages.StringField(1))
                        
GUESS_LETTER_REQUEST = endpoints.ResourceContainer(
    GuessLetterForm, urlsafe_game_key=messages.StringField(1))
 
GUESS_WORD_REQUEST = endpoints.ResourceContainer(
    GuessWordForm, urlsafe_game_key=messages.StringField(1))
                        
USER_SCORE_REQUEST   = endpoints.ResourceContainer(
    user_name=messages.StringField(1))

GET_USER_GAMES_REQUEST = endpoints.ResourceContainer(
    user_name=messages.StringField(1))

GET_SCORES_REQUEST = endpoints.ResourceContainer(
    number_of_results=messages.StringField(1, required=False))

