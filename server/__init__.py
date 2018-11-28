from flask import Flask


flask_server = Flask(__name__)

from server import routes
