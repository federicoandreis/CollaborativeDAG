import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_file
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Project
from config import Config
import json
from io import BytesIO
import networkx as nx
import logging

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Set up logging
logging.basicConfig(level=logging.DEBUG)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_default_user():
    username = 'fede'
    password = 'admin'
    if not User.query.filter_by(username=username).first():
        new_user = User(username=username, password=generate_password_hash(password), is_admin=True)
        db.session.add(new_user)
        db.session.commit()
        logging.info(f"Default user '{username}' created with admin privileges.")
    else:
        logging.info(f"Default user '{username}' already exists.")

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            logging.info(f"User '{username}' logged in successfully.")
            return redirect(url_for('index'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        is_admin = request.form.get('is_admin') == 'on'
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
        else:
            new_user = User(username=username, is_admin=is_admin)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            logging.info(f"New user '{username}' registered successfully.")
            flash('Registration successful')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/admin')
@login_required
def admin():
    logging.info(f"User '{current_user.username}' attempting to access admin dashboard.")
    logging.info(f"User admin status: {current_user.is_admin}")
    if not current_user.is_admin:
        logging.warning(f"Access denied for user '{current_user.username}' - not an admin.")
        flash('Access denied')
        return redirect(url_for('index'))
    users = User.query.all()
    projects = Project.query.all()
    logging.info(f"Admin dashboard accessed by '{current_user.username}'.")
    return render_template('admin.html', users=users, projects=projects)

# ... (rest of the file remains unchanged)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_default_user()
    app.run(host='0.0.0.0', port=5000)
