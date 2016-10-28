from protorpc import messages
from google.appengine.ext import ndb

class Test(messages.Message):
    """This is a test endpoint, for dev purposes"""
    message = messages.StringField(1)
    
class User(ndb.Model):
    pass

class Game(ndb.Model):
    pass