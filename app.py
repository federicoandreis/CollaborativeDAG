from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_file
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import db, User, Project
from config import Config
import os
import json
from io import BytesIO
from openai import OpenAI
from urllib.parse import urlparse

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# ... (keep all other routes and functions unchanged)

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/admin/generate_graph', methods=['POST'])
@login_required
def generate_graph():
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Access denied'})

    prompt = request.json.get('prompt') if request.json else None
    if not prompt:
        return jsonify({'success': False, 'error': 'No prompt provided'})

    try:
        graph_data = generate_graph_data_with_gpt(prompt)
        return jsonify({'success': True, 'graph_data': graph_data})
    except Exception as e:
        app.logger.error(f"Error generating graph: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

def generate_graph_data_with_gpt(prompt):
    try:
        client = OpenAI(
            api_key=os.environ.get('OPENAI_API_KEY'),
            organization='org-SltZ4uEu1VAOxCnlY8qzWH3a'
        )
    except Exception as e:
        app.logger.error(f"Error initializing OpenAI client: {str(e)}")
        raise Exception("Failed to initialize OpenAI client. Please check your API key and organization.")

    gpt_prompt = f"""
    You are an AI assistant and expert scientist, tasked with creating a comprehensive and detailed Directed Acyclic Graph (DAG) that illustrates causal mechanisms based on established scientific evidence. Your goal is to analyze the given prompt and generate a structured representation of the specific causal links described in the scientific literature, including relevant context, confounders, mediators, moderators, and indirect pathways.

    Please follow these guidelines:

    1. **Identify Key Concepts, Contextual Factors, and Confounders:**
       - Extract specific factors, processes, outcomes, and context factors mentioned or implied in the prompt.
       - Include potential **confounders**, **mediators**, **moderators**, and other variables that may influence the causal relationships.
       - Use your domain knowledge to include relevant intermediate steps and contextual factors supported by scientific evidence.

    2. **Determine Causal Relationships:**
       - Map out how each concept, context factor, or event causally influences others.
       - Include **direct and indirect pathways**, **interactions**, and complex relationships.
       - Capture biological, chemical, environmental, social, economic, and behavioral mechanisms as appropriate.

    3. **Create a Detailed and Comprehensive DAG Structure:**
       - Each node should represent a specific concept, factor, event, or variable.
       - Include nodes for confounders, mediators, moderators, and other relevant variables.
       - Each edge should represent a direct causal link from one node to another.
       - The DAG should reflect the **complexity of the causal relationships**, including multiple pathways and interconnected nodes, not just a simple linear sequence.

    4. **Ensure Graph Acyclicity:**
       - The graph must be acyclic with no circular dependencies.

    5. **Provide Clear Labels and Annotations:**
       - **Nodes:**
         - Include 'id', 'label', and 'title' for each node.
         - 'label' should be concise yet descriptive.
         - 'title' should provide a brief explanation or reference to scientific evidence (e.g., "Socioeconomic status influences smoking rates [Smith et al., 2020]").

    6. **Cite Sources:**
       - When possible, reference scientific studies or reviews that support each causal link (use placeholder citations if necessary).

    7. **Output Format:**
       - Return the result as a JSON object with two keys: **'nodes'** and **'edges'**.
       - **'nodes'**: A list of objects, each with 'id', 'label', and 'title'.
       - **'edges'**: A list of objects, each with 'from' and 'to' keys representing connections between nodes.

    **Example Format:**

    {{
      "nodes": [
        {{"id": 1, "label": "Policy X Implementation", "title": "Introduction of Policy X to address issue Y"}},
        {{"id": 2, "label": "Resource Allocation", "title": "Policy X reallocates resources [Doe et al., 2021]"}},
        {{"id": 3, "label": "Service Access", "title": "Changes in access to services [Smith et al., 2020]"}},
        {{"id": 4, "label": "Outcome Y", "title": "Impact on Outcome Y"}},
        {{"id": 5, "label": "Socioeconomic Status", "title": "Influences access and effectiveness of Policy X [Marmot, 2005]"}},
        {{"id": 6, "label": "Geographical Location", "title": "Affects policy implementation and service availability [Lee et al., 2019]"}},
        {{"id": 7, "label": "Cultural Factors", "title": "Modulate response to Policy X [Garcia et al., 2018]"}},
        {{"id": 8, "label": "Public Awareness", "title": "Awareness campaigns influence effectiveness [Nguyen et al., 2021]"}}
      ],
      "edges": [
        {{"from": 1, "to": 2}},
        {{"from": 2, "to": 3}},
        {{"from": 3, "to": 4}},
        {{"from": 5, "to": 3}},
        {{"from": 6, "to": 1}},
        {{"from": 7, "to": 3}},
        {{"from": 8, "to": 3}},
        {{"from": 5, "to": 4}},
        {{"from": 6, "to": 4}},
        {{"from": 7, "to": 4}}
      ]
    }} 

    Now, based on this information, create a DAG for the following prompt:
    {prompt}
    """

    try:
        response = client.chat.completions.create(
            model='gpt-3.5-turbo-0125',
            messages=[
                {'role': 'system', 'content': 'You are an AI assistant tasked with creating a Directed Acyclic Graph (DAG) based on causal relationships.'},
                {'role': 'user', 'content': gpt_prompt}
            ],
            max_tokens=1000,
            n=1,
            temperature=0.5,
        )
    except Exception as e:
        app.logger.error(f"Error calling OpenAI API: {str(e)}")
        raise Exception("Failed to generate graph data. Please try again later.")

    try:
        gpt_output = response.choices[0].message.content.strip()
        app.logger.info(f'Raw GPT response: {gpt_output}')  # Log the raw API response
        graph_structure = json.loads(gpt_output)

        # Validate the structure of the graph data
        if not isinstance(graph_structure, dict):
            raise ValueError("Invalid graph structure: not a dictionary")
        if 'nodes' not in graph_structure or 'edges' not in graph_structure:
            raise ValueError("Invalid graph structure: missing 'nodes' or 'edges' key")
        if not isinstance(graph_structure['nodes'], list) or not isinstance(graph_structure['edges'], list):
            raise ValueError("Invalid graph structure: 'nodes' or 'edges' is not a list")

        # Ensure all nodes have required fields and valid types
        for i, node in enumerate(graph_structure['nodes']):
            if not isinstance(node, dict):
                raise ValueError(f"Invalid node structure at index {i}: not a dictionary")
            if not all(key in node for key in ('id', 'label', 'title')):
                raise ValueError(f"Invalid node structure at index {i}: missing required fields")
            if not isinstance(node['id'], int):
                raise ValueError(f"Invalid node structure at index {i}: 'id' is not an integer")
            if not isinstance(node['label'], str) or not isinstance(node['title'], str):
                raise ValueError(f"Invalid node structure at index {i}: 'label' or 'title' is not a string")

        # Ensure all edges have required fields and valid types
        for i, edge in enumerate(graph_structure['edges']):
            if not isinstance(edge, dict):
                raise ValueError(f"Invalid edge structure at index {i}: not a dictionary")
            if not all(key in edge for key in ('from', 'to')):
                raise ValueError(f"Invalid edge structure at index {i}: missing required fields")
            if not isinstance(edge['from'], int) or not isinstance(edge['to'], int):
                raise ValueError(f"Invalid edge structure at index {i}: 'from' or 'to' is not an integer")

        return graph_structure
    except json.JSONDecodeError as jde:
        app.logger.error(f"Failed to parse JSON from GPT response: {str(jde)}")
        raise Exception("Failed to parse graph data. The API response was not valid JSON. Please try again.")
    except ValueError as ve:
        app.logger.error(f"Validation error in GPT response: {str(ve)}")
        raise Exception(f"Generated graph data is invalid: {str(ve)}. Please try again with a different prompt.")
    except Exception as e:
        app.logger.error(f"Unexpected error processing GPT response: {str(e)}")
        raise Exception("An unexpected error occurred while processing the graph data. Please try again later.")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000)
