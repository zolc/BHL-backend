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
    if result is None:
        return None
    #Read new tasks/infos before changing last_online
    user = User(
        username=result['username'],
        email=result['email'],
        first_name=result['first_name'],
        last_name=result['last_name'],
        phone=result['phone'],
        last_online=result['last_online'],
        groups=result['groups']
    )
    return user


def create_group(token, group_name, password):
    creator = self_info(token)
    result = mongo.db.groups.find_one({'name': group_name})
    print(result, file=sys.stderr)
    if result is not None:
        return False
    record = {
        "name": group_name,
        "password": password,
        "users": [],
        "admins": [creator.username]

    }
    print('Adding {}'.format(record), file=sys.stderr)
    mongo.db.groups.insert_one(record)
    creator.groups.append(group_name)
    mongo.db.users.update_one({'username': creator.username}, {'$set': {'groups': creator.groups}})
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
        "phone": phone,
        "groups": [],
        "last_online": datetime.now()
    }
    print('Adding {}'.format(record), file=sys.stderr)
    mongo.db.users.insert_one(record)
    return True


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
        group_id = mongo.db['groups'].find_one({"name": group_name})["_id"]
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
        mongo.db.groups.update_one({'name': group_name}, {'$set': {'admins': group_admins}})
        return True
    return False


def remove_admin_from_group(token, username, group_name):
    user = self_info(token)
    if is_admin(user.username, group_name) is False:
        return False
    group_admins = mongo.db['groups'].find_one({"name": group_name})["admins"]
    if username not in group_admins:
        return False
    group_admins.remove(username)
    mongo.db.groups.update_one({'name': group_name}, {'$set': {'admins': group_admins}})
    return True


def register_to_group(token, group_name, password):
    user = self_info(token)

    if user is None:
        print("user is none", file=sys.stderr)
        return False
    result = mongo.db.groups.find_one({'name': group_name})
    if result is None or password != result['password']:
        print("Group is none / wrong password", file=sys.stderr)
        return False
    users = result['users']
    if users is None or user.username in users:
        return False
    user.groups.append(group_name)
    users.append(user.username)
    mongo.db.groups.update_one({'name': group_name}, {'$set': {'users': users}})
    mongo.db.users.update_one({'username': user.username}, {'$set': {'groups': user.groups}})
    return True


def remove_from_group(token,group_name):
    user = self_info(token)
    if user is None:
        return False
    result = mongo.db.groups.find_one({'name': group_name})
    if result is None:
        return False
    admins_list=result['admins']
    users_list = result['users']
    if user.username in admins_list:
        if len(admins_list)<2:
            return False
        admins_list.remove(user.username)
        if group_name in user.groups:
            user.groups.remove(group_name)
        mongo.db.groups.update_one({'name': group_name}, {'$set': {'admins': admins_list}})
        mongo.db.users.update_one({'username': user.username}, {'$set': {'groups': user.groups}})
        return True
    if user.username in users_list:
        users_list.remove(user.username)
        if group_name in user.groups:
            user.groups.remove(group_name)
        mongo.db.groups.update_one({'name': group_name}, {'$set': {'admins': admins_list}})
        mongo.db.users.update_one({'username': user.username}, {'$set': {'groups': user.groups}})
        return True


