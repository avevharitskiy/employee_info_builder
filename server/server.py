try:
    from flask import Flask
except ImportError:
    print("Can't import flask")

flask_server = Flask(__name__)

@flask_server.route('/', methods=['GET', 'POST'])
def about():
    return "This is Flask server."

if __name__ == '__main__':
    flask_server.run()
