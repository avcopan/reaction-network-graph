"""reaction-network-graph tests."""

import reaction_network_graph


def test_stub() -> None:
    """Stub test to ensure the test suite runs."""
    print(reaction_network_graph.__version__)  # noqa: T201


def test__greet() -> None:
    """Test the greet function."""
    assert reaction_network_graph.greet("World") == "Hello, World!"


def test__greet_jim() -> None:
    """Test the greet_jim function."""
    assert reaction_network_graph.greet_jim() == "Hello, Jim!"
