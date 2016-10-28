from protorpc import messages
from google.appengine.ext import ndb


##### DATABASE MODELS #####

class User(ndb.Model):
    """A User Profile"""
    name = ndb.StringProperty(required = True)


##### MESSAGES #####

class Test(messages.Message):
    """This is a test endpoint, for dev purposes"""
    message = messages.StringField(1)
    
class StringMessage(messages.Message):
    """A generic outbound string message"""
    message = messages.StringField(1, required = True)
