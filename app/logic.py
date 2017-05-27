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



def sign_in(username, password):
    result = mongo.db.users.find_one({'username': username})
    print(result, file=sys.stderr)
    if result is None:
        return (False, "")
    sha = hashlib.sha256()
    sha.update(password.encode('utf-8'))
    password = sha.hexdigest()
    if password == result['pass_hash']:
        encoded = jwt.encode({'username': username}, 'secret', algorithm='HS256').decode("utf-8")
        return (True, encoded)
    return (False, "")


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
        "password": password,
        "users": [],
        "admins": [creator.username]
    }
    print('Adding {}'.format(record), file=sys.stderr)
    mongo.db.groups.insert_one(record)
    return True


def add_to_users(username, password, email, first_name=None, last_name=None, phone=None):
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


def self_info(token):
    from .models import User
    decoded = jwt.decode(token, 'secret', algorithms=['HS256'])
    result = mongo.db.users.find_one({'username': str(decoded['username'])})
    if result is not None:
        return User(
            username=result['username'],
            email=result['email'],
            first_name=result['first_name'],
            last_name=result['last_name'],
            phone=result['phone']
        )
    else:
        return None



def add_to_tasks(token, group_name, title, description=None, due_date=None):
    user = self_info(token)
    if is_admin(user.username, group_name):
        group_id = mongo.db['groups'].find_one({"name": group_name})["_id"]
        record = {
            "group_id": group_id,
            "title": title,
            "description": description,
            "published_date": datetime.now(),
            "due_date": due_date,
            "users_completed": [],
            "users_important": [],
            "creator": user.username
        }
        print('Adding {} to tasks'.format(record), file=sys.stderr)
        mongo.db['tasks'].insert_one(record)
        return True
    return False


def add_to_info(token, group_name, title, description=None):
    user = self_info(token)
    if is_admin(user.username, group_name):
        group_id = mongo.db['groups'].find_one({"name":group_name})["_id"]
        record = {
            "group_id": group_id,
            "title": title,
            "description": description,
            "published_date": datetime.now(),
            "creator": user.username
        }
        print('Adding {} to info'.format(record), file=sys.stderr)
        mongo.db['info'].insert_one(record)
        return True
    return False


def is_admin(username, group_name):
    group = mongo.db['groups'].find_one({"name": group_name})
    if group is not None:
        admin_list = group['admins']
        if username in admin_list:
            return True
    return False


def add_admin_to_group(token, username, group_name):
    user = self_info(token)
    if is_admin(user.username, group_name):
        group_admins = mongo.db['groups'].find_one({"name": group_name})["admins"]
        group_admins.append(username)
        mongo.db.groups.update_one({'name': group_name}, {'admins': group_admins})
        return True
    return False


def register_to_group(token, group_name, password):
    user = self_info(token)
    if user is None:
        return False
    result = mongo.db.groups.find_one({'name': group_name})
    if result is None or password != result.password:
        return False
    users = result.users
    if users is None or user.username in users:
        return False
    users.append(user.username)
    mongo.db.groups.update_one({'name': group_name}, {'users': users})
    return True
