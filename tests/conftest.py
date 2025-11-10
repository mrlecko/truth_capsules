# conftest.py
import pytest

def pytest_addoption(parser):
    parser.addoption(
        "--all-green",
        action="store_true",
        default=False,
        help="Run with good artifacts so RED-path witnesses pass.",
    )

@pytest.fixture(scope="session")
def all_green(request):
    return request.config.getoption("--all-green")
