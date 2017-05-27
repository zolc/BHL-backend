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


from .models import User

def add_to_users(username, password, email, first_name, last_name, phone):
    result = mongo.db.users.find_one({'username': username})
    print(result, file=sys.stderr)
    if result is not None:
        return False
    sha = hashlib.sha256()
    sha.update(password.encode('utf-8'))
    password = sha.hexdigest()
    record = {
        "username": username,
        "pass_hash": password,
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
        "phone": phone
    }
    print('Adding {}'.format(record), file=sys.stderr)
    mongo.db.users.insert_one(record)
    return True

def add_to_tasks(token, group_name, title, description, due_date):
    user = self_info(token)
    if is_admin(user.username, group_name):
        group_id = mongo.db['groups'].find_one({"name":group_name})["_id"]
        record = {
            "group_id": group_id,
            "title": title,
            "description": description,
            "published_date": datetime.now(),
            "due_date": due_date,
            "users_completed": [],
            "users_important": [],
            "creator_id": user.username
        }
        print('Adding {} to tasks'.format(record), file=sys.stderr)
        mongo.db.tasks.insert_one(record)
        return True
    return False

def is_admin(username, group_name):
    group = mongo.db['groups'].find_one({"name":group_name})
    if group is not None:
        admin_list = group['admins']
        if username in admin_list:
            return True
    return False


def sign_in(username, password):
    result = mongo.db.users.find_one({'username': username})
    print(result, file=sys.stderr)
    if result is None:
        return ""
    sha = hashlib.sha256()
    sha.update(password.encode('utf-8'))
    password = sha.hexdigest()
    if password == result['pass_hash']:
        encoded = jwt.encode({'username': username}, 'secret', algorithm='HS256').decode("utf-8")
        return encoded
    return ""


def self_info(token):
    from .models import User
    decoded = jwt.decode(token, 'secret', algorithms=['HS256'])
    result = mongo.db.users.find_one({'username': str(decoded['username'])})
    return User(
        username=result['username'],
        email=result['email'],
        first_name=result['first_name'],
        last_name=result['last_name'],
        phone=result['phone']
    )


def create_group(token, name, password):
    creator = self_info(token)
    result = mongo.db.groups.find_one({'name': name})
    print(result, file=sys.stderr)
    if result is not None:
        return False
    record = {
        "name": name,
        "pass_hash": password,
        "users": [],
        "admins": [creator.username]
    }
    print('Adding {}'.format(record), file=sys.stderr)
    mongo.db.groups.insert_one(record)
    return True
