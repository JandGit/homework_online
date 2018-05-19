#! /usr/bin/python

import sys
import logging

sys.path.insert(0, "/var/www/cgi-scripts")

from cgi.cgi_register import app as application

application.debug = True
handler = logging.FileHandler("/home/ljj/flask.log")
application.logger.addHandler(handler)
