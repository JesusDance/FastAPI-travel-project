def test_user_registration(test_client):
    response = test_client.post(
        "/register",
        json={
            "username": "Bob2",
            "password": "12345678",
            "email": "bob1234@gmail.com"
        }
    )
    json_response = response.json()

    assert response.status_code == 201
    assert "id" in json_response
    assert "username" in json_response
    assert "password" not in json_response
    assert "email" in json_response


def test_user_valid_registration(test_client):
    response = test_client.post(
        "/register",
        json={
            "username": "Steve2",
            "password": "12345678",
            "email": "steve1234@gmail.com"
        }
    )
    json_response = response.json()

    assert response.status_code == 201
    assert json_response["username"] == "Steve2"
    assert "password" not in json_response
    assert json_response["email"] == "steve1234@gmail.com"
    assert json_response["projects"] == []


def test_user_invalid_registration(test_client):
    response = test_client.post(
        "/register",
        json={
            "username": "Bo",
            "password": "1234567",
            "email": "bob1234gmail.com"
        }
    )
    assert response.status_code == 422


def test_duplicate_user(test_client):
    response = test_client.post(
        "/register",
        json={
            "username": "Bob",
            "password": "12345678",
            "email": "bob123@gmail.com"
        }
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "User already exists"


def test_user_login(test_client):
    response = test_client.post(
        "/register/login",
        json={
            "username": "Bob",
            "password": "12345678",
            "email": "bob123@gmail.com"
        }
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_user_invalid_login(test_client):
    response = test_client.post(
        "/register/login",
        json={
            "username": "Bob",
            "password": "22345678",
            "email": "bob123@gmail.com"
        }
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"