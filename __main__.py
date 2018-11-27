
import os
from inspect import getsourcefile

from api.data_miner import test
from helpers import Configuration, Database
from saby_invoker import SabyInvoker

# change directory to package directory
package_dir = os.path.dirname(os.path.abspath(getsourcefile(lambda: 0)))
os.chdir(package_dir)

#   read configuration from config file
Configuration.load_configuration()

#   connect to database
Database.connect_to_database()

#   init RpcInvoker
SabyInvoker.initialize()

#   TODO: add flask running

test()