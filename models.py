import json
from datetime import date

import endpoints
from protorpc import messages
from google.appengine.ext import ndb

from utils import secret_word_generator, get_by_urlsafe
from config import LETTER_POINT, WORD_POINT, BLANK_POINT



##### DATABASE MODELS #####
class User(ndb.Model):
    """A User Profile object"""
    user_name = ndb.StringProperty(required=True)
    email     = ndb.StringProperty()
    score     = ndb.IntegerProperty(default=0)

    @classmethod
    def create_user(cls, user_name, email):
        """Creates a user and saves to the DB"""
        # Check if the user already exists
        if cls.query(cls.user_name == user_name).get():
            msg = 'Sorry, that username already exists'
            raise endpoints.ConflictException(msg)
        # Create the user and store in the database
        user = cls(user_name=user_name, email=email)
        user.put()
        return user


    @classmethod
    def get_user(cls, user_name):
        """Gets a user from the DB and returns it"""
        user = cls.query(cls.user_name == user_name).get()
        if not user:
            msg = 'A user with that name does not exist!'
            raise endpoints.NotFoundException(msg)
        return user


    def create_ranking_form(self):
        """Creates and returns a RankingForm"""
        return RankingForm(user_name=self.user_name,
                           score=self.score)


class Game(ndb.Model):
    """A Game object"""
    user                = ndb.KeyProperty(required=True, kind='User')
    misses_allowed      = ndb.IntegerProperty(required=True, default=5)
    misses_remaining    = ndb.IntegerProperty(required=True)
    letters_guessed     = ndb.StringProperty(default='')
    game_over           = ndb.BooleanProperty(required=True, default=False)
    game_cancelled      = ndb.BooleanProperty(required=True, default=False)
    secret_word         = ndb.StringProperty(required=True)
    current_solution    = ndb.StringProperty(required=True)
    score               = ndb.IntegerProperty(required=True, default=0)
    history             = ndb.JsonProperty(repeated=True)


    @classmethod
    def create_game(cls, user, misses_allowed=5):
        """Creates and returns a new game"""
        secret_word = secret_word_generator()
        current_solution = ''.join(['_' for l in secret_word])
        game = Game(parent=user,
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


    def cancel_game(self):
        """Cancels a game"""
        msg = 'The game has been cancelled'

        # If the requested game is already over.
        if self.game_over:
            raise endpoints.BadRequestException('This game is already over')

        # If the requested game has already been cancelled.
        if self.game_cancelled:
            raise endpoints.BadRequestException('This game has already been cancelled')

        self.game_cancelled = True
        self.update_history(guess='', result='Game Cancelled')
        self.put()
        return self.game_state(msg)


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


    def guess_word(self, word_guess):
        """Handles the logic to guess a word in a game"""
        # If the game is already over
        if self.game_over:
            msg = 'Error, This game is already over.'
            raise endpoints.BadRequestException(msg)

        # If the game has been cancelled
        if self.game_cancelled:
            msg = 'Error, this game has been cancelled.'
            raise endpoints.BadRequestException(msg)

        # If the guess is incorrect
        if word_guess != self.secret_word:
            self.decrement_misses_remaining()
            self.update_history(guess=word_guess, result='Incorrect')
            if self.misses_remaining < 1:
                self.end_game(won=False)
                self.update_history(guess='', result='Game Lost')
                msg = 'Sorry, that was the wrong answer and the game is over'
            else:
                msg = 'Sorry, that was not the correct answer'

            self.put()
            return self.game_state(msg)

        # If the guess is correct
        if word_guess == self.secret_word:
            blanks = self.current_solution.count('_')
            self.update_score(blanks=blanks, words=1)
            self.update_history(guess=word_guess, result='Correct')
            self.end_game(won=True)
            msg = 'Congratulations! you win!'

            self.put()
            return self.game_state(msg)


    def letter_guess(self, letter_guess):
        """Handles the logic to guess a letter in a game"""
        # If the game is already over
        if self.game_over:
            msg = 'Error, This game is already over.'
            raise endpoints.BadRequestException(msg)

        # If the game has been cancelled
        if self.game_cancelled:
            msg = 'Error, this game has been cancelled.'
            raise endpoints.BadRequestException(msg)

        # If more than one letter is submitted.
        if len(letter_guess) > 1:
            msg = 'Error, you can only choose one letter at a time.'
            raise endpoints.BadRequestException(msg)

        # If letter guess has already been tried.
        if self.letters_guessed and letter_guess in self.letters_guessed:
            msg = 'Sorry, you already tried that letter, please pick another.'
            return self.game_state(msg)

        # If letter guess is incorrect.
        if letter_guess not in self.secret_word:
            msg = 'Sorry, that is incorrect'
            self.decrement_misses_remaining()
            self.update_letters_guessed(letter_guess)
            self.update_history(guess=letter_guess, result='Incorrect')

            if self.misses_remaining < 1:
                self.end_game(False)
                self.put()
                msg = 'Sorry, that is incorrect and the game is now over.'
                return game.game_state(msg)

            self.put()
            return self.game_state(msg)

        # If letter guess is correct
        if letter_guess in self.secret_word:
            num_of_letters = self.secret_word.count(letter_guess)
            game_won = self.update_current_solution(letter_guess)
            self.update_letters_guessed(letter_guess)
            self.update_history(guess=letter_guess, result='Correct')

            if game_won:
                msg = "Great Job, you won the game!"
                self.update_score(letters=num_of_letters, words=1)
                self.end_self(True)
            else:
                self.update_score(letters=num_of_letters)
                msg = 'Nice Job, the letter {} is in the secret word'.format(letter_guess)

            self.put()
            return self.game_state(msg)


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


class Score(ndb.Model):
    """Score Object"""
    user    = ndb.KeyProperty(required=True, kind='User')
    date    = ndb.DateProperty(required=True)
    won     = ndb.BooleanProperty(required=True)
    score   = ndb.IntegerProperty(required=True)

    def create_form(self):
        """Creates and returns a ScoreForm"""
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
    misses_allowed = messages.IntegerField(2, required=True)


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

