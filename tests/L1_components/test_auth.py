def test_post_auth_token_with_valid_credentials(client):
    response = client.post("/auth/token", auth=("admin", "admin_pass"))
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    json_data = response.json()
    assert "access_token" in json_data
    assert "token_type" in json_data
    assert "expires_in_minutes" in json_data

    assert isinstance(json_data["access_token"], str) and len(json_data["access_token"]) > 0
    assert json_data["token_type"].lower() == "bearer"
    assert json_data["expires_in_minutes"] == 60


def test_post_auth_token_with_invalid_credentials(client):
    response = client.post("/auth/token", auth=("admin123", "admin_pass123"))
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"

    json_resp = response.json()
    error_detail = json_resp.get("detail") or json_resp.get("error") or json_resp.get("message")
    assert error_detail is not None, "Error detail message not found in response"
    assert "invalid" in error_detail.lower()


def test_post_auth_token_missing_authorization_header(client):
    response = client.post("/auth/token")
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"

    json_response = response.json()
    assert isinstance(json_response, dict)
    detail = json_response.get("detail") or json_response.get("error") or json_response.get("message")
    assert detail is not None
