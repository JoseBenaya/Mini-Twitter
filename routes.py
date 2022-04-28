from sqlalchemy import create_engine
from flask import render_template, request, url_for, redirect, session, flash, abort
from functools import wraps
from sqlalchemy import exc
from hashlib import md5
from sqlalchemy.orm import Session
from app import db
from app import app
from models import User, Relationship, Message

#Business Layer

database = create_engine('mysql://root:''@localhost/uts')

# ============================= Helper Function ==========================

@app.before_request
def before_request():
    database.connect()


@app.after_request
def after_request(response):
    database.dispose()
    return response

#membuat fungsi untuk memvalidasi user
def auth_user(user):
    session['logged_in'] = True
    session['user_id'] = user.id
    session['username'] = user.username
    flash('Berhasil login sebagai ' + session['username'])

#fungsi untuk mewajibkan setiap session untuk login terlebih dahulu
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

#fungsi untuk langsung direct ke homepage apabila sudah melakukan login
def redirect_if_loggedin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('logged_in'):
            return redirect(url_for('homepage'))
        return f(*args, **kwargs)
    return decorated_function

#fungsi untuk mengambil data user pada session yang sedang berjalan
def get_current_user():
    if session.get('logged_in'):
        return User.query.filter(User.id == session['user_id']).first()


#membuat fungsi yang akan mereturn fungsi yang sedang berjalan
@app.context_processor
def inject_user():
    return {'active_user': get_current_user()}

# ============================= ROUTING ==========================

#untuk masuk ke dalam dashboard user harus melakukan login terlebih dahulu
@app.route('/')
@login_required
def homepage():
    # menampilkan pos kita dan pos orang yang kita follow
    user = get_current_user()
    messages = db.session.query(Message).filter((Message.user_id.in_([user.id for user in user.following()])) | (
        Message.user_id == user.id)).order_by(Message.published_at.desc()).all()
    data = db.session.query(User.id, User.username).join(Message).all()

    #melakukan join data antara User dengan Message
    get_data = []
    for test in messages:
        for id, username in data:
            if id == test.user_id:
                row = (test.user_id, username, test.content, test.published_at)
                get_data.append(row)
                break
    return render_template('index.html', get_data=get_data)

#ketika user sudah register akan langsung ke direct
@app.route('/register', methods=['GET', 'POST'])
@redirect_if_loggedin
def register():
    session = Session(database)
    if request.method == 'POST' and request.form['username']:
        try:
            with session.begin():
                user = User(
                    username=request.form['username'],
                    password=md5(request.form['password'].encode(
                        'utf-8')).hexdigest(),
                    email=request.form['email'],
                )
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('homepage'))

        except exc.IntegrityError:
            # session.rollback()
            flash('User sudah terdaftar')

    return render_template('register.html')

#membuat fungsi untuk menghandle login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form['username']:
        hashed_pass = md5(request.form['password'].encode('utf-8')).hexdigest()
        user = User.query.filter(
            User.username == request.form['username'], User.password == hashed_pass
        ).first()
        #akan dicek terlebih dahulu apakah user register atau belum
        if user:
            auth_user(user)
            return redirect(url_for('homepage'))
        else:
            flash('User tidak ada')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('Logout berhasil')
    return redirect(url_for('homepage'))


# ===================== Routing Post ====================

#fungsi untuk membuat post baru
@app.route('/new', methods=['GET', 'POST'])
@login_required
def create():
    session = Session(database)
    user = get_current_user()
    if request.method == 'POST' and request.form['content']:
        message = Message(user_id=user.id, content=request.form['content'])
        session.add(message)
        session.commit()
        flash('status kamu sudah terupdate!')
        return redirect(url_for('user_profile', username=user.username))

    return render_template('newpost.html')

#fungsi untuk mendapatkan data query profil user
@app.route('/user/<username>')
def user_profile(username):
    user = User.query.filter(User.username == username).first()
    if user:
        messages = user.messages.order_by(Message.published_at.desc())
    else:
        abort(404)
    return render_template('profile.html', messages=messages, user=user)

#melakukan follow terhadap user lain
@app.route('/user_follow/<username>', methods=['POST'])
def user_follow(username):
    session = Session(database)
    try:
        user = User.query.filter(User.username == username).first()
    except:
        abort(404)

    try:
        with session.begin():
            relation = Relationship(from_user=get_current_user().id,
                                    to_user=user.id)
            session.add(relation)
            session.commit()
    except:
        pass
    flash("Kamu berhasil follow " + username)
    return redirect(url_for('user_profile', username=username))

#melakukan unfollow terhadap user lain
@app.route('/user_unfollow/<username>', methods=['POST'])
def user_unfollow(username):
    session = Session(database)
    user = User.query.filter(User.username == username).first()
    try:
        user = User.query.filter(User.username == username).first()
    except:
        abort(404)

    session.query(Relationship).filter(Relationship.from_user ==
                                       get_current_user().id, Relationship.to_user == user.id).delete()
    session.commit()

    flash("Kamu berhasil unfollow " + username)
    return redirect(url_for('user_profile', username=username))

#fungsi untuk menunjukan siapa saja following user
@app.route('/user/<username>/following')
def show_following(username):
    try:
        user = User.query.filter(User.username == username).first()
    except:
        abort(404)

    return render_template('userlist.html', users=user.following())


#fungsi untuk menunjukan siapa saja followers user
@app.route('/user/<username>/followers')
def show_followers(username):
    try:
        user = User.query.filter(User.username == username).first()
    except:
        abort(404)

    return render_template('userlist.html', users=user.followers())
