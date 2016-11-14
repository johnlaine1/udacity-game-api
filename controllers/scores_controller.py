import endpoints
from datetime import date

from models.user_model import User
from models.game_model import Game
from models.score_model import (
    Score,
    ScoreForm,
    ScoreForms,
)

def get_scores():
    """Get all scores"""
    return ScoreForms(items=[score.create_form() for score in Score.query()])


def get_user_scores(user_name):
    """Get a user's scores"""
    user = User.get_by_name(user_name)
    scores = Score.query(Score.user == user.key)
    return ScoreForms(items=[score.create_form() for score in scores])


def get_high_scores(number_of_results):
    """Return the high scores"""
    scores = Score.query().order(-Score.score)
    if number_of_results:
        scores = scores.fetch(int(number_of_results))
    return ScoreForms(items=[score.create_form() for score in scores])