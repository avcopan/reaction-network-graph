"""The ``ReactionNetwork`` data structure: stages connected by steps."""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

import networkx as nx
from pydantic import BaseModel, ConfigDict, model_validator

from .models import Stage, Step

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence

_STAGE_KEY = "stage"
_STEP_KEY = "step"


def _coerce[T: BaseModel](value: object, model: type[T]) -> T:
    """Coerce a raw dict or an existing model instance to `model`."""
    if isinstance(value, model):
        return value
    if isinstance(value, dict):
        return model.model_validate(value)
    msg = f"Expected {model.__name__} or dict, got {type(value).__name__}"
    raise TypeError(msg)


class ReactionNetwork[StageT: Stage, StepT: Step](BaseModel):
    """A reaction network: stages (nodes) connected by steps (edges).

    The underlying `networkx.MultiGraph` only ever stores generic nodes and
    edges; the `Stage`/`Step` payloads are validated on construction and
    whenever the model is (re)built.

    Examples
    --------
    >>> from reaction_network_graph.models import Species
    >>> a = Stage(name="A", species=[Species(name="A")])
    >>> bc = Stage(name="B+C", species=[Species(name="B"), Species(name="C")])
    >>> ts = Step(name="TS1")
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
        steps: Sequence[tuple[str, str, StepT]],
    ) -> Self:
        """Build a network from stages and (stage_a, stage_b, step) triples."""
        graph = nx.MultiGraph()
        for stage in stages:
            if stage.name in graph:
                msg = f"Duplicate stage name: {stage.name!r}"
                raise ValueError(msg)
            graph.add_node(stage.name, **{_STAGE_KEY: stage})
        for stage_a, stage_b, step in steps:
            for endpoint in (stage_a, stage_b):
                if endpoint not in graph:
                    msg = f"Step {step.name!r} references unknown stage {endpoint!r}"
                    raise ValueError(msg)
            graph.add_edge(stage_a, stage_b, key=step.name, **{_STEP_KEY: step})
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

        step_names: set[str] = set()
        for u, v, key, data in graph.edges(keys=True, data=True):
            if u == v:
                msg = f"Step {key!r} cannot connect stage {u!r} to itself"
                raise ValueError(msg)
            step = _coerce(data.get(_STEP_KEY), Step)
            if step.name != key:
                msg = f"Step name {step.name!r} does not match edge key {key!r}"
                raise ValueError(msg)
            if step.name in step_names:
                msg = f"Duplicate step name: {step.name!r}"
                raise ValueError(msg)
            step_names.add(step.name)
            data[_STEP_KEY] = step

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

    def step(self, name: str) -> Step:
        """Look up a step by name."""
        for _, _, data in self.graph.edges(data=True):
            step = data[_STEP_KEY]
            if step.name == name:
                return step
        msg = f"No step named {name!r}"
        raise LookupError(msg)

    def steps(self) -> Iterator[tuple[str, str, Step]]:
        """Iterate over (stage_a, stage_b, step) triples in insertion order."""
        for u, v, data in self.graph.edges(data=True):
            yield u, v, data[_STEP_KEY]

    def steps_at(self, name: str) -> Iterator[tuple[str, Step]]:
        """Iterate over (neighbor stage, step) pairs touching `name`."""
        for _, neighbor, data in self.graph.edges(name, data=True):
            yield neighbor, data[_STEP_KEY]
