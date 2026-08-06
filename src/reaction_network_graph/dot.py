"""Graphviz DOT/SVG export for reaction networks, via pydot."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pydot

if TYPE_CHECKING:
    from .models import Species, Stage, Step
    from .network import ReactionNetwork

_STAGE_COLOR = "#df8bbb"
_STEP_COLOR = "#8da0cb"
_SPECIES_COLOR = "#fc8d62"
_STEP_EDGE_ATTRS = {"color": _STEP_COLOR, "penwidth": "3"}
_SPECIES_EDGE_ATTRS = {"color": "black", "penwidth": "1"}


def to_dot(
    network: ReactionNetwork,
    *,
    graph_name: str = "reaction_network",
    layout: str = "neato",
) -> str:
    """Render a reaction network as Graphviz DOT text.

    Stages are pink circles, steps are blue squares sitting between the two
    stages they connect, and each stage's species are drawn as small orange
    satellite nodes - matching the OntoRXN-style rendering this package
    targets.

    Examples
    --------
    >>> from reaction_network_graph.models import Species, Stage
    >>> from reaction_network_graph.network import ReactionNetwork
    >>> a = Stage(name="A", species=[Species(name="A")])
    >>> network = ReactionNetwork.build([a], [])
    >>> print(to_dot(network, graph_name="example"))
    graph example {
    layout=neato;
    overlap=false;
    splines=true;
    node [fontname=Helvetica];
    "A" [label=A, shape=circle, style=filled, fillcolor="#df8bbb"];
    "A__species0" [label=A, shape=circle, style=filled, fillcolor="#fc8d62"];
    "A" -- "A__species0" [color=black, penwidth=1];
    }
    <BLANKLINE>
    """
    return _build_graph(network, graph_name=graph_name, layout=layout).to_string()


def write_dot(
    network: ReactionNetwork,
    path: str | Path,
    *,
    graph_name: str = "reaction_network",
    layout: str = "neato",
) -> None:
    """Render a reaction network as DOT text and write it to `path`.

    Examples
    --------
    >>> import tempfile
    >>> from reaction_network_graph.models import Species, Stage
    >>> from reaction_network_graph.network import ReactionNetwork
    >>> a = Stage(name="A", species=[Species(name="A")])
    >>> network = ReactionNetwork.build([a], [])
    >>> with tempfile.TemporaryDirectory() as tmp:
    ...     out = Path(tmp) / "network.dot"
    ...     write_dot(network, out)
    ...     out.read_text().splitlines()[0]
    'graph reaction_network {'
    """
    Path(path).write_text(to_dot(network, graph_name=graph_name, layout=layout))


def write_svg(
    network: ReactionNetwork,
    path: str | Path,
    *,
    graph_name: str = "reaction_network",
    layout: str = "neato",
) -> None:
    """Render a reaction network directly to an SVG file via Graphviz `dot`.

    Requires the Graphviz `dot` command to be available on PATH (raises
    `FileNotFoundError` if it isn't).

    Examples
    --------
    >>> import tempfile
    >>> from reaction_network_graph.models import Species, Stage
    >>> from reaction_network_graph.network import ReactionNetwork
    >>> a = Stage(name="A", species=[Species(name="A")])
    >>> network = ReactionNetwork.build([a], [])
    >>> with tempfile.TemporaryDirectory() as tmp:
    ...     out = Path(tmp) / "network.svg"
    ...     write_svg(network, out)
    ...     out.read_text().startswith("<?xml")
    True
    """
    _build_graph(network, graph_name=graph_name, layout=layout).write(
        str(path), format="svg"
    )


def _node(name: str, attrs: dict[str, str]) -> pydot.Node:
    """Build a pydot Node, applying `attrs` via `.set()` (not `**attrs`).

    pydot's `Node.__init__` has a same-named `obj_dict` parameter ahead of
    its `**attrs` catch-all, so a type checker can't rule out one of our
    `dict[str, str]` attribute keys colliding with it if unpacked with `**`
    - applying attributes one at a time via `.set()` sidesteps that.
    """
    node = pydot.Node(name)
    for key, value in attrs.items():
        node.set(key, value)
    return node


def _edge(src: str, dst: str, attrs: dict[str, str]) -> pydot.Edge:
    """Build a pydot Edge, applying `attrs` via `.set()` (see `_node`)."""
    edge = pydot.Edge(src, dst)
    for key, value in attrs.items():
        edge.set(key, value)
    return edge


def _build_graph(
    network: ReactionNetwork, *, graph_name: str, layout: str
) -> pydot.Dot:
    """Build a pydot graph for a reaction network's stages, steps, and species."""
    graph = pydot.Dot(
        graph_name, graph_type="graph", layout=layout, overlap="false", splines="true"
    )
    graph.set_node_defaults(fontname="Helvetica")
    for stage in network.stages():
        graph.add_node(_node(_quote_id(stage.name), _stage_attrs(stage)))
        for index, species in enumerate(stage.species):
            species_id = _species_node_id(stage.name, index)
            graph.add_node(_node(_quote_id(species_id), _species_attrs(species)))
            graph.add_edge(
                _edge(_quote_id(stage.name), _quote_id(species_id), _SPECIES_EDGE_ATTRS)
            )
    for stage_a, stage_b, step in network.steps():
        graph.add_node(_node(_quote_id(step.name), _step_attrs(step)))
        graph.add_edge(
            _edge(_quote_id(stage_a), _quote_id(step.name), _STEP_EDGE_ATTRS)
        )
        graph.add_edge(
            _edge(_quote_id(step.name), _quote_id(stage_b), _STEP_EDGE_ATTRS)
        )
    return graph


def _quote_id(value: str) -> str:
    """Quote and escape a value for safe use as a DOT node/edge identifier.

    pydot reliably quotes/escapes Node and Edge *attribute values* itself,
    but not node/edge *identifiers* (e.g. an embedded `"` in a bare
    identifier is passed through unescaped, and an unquoted `::` is
    misparsed as DOT port syntax) - so identifiers are quoted explicitly
    here before being handed to pydot.
    """
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _species_node_id(stage_name: str, index: int) -> str:
    """Synthesize a unique identifier for a stage's species satellite node."""
    return f"{stage_name}__species{index}"


def _stage_attrs(stage: Stage) -> dict[str, str]:
    """Derive Graphviz node attributes for a stage."""
    label = stage.label or stage.name
    if stage.energy is not None:
        label = f"{label}\n({stage.energy:.1f})"
    return {
        "label": label,
        "shape": "circle",
        "style": "filled",
        "fillcolor": _STAGE_COLOR,
    }


def _step_attrs(step: Step) -> dict[str, str]:
    """Derive Graphviz node attributes for a step."""
    label = step.label or step.name
    if step.energy is not None:
        label = f"{label}\n({step.energy:.1f})"
    return {
        "label": label,
        "shape": "square",
        "style": "filled",
        "fillcolor": _STEP_COLOR,
    }


def _species_attrs(species: Species) -> dict[str, str]:
    """Derive Graphviz node attributes for a species satellite node."""
    return {
        "label": species.name,
        "shape": "circle",
        "style": "filled",
        "fillcolor": _SPECIES_COLOR,
    }
