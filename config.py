import json
import sqlalchemy
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

with open(basedir / "config.json") as f:
    config = json.load(f)


# MongoDB connection
mongo_uri = "mongodb+srv://" + config["mongodb"]["username"] + ":" + config["mongodb"]["password"] + "@" + config["mongodb"]["host"] + "/" + config["mongodb"]["database"] + "?retryWrites=true&w=majority"
mongo_conn = MongoClient(uri, server_api=ServerApi('1'))
mongo = mongo_conn[config["mongodb"]["database"]]

# MySQL connection
mysql_uri = "mysql+mysqlconnector://" + config["mysql"]["username"] + ":" + config["mysql"]["password"] + "@" + config["mysql"]["host"] + ":" + config["mysql"]["port"] + "/" + config["mysql"]["database"]
mysql_engine = sqlalchemy.create_engine(mysql_uri)

# Twitter
twitter = config['twitter']