from app import app, mongo
from flask import Response
import sys
from .logic import add_to_users, create_group, sign_in, add_to_tasks, add_to_info, register_to_group


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
    add_to_users("guest", "test", "przemek.proszewski@gmail.com", "Jan", "Kowalski", "914871918")
    add_to_users("admin", "pass", "test@example.com", "Pan", "Profesor", "602100100")
    add_to_users("student1", "student1", "student@example.com")
    add_to_users("student2", "student2", "student2@example.com")
    _, token = sign_in("guest", "test")
    _, token2 = sign_in("admin", "pass")
    create_group(token, "ASD2", "mini-d1234")
    create_group(token2, "SOP", "niktniezda")
    _id = mongo.db.groups.find_one({"name": "ASD2"})["_id"]
    _id2 = mongo.db.groups.find_one({"name": "SOP"})["_id"]
    register_to_group(token, _id2, "niktniezda")
    add_to_tasks(token, _id, "Przygotowanie do kolokwium ASD2","May 28 2017 13:10:00", "Zakres: wykłady 1 - 10")
    add_to_tasks(token, _id, "Część domowa z LAB 12", "May 28 2017 13:15:00","Rozwiązania proszę wysłać na maila asd@mini.pw.edu.pl")
    add_to_tasks(token, _id, "Egzamin","May 28 2017 13:20:00", "Łatwy nie będzie")
    add_to_info(token, _id, "Zakres materiału na LAB13", "Description")
    add_to_info(token, _id, "Osoby nie posiadające 50 punktów mogą zaliczyć egzamin po spełnieniu dodatkowych warunków.", "Należy przygotować własną implementację algorytmu Hoare'a")
    add_to_tasks(token2, _id2, "Poprawa laboratoriów 3 i 4","May 28 2017 15:00:00", "Poprawa odbędzie się jutro o godzinie 14:00 w sali 218")
    add_to_tasks(token2, _id2, "Wyniki z laboratorium 2","May 28 2017 15:00:00","Wyniki dostępne na mojej stronie")
    # add_to_tasks(token2, _id2, "test", "sdad")
    # add_to_info(token, _id, "Title", "Description")
    return 'DB RESETED'
