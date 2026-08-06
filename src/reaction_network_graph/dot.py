"""Graphviz DOT export for reaction networks."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import Stage, Transition
    from .network import ReactionNetwork


def to_dot(network: ReactionNetwork, *, graph_name: str = "reaction_network") -> str:
    """Render a reaction network as undirected Graphviz DOT text.

    Examples
    --------
    >>> from reaction_network_graph.models import Species, Stage, Transition
    >>> from reaction_network_graph.network import ReactionNetwork
    >>> a = Stage(name="A", species=[Species(name="A")])
    >>> bc = Stage(name="B+C", species=[Species(name="B"), Species(name="C")])
    >>> ts = Transition(name="TS1")
    >>> network = ReactionNetwork.build([a, bc], [("A", "B+C", ts)])
    >>> print(to_dot(network, graph_name="example"))
    graph "example" {
        node [fontname="Helvetica"];
        edge [fontname="Helvetica"];
    <BLANKLINE>
        "A" [label="A", shape=box, style=filled, fillcolor=lightgrey];
        "B+C" [label="B + C", shape=ellipse];
    <BLANKLINE>
        "A" -- "B+C" [id="TS1", label="TS1"];
    }
    """
    lines = [
        f'graph "{_escape(graph_name)}" {{',
        '    node [fontname="Helvetica"];',
        '    edge [fontname="Helvetica"];',
        "",
    ]
    lines.extend(
        f"    {_quote(stage.name)} [{_format_attrs(_stage_attrs(stage))}];"
        for stage in network.stages()
    )
    lines.append("")
    lines.extend(
        f"    {_quote(stage_a)} -- {_quote(stage_b)} "
        f"[{_format_attrs(_transition_attrs(transition))}];"
        for stage_a, stage_b, transition in network.transitions()
    )
    lines.append("}")
    return "\n".join(lines)


def write_dot(
    network: ReactionNetwork,
    path: str | Path,
    *,
    graph_name: str = "reaction_network",
) -> None:
    """Render a reaction network as DOT text and write it to `path`.

    Examples
    --------
    >>> import tempfile
    >>> from reaction_network_graph.models import Species, Stage, Transition
    >>> from reaction_network_graph.network import ReactionNetwork
    >>> a = Stage(name="A", species=[Species(name="A")])
    >>> b = Stage(name="B", species=[Species(name="B")])
    >>> ts = Transition(name="TS1")
    >>> network = ReactionNetwork.build([a, b], [("A", "B", ts)])
    >>> with tempfile.TemporaryDirectory() as tmp:
    ...     out = Path(tmp) / "network.dot"
    ...     write_dot(network, out)
    ...     out.read_text().splitlines()[0]
    'graph "reaction_network" {'
    """
    Path(path).write_text(to_dot(network, graph_name=graph_name) + "\n")


def _escape(value: str) -> str:
    """Escape backslashes and double quotes for a DOT quoted string."""
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _quote(value: str) -> str:
    """Wrap a value in double quotes, escaping as needed for DOT."""
    return f'"{_escape(value)}"'


def _stage_attrs(stage: Stage) -> dict[str, str]:
    """Derive Graphviz node attributes from a stage."""
    label = stage.label or " + ".join(species.name for species in stage.species)
    if stage.energy is not None:
        label = f"{label}\n({stage.energy:.1f})"
    shape = "box" if stage.is_unimolecular else "ellipse"
    attrs = {"label": _quote(label), "shape": shape}
    if stage.is_unimolecular:
        attrs["style"] = "filled"
        attrs["fillcolor"] = "lightgrey"
    return attrs


def _transition_attrs(transition: Transition) -> dict[str, str]:
    """Derive Graphviz edge attributes from a transition."""
    label = transition.label or transition.name
    if transition.energy is not None:
        label = f"{label}\n({transition.energy:.1f})"
    return {"id": _quote(transition.name), "label": _quote(label)}


def _format_attrs(attrs: dict[str, str]) -> str:
    """Format a Graphviz attribute mapping as ``key=value, ...``."""
    return ", ".join(f"{key}={value}" for key, value in attrs.items())
