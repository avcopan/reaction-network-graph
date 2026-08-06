"""Tests for reaction_network_graph.dot."""

from pathlib import Path

from reaction_network_graph.dot import to_dot, write_dot, write_svg
from reaction_network_graph.models import Species, Stage, Step
from reaction_network_graph.network import ReactionNetwork


def test__to_dot_renders_stage_as_pink_circle() -> None:
    """A stage should be rendered as a filled pink circle."""
    stage = Stage(name="A", species=[Species(name="A")])
    network = ReactionNetwork.build([], stages=[stage])
    dot = to_dot(network)
    assert '"A" [label=A, shape=circle, style=filled, fillcolor="#df8bbb"];' in dot


def test__to_dot_renders_species_as_satellite_node() -> None:
    """Each species should be its own satellite node, edged to its stage."""
    stage = Stage(name="A", species=[Species(name="A")])
    network = ReactionNetwork.build([], stages=[stage])
    dot = to_dot(network)
    assert (
        '"A__species0" [label=A, shape=circle, style=filled, fillcolor="#fc8d62"];'
        in dot
    )
    assert '"A" -- "A__species0" [color=black, penwidth=1];' in dot


def test__to_dot_renders_multiple_species_satellites() -> None:
    """A bimolecular stage should get one satellite node per species."""
    stage = Stage(name="B+C", species=[Species(name="B"), Species(name="C")])
    network = ReactionNetwork.build([], stages=[stage])
    dot = to_dot(network)
    assert '"B+C__species0" [label=B,' in dot
    assert '"B+C__species1" [label=C,' in dot


def test__to_dot_renders_step_as_blue_square_between_stages() -> None:
    """A step should be a blue square with edges to both of its stages."""
    a = Stage(name="A", species=[Species(name="A")])
    b = Stage(name="B", species=[Species(name="B")])
    step = Step(name="TS1")
    network = ReactionNetwork.build([(a, b, step)])
    dot = to_dot(network)
    assert '"TS1" [label=TS1, shape=square, style=filled, fillcolor="#8da0cb"];' in dot
    assert '"A" -- "TS1" [color="#8da0cb", penwidth=3];' in dot
    assert '"TS1" -- "B" [color="#8da0cb", penwidth=3];' in dot


def test__to_dot_stage_label_with_energy() -> None:
    """A stage's energy should be appended to its label on a second line."""
    stage = Stage(name="A", species=[Species(name="A")], energy=1.5)
    network = ReactionNetwork.build([], stages=[stage])
    dot = to_dot(network)
    assert (
        '"A" [label="A\\n(1.5)", shape=circle, style=filled, fillcolor="#df8bbb"];'
        in dot
    )


def test__to_dot_step_label_with_energy() -> None:
    """A step's energy should be appended to its label on a second line."""
    a = Stage(name="A", species=[Species(name="A")])
    b = Stage(name="B", species=[Species(name="B")])
    step = Step(name="TS1", energy=10.0)
    network = ReactionNetwork.build([(a, b, step)])
    dot = to_dot(network)
    assert (
        '"TS1" [label="TS1\\n(10.0)", shape=square, style=filled, fillcolor="#8da0cb"];'
        in dot
    )


def test__to_dot_uses_undirected_graph_syntax() -> None:
    """DOT output should use the `graph`/`--` undirected syntax, not `digraph`/`->`."""
    stage = Stage(name="A", species=[Species(name="A")])
    network = ReactionNetwork.build([], stages=[stage])
    dot = to_dot(network)
    assert dot.startswith("graph ")
    assert "--" in dot
    assert "->" not in dot


def test__to_dot_escapes_special_characters_in_identifiers() -> None:
    """Stage names containing quotes should be escaped in DOT identifiers."""
    stage = Stage(name='A"1', species=[Species(name="A")])
    network = ReactionNetwork.build([], stages=[stage])
    dot = to_dot(network)
    assert '"A\\"1"' in dot


def test__write_dot(tmp_path: Path) -> None:
    """write_dot() should write the same DOT text to_dot() returns."""
    stage = Stage(name="A", species=[Species(name="A")])
    network = ReactionNetwork.build([], stages=[stage])
    out = tmp_path / "network.dot"
    write_dot(network, out)
    assert out.read_text() == to_dot(network)


def test__write_svg(tmp_path: Path) -> None:
    """write_svg() should render a real SVG file via Graphviz."""
    stage = Stage(name="A", species=[Species(name="A")])
    network = ReactionNetwork.build([], stages=[stage])
    out = tmp_path / "network.svg"
    write_svg(network, out)
    assert out.read_text().startswith("<?xml")
