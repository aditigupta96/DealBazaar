import time

from datetime import datetime
from couchdb.mapping import Document, TextField, DateTimeField, ListField, FloatField, IntegerField

class User(Document):
    name = TextField()
    email = TextField()
    password = TextField()
    contact = IntegerField()
    college = TextField()
    city = TextField()
    address = TextField()
    createdate = DateTimeField(default=datetime.now)