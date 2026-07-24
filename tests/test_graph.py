import networkx as nx

from cashflower.graph import set_cycle_order


class Node:
    """Minimal stand-in for a variable node (set_cycle_order only reads name and sets cycle_order)."""
    def __init__(self, name):
        self.name = name
        self.cycle_order = None

    def __repr__(self):
        return self.name


class TestSetCycleOrder:
    def test_peers_at_same_level_are_ordered_by_name(self):
        # 'x' and 'y' are peers: both depend on 'a' and are depended on by 'b'
        # (mirrors dev_model_22, where x and y both `return a(t)`).
        # Edges are inserted so that 'y' precedes 'x' in node order, which is the
        # order that previously leaked into the output column order and made it
        # non-deterministic across runs.
        a, b, x, y = Node("a"), Node("b"), Node("x"), Node("y")
        dg = nx.DiGraph()
        dg.add_edge(a, y)
        dg.add_edge(a, x)
        dg.add_edge(y, b)
        dg.add_edge(x, b)

        set_cycle_order(dg)

        assert a.cycle_order == 1
        assert x.cycle_order == 2
        assert y.cycle_order == 3
        assert b.cycle_order == 4
