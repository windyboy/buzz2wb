'''
Created on 2011-3-8

@author: windy
'''
from google.appengine.ext import webapp
import oauth2 as oauth
import logging
#import urllib2
from google.appengine.api import urlfetch 

REQUEST_TOKEN_URL = 'http://api.t.sina.com.cn/oauth/request_token'
ACCESS_TOKEN_URL = 'http://api.t.sina.com.cn/oauth/access_token'
AUTHORIZATION_URL = 'http://api.t.sina.com.cn/oauth/authorize'
CALLBACK_URL = 'http://buzz2wb.appspot.com/request_token_ready'
RESOURCE_URL = 'http://photos.example.net/photos'

CONSUMER_KEY= "3586635050"
CONSUMER_SECRET ="6e022c4ce4826e4bc72b002dd24f0ecb"



class AuthHandler(webapp.RequestHandler):
    def get(self):
        '''  sina oauth '''
        logging.info('begin to auth')
        consumer = oauth.Consumer(CONSUMER_KEY, CONSUMER_SECRET)
        signature_method_hmac_sha1 = oauth.SignatureMethod_HMAC_SHA1()
        oauth_token_request = oauth.Request.from_consumer_and_token(consumer,http_url=REQUEST_TOKEN_URL)
        oauth_token_request.sign_request(signature_method_hmac_sha1, consumer, None)
#        response = urllib2.urlopen(oauth_token_request.to_url()).read()
        logging.info('request token url: %s ' % oauth_token_request.to_url())
        response = urlfetch.fetch(oauth_token_request.to_url())
        if response.status_code != 200:
            logging.error('error in read token : %s' % response.status_code)
        else :
            logging.info('response: %s' % response.content)
            token = oauth.Token.from_string(response.content)
            logging.info( 'key: %s' % str(token.key))
            logging.info( 'secret: %s' % str(token.secret))
            oauth_request = oauth.Request.from_token_and_callback(token=token, http_url=AUTHORIZATION_URL)
            oauth_request.sign_request(signature_method_hmac_sha1, consumer, token)
            # Redirect user to get authentication token.
            logging.info('redirect to: %s'%oauth_request.to_url())
            self.redirect(oauth_request.to_url())