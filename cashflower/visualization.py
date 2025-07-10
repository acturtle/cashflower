import json
import os
import tempfile
import webbrowser


def show_graph(dg):
    """
    Create and display an interactive graph visualization of variable dependencies using dagre-d3.

    Args:
        dg (networkx.DiGraph): Directed graph of variable dependencies
    """
    # Generate the HTML content
    html_content = _generate_html_content(dg)

    # Create a temporary HTML file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        f.write(html_content)
        temp_file = f.name

    # Open the file in the default web browser
    webbrowser.open(f'file://{os.path.abspath(temp_file)}')

    print(f"Graph visualization opened in your default browser.")
    print(f"Temporary file: {temp_file}")


def _generate_html_content(dg):
    """
    Generate HTML content with dagre-d3 visualization.

    Args:
        dg (networkx.DiGraph): Directed graph of variable dependencies

    Returns:
        str: HTML content as string
    """
    # Create nodes and edges data for dagre-d3
    nodes = []
    edges = []

    # Process nodes
    for node in dg.nodes():
        nodes.append({
            "id": node.name,
            "label": node.name
        })

    # Process edges
    for source, target in dg.edges():
        edges.append({
            "source": source.name,
            "target": target.name
        })

    html_template = f'''
<!DOCTYPE html>
<html>
<head>
    <title>Cashflow Model - Variable Dependencies</title>
    <script src="https://d3js.org/d3.v5.min.js"></script>
    <script src="https://unpkg.com/dagre-d3@0.6.4/dist/dagre-d3.min.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}

        .graph-container {{
            background: white;
            border: 1px solid #ddd;
            border-radius: 5px;
            overflow: auto;
            height: 90vh;
            position: relative;
        }}

        .graph-container svg {{
            width: 100%;
            height: 100%;
        }}

        .node rect {{
            stroke: #333;
            fill: #fff;
            stroke-width: 1.5px;
        }}

        .edgePath path {{
            stroke: #333;
            fill: none;
            stroke-width: 1.5px;
        }}

        .controls {{
            position: absolute;
            top: 10px;
            right: 10px;
            background: rgba(255, 255, 255, 0.9);
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #ddd;
        }}
    </style>
</head>
<body>
    <div class="graph-container">
        <svg id="svg-canvas"></svg>
    </div>

    <script>
        // Create a new directed graph
        var g = new dagreD3.graphlib.Graph()
            .setGraph({{}})
            .setDefaultEdgeLabel(function() {{ return {{}}; }});

        // Add nodes
        var nodes = {json.dumps(nodes)};
        nodes.forEach(function(node) {{
            g.setNode(node.id, {{ label: node.label }});
        }});

        // Add edges
        var edges = {json.dumps(edges)};
        edges.forEach(function(edge) {{
            g.setEdge(edge.source, edge.target);
        }});

        // Create the renderer
        var render = new dagreD3.render();

        // Set up an SVG group so that we can translate the final graph.
        var svg = d3.select("#svg-canvas");
        var svgGroup = svg.append("g");

        // Run the renderer
        render(svgGroup, g);

        // Set up zoom support
        var zoom = d3.zoom()
            .scaleExtent([0.1, 3])
            .on("zoom", function() {{
                svgGroup.attr("transform", d3.event.transform);
            }});

        svg.call(zoom);
    </script>
</body>
</html>
    '''

    return html_template
