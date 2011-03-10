from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.api import urlfetch 
import os
from google.appengine.ext.webapp import template
import urllib
#from google.appengine.api import urlfetch
#from google.appengine.api.urlfetch import DownloadError
import logging
#import threading  
import sinaauth
from entities import Feed

from google.appengine.dist import use_library
use_library('django', '0.96')


HUB_SUB_URL = 'http://pubsubhubbub.appspot.com/subscribe'
HUB_CALLBACK_URL = 'http://buzz2wb.appspot.com/callback'
SUBSCRIBE_ACTION = "subscribe"
UNSUBSCRIBE_ACTION = "unsubscribe"
    
class MainPage(webapp.RequestHandler):
    def get(self):
        ''' display home page'''
        current_user = users.get_current_user()
        name = ''        
        if current_user:
            name = current_user.nickname()            
            hub_topic = 'https://www.googleapis.com/buzz/v1/activities/%s/@public' % name
            feeds = Feed.gql('WHERE g_user = :1', current_user)
            feed_count = feeds.count()
            logging.debug('feeds: %s' % feed_count)
            if feed_count < 1:
                ''' add a new feed record '''
                feed = Feed()
                feed.g_user = current_user
                feed.topic = hub_topic
                feed.topic_verified = False
                feed.put()
                logging.info("add new feed record for user {%s}" % current_user)
                
        template_values = {
                           'user': name,
                           'feeds': feeds,
                           'feed_count': feed_count,
                           'login_url': users.create_login_url(self.request.uri),
                           'logout_url': users.create_logout_url(self.request.uri),
                           }
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path, template_values))

class BuzzHandler(webapp.RequestHandler):
    def post(self):
        ''' '''
        logging.info( 'call back post' )
        
    def get(self):
        challenge = self.request.get('hub.challenge')
        mode = self.request.get('hub.mode')
        topic = self.request.get('hub.topic')
        logging.info('challenge: %s' % challenge)
        logging.info('mode: %s' % mode)
        logging.info('topic: %s' % topic)
#        logging.info('current user: %s '% users.get_current_user())
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write(challenge)
        if mode == 'subscribe':
            feed = Feed.gql('WHERE topic = :1', topic)
            if feed.count()>0:
                r = feed.get()
                r.topic_verified = True
                db.put(r)
                logging.info('topic {%s} is verified'% r.topic)
            else:
                logging.error('can not find the topic {%s}'% topic)
        elif mode == 'unsubscribe':
            feeds = Feed.gql('WHERE topic = :1', topic)
            logging.debug('%s feeds to delete' % feeds.count())
            for feed in feeds:
                logging.info('deleting {%s}'%feed.topic)
                db.delete(feed)
            logging.debug('delete feed')
            
class HubHandler(webapp.RequestHandler):
    def process(self, hub_mode, hub_verify = 'sync'):
        ''' subscribe or unsubscribe the topic'''
        hub_topic = 'https://www.googleapis.com/buzz/v1/activities/%s/@public' % users.get_current_user().nickname()
        values = {
                  'hub.topic': hub_topic,
                  'hub.mode': hub_mode,
                  'hub.verify': hub_verify,
                  'hub.callback': HUB_CALLBACK_URL,
                  }
        logging.info('post sub to: %s' % HUB_SUB_URL)
        logging.info('callback url: %s' % HUB_CALLBACK_URL)
        
        postdata = urllib.urlencode(values)
        logging.info('data: %s' % values)
        try:
            result = urlfetch.fetch(
                        url=HUB_SUB_URL,
                        payload=postdata,
                        method=urlfetch.POST,
                        follow_redirects = False, 
                        headers={'Content-Type': 'application/x-www-form-urlencoded'})
#            logging.info(result.status_code)
            if result.status_code != 204:
                logging.error('error in %s ')
            else:
                logging.info('success')
            
        except urlfetch.DownloadError, err :
            logging.error('error : %s '% err)
            
            
class SubscribeHandler(HubHandler):
    def get(self):
        ''' subscribe the public feed'''
        self.process(SUBSCRIBE_ACTION)
        self.redirect('/')
        
class UnSubscribeHandler(HubHandler):
    def get(self):
        ''' unsubscribe the public feed'''
        self.process(UNSUBSCRIBE_ACTION)
        self.redirect('/')



class AuthCallbackHandler(webapp.RequestHandler):
    def get(self):
        logging.info('oauth callback')
        
        
application = webapp.WSGIApplication(
                                     [('/', MainPage),
                                      ('/callback', BuzzHandler),
                                      ('/sub', SubscribeHandler),
                                      ('/unsub', UnSubscribeHandler),
                                      ('/auth', sinaauth.AuthHandler),
                                      ('/request_token_ready', AuthCallbackHandler)],
                                     debug=True)

def main():
    run_wsgi_app(application)


if __name__ == "__main__":
    main()
