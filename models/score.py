from datetime import date

import endpoints
from protorpc import messages
from google.appengine.ext import ndb


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


class ScoreForm(messages.Message):
    """Outbound, score information"""
    user_name = messages.StringField(1, required=True)
    date = messages.StringField(2, required=True)
    won = messages.BooleanField(3, required=True)
    score = messages.IntegerField(4, required=True)


class ScoreForms(messages.Message):
    """Outbound, create multiple instances of ScoreForm"""
    items=messages.MessageField(ScoreForm, 1, repeated=True)