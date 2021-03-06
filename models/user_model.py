import endpoints
from protorpc import messages
from google.appengine.ext import ndb


class User(ndb.Model):
    """A User Profile object"""
    user_name = ndb.StringProperty(required=True)
    email     = ndb.StringProperty()
    score     = ndb.IntegerProperty(default=0)


    def create_ranking_form(self):
        """Creates and returns a RankingForm"""
        return RankingForm(user_name=self.user_name,
                           score=self.score)

    @classmethod
    def create(cls, user_name, email=''):
        """Create a user"""
        if cls.query(cls.user_name == user_name).get():
            msg = 'Error, that username already exists'
            raise endpoints.ConflictException(msg)
        user = cls(user_name=user_name, email=email)
        user.put()
        return user

    @classmethod
    def get_by_name(cls, user_name):
        """Get a user"""
        user = cls.query(cls.user_name == user_name).get()
        if not user:
            msg = 'A user with that name does not exist!'
            raise endpoints.NotFoundException(msg)
        return user


class RankingForm(messages.Message):
    """Outbound, user ranking information"""
    user_name = messages.StringField(1, required=True)
    score = messages.IntegerField(2, required=True)


class RankingForms(messages.Message):
    """Outbound, create mutiple instances of RankingForm"""
    items = messages.MessageField(RankingForm, 1, repeated=True)


class UserMessage(messages.Message):
    """Outbound: user notification"""
    message = messages.StringField(1, required=True)


class CreateUserForm(messages.Message):
    """Inbound: Used to create a new user"""
    user_name = messages.StringField(1, required = True)
    email = messages.StringField(2)