import pytest

from homedant_linkedin.catalog import Catalog


@pytest.fixture
def catalog() -> Catalog:
    return Catalog.load()
