from app import app, mongo
from flask import Response

@app.route('/')
def index():
    return 'Hello world!'


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
                "groups": [],
                "admins": []
            },
            {
                "name": "group2",
                "password": "a5hetbf",
                "groups": [],
                "admins": []
            },
        ])
    return 'DB RESETED'
