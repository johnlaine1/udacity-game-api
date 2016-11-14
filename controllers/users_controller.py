import endpoints

from models.user_model import (
    User,
    RankingForm,
    RankingForms,
    UserMessage,
    CreateUserForm
)

def create_user(user_name, email=''):
    """Create a user"""
    user = User.create(user_name=user_name, email=email)
    return UserMessage(message = 'User {} has been created'.format(
            user.user_name))

def get_user(user_name):
    """Get a user"""
    user = User.get_by_name(user_name)
    return user

def get_user_rankings():
    """Get all user rankings"""
    users = User.query().order(-User.score)
    return RankingForms(items=[user.create_ranking_form() for user in users])




