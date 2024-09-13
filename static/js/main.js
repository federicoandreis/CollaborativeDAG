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
    const showStatisticsBtn = document.getElementById('show-statistics');
    const statisticsModal = document.getElementById('statistics-modal');
    const closeStatisticsModal = statisticsModal.getElementsByClassName('close')[0];
    const statisticsList = document.getElementById('statistics-list');
    const suggestedNodesList = document.getElementById('suggested-nodes-list');

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

    showStatisticsBtn.addEventListener('click', () => {
        const graphData = {
            nodes: nodes.get(),
            edges: edges.get()
        };

        fetch('/graph_statistics', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(graphData),
        })
        .then(response => response.json())
        .then(stats => {
            statisticsList.innerHTML = '';
            for (const [key, value] of Object.entries(stats)) {
                const li = document.createElement('li');
                if (typeof value === 'object') {
                    li.textContent = `${key}:`;
                    const ul = document.createElement('ul');
                    for (const [subKey, subValue] of Object.entries(value)) {
                        const subLi = document.createElement('li');
                        subLi.textContent = `${subKey}: ${subValue.toFixed(4)}`;
                        ul.appendChild(subLi);
                    }
                    li.appendChild(ul);
                } else {
                    li.textContent = `${key}: ${value}`;
                }
                statisticsList.appendChild(li);
            }
            statisticsModal.style.display = 'block';
        })
        .catch(error => console.error('Error:', error));
    });

    closeStatisticsModal.addEventListener('click', () => {
        statisticsModal.style.display = 'none';
    });

    window.addEventListener('click', (event) => {
        if (event.target == statisticsModal) {
            statisticsModal.style.display = 'none';
        }
    });

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
