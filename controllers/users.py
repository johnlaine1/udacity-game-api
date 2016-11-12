from models.user import (
    User,
    RankingForm,
    RankingForms,
    UserMessage,
    CreateUserForm
)

def create(req):
    """Create a user"""
    if User.query(User.user_name == req.user_name).get():
        msg = 'Error, that username already exists'
        raise endpoints.ConflictException(msg)

    user = User(user_name=req.user_name, email=req.email)
    user.put()

    return UserMessage(message = 'User {} has been created'.format(
            user.user_name))




