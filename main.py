#!/usr/bin/env python

"""main.py - This file contains handlers that are called by taskqueue and/or
cronjobs."""
import logging

import webapp2
from google.appengine.api import mail, app_identity
from api import HangmanAPI

from models import User, Game


class SendReminderEmail(webapp2.RequestHandler):
    def get(self):
        pass

class SendTestEmail(webapp2.RequestHandler):
    def get(self):
        """Send a reminder email to users.

        This handler will be called every hour using a cron job.
        An email will only be sent to users that have active games, that is
        games that are not 'over' or 'canceled'
        """

        app_id = app_identity.get_application_id()
        users = User.query(User.email != None)

        for user in users:
            games = (
                Game.query(ancestor=user.key)
                .filter(Game.game_over == False)
                .filter(Game.game_cancelled == False)
                .fetch())
            if games:
                email_from = 'noreply@{}.appspotmail.com'.format(app_id)
                email_to = user.email
                email_subject = 'Have you given up on your game of Hangman?'
                email_body = ('Hello {}, it\'s been awhile since you played'
                              ' your game of hangman').format(user.user_name)
                mail.send_mail(email_from, email_to, email_subject, email_body)


app = webapp2.WSGIApplication([
    ('/crons/send_reminder', SendReminderEmail),
    ('/sendtestemail', SendTestEmail),
], debug=True)
