"""Tests for reaction_network_graph.network."""

import networkx as nx
import pytest
from pydantic import ValidationError

from reaction_network_graph.models import Species, Stage, Transition
from reaction_network_graph.network import ReactionNetwork


def _stages() -> list[Stage]:
    return [
        Stage(name="A", species=[Species(name="A")]),
        Stage(name="B+C", species=[Species(name="B"), Species(name="C")]),
        Stage(name="D", species=[Species(name="D")]),
    ]


def test__build_happy_path() -> None:
    """build() should construct a valid network from stages and transitions."""
    transitions = [
        ("A", "B+C", Transition(name="TS1")),
        ("A", "B+C", Transition(name="TS2")),
        ("B+C", "D", Transition(name="TS3")),
    ]
    network = ReactionNetwork.build(_stages(), transitions)
    assert network.stage_names() == ["A", "B+C", "D"]
    assert {t.name for _, _, t in network.transitions()} == {"TS1", "TS2", "TS3"}


def test__stage_accessor() -> None:
    """stage() should look up a stage by name."""
    network = ReactionNetwork.build(_stages(), [])
    assert network.stage("A").name == "A"


def test__stage_accessor_missing_raises() -> None:
    """stage() should raise KeyError for an unknown stage."""
    network = ReactionNetwork.build(_stages(), [])
    with pytest.raises(KeyError):
        network.stage("nonexistent")


def test__transition_accessor() -> None:
    """transition() should look up a transition by name."""
    transitions = [("A", "D", Transition(name="TS1"))]
    network = ReactionNetwork.build(_stages(), transitions)
    assert network.transition("TS1").name == "TS1"


def test__transition_accessor_missing_raises() -> None:
    """transition() should raise LookupError for an unknown transition."""
    network = ReactionNetwork.build(_stages(), [])
    with pytest.raises(LookupError):
        network.transition("nonexistent")


def test__transitions_returns_endpoints() -> None:
    """transitions() should yield (stage_a, stage_b, transition) triples."""
    transitions = [("A", "B+C", Transition(name="TS1"))]
    network = ReactionNetwork.build(_stages(), transitions)
    assert list(network.transitions()) == [("A", "B+C", transitions[0][2])]


def test__transitions_at() -> None:
    """transitions_at() should return (neighbor, transition) pairs for a stage."""
    transitions = [
        ("A", "B+C", Transition(name="TS1")),
        ("B+C", "D", Transition(name="TS3")),
    ]
    network = ReactionNetwork.build(_stages(), transitions)
    assert dict(network.transitions_at("B+C")).keys() == {"A", "D"}
    assert {name for name, _ in network.transitions_at("A")} == {"B+C"}


def test__build_rejects_duplicate_stage_name() -> None:
    """build() should reject duplicate stage names."""
    stages = [
        Stage(name="A", species=[Species(name="A")]),
        Stage(name="A", species=[Species(name="A")]),
    ]
    with pytest.raises(ValueError, match="Duplicate stage"):
        ReactionNetwork.build(stages, [])


def test__build_rejects_unknown_endpoint() -> None:
    """build() should reject a transition referencing an unknown stage."""
    transitions = [("A", "nonexistent", Transition(name="TS1"))]
    with pytest.raises(ValueError, match="unknown stage"):
        ReactionNetwork.build(_stages(), transitions)


def test__validator_rejects_self_loop_transition() -> None:
    """The network should reject a transition connecting a stage to itself."""
    graph = nx.MultiGraph()
    graph.add_node("A", stage=Stage(name="A", species=[Species(name="A")]))
    graph.add_edge("A", "A", key="TS1", transition=Transition(name="TS1"))
    with pytest.raises(ValidationError, match="cannot connect stage"):
        ReactionNetwork(graph=graph)


def test__validator_rejects_duplicate_transition_name_across_stage_pairs() -> None:
    """A transition name must be globally unique, not just per stage pair."""
    graph = nx.MultiGraph()
    graph.add_node("A", stage=Stage(name="A", species=[Species(name="A")]))
    graph.add_node("B", stage=Stage(name="B", species=[Species(name="B")]))
    graph.add_node("C", stage=Stage(name="C", species=[Species(name="C")]))
    graph.add_edge("A", "B", key="TS1", transition=Transition(name="TS1"))
    graph.add_edge("B", "C", key="TS1", transition=Transition(name="TS1"))
    with pytest.raises(ValidationError, match="Duplicate transition"):
        ReactionNetwork(graph=graph)


def test__construction_from_raw_graph_coerces_dict_payloads() -> None:
    """Constructing directly from an nx.MultiGraph should coerce raw dict payloads."""
    graph = nx.MultiGraph()
    graph.add_node("A", stage={"name": "A", "species": [{"name": "A"}]})
    graph.add_node("B", stage={"name": "B", "species": [{"name": "B"}]})
    graph.add_edge("A", "B", key="TS1", transition={"name": "TS1"})
    network = ReactionNetwork(graph=graph)
    assert isinstance(network.stage("A"), Stage)
    assert isinstance(network.transition("TS1"), Transition)


def test__construction_does_not_alias_input_graph() -> None:
    """The wrapper should not mutate or alias the caller's original graph object."""
    graph = nx.MultiGraph()
    graph.add_node("A", stage=Stage(name="A", species=[Species(name="A")]))
    network = ReactionNetwork(graph=graph)
    assert network.graph is not graph
    graph.add_node("B", stage=Stage(name="B", species=[Species(name="B")]))
    assert "B" not in network.graph
