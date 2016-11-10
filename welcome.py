# Copyright 2015 IBM Corp. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os 
import couchdb
import uuid

from flask import Flask, jsonify, session, render_template, request, redirect, g, url_for, flash
# from .models import User
from datetime import datetime
from couchdb.mapping import Document, TextField, DateTimeField, ListField, FloatField, IntegerField, ViewField
from werkzeug.utils import secure_filename
from werkzeug import FileStorage
from flask_uploads import (UploadSet, configure_uploads, IMAGES, UploadNotAllowed)
# from cloudant.view import View



# UPLOADED_PHOTOS_DEST = 'uploads'

cloudant_data = {
    "username": "052ca863-0f20-49a8-9813-330b0813683a-bluemix",
    "password": "68e8bdaa4739229b83095bf31b9c8256d5790022a184e8cdfefec270ea2be740",
    "host": "052ca863-0f20-49a8-9813-330b0813683a-bluemix.cloudant.com",
    "port": '443',
}

DATABASE_URL = "https://052ca863-0f20-49a8-9813-330b0813683a-bluemix.cloudant.com/bazaardata/"

app = Flask(__name__)
app.config.from_object(__name__)
# app.config.from_envvar('DEALBAZAAR_SETTINGS', silent=True)
app.secret_key = os.urandom(24)



# uploaded_photos = UploadSet('photos', IMAGES)
# configure_uploads(app, uploaded_photos)


class User(Document):
    doc_type = 'user'
    name = TextField()
    email = TextField()
    password = TextField()
    contact = IntegerField()
    college = TextField()
    city = TextField()
    address = TextField()
    createdate = DateTimeField(default=datetime.now)

    @classmethod
    def get_user(cls,email):
        db = get_db()
        user = db.get(email,None)

        if user is None:
            return None
        
        return cls.wrap(user)

class Item(Document):
    doc_type = TextField(default='item')
    name = TextField()
    item_type = TextField()
    description = TextField()
    original_price = FloatField()
    date = DateTimeField(default=datetime.now)
    user = TextField()
    filename = TextField()

    @classmethod
    def all(cls,db):
        return cls.view(db,'_design/items/_view/all-items')

    @classmethod
    def by_date(cls,limit = None):
        db = get_db()
        item_obj = cls.view(
                            db,
                            '_design/items/_view/byDate',
                            descending=True,
                            include_docs=True
                            )
        items = []
        for item in item_obj:
            items.append(cls.wrap(item))

        if limit is not None:
            return items[0:limit]

        return items
    
    @classmethod
    def by_user(cls,email):
        db = get_db()
        item_obj = cls.view(
                            db,
                            '_design/items/_view/byUser',
                            key=email,
                            include_docs=True
                            )
        items = []
        for item in item_obj:
            items.append(cls.wrap(item))

        return items

    @classmethod
    def by_item_type(cls,item_type):
        db = get_db()
        item_obj = cls.view(
                            db,
                            '_design/items/_view/byItemType',
                            key=item_type,
                            include_docs=True
                            )
        items = []
        for item in item_obj:
            items.append(cls.wrap(item))

        return items

    @classmethod
    def get_item(cls,id):
        db = get_db()
        item = db.get(id,None)

        if item is None:
            return None
        
        return cls.wrap(item)


class Bid(Document):
    doc_type = TextField(default='bid')
    amount = FloatField()
    user = TextField()
    item = TextField()
    created = DateTimeField()

    @classmethod
    def get_bid(cls,id):
        db = get_db()
        bid = db.get(id,None)

        if bid is None:
            return None
        
        return cls.wrap(bid)
    
    @classmethod
    def get_by_item(cls,db,item_id):
        # print '_design/bids/_view/get-bids'+item_id
        bids = []
        bids_obj = cls.view(
                            db,
                            '_design/bids/_view/get-bids',
                            key=item_id,
                            include_docs=True
                            )
        for row in bids_obj:
            bids.append(cls.wrap(row))
        return bids


def get_db():
    if not hasattr(g, 'db'):
        server = couchdb.Server("https://"+cloudant_data['username']+':'+cloudant_data['password']
          +'@'+cloudant_data['host']+':'+cloudant_data['port'])

        try:
            g.db = server.create('bazaardata')
        except:
            g.db = server['bazaardata']        
    
    return g.db

# @app.teardown_appcontext
# def close_db(error):
#     if hasattr(g, 'db')

@app.before_request
def before_request():
    g.user = None
    if 'user' in session:
        g.user = session['user']


@app.route('/')
def Welcome():
    return app.send_static_file('index.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        user = User()

        form_data = request.form

        if form_data.get('name'):
            user.name = form_data.get('name',None)
        else:
            flash('Name field is required', category = "error")
            return render_template('signup.html')

        if form_data.get('email'):    
            user.email = form_data.get('email',None)
        else:
            flash('Email field is required', category = "error")
            return render_template('signup.html')

        if form_data.get('password'):
            user.password = form_data.get('password',None)
        else:
            flash('Password field is required', category = "error")
            return render_template('signup.html')

        if form_data.get('contact'):
            user.contact = form_data.get('contact',None)
        else:
            flash('Contact field is required', category = "error")
            return render_template('signup.html')

        if form_data.get('college'):
            user.college = form_data.get('college',None)
        else:
            flash('College field is required', category = "error")
            return render_template('signup.html')

        if form_data.get('city'):
            user.city = form_data.get('city',None)
        else:
            flash('City field is required', category = "error")
            return render_template('signup.html')

        if form_data.get('address'):
            user.address = form_data.get('address',None)
        else:
            flash('Address field is required', category = "error")
            return render_template('signup.html')

        print user

        db = get_db()
        db[user.email] = user._data

        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session.pop('user', None)

        email = request.form['email']
        db = get_db()
        
        user = db.get(email,None)
        if user is not None:
            if request.form['password'] == user['password']:
                session['user'] = user
                return redirect(url_for('after_login'))
            else:
                flash('Invalid email or password', category="error")
        return render_template('login.html')
        # if request.form['password'] == 'password':
        #     session['user'] = request.form['email']
        #     return redirect(url_for('after_login'))

    return render_template('login.html')        

@app.route('/home')
def after_login():
    if g.user:
        recent_items = Item.by_date(3)

        for i in recent_items:
            i.src = DATABASE_URL + i.id + '/' + i.name + '.jpg/'


        return render_template('home.html', recent_items = recent_items)

    return redirect(url_for('login'))

@app.route('/posted_items')
def posted_items():
    if g.user:
        user_items = Item.by_user(g.user['email'])

        for i in user_items:
            i.src = DATABASE_URL + i.id + '/' + i.name + '.jpg/'
            #print i.src
            
        return render_template('posted_items.html', user_items = user_items)

    return redirect(url_for('login'))


@app.route('/sell', methods=['GET', 'POST'])
def post_item():
    if g.user:
        if request.method == 'POST':
            item = Item()

            form_data = request.form

            if request.files.get('photo'):
                photo = request.files.get('photo')
            else:
                flash('Image is required', category = "error")
                return render_template('upload.html')

            if form_data.get('item_name'):
                item.name = form_data.get('item_name',None)
            else:
                flash('Item Name is required', category = "error")
                return render_template('upload.html')

            item.description = form_data.get('description',None)
            item.item_type = form_data.get('item_type', None)

            if int(form_data.get('original_price')) > 0:
                #print "adadad"
                item.original_price = form_data.get('original_price',None)
            else:
                #print "errrrrr"
                flash('Invalid price', category = "error")
                return render_template('upload.html')


            item.user = g.user.get('email', None)
            #item.date = datetime.datetime.now

            db = get_db()
            # try:
            #     filename = uploaded_photos.save(photo)
            # except UploadNotAllowed:
            #     flash("The upload was not allowed")
            # else:
            #     item.filename = filename

            item.id = uuid.uuid4().hex
            item.store(db)
            db.put_attachment(item,photo,filename=str(item.name)+'.jpg',content_type='image/jpeg')

            #return "Success...!!!"
            return render_template('home.html')
        return render_template('upload.html')
    else:
        return redirect(url_for('login'))

@app.route('/view/', methods=['GET', 'POST'])
def view():
    if g.user:
        if request.method == 'POST':
            item_type = request.form.get('search')
            print item_type

            item_type_filter = Item.by_item_type(item_type)

            for i in item_type_filter:
                i.src = DATABASE_URL + i.id + '/' + i.name + '.jpg/'

            return render_template('search.html', items = item_type_filter)
    
        else:    
            db = get_db()
            it = Item.all(db)

            for i in it:
                i.src = DATABASE_URL + i.id + '/' + i.name + '.jpg/'
                #print i.src

            return render_template('search.html', items = it)
    
    return redirect(url_for('login'))

@app.route('/view/<id>', methods=['GET', 'POST'])
def item_details(id=None):
    if request.method == 'POST':
        bid = Bid()

        if int(request.form.get('amount')) > 0:
            bid.amount = request.form.get('amount')
        else:
            flash('Invalid Bid', category = "error")
            return redirect('/view/'+id)

        bid.item = id
        bid.user = g.user['email']

        db = get_db()
        bid.id = uuid.uuid4().hex
        bid.store(db)

        return redirect('/view/'+id)
    else:
        if(id):
            db = get_db()
            item = Item.get_item(id)
            
            items = item._data
            src = DATABASE_URL + id + '/' + item.name + '.jpg/'
            
            return render_template('item_description.html', item = items,src=src)

@app.route('/view/<id>/bid')
def view_bids(id=None):
    if g.user:
        db = get_db()
        bids = Bid.get_by_item(db,id)
        print 
    
        item = Item.get_item(id)
            
        items = item._data
        src = DATABASE_URL + id + '/' + item.name + '.jpg/'

        return render_template('view_bid.html',bids=bids,src=src,item=items)
    else:
        return redirect(url_for('login'))

port = os.getenv('PORT', '5000')
if __name__ == "__main__":
	app.run(host='0.0.0.0', port=int(port), debug=True)
