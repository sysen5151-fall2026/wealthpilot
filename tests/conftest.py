"""Shared fixtures. Every test uses synthetic prices in a temporary folder, never data/prices/."""

import copy

import pytest
from synthetic_market import write_synthetic_snapshot

from investor_interface.console import SAMPLE_INVESTOR
from system_administration import load_configuration


def pytest_addoption(parser):
    parser.addoption("--run-pending-acceptance", action="store_true", default=False,
                     help="Legacy compatibility option; coursework checks now run by default.")


@pytest.fixture(scope="session")
def snapshot_directory(tmp_path_factory):
    directory = tmp_path_factory.mktemp("synthetic_prices")
    write_synthetic_snapshot(directory)
    return directory


@pytest.fixture(scope="session")
def configuration():
    return load_configuration()


@pytest.fixture
def investor():
    """The console's sample investor, as a fresh copy each test can change."""
    return copy.deepcopy(SAMPLE_INVESTOR)
