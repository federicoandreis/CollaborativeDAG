from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_file
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Project
from config import Config
import os
import json
from io import BytesIO
import requests
from urllib.parse import urlparse

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
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user is None or not user.check_password(password):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user)
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user is not None:
            flash('Username already exists')
            return redirect(url_for('register'))
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('index'))
    users = User.query.all()
    projects = Project.query.all()
    return render_template('admin.html', users=users, projects=projects)

@app.route('/save_project', methods=['POST'])
@login_required
def save_project():
    data = request.json
    project = Project.query.filter_by(name=data['name'], user_id=current_user.id).first()
    if project:
        project.content = json.dumps(data['content'])
    else:
        project = Project(name=data['name'], content=json.dumps(data['content']), user_id=current_user.id)
        db.session.add(project)
    db.session.commit()
    return jsonify(success=True)

@app.route('/get_projects')
@login_required
def get_projects():
    projects = Project.query.filter_by(user_id=current_user.id).all()
    return jsonify([{'id': p.id, 'name': p.name, 'content': json.loads(p.content)} for p in projects])

@app.route('/get_node_suggestions')
def get_node_suggestions():
    with open('node_suggestions.json', 'r') as f:
        suggestions = json.load(f)
    return jsonify(suggestions)

@app.route('/export_graph', methods=['POST'])
@login_required
def export_graph():
    graph_data = request.json
    json_data = json.dumps(graph_data, indent=2)
    return send_file(BytesIO(json_data.encode()), mimetype='application/json', as_attachment=True, download_name='graph_export.json')

@app.route('/import_graph', methods=['POST'])
@login_required
def import_graph():
    if 'file' not in request.files:
        return jsonify(success=False, error='No file part')
    file = request.files['file']
    if file.filename == '':
        return jsonify(success=False, error='No selected file')
    if file:
        try:
            graph_data = json.load(file)
            return jsonify(success=True, content=graph_data)
        except json.JSONDecodeError:
            return jsonify(success=False, error='Invalid JSON file')

@app.route('/admin/generate_graph', methods=['POST'])
@login_required
def generate_graph():
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Access denied'})

    prompt = request.json.get('prompt') if request.json else None
    if not prompt:
        return jsonify({'success': False, 'error': 'No prompt provided'})

    try:
        # Call Elicit.org API
        elicit_response = call_elicit_api(prompt)

        # Process the response using OpenAI's GPT
        processed_data = process_with_gpt(elicit_response)

        # Generate graph data
        graph_data = generate_graph_data(processed_data)

        return jsonify({'success': True, 'graph_data': graph_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def call_elicit_api(prompt):
    # Replace with actual Elicit.org API endpoint and key
    api_key = os.environ.get('ELICIT_API_KEY')
    url = "https://api.elicit.org/v1/search"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {"query": prompt}
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()

def process_with_gpt(elicit_response):
    # Implement the processing logic here without using OpenAI
    # For now, we'll return a dummy response
    return {
        "nodes": ["Node 1", "Node 2", "Node 3"],
        "edges": [{"from": "Node 1", "to": "Node 2"}, {"from": "Node 2", "to": "Node 3"}]
    }

def generate_graph_data(processed_data):
    # Convert the processed data into the format expected by vis.js
    nodes = [{"id": i, "label": node} for i, node in enumerate(processed_data['nodes'])]
    edges = [{"from": processed_data['nodes'].index(edge['from']), "to": processed_data['nodes'].index(edge['to'])} for edge in processed_data['edges']]
    return {"nodes": nodes, "edges": edges}

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000)
