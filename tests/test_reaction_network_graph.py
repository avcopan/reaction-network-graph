"""reaction-network-graph tests."""

import reaction_network_graph


def test__version() -> None:
    """The package should expose a version string."""
    assert isinstance(reaction_network_graph.__version__, str)


def test__public_api_is_importable() -> None:
    """Every name in __all__ should be importable from the top-level package."""
    for name in reaction_network_graph.__all__:
        assert hasattr(reaction_network_graph, name)
