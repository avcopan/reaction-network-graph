"""Pydantic data models for species, stages, and transitions."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class _EnergyLevel(BaseModel):
    """Fields shared by stages and transitions.

    Both a `Stage` (a well or bimolecular channel) and a `Transition` (a
    transition state) are described by the same kind of energetic data, as
    they are in master-equation solver inputs.
    """

    model_config = ConfigDict(frozen=True)

    name: str
    label: str | None = None
    energy: float | None = None


class Species(BaseModel):
    """A single chemical species.

    Examples
    --------
    >>> species = Species(name="CH3", formula="CH3", multiplicity=2)
    >>> species.name
    'CH3'
    """

    model_config = ConfigDict(frozen=True)

    name: str
    formula: str | None = None
    charge: int = 0
    multiplicity: int | None = None
    smiles: str | None = None


class Stage(_EnergyLevel):
    """A network node: a well (unimolecular) or bimolecular/termolecular channel.

    Examples
    --------
    >>> stage = Stage(name="A", species=[Species(name="A")])
    >>> stage.is_unimolecular
    True
    >>> stage = Stage(name="B+C", species=[Species(name="B"), Species(name="C")])
    >>> stage.is_unimolecular
    False
    """

    species: tuple[Species, ...] = Field(min_length=1)

    @property
    def is_unimolecular(self) -> bool:
        """Whether this stage is a single-species well."""
        return len(self.species) == 1


class Transition(_EnergyLevel):
    """A network edge: the transition state connecting two stages.

    Which two stages a transition connects is determined entirely by its
    position in a `ReactionNetwork`'s graph, not by any field on this model
    - so the same `Transition` payload can be freely rewired to a different
    pair of stages without needing to be reconstructed.

    Examples
    --------
    >>> transition = Transition(name="TS1", energy=12.0)
    >>> transition.name
    'TS1'
    """
