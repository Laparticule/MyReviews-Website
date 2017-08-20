import requests
from flask import Flask, request, render_template, url_for, session, redirect, abort
import os, sys
from sqlalchemy import Integer, String, create_engine, Column, update
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import hashlib
from flask_mail import Mail, Message
import random

app = Flask(__name__)

app.secret_key = "enter_your_secret_key_here"

app.config['MAIL_SERVER'] = "smtp.gmail.com" #If you're using Gmail
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'enter_email_address_here'
app.config['MAIL_PASSWORD'] = 'enter_password_here'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mymail = Mail(app)
Base = declarative_base()

class user(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    account = Column(String(50), nullable=False)
    email = Column(String(50), nullable=False)
    password = Column(String(50), nullable=False)

class articles(Base):
    __tablename__ = 'articles'
    id = Column(Integer, primary_key=True)
    user = Column(String(50), nullable=False)
    title = Column(String(50), nullable=False)
    grade = Column(Integer, nullable=False)
    content = Column(String(5000), nullable=False)
    category = Column(String(20), nullable=False)

class mail(Base):
    __tablename__ = 'mail'
    id = Column(Integer, primary_key=True)
    sender = Column(String(50), nullable=False)
    receiver = Column(String(50), nullable=False)
    title = Column(String(50), nullable=False)
    content = Column(String(5000), nullable=False)

class comments(Base):
    __tablename__ = 'comments'
    id = Column(Integer, primary_key=True)
    user = Column(String(50), nullable=False)
    reviewid = Column(Integer, nullable=False)
    title = Column(String(50), nullable=False)
    content =  Column(String(500), nullable=False)

engine = create_engine('mysql+pymysql://enter_mysql_user:enter_mysql_password@server/enter_database_name')
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
sessiondb = Session()

@app.route("/")
def nothing():
    return redirect(url_for('index'))

@app.route("/index")
def index():
    return render_template("index.html")

@app.route("/home")
def home():
    if 'username' in session:
        name = session.get("username", None)
        return render_template("home.html", name=name)
    else:
        msg = "Access denied. You have to log in first..."
        return render_template("log.html", msg=msg)

@app.route("/logout", methods=['GET'])
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route("/login", methods=['GET','POST'])
def login():
    if request.method == 'GET':
        return render_template('log.html')
    else:
        if sessiondb.query(user).filter(user.account==request.form.get("account"), user.password==hashlib.sha1(request.form.get("password")).hexdigest()).first() is None:
            msg = "Invalid Username or Password. Click on the link below if you don't already have an account"
            return render_template('log.html', msg=msg)
        else:
            session['username'] = request.form.get("account")
            return redirect(url_for("home"))

@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method =='GET':
        return render_template('reg.html')
    else:
        if sessiondb.query(user).filter(user.account==request.form.get("account")).first() is None and sessiondb.query(user).filter(user.email==request.form.get("email")).first() is None:
            if request.form.get("password1")==request.form.get("password2"):
                new_user = user(account=request.form.get("account"), email=request.form.get("email"), password=hashlib.sha1(request.form.get("password1")).hexdigest())
                sessiondb.add(new_user)
                sessiondb.commit()
                msg = "Congrats! Your account now exists. Click on the link below to log in"
                return render_template('reg.html', msg=msg)
            else:
                msg = "Passwords do not match"
                return render_template('reg.html', msg=msg)
        else:
            if sessiondb.query(user).filter(user.email==request.form.get("email")).first() is None:
                msg = "This Username is already taken. Click on the link below if you already have an account"
            else:
                msg = "This Email is already taken. Click on the link below if you already have an account"
            return render_template('reg.html', msg=msg)

@app.route("/reset", methods =['GET', 'POST'])
def reset():
    if request.method == 'GET':
        return render_template("ret.html")
    if request.method == 'POST':
        if sessiondb.query(user).filter(user.email==request.form.get("email")).first() is None:
            msg = "We have no account linked to this email address"
            return render_template("ret.html", msg=msg)
        else:
            secret_code = random.randint(1,999999)
            session['secret_code'] = secret_code
            session['email'] = request.form.get("email")
            secret_msg = "Here is your secret code that will allow you to reset your password : {0}".format(secret_code)
            email = Message("Secret Code", sender = "enter_your_email_address", recipients = [request.form.get("email")])
            email.body = secret_msg
            mymail.send(email)
            return redirect(url_for('verification'))


@app.route("/verification", methods=['GET','POST'])
def verification():
    if request.method == 'GET':
        return render_template("ret2.html")
    else:
        if session.get('secret_code', None) == int(request.form.get("code")):
            our_user = sessiondb.query(user).filter(user.email==session.get("email", None)).first()
            our_user.password = hashlib.sha1(request.form.get("password")).hexdigest()
            sessiondb.commit()
            msg = "Congratulations! Your password has been changed. You can now log in."
            return render_template("log.html", msg=msg)
        else:
            msg = "The secret code entered was not the one expected"
            return render_template("ret2.html", msg=msg)

@app.route("/mail/received")
def mail_received():
    if 'username' in session:
        name = session.get("username")
        mp = sessiondb.query(mail).filter(mail.receiver == session.get("username")).all()
        return render_template("mail_received.html", name=name, mp=mp)

    else:
        msg = "Access denied. You have to log in first..."
        return render_template("log.html", msg=msg)

@app.route("/mail/received/<re>")
def mail_re(re):
    if 'username' in session:
        name = session.get("username")
        mp = sessiondb.query(mail).filter(mail.id == re).first()
        return render_template("mail_re.html", name=name, mp=mp)
    else:
        msg = "Access denied. You have to log in first..."
        return render_template("log.html", msg=msg)

@app.route("/mail/new", methods=['GET', 'POST'])
def mail_new():
    if 'username' in session:
        name = session.get("username")
        if request.method == 'GET':
            return render_template("mail_new.html", name=name)
        else:
            if sessiondb.query(user).filter(user.account == request.form.get("receiver")).first() != None:
                mp = mail(sender=session.get("username"), receiver=request.form.get("receiver"), title=request.form.get("title"), content=request.form.get("content"))
                sessiondb.add(mp)
                sessiondb.commit()
                msg = "Your message has been correctly sent!"
                return render_template("mail_received.html", msg=msg, name=name)
            else:
                msg = "Sorry, this user doesn't exist"
                return render_template("mail_received.html", msg=msg, name=name)

    else:
        msg = "Access denied. You have to log in first..."
        return render_template("log.html", msg=msg)

@app.route("/mail/sent")
def mail_sent():
    if 'username' in session:
        name = session.get("username")
        mp = sessiondb.query(mail).filter(mail.sender == session.get("username")).all()
        return render_template("mail_sent.html", name=name, mp=mp)
    else:
        msg = "Access denied. You have to log in first..."
        return render_template("log.html", msg=msg)

@app.route("/my_rv")
def my_rv():
    if 'username' in session:
        name = session.get("username")
        rv = sessiondb.query(articles).filter(articles.user==session.get("username")).all()
        return render_template("my_rv.html", rv=rv, name=name)
    else:
        msg = "Access denied. You have to log in first..."
        return render_template("log.html", msg=msg)

@app.route("/my_rv/edit/<idrev>", methods=['POST', 'GET'])
def my_rv_edit(idrev):
    if 'username' in session and sessiondb.query(articles).filter(articles.id == idrev and articles.user == 'username').first() != None:
        if request.method == 'GET':
            name = session.get("username")
            rv = sessiondb.query(articles).filter(articles.id == idrev).first()
            return render_template("edit_rv.html", name=name, rv=rv, idrev=idrev)
        else:
            myrv = sessiondb.query(articles).filter(articles.id == idrev).first()
            myrv.title = request.form.get("title")
            myrv.grade = request.form.get("grade")
            myrv.content = request.form.get("review")
            myrv.category = request.form.get("category")
            sessiondb.commit()
            return redirect(url_for("my_rv"))
    else:
        abort(404)

@app.route("/my_rv/delete/<idrev>")
def my_rv_delete(idrev):
    if 'username' in session and sessiondb.query(articles).filter(articles.id == idrev and articles.user == 'username').first() != None:
        sessiondb.query(articles).filter(articles.id == idrev).delete()
        for rv in sessiondb.query(articles).filter(articles.id > idrev):
            rv.id = rv.id - 1
        sessiondb.commit()
        return redirect(url_for("my_rv"))
    else:
        abort(404)

@app.route("/user_profile/<usr>")
def user_profile(usr):
    if 'username' in session:
        name = session.get("username")
        if sessiondb.query(user).filter(user.account == usr).first() != None:
            rv = sessiondb.query(articles).filter(articles.user == usr).all()
            return render_template("user_profile.html", usr=usr, name=name, rv=rv)
        else:
            abort(404)
    else:
        msg = "Access denied. You have to log in first..."
        return render_template("log.html", msg=msg)

@app.route("/comments/<revid>", methods=['GET', 'POST'])
def all_comments(revid):
    if 'username' in session:
        name = session.get("username")
        if request.method=='POST':
            com = comments(user=session.get('username'), reviewid=revid, title=request.form.get('title'), content=request.form.get('content'))
            sessiondb.add(com)
            sessiondb.commit()
        cmt = sessiondb.query(comments).filter(comments.reviewid==revid).all()
        rev = sessiondb.query(articles).filter(articles.id==revid).first()
        return render_template("all_comments.html", name=name, rev=rev, cmt=cmt, revid=revid)
    else:
        msg = "Access denied. You have to log in first..."
        return render_template("log.html", msg=msg, revid=revid)

@app.route("/read_rv", methods=['GET','POST'])
def read_rv():
    if 'username' in session:
        name = session.get("username")
        if request.method == 'GET':
            rv = sessiondb.query(articles).all()
            return render_template("read_rv.html", name=name, rv=rv)
        else:
            if request.form.get('category') == 'Everything':
                rv = sessiondb.query(articles).all()
            else:
                rv = sessiondb.query(articles).filter(articles.category==request.form.get('category')).all()
            return render_template("read_rv.html", name=name, rv=rv)
    else:
        msg = "Access denied. You have to log in first..."
        return render_template("log.html", msg=msg)

@app.route("/write_rv", methods=['GET','POST'])
def write_rv():
    if 'username' in session:
        if request.method == 'GET':
            name = session.get("username")
            return render_template("write_rv.html", name=name)
        else:
            new_article = articles(user=session.get('username'), title=request.form.get('title'), grade=request.form.get('grade'), content=request.form.get('review'), category=request.form.get('category'))
            sessiondb.add(new_article)
            sessiondb.commit()
            return redirect(url_for("read_rv"))
    else:
        msg = "Access denied. You have to log in first..."
        return render_template("log.html", msg=msg)

@app.route("/about")
def about():
    if 'username' in session:
        name = session.get("username")
        return render_template("about.html", name=name)
    else:
        msg = "Access denied. You have to log in first..."
        return render_template("log.html", msg=msg)

@app.route("/nytimes", methods=['GET', 'POST'])
def nytimes():
    if 'username' in session:
        if request.method == 'GET':
            name = session.get("username")
            return render_template('nytimes.html', name=name)
        else:
            mv = ""
            bk = ""
            req1 = requests.get("http://api.nytimes.com/svc/movies/v2/reviews/search.json?api-key=enter_api_key&query={0}".format(request.form.get("name")))
            req2 = requests.get("http://api.nytimes.com/svc/books/v2/reviews.json?api-key=enter_api_key&author={0}".format(request.form.get("name")))
            result1 = req1.json()
            result2 = req2.json()
            mv = []
            bk = []
            for review1 in result1["results"]:
                mv.append({'url':review1['link']['url'], 'name':review1['display_title']})
            for review2 in result2["results"]:
                bk.append({'url':review2['url'], 'name':review2['book_title']})
            return render_template('nytimes.html', mv=mv, bk=bk)
    else:
        msg = "Access denied. You have to log in first..."
        return render_template("log.html", msg=msg)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.debug = True
    app.run()
