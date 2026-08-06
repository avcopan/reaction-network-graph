"""Tests for reaction_network_graph.dot."""

from pathlib import Path

from reaction_network_graph.dot import to_dot, write_dot
from reaction_network_graph.models import Species, Stage, Transition
from reaction_network_graph.network import ReactionNetwork


def test__to_dot_well_shape() -> None:
    """A unimolecular stage should be rendered as a filled box."""
    network = ReactionNetwork.build([Stage(name="A", species=[Species(name="A")])], [])
    dot = to_dot(network)
    assert '"A" [label="A", shape=box, style=filled, fillcolor=lightgrey];' in dot


def test__to_dot_bimolecular_shape() -> None:
    """A bimolecular stage should be rendered as an unfilled ellipse."""
    stage = Stage(name="B+C", species=[Species(name="B"), Species(name="C")])
    network = ReactionNetwork.build([stage], [])
    dot = to_dot(network)
    assert '"B+C" [label="B + C", shape=ellipse];' in dot


def test__to_dot_stage_label_with_energy() -> None:
    """A stage's energy should be appended to its label on a second line."""
    stage = Stage(name="A", species=[Species(name="A")], energy=1.5)
    network = ReactionNetwork.build([stage], [])
    dot = to_dot(network)
    assert (
        '"A" [label="A\n(1.5)", shape=box, style=filled, fillcolor=lightgrey];' in dot
    )


def test__to_dot_transition_label_with_energy() -> None:
    """A transition's energy should be appended to its label on a second line."""
    stages = [
        Stage(name="A", species=[Species(name="A")]),
        Stage(name="B", species=[Species(name="B")]),
    ]
    transition = Transition(name="TS1", energy=10.0)
    network = ReactionNetwork.build(stages, [("A", "B", transition)])
    dot = to_dot(network)
    assert '"A" -- "B" [id="TS1", label="TS1\n(10.0)"];' in dot


def test__to_dot_uses_undirected_edge_syntax() -> None:
    """DOT output should use the `graph`/`--` undirected syntax, not `digraph`/`->`."""
    stages = [
        Stage(name="A", species=[Species(name="A")]),
        Stage(name="B", species=[Species(name="B")]),
    ]
    transition = Transition(name="TS1")
    network = ReactionNetwork.build(stages, [("A", "B", transition)])
    dot = to_dot(network)
    assert dot.startswith("graph ")
    assert "--" in dot
    assert "->" not in dot


def test__to_dot_escapes_special_characters() -> None:
    """Stage names containing quotes should be escaped in the DOT output."""
    stage = Stage(name='A"1', species=[Species(name="A")])
    network = ReactionNetwork.build([stage], [])
    dot = to_dot(network)
    assert '"A\\"1"' in dot


def test__write_dot(tmp_path: Path) -> None:
    """write_dot() should write to_dot()'s content plus a trailing newline."""
    stage = Stage(name="A", species=[Species(name="A")])
    network = ReactionNetwork.build([stage], [])
    out = tmp_path / "network.dot"
    write_dot(network, out)
    assert out.read_text() == to_dot(network) + "\n"
