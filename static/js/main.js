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
        },
        physics: {
            stabilization: {
                enabled: true,
                iterations: 1000,
                updateInterval: 100
            }
        }
    });

    network.once("stabilizationIterationsDone", function() {
        network.setOptions( { physics: false } );
    });

    // Rest of the code remains unchanged...
    
    // Initial project and suggested nodes load
    loadProjects();
    loadSuggestedNodes();
});
