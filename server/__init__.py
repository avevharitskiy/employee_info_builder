try:
    from flask import Flask
except ImportError:
    print("Can't import flask")

flask_server = Flask(__name__)

from server import routes
