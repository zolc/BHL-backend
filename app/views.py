from app import app, mongo
from flask import Response
import sys
from .logic import add_to_users, create_group, sign_in, add_to_tasks, add_to_info


@app.route('/')
def index():
    text = '''
    token(guest) eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VybmFtZSI6Imd1ZXN0In0.QWIrBbwfGi6PDmWWEG-LEmmcXVaQNH68GOzLeTxBnI4
    '''
    return text


@app.route('/listusers')
def list_users():
    cursor = mongo.db.users.find()
    file = ""
    for doc in cursor:
        file += str(doc)
        file += '\n'
    return Response(file, mimetype='text')


@app.route('/listgroups')
def list_groups():
    cursor = mongo.db.groups.find()
    file = ""
    for doc in cursor:
        file += str(doc)
        file += '\n'
    return Response(file, mimetype='text')


@app.route('/listtasks')
def list_tasks():
    cursor = mongo.db.tasks.find()
    file = ""
    for doc in cursor:
        file += str(doc)
        file += '\n'
    return Response(file, mimetype='text')


@app.route('/listinfo')
def list_info():
    cursor = mongo.db.info.find()
    file = ""
    for doc in cursor:
        file += str(doc)
        file += '\n'
    return Response(file, mimetype='text')


@app.route('/resetdb')
def reset_db():
    for collection in mongo.db.collection_names():
        mongo.db[collection].drop()
    mongo.db["users"].insert_many(
        [
            {
                "username": "testuser1",
                "pass_hash": "Aa83SJe",
                "email": "testuser1@example.com",
                "first_name": "Jan",
                "last_name": "Kowalski",
                "phone": "123456789",
                "groups": [],
                "last_login_date": "2017-05-27 15:16:20"
            },
            {
                "username": "testuser2",
                "pass_hash": "2agdsS8U",
                "email": "testuser2@example.com",
                "first_name": "John",
                "last_name": "Smith",
                "phone": "000111222",
                "groups": [],
                "last_login_date": "2017-05-27 15:17:20"
            },
        ])
    mongo.db["groups"].insert_many(
        [
            {
                "name": "group1",
                "password": "pass1",
                "users": [],
                "admins": []

            },
            {
                "name": "group2",
                "password": "a5hetbf",
                "users": [],
                "admins": []
            },
        ])
    add_to_users("guest", "test", "email@example.com", "gra", "żyna", "91487198")
    add_to_users("adam", "adam", "mail@mail.com")
    add_to_users("qwerty", "uiop", "mail2@mail.com")
    _,token = sign_in("guest", "test")
    print("Token:",file=sys.stderr)
    print(token, file=sys.stderr)
    create_group(token, "TESTGROUP", "PASS")
    add_to_tasks(token, "TESTGROUP", "Title", "Description")
    add_to_info(token, "TESTGROUP", "Title", "Description")
    return 'DB RESETED'
