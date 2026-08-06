"""The ``ReactionNetwork`` data structure: stages connected by transitions."""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

import networkx as nx
from pydantic import BaseModel, ConfigDict, model_validator

from .models import Stage, Transition

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence

_STAGE_KEY = "stage"
_TRANSITION_KEY = "transition"


def _coerce[T: BaseModel](value: object, model: type[T]) -> T:
    """Coerce a raw dict or an existing model instance to `model`."""
    if isinstance(value, model):
        return value
    if isinstance(value, dict):
        return model.model_validate(value)
    msg = f"Expected {model.__name__} or dict, got {type(value).__name__}"
    raise TypeError(msg)


class ReactionNetwork[StageT: Stage, TransitionT: Transition](BaseModel):
    """A reaction network: stages (nodes) connected by transitions (edges).

    The underlying `networkx.MultiGraph` only ever stores generic nodes and
    edges; the `Stage`/`Transition` payloads are validated on construction
    and whenever the model is (re)built.

    Examples
    --------
    >>> from reaction_network_graph.models import Species
    >>> a = Stage(name="A", species=[Species(name="A")])
    >>> bc = Stage(name="B+C", species=[Species(name="B"), Species(name="C")])
    >>> ts = Transition(name="TS1")
    >>> network = ReactionNetwork.build([a, bc], [("A", "B+C", ts)])
    >>> network.stage("A").name
    'A'
    >>> network.stage_names()
    ['A', 'B+C']
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    graph: nx.MultiGraph

    @classmethod
    def build(
        cls,
        stages: Sequence[StageT],
        transitions: Sequence[tuple[str, str, TransitionT]],
    ) -> Self:
        """Build a network from stages and (stage_a, stage_b, transition) triples."""
        graph = nx.MultiGraph()
        for stage in stages:
            if stage.name in graph:
                msg = f"Duplicate stage name: {stage.name!r}"
                raise ValueError(msg)
            graph.add_node(stage.name, **{_STAGE_KEY: stage})
        for stage_a, stage_b, transition in transitions:
            for endpoint in (stage_a, stage_b):
                if endpoint not in graph:
                    msg = (
                        f"Transition {transition.name!r} references "
                        f"unknown stage {endpoint!r}"
                    )
                    raise ValueError(msg)
            graph.add_edge(
                stage_a, stage_b, key=transition.name, **{_TRANSITION_KEY: transition}
            )
        return cls(graph=graph)

    @model_validator(mode="after")
    def _validate_graph(self) -> Self:
        """Coerce node/edge payloads and enforce cross-cutting invariants."""
        graph = self.graph.copy()

        for node, data in graph.nodes(data=True):
            stage = _coerce(data.get(_STAGE_KEY), Stage)
            if stage.name != node:
                msg = f"Stage name {stage.name!r} does not match graph node {node!r}"
                raise ValueError(msg)
            data[_STAGE_KEY] = stage

        transition_names: set[str] = set()
        for u, v, key, data in graph.edges(keys=True, data=True):
            if u == v:
                msg = f"Transition {key!r} cannot connect stage {u!r} to itself"
                raise ValueError(msg)
            transition = _coerce(data.get(_TRANSITION_KEY), Transition)
            if transition.name != key:
                msg = (
                    f"Transition name {transition.name!r} "
                    f"does not match edge key {key!r}"
                )
                raise ValueError(msg)
            if transition.name in transition_names:
                msg = f"Duplicate transition name: {transition.name!r}"
                raise ValueError(msg)
            transition_names.add(transition.name)
            data[_TRANSITION_KEY] = transition

        self.graph = graph
        return self

    def stage(self, name: str) -> Stage:
        """Look up a stage by name."""
        try:
            return self.graph.nodes[name][_STAGE_KEY]
        except KeyError as exc:
            msg = f"No stage named {name!r}"
            raise KeyError(msg) from exc

    def stages(self) -> Iterator[Stage]:
        """Iterate over all stages in insertion order."""
        for _, data in self.graph.nodes(data=True):
            yield data[_STAGE_KEY]

    def stage_names(self) -> list[str]:
        """List the names of all stages, in insertion order."""
        return list(self.graph.nodes)

    def transition(self, name: str) -> Transition:
        """Look up a transition by name."""
        for _, _, data in self.graph.edges(data=True):
            transition = data[_TRANSITION_KEY]
            if transition.name == name:
                return transition
        msg = f"No transition named {name!r}"
        raise LookupError(msg)

    def transitions(self) -> Iterator[tuple[str, str, Transition]]:
        """Iterate over (stage_a, stage_b, transition) triples in insertion order."""
        for u, v, data in self.graph.edges(data=True):
            yield u, v, data[_TRANSITION_KEY]

    def transitions_at(self, name: str) -> Iterator[tuple[str, Transition]]:
        """Iterate over (neighbor stage, transition) pairs touching `name`."""
        for _, neighbor, data in self.graph.edges(name, data=True):
            yield neighbor, data[_TRANSITION_KEY]
