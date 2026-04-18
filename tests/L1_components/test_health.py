def test_get_health_check_success(client):
    response = client.get("/health")
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"

    json_response = response.json()
    assert isinstance(json_response, dict), "Response should be a JSON object"
    assert "status" in json_response, "Key 'status' missing in response"
    assert json_response["status"] == "ok", f"Expected status 'ok', got {json_response['status']}"
