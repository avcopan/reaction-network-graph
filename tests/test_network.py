"""Tests for reaction_network_graph.network."""

import networkx as nx
import pytest
from pydantic import ValidationError

from reaction_network_graph.models import Species, Stage, Step
from reaction_network_graph.network import ReactionNetwork


def _stages() -> list[Stage]:
    return [
        Stage(name="A", species=[Species(name="A")]),
        Stage(name="B+C", species=[Species(name="B"), Species(name="C")]),
        Stage(name="D", species=[Species(name="D")]),
    ]


def test__build_happy_path() -> None:
    """build() should construct a valid network from stages and steps."""
    steps = [
        ("A", "B+C", Step(name="TS1")),
        ("A", "B+C", Step(name="TS2")),
        ("B+C", "D", Step(name="TS3")),
    ]
    network = ReactionNetwork.build(_stages(), steps)
    assert network.stage_names() == ["A", "B+C", "D"]
    assert {s.name for _, _, s in network.steps()} == {"TS1", "TS2", "TS3"}


def test__stage_accessor() -> None:
    """stage() should look up a stage by name."""
    network = ReactionNetwork.build(_stages(), [])
    assert network.stage("A").name == "A"


def test__stage_accessor_missing_raises() -> None:
    """stage() should raise KeyError for an unknown stage."""
    network = ReactionNetwork.build(_stages(), [])
    with pytest.raises(KeyError):
        network.stage("nonexistent")


def test__step_accessor() -> None:
    """step() should look up a step by name."""
    steps = [("A", "D", Step(name="TS1"))]
    network = ReactionNetwork.build(_stages(), steps)
    assert network.step("TS1").name == "TS1"


def test__step_accessor_missing_raises() -> None:
    """step() should raise LookupError for an unknown step."""
    network = ReactionNetwork.build(_stages(), [])
    with pytest.raises(LookupError):
        network.step("nonexistent")


def test__steps_returns_endpoints() -> None:
    """steps() should yield (stage_a, stage_b, step) triples."""
    steps = [("A", "B+C", Step(name="TS1"))]
    network = ReactionNetwork.build(_stages(), steps)
    assert list(network.steps()) == [("A", "B+C", steps[0][2])]


def test__steps_at() -> None:
    """steps_at() should return (neighbor, step) pairs for a stage."""
    steps = [
        ("A", "B+C", Step(name="TS1")),
        ("B+C", "D", Step(name="TS3")),
    ]
    network = ReactionNetwork.build(_stages(), steps)
    assert dict(network.steps_at("B+C")).keys() == {"A", "D"}
    assert {name for name, _ in network.steps_at("A")} == {"B+C"}


def test__build_rejects_duplicate_stage_name() -> None:
    """build() should reject duplicate stage names."""
    stages = [
        Stage(name="A", species=[Species(name="A")]),
        Stage(name="A", species=[Species(name="A")]),
    ]
    with pytest.raises(ValueError, match="Duplicate stage"):
        ReactionNetwork.build(stages, [])


def test__build_rejects_unknown_endpoint() -> None:
    """build() should reject a step referencing an unknown stage."""
    steps = [("A", "nonexistent", Step(name="TS1"))]
    with pytest.raises(ValueError, match="unknown stage"):
        ReactionNetwork.build(_stages(), steps)


def test__validator_rejects_self_loop_step() -> None:
    """The network should reject a step connecting a stage to itself."""
    graph = nx.MultiGraph()
    graph.add_node("A", stage=Stage(name="A", species=[Species(name="A")]))
    graph.add_edge("A", "A", key="TS1", step=Step(name="TS1"))
    with pytest.raises(ValidationError, match="cannot connect stage"):
        ReactionNetwork(graph=graph)


def test__validator_rejects_duplicate_step_name_across_stage_pairs() -> None:
    """A step name must be globally unique, not just per stage pair."""
    graph = nx.MultiGraph()
    graph.add_node("A", stage=Stage(name="A", species=[Species(name="A")]))
    graph.add_node("B", stage=Stage(name="B", species=[Species(name="B")]))
    graph.add_node("C", stage=Stage(name="C", species=[Species(name="C")]))
    graph.add_edge("A", "B", key="TS1", step=Step(name="TS1"))
    graph.add_edge("B", "C", key="TS1", step=Step(name="TS1"))
    with pytest.raises(ValidationError, match="Duplicate step"):
        ReactionNetwork(graph=graph)


def test__construction_from_raw_graph_coerces_dict_payloads() -> None:
    """Constructing directly from an nx.MultiGraph should coerce raw dict payloads."""
    graph = nx.MultiGraph()
    graph.add_node("A", stage={"name": "A", "species": [{"name": "A"}]})
    graph.add_node("B", stage={"name": "B", "species": [{"name": "B"}]})
    graph.add_edge("A", "B", key="TS1", step={"name": "TS1"})
    network = ReactionNetwork(graph=graph)
    assert isinstance(network.stage("A"), Stage)
    assert isinstance(network.step("TS1"), Step)


def test__construction_does_not_alias_input_graph() -> None:
    """The wrapper should not mutate or alias the caller's original graph object."""
    graph = nx.MultiGraph()
    graph.add_node("A", stage=Stage(name="A", species=[Species(name="A")]))
    network = ReactionNetwork(graph=graph)
    assert network.graph is not graph
    graph.add_node("B", stage=Stage(name="B", species=[Species(name="B")]))
    assert "B" not in network.graph
