from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_file
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Project
from config import Config
import os
import json
from io import BytesIO

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

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
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
        else:
            new_user = User(username=username)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/save_project', methods=['POST'])
@login_required
def save_project():
    data = request.json
    project = Project(user_id=current_user.id, name=data['name'], content=json.dumps(data['content']))
    db.session.add(project)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/get_projects')
@login_required
def get_projects():
    projects = Project.query.filter_by(user_id=current_user.id).all()
    return jsonify([{'id': p.id, 'name': p.name, 'content': json.loads(p.content)} for p in projects])

@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('index'))
    users = User.query.all()
    projects = Project.query.all()
    return render_template('admin.html', users=users, projects=projects)

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('index'))
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        flash(f'User {user.username} deleted successfully')
    else:
        flash('User not found')
    return redirect(url_for('admin'))

@app.route('/admin/delete_project/<int:project_id>', methods=['POST'])
@login_required
def delete_project(project_id):
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('index'))
    project = Project.query.get(project_id)
    if project:
        db.session.delete(project)
        db.session.commit()
        flash(f'Project {project.name} deleted successfully')
    else:
        flash('Project not found')
    return redirect(url_for('admin'))

@app.route('/admin/make_admin/<int:user_id>', methods=['POST'])
@login_required
def make_user_admin(user_id):
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('index'))
    user = User.query.get(user_id)
    if user:
        user.is_admin = True
        db.session.commit()
        flash(f'User {user.username} is now an admin')
    else:
        flash('User not found')
    return redirect(url_for('admin'))

@app.route('/get_node_suggestions')
@login_required
def get_node_suggestions():
    with open('node_suggestions.json', 'r') as f:
        suggestions = json.load(f)
    return jsonify(suggestions)

@app.route('/export_graph', methods=['POST'])
@login_required
def export_graph():
    data = request.json
    json_data = json.dumps(data, indent=2)
    return send_file(
        BytesIO(json_data.encode()),
        mimetype='application/json',
        as_attachment=True,
        download_name='graph_export.json'
    )

@app.route('/import_graph', methods=['POST'])
@login_required
def import_graph():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file part'})
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No selected file'})
    if file and file.filename.endswith('.json'):
        try:
            content = json.loads(file.read().decode('utf-8'))
            return jsonify({'success': True, 'content': content})
        except json.JSONDecodeError:
            return jsonify({'success': False, 'error': 'Invalid JSON file'})
    return jsonify({'success': False, 'error': 'Invalid file type'})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000)
