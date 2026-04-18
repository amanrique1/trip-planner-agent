import pytest
from fastapi.testclient import TestClient
from api.app import application

def pytest_collection_modifyitems(items):
    """Automatically adds the 'L1' marker to all tests collected in this directory."""
    for item in items:
        if "/L1_components/" in str(item.fspath):
            item.add_marker(pytest.mark.L1)


@pytest.fixture(scope="module")
def client():
    """Provides a TestClient instance for the FastAPI application."""
    with TestClient(application) as c:
        yield c

@pytest.fixture(scope="module")
def valid_auth_headers(client):
    """Provides a valid authorization header by authenticating with default admin credentials."""
    response = client.post("/auth/token", auth=("admin", "admin_pass"))
    assert response.status_code == 200, "Failed to get auth token for fixture"
    token = response.json()["access_token"]
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
