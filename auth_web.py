#! /usr/bin/env python

import cherrypy
import json
import os
import requests
import socket

try:
    from creds import *
except ImportError:
    print "Missing creds.py"
    print "Create a credentials file without refresh_token specified"
    exit()

from cherrypy.process import servers

try:
    from urllib.parse import quote
except ImportError:
    from urllib import quote

debug = True # expose the refresh token on provisioning broswer in plaintext

class Start(object):
    def index(self):
        scope="alexa_all"
        sd = json.dumps({
            "alexa:all": {
                "productID": ProductID,
                "productInstanceAttributes": {
                    "deviceSerialNumber": "001"
                }
            }
        })
        url = "https://www.amazon.com/ap/oa"

        # Establish AMZN callback URL
        callback = cherrypy.url()  + "code"

        payload = { "client_id" : Client_ID,
                    "scope" : "alexa:all",
                    "scope_data" : sd,
                    "response_type" : "code", 
                    "redirect_uri" : callback }

        req = requests.Request('GET', url, params=payload)
        p = req.prepare()
        raise cherrypy.HTTPRedirect(p.url)
    
    def code(self, var=None, **params):
        code = quote(cherrypy.request.params['code'])
        callback = cherrypy.url()
        payload = {"client_id" : Client_ID, 
                   "client_secret" : Client_Secret,
                   "code" : code,
                   "grant_type" : "authorization_code", 
                   "redirect_uri" : callback }
        url = "https://api.amazon.com/auth/o2/token"
        r = requests.post(url, data = payload)
        resp = r.json()
        
        # write refresh_token line from AMZN response
        line = 'refresh_token = "{}"'.format(resp['refresh_token'])
        with open("creds.py", 'a') as f:
            f.write(line)
        
        # sent to provisioning browser
        success_msg = "<H1>Success!</H1>"
        success_msg +="<p>{} has been provisioned</p>".format(ProductID)
        success_msg +="<p>The refresh token has been added to your creds file</p>"

        if debug is True:
            success_msg +="<H2>Debug</H2>"
            success_msg +="<p>refresh_token:<br>"
            success_msg +="{}</p>".format(resp['refresh_token'])
        return success_msg
    
    index.exposed = True
    code.exposed = True
        
cherrypy.config.update({'server.socket_host': '0.0.0.0',})
cherrypy.config.update({'server.socket_port': int(os.environ.get('PORT', '5000'))})
cherrypy.config.update({'environment': 'embedded'})

ip = [(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]
print("Ready goto https://{} or https://localhost  to begin the auth process".format(ip))
print("(Press Ctrl-C to exit this script once authorization is complete)")
cherrypy.quickstart(Start())

