from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_file
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Project
from config import Config
import os
import json
from io import BytesIO
import networkx as nx

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

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
    return render_template('admin.html', users=users)

@app.route('/graph_statistics', methods=['POST'])
@login_required
def graph_statistics():
    data = request.json
    nodes = data.get('nodes', [])
    edges = data.get('edges', [])

    G = nx.DiGraph()
    for node in nodes:
        G.add_node(node['id'])
    for edge in edges:
        G.add_edge(edge['from'], edge['to'])

    stats = {
        'num_nodes': G.number_of_nodes(),
        'num_edges': G.number_of_edges(),
        'avg_degree': sum(dict(G.degree()).values()) / G.number_of_nodes() if G.number_of_nodes() > 0 else 0,
        'is_dag': nx.is_directed_acyclic_graph(G),
        'connected_components': nx.number_connected_components(G.to_undirected()),
        'strongly_connected_components': nx.number_strongly_connected_components(G),
    }

    if stats['is_dag']:
        longest_path = nx.dag_longest_path(G)
        stats['longest_path_length'] = len(longest_path) - 1
        stats['longest_path_nodes'] = [nodes[i]['label'] for i in longest_path]

    stats['degree_centrality'] = nx.degree_centrality(G)
    stats['betweenness_centrality'] = nx.betweenness_centrality(G)
    stats['closeness_centrality'] = nx.closeness_centrality(G)

    return jsonify(stats)

@app.route('/get_node_suggestions')
@login_required
def get_node_suggestions():
    with open('node_suggestions.json', 'r') as f:
        suggestions = json.load(f)
    return jsonify(suggestions)

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()  # Drop all existing tables
        db.create_all()  # Recreate all tables with the updated schema
    app.run(host='0.0.0.0', port=5000)
