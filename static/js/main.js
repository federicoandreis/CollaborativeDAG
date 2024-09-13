document.addEventListener('DOMContentLoaded', () => {
    const graphDiv = document.getElementById('graph');
    const saveProjectBtn = document.getElementById('save-project');
    const projectNameInput = document.getElementById('project-name');
    const projectsList = document.getElementById('projects-list');
    const nodeLabelInput = document.getElementById('node-label');
    const addNodeBtn = document.getElementById('add-node');
    const addEdgeBtn = document.getElementById('add-edge');
    const removeSelectedBtn = document.getElementById('remove-selected');
    const clearAllBtn = document.getElementById('clear-all');
    const suggestedNodesList = document.getElementById('suggested-nodes-list');
    const exportGraphBtn = document.getElementById('export-graph');
    const importGraphInput = document.getElementById('import-graph');

    let nodes = new vis.DataSet();
    let edges = new vis.DataSet();

    let network = new vis.Network(graphDiv, { nodes, edges }, {
        manipulation: {
            enabled: true,
            addEdge: function(edgeData, callback) {
                if (edgeData.from === edgeData.to) {
                    var r = confirm("Do you want to connect the node to itself?");
                    if (r === true) {
                        callback(edgeData);
                    }
                }
                else {
                    callback(edgeData);
                }
            }
        },
        edges: {
            arrows: {
                to: { enabled: true, scaleFactor: 1, type: 'arrow' }
            }
        }
    });

    function saveProject() {
        const name = projectNameInput.value;
        const content = {
            nodes: nodes.get(),
            edges: edges.get()
        };
        
        if (!name) {
            alert('Please provide a project name');
            return;
        }

        fetch('/save_project', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name, content }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Project saved successfully');
                loadProjects();
            }
        })
        .catch(error => console.error('Error:', error));
    }

    function loadProjects() {
        fetch('/get_projects')
        .then(response => response.json())
        .then(projects => {
            projectsList.innerHTML = '<h2>Your Projects</h2>';
            const ul = document.createElement('ul');
            projects.forEach(project => {
                const li = document.createElement('li');
                li.textContent = project.name;
                li.addEventListener('click', () => {
                    nodes.clear();
                    edges.clear();
                    nodes.add(project.content.nodes);
                    edges.add(project.content.edges);
                    projectNameInput.value = project.name;
                });
                ul.appendChild(li);
            });
            projectsList.appendChild(ul);
        })
        .catch(error => console.error('Error:', error));
    }

    function loadSuggestedNodes() {
        fetch('/get_node_suggestions')
        .then(response => response.json())
        .then(data => {
            suggestedNodesList.innerHTML = '';
            data.nodes.forEach(node => {
                const div = document.createElement('div');
                div.textContent = node.label;
                div.title = node.annotation;
                div.addEventListener('click', () => {
                    nodes.add({ label: node.label, title: node.annotation });
                });
                suggestedNodesList.appendChild(div);
            });
        })
        .catch(error => console.error('Error:', error));
    }

    function exportGraph() {
        const graphData = {
            nodes: nodes.get(),
            edges: edges.get()
        };

        fetch('/export_graph', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(graphData),
        })
        .then(response => response.blob())
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = 'graph_export.json';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
        })
        .catch(error => console.error('Error:', error));
    }

    function importGraph(event) {
        const file = event.target.files[0];
        if (file) {
            const formData = new FormData();
            formData.append('file', file);

            fetch('/import_graph', {
                method: 'POST',
                body: formData,
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    nodes.clear();
                    edges.clear();
                    nodes.add(data.content.nodes);
                    edges.add(data.content.edges);
                    alert('Graph imported successfully');
                } else {
                    alert('Error importing graph: ' + data.error);
                }
            })
            .catch(error => console.error('Error:', error));
        }
    }

    saveProjectBtn.addEventListener('click', saveProject);

    addNodeBtn.addEventListener('click', () => {
        const label = nodeLabelInput.value || 'New Node';
        nodes.add({ label: label });
        nodeLabelInput.value = '';
    });

    addEdgeBtn.addEventListener('click', () => {
        network.addEdgeMode();
    });

    removeSelectedBtn.addEventListener('click', () => {
        const selectedNodes = network.getSelectedNodes();
        const selectedEdges = network.getSelectedEdges();
        nodes.remove(selectedNodes);
        edges.remove(selectedEdges);
    });

    clearAllBtn.addEventListener('click', () => {
        nodes.clear();
        edges.clear();
    });

    exportGraphBtn.addEventListener('click', exportGraph);
    importGraphInput.addEventListener('change', importGraph);

    // Right-click annotation functionality
    network.on("oncontext", function (params) {
        params.event.preventDefault();
        const nodeId = network.getNodeAt(params.pointer.DOM);
        if (nodeId) {
            const annotation = prompt('Enter annotation:');
            if (annotation) {
                const node = nodes.get(nodeId);
                node.title = annotation;
                nodes.update(node);
            }
        }
    });

    // Initial project and suggested nodes load
    loadProjects();
    loadSuggestedNodes();
});
