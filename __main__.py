
import os
from inspect import getsourcefile

from helpers import Configuration, Database
from saby_invoker import SabyInvoker
from server import flask_server
from neural_network import NeuralNetwork

# change directory to package directory
package_dir = os.path.dirname(os.path.abspath(getsourcefile(lambda: 0)))
os.chdir(package_dir)

#   read configuration from config file
Configuration.load_configuration()

#   connect to database
Database.connect_to_database()

#   init RpcInvoker
SabyInvoker.initialize()

#   init NeuralNetwork
NeuralNetwork.initialize()

#   run server on flask
flask_server.run()
# from api import get_user_info
# get_user_info(14893668, '00000003-007537f4-00bd-310e086f458d384b')