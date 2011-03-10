'''
Created on 2011-3-9

@author: windy
'''
from google.appengine.ext import db

class Feed(db.Model):
    topic = db.StringProperty()
    hub_token = db.StringProperty()
    date = db.DateTimeProperty(auto_now_add=True)
    token_key = db.StringProperty()
    token_secret = db.StringProperty()
    g_user = db.UserProperty()