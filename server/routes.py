from server import flask_server
@flask_server.route('/')
def index():
    return "Hello World!"

