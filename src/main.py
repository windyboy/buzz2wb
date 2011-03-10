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


    
class MainPage(webapp.RequestHandler):
    def get(self):
        current_user = users.get_current_user()
        name = ''
        #sub_url = 'http://localhost:8080/subscribe'
        sub_url = 'http://pubsubhubbub.appspot.com/subscribe'
        hub_verify = 'sync'
        #hub_callback = 'http://localhost:9999/callback'
        hub_callback = 'http://buzz2wb.appspot.com/callback'
        hub_topic = ''
        feeds = None
        feed_count = None
        
        if current_user:
            name = current_user.nickname()            
            hub_topic = 'https://www.googleapis.com/buzz/v1/activities/%s/@public' % name
            feeds = Feed.gql('WHERE g_user = :1', current_user)
            feed_count = feeds.count()
            logging.debug('feeds: %s' % feed_count)

        template_values = {
                           'user': name,
                           'hub_topic': hub_topic,
                           'hub_verify': hub_verify,
                           'hub_callback': hub_callback,
                           'action': sub_url,
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
        logging.info('current user: %s '% users.get_current_user())
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write(challenge)
        if mode == 'subscribe':
            feed = Feed()
            feed.topic = topic
            feed.put()
            logging.info('save feed')
        elif mode == 'unsubscribe':
            feeds = Feed.gql('WHERE topic = :1', topic)
            logging.debug('%s feeds to delete' % feeds.count())
            for feed in feeds:
                db.delete(feed)
            logging.debug('delete feed')
            

class SubscribeHandler(webapp.RequestHandler):
#    sub_url = "http://localhost:9090/subscribe"
    sub_url = 'http://pubsubhubbub.appspot.com/subscribe'
#    hub_callback = 'http://localhost:9999/callback'
    hub_callback = 'http://buzz2wb.appspot.com/callback'
    def get(self):
        ''' subscribe the public feed'''
#        sub_url = ''
        hub_topic = 'https://www.googleapis.com/buzz/v1/activities/%s/@public' % users.get_current_user().nickname()
        hub_mode = 'subscribe'
        hub_verify = 'sync'
        
        values = {
                  'hub.topic': hub_topic,
                  'hub.mode': hub_mode,
                  'hub.verify': hub_verify,
                  'hub.callback': self.hub_callback,
                  }
        logging.info('post sub to: %s' % self.sub_url)
        logging.info('callback url: %s' % self.hub_callback)
        postdata = urllib.urlencode(values)
        logging.info('data: %s' % values)
        try:
            result = urlfetch.fetch(
                        url=self.sub_url,
                        payload=postdata,
                        method=urlfetch.POST,
                        follow_redirects = False, 
                        headers={'Content-Type': 'application/x-www-form-urlencoded'})
            logging.info(result.status_code)
        except urlfetch.DownloadError, err :
            logging.error('error : %s '% err)
        self.redirect('/')



class AuthCallbackHandler(webapp.RequestHandler):
    def get(self):
        logging.info('oauth callback')
        
        
application = webapp.WSGIApplication(
                                     [('/', MainPage),
                                      ('/callback', BuzzHandler),
                                      ('/sub', SubscribeHandler),
                                      ('/auth', sinaauth.AuthHandler),
                                      ('/request_token_ready', AuthCallbackHandler)],
                                     debug=True)

def main():
    run_wsgi_app(application)


if __name__ == "__main__":
    main()
