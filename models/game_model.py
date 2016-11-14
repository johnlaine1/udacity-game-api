import json
from datetime import date

import endpoints
from protorpc import messages
from google.appengine.ext import ndb

from utils import get_by_urlsafe
from config import LETTER_POINT, WORD_POINT, BLANK_POINT


class Game(ndb.Model):
    """A Game object"""
    user                = ndb.KeyProperty(required=True, kind='User')
    misses_allowed      = ndb.IntegerProperty(required=True)
    misses_remaining    = ndb.IntegerProperty(required=True)
    letters_guessed     = ndb.StringProperty(default='')
    game_over           = ndb.BooleanProperty(required=True, default=False)
    game_cancelled      = ndb.BooleanProperty(required=True, default=False)
    secret_word         = ndb.StringProperty(required=True)
    current_solution    = ndb.StringProperty(required=True)
    score               = ndb.IntegerProperty(required=True, default=0)
    history             = ndb.JsonProperty(repeated=True)


    @classmethod
    def create_game(cls, user, misses_allowed, secret_word, current_solution):
        """Creates and returns a new game"""
        game = cls(parent=user,
                    user=user,
                    misses_allowed=misses_allowed,
                    misses_remaining=misses_allowed,
                    secret_word=secret_word,
                    current_solution=current_solution)
        game.put()
        return game


    @classmethod
    def get_game(cls, key):
        """Returns a GameStateForm"""
        game = get_by_urlsafe(key, cls)
        if game:
            return game
        else:
            raise endpoints.NotFoundException('No Game Found')


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
        """Decrement the misses remaining property"""
        self.misses_remaining -=1


    def update_letters_guessed(self, letter):
        """Update the letter_guessed property"""
        self.letters_guessed = self.letters_guessed + letter


    def update_score(self, blanks=0, letters=0, words=0):
        """Updates the score property"""
        points = 0
        points += letters * LETTER_POINT
        points += words * WORD_POINT
        points += blanks * BLANK_POINT
        self.score += points


    def update_history(self, guess='', result=''):
        """Updates the history property"""
        item = json.dumps({'guess': guess, 'result': result})
        self.history.append(item)


    def create_history_form(self):
        """Creates and returns a history form"""
        history_items = [json.loads(item) for item in self.history]

        history_form_items = []
        for item in history_items:
            history_form_items.append(GameHistoryForm(guess=item.get('guess'),
                                                      result=item.get('result')))

        return GameHistoryForms(history=history_form_items)


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


class CreateGameForm(messages.Message):
    """Inbound, used to create a new game"""
    user_name = messages.StringField(1, required=True)
    misses_allowed = messages.StringField(2)


class GuessLetterForm(messages.Message):
    """Inbound, used to guess a letter in a game"""
    letter_guess = messages.StringField(1, required=True)


class GuessWordForm(messages.Message):
    """Inbound, used to guess the secret word in a game"""
    word_guess = messages.StringField(1, required=True)


class GameHistoryForm(messages.Message):
    """Outbound, game history information"""
    guess = messages.StringField(1)
    result = messages.StringField(2)


class GameHistoryForms(messages.Message):
    """Outbound, create multiple instances of GameHistoryForm"""
    history = messages.MessageField(GameHistoryForm, 1, repeated=True)