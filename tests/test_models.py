"""Tests for reaction_network_graph.models."""

import pytest
from pydantic import ValidationError

from reaction_network_graph.models import Species, Stage, Transition


def test__species_defaults() -> None:
    """Species should default optional fields to None/0."""
    species = Species(name="A")
    assert species.formula is None
    assert species.charge == 0
    assert species.multiplicity is None
    assert species.smiles is None


def test__species_is_frozen_and_hashable() -> None:
    """Species instances should be frozen and hashable, with value equality."""
    species = Species(name="A")
    with pytest.raises(ValidationError):
        species.name = "B"  # ty: ignore[invalid-assignment]
    assert hash(species) == hash(Species(name="A"))
    assert species == Species(name="A")


def test__stage_is_unimolecular() -> None:
    """A stage with one species should be unimolecular."""
    stage = Stage(name="A", species=[Species(name="A")])
    assert stage.is_unimolecular


def test__stage_is_not_unimolecular_when_bimolecular() -> None:
    """A stage with two or more species should not be unimolecular."""
    stage = Stage(name="B+C", species=[Species(name="B"), Species(name="C")])
    assert not stage.is_unimolecular


def test__stage_rejects_empty_species() -> None:
    """Stage construction should fail with an empty species list."""
    with pytest.raises(ValidationError):
        Stage(name="A", species=[])


def test__stage_allows_duplicate_species() -> None:
    """Stage construction should allow repeated species, e.g. `2 CH3`."""
    stage = Stage(name="2A", species=[Species(name="A"), Species(name="A")])
    assert stage.species == (Species(name="A"), Species(name="A"))


def test__stage_is_frozen_and_hashable() -> None:
    """Stage instances should be frozen and hashable, with value equality."""
    stage = Stage(name="A", species=[Species(name="A")])
    with pytest.raises(ValidationError):
        stage.energy = 1.0  # ty: ignore[invalid-assignment]
    assert hash(stage) == hash(Stage(name="A", species=[Species(name="A")]))
    assert stage == Stage(name="A", species=[Species(name="A")])


def test__transition_is_frozen_and_hashable() -> None:
    """Transition instances should be frozen and hashable, with value equality."""
    transition = Transition(name="TS1")
    with pytest.raises(ValidationError):
        transition.energy = 1.0  # ty: ignore[invalid-assignment]
    assert hash(transition) == hash(Transition(name="TS1"))
    assert transition == Transition(name="TS1")
