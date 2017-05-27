from app import app
from flask import Response

@app.route('/')
def index():
    return 'Hello world!'
