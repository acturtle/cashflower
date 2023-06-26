import matplotlib.pyplot as plt
import networkx as nx


# print(DG.number_of_edges())
# print(list(DG.successors(1)))
# print(list(DG.predecessors(2)))


def draw(DG):
    nx.draw(DG, with_labels=True)
    plt.show()


def get_nodes_without_predecessors(DG):
    return [node for node in DG.nodes if len(list(DG.predecessors(node))) == 0]


if __name__ == "__main__":
    # Create graph
    DG = nx.DiGraph()
    DG.add_node(1)
    DG.add_nodes_from([2, 3])
    DG.add_edge(1, 2)

    # Remove nodes without predecessors
    nodes_without_predecessors = get_nodes_without_predecessors(DG)
    DG.remove_nodes_from(nodes_without_predecessors)
    draw(DG)
