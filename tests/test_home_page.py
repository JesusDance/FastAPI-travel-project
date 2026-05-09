def test_home_page(test_client):
    response = test_client.get("/")
    json_response = response.json()

    assert response.status_code == 200
    assert "message" in json_response
    assert json_response["message"] == "Hello from backend!"