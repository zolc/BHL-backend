from flask import Flask
from flask_pymongo import PyMongo
from flask_graphql import GraphQLView



app = Flask(__name__)

app.config['MONGO_DBNAME'] = 'main_db'
app.config['MONGO_URI'] = 'mongodb://database/main_db'

mongo = PyMongo(app)

from app import views

'''
from app.models import schema

app.add_url_rule(
    '/graphql',
    view_func=GraphQLView.as_view(
        'graphql',
        schema=schema,
        graphicql=True # GUI not working, why?
    )
)
'''
