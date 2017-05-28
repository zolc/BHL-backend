import sys
from datetime import datetime
from flask_pymongo import PyMongo
from app import app, mongo
import os
from pprint import pprint
from flask import Response
import requests
import hashlib
import base64
import jwt
from twilio.rest import Client
import smtplib
from bson.objectid import ObjectId


def sign_in(username, password):
    result = mongo.db.users.find_one({'username': username})
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
    # Read new tasks/infos before changing last_online
    user = User(
        _id=result['_id'],
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
    _id = mongo.db.groups.insert_one(record).inserted_id

    creator.groups.append(_id)
    print(creator.groups, file=sys.stderr)
    mongo.db.users.update_one({'_id': ObjectId(creator._id)}, {'$set': {'groups': creator.groups}})
    return True


def add_to_users(username, password, email, first_name=None, last_name=None, phone=None):
    result = mongo.db.users.find_one({'username': username})
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
    mongo.db.users.insert_one(record)
    return True


def change_settings(token, email, phone, password):
    user = self_info(token)
    if user is None:
        return False
    result = mongo.db.users.find_one({'username': user.username})
    if email is not None:
        result['email'] = email
        print(result['username'], file=sys.stderr)
        mongo.db.users.update_one({'username': user.username}, {'$set': {'email': result['email']}})
    if phone is not None:
        result['phone'] = phone
        mongo.db.users.update_one({'username': user.username}, {'$set': {'phone': result['phone']}})
    if password is not None:
        sha = hashlib.sha256()
        sha.update(password.encode('utf-8'))
        password = sha.hexdigest()
        result['password'] = password
        mongo.db.users.update_one({'username': user.username}, {'$set': {'phone': result['phone']}})
    return True


def add_to_tasks(token, group_id, title, description=None, due_date=None):
    user = self_info(token)
    if is_admin(user.username, group_id):
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
        mongo.db['tasks'].insert_one(record)
        return True
    return False


def toggle_task_completed(token, task_id):
    user = self_info(token)
    task = mongo.db.tasks.find_one({'_id': ObjectId(task_id)})
    if user.username in task['users_completed']:
        task['users_completed'].remove(user.username)
        return True
    task['users_completed'].append(user.username)
    mongo.db.tasks.update_one({'_id': ObjectId(task_id)}, {'$set': {'users_completed': task['users_completed']}})
    return True


def toggle_task_important(token, task_id):
    user = self_info(token)
    task = mongo.db.tasks.find_one({'_id': ObjectId(task_id)})
    if user.username in task['users_completed']:
        task['users_important'].remove(user.username)
        return True
    task['users_important'].append(user.username)
    mongo.db.tasks.update_one({'_id': ObjectId(task_id)}, {'$set': {'users_important': task['users_important']}})
    return True


def add_to_info(token, group_id, title, description=None):
    user = self_info(token)
    if is_admin(user.username, group_id):
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


def is_admin(username, group_id):
    group = mongo.db['groups'].find_one({"_id": ObjectId(group_id)})
    if group is not None:
        admin_list = group['admins']
        if username in admin_list:
            return True
    return False


def add_admin_to_group(token, username, group_id):
    user = self_info(token)
    if is_admin(user.username, group_id):
        group_admins = mongo.db['groups'].find_one({"_id": ObjectId(group_id)})["admins"]
        group_admins.append(username)
        mongo.db.groups.update_one({'_id': ObjectId(group_id)}, {'$set': {'admins': group_admins}})
        return True
    return False


def remove_admin_from_group(token, username, group_id):
    user = self_info(token)
    if is_admin(user.username, group_id) is False:
        return False
    group_admins = mongo.db['groups'].find_one({"_id": ObjectId(group_id)})["admins"]
    if username not in group_admins:
        return False
    group_admins.remove(username)
    mongo.db.groups.update_one({'_id': ObjectId(group_id)}, {'$set': {'admins': group_admins}})
    return True


def register_to_group(token, group_id, password):
    user = self_info(token)
    if user is None:
        print("user is none", file=sys.stderr)
        return False

    result = mongo.db.groups.find_one({'_id': ObjectId(group_id)})
    if result is None or password != result['password']:
        print("Group is none / wrong password", file=sys.stderr)
        return False

    users = result['users']
    if users is None or user.username in users:
        return False
    users.append(user.username)
    user.groups.append(group_id)
    mongo.db.groups.update_one({'_id': ObjectId(group_id)}, {'$set': {'users': users}})
    mongo.db.users.update_one({'username': user.username}, {'$set': {'groups': user.groups}})
    return True


def remove_from_group(token, group_id):
    user = self_info(token)
    if user is None:
        return False

    result = mongo.db.groups.find_one({'_id': ObjectId(group_id)})
    if result is None:
        return False
    admins_list = result['admins']
    users_list = result['users']

    if user.username in admins_list:
        if len(admins_list) < 2:
            return False
        admins_list.remove(user.username)
        if group_id in user.groups:
            user.groups.remove(ObjectId(group_id))
        mongo.db.groups.update_one({'_id': ObjectId(group_id)}, {'$set': {'admins': admins_list}})
        mongo.db.users.update_one({'username': user.username}, {'$set': {'groups': user.groups}})
        return True

    if user.username in users_list:
        users_list.remove(user.username)
        if group_id in user.groups:
            user.groups.remove(group_id)
        mongo.db.groups.update_one({'_id': ObjectId(group_id)}, {'$set': {'admins': admins_list}})
        mongo.db.users.update_one({'username': user.username}, {'$set': {'groups': user.groups}})
        return True


def delete_group(token, group_id):
    admin = self_info(token)
    if is_admin(admin.username, group_id) is False:
        return False
    result = mongo.db.groups.find_one({'_id': ObjectId(group_id)})
    users_list = result['users']
    admins_list = result['admins']
    for username in users_list:
        user = mongo.db.users.find_one({'username': username})
        user['groups'].remove(ObjectId(group_id))
        mongo.db.users.update_one({'username': username}, {'$set': {'groups': user['groups']}})
    for username in admins_list:
        user = mongo.db.users.find_one({'username': username})
        user['groups'].remove(ObjectId(group_id))
        mongo.db.users.update_one({'username': username}, {'$set': {'groups': user['groups']}})
    mongo.db.groups.delete_one(result)
    return True


def send_mail_notification(token, task_id):
    user = self_info(token)
    if user is None or user.email is None:
        return False
    task = mongo.db.tasks.find_one({'_id': ObjectId(task_id)})
    if task is None:
        return False
    APP_ROOT = os.path.dirname(os.path.abspath(__file__))
    login_file = open(os.path.join(APP_ROOT, 'logindata.txt'))
    line = login_file.readline()
    gmail_user = ""
    gmail_pwd = ""
    while line:
        sout = line.split(':')
        gmail_user = sout[0]
        gmail_pwd = sout[1]
        line = login_file.readline()
    to = user.email
    smtp_server = smtplib.SMTP("smtp.gmail.com", 587)
    smtp_server.ehlo()
    smtp_server.starttls()
    smtp_server.ehlo()
    smtp_server.login(gmail_user, gmail_pwd)
    header = 'To:' + to + '\n' + 'From: ' + gmail_user + '\n' + 'Subject:' + task['title'] + '\n'
    msg = header + '\n You have x time remaining for task:' + task['title'] + ' \n\n'
    smtp_server.sendmail(gmail_user, to, msg)
    smtp_server.quit()
    return True


def text_message(token, task_id):
    user = self_info(token)
    if user is None or user.email is None:
        return False

    task = mongo.db.tasks.find_one({'_id': ObjectId(task_id)})
    if task is None:
        return False
    APP_ROOT = os.path.dirname(os.path.abspath(__file__))
    login_file = open(os.path.join(APP_ROOT, 'twilioauth.txt'))
    line = login_file.readline()
    while line:
        sout = line.split(':')
        accountSid = sout[0]
        authToken = sout[1]
        line = login_file.readline()
    twilioClient = Client(accountSid, authToken)
    myTwilioNumber = "+48732230784"
    destCellPhone = "+48796176303" #hardcoded because of limited options in trial version of twilio
    msgIs = 'Remember about: ' + task['title']
    twilioClient.messages.create(
        body=msgIs, from_=myTwilioNumber, to=destCellPhone)
    return True
