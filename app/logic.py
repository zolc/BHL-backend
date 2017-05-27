import sys
from datetime import datetime
from flask_pymongo import PyMongo
from app import app, mongo
from pprint import pprint
from flask import Response
import requests
import hashlib
import base64
import jwt


def add_to_users(login, password, email, first_name, last_name, phone):
    result = mongo.db.users.find_one({'login': login})
    print(result, file=sys.stderr)
    if result is not None:
        return False
    sha = hashlib.sha256()
    sha.update(password.encode('utf-8'))
    password = sha.hexdigest()
    record = {
        "login": login,
        "pass_hash": password,
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
        "phone": phone
    }
    print('Adding {}'.format(record), file=sys.stderr)
    mongo.db.users.insert_one(record)
    return True
