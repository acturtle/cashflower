# cashflower/visualize.py
import json
import os
import tempfile
import webbrowser
import inspect


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

    print("Graph visualization opened in your default browser.")
    print(f"Temporary file: {temp_file}")


def _generate_html_content(dg):
    """
    Generate HTML content with dagre-d3 visualization using template.

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
        # Get the source code of the variable's function
        try:
            source_code = inspect.getsource(node.func)
        except (OSError, TypeError):
            source_code = "# Source code not available"

        nodes.append({
            "id": node.name,
            "label": node.name,
            "source": source_code
        })

    # Process edges
    for source, target in dg.edges():
        edges.append({
            "source": source.name,
            "target": target.name
        })

    # Load template file
    template_path = os.path.join(os.path.dirname(__file__), 'html_tpl', 'graph.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()

    # Replace placeholders with actual data
    html_content = template_content.replace('{{NODES_DATA}}', json.dumps(nodes))
    html_content = html_content.replace('{{EDGES_DATA}}', json.dumps(edges))

    return html_content
