def test_create_project(test_client, default_user_token):
    response = test_client.post(
        "/projects",
        headers={"Authorization": "Bearer " + default_user_token},
        json={
            "name": "USA",
            "description": "Visit USA in summer",
            "is_completed": False
        }
    )
    json_response = response.json()
    assert response.status_code == 201
    assert "name" in json_response
    assert "description" in json_response
    assert json_response["is_completed"] == False


def test_create_valid_project(test_client, default_user_token):
    response = test_client.post(
        "/projects",
        headers={"Authorization": "Bearer " + default_user_token},
        json={
            "name": "Europe",
            "description": "Visit europe in summer",
            "is_completed": False
        }
    )
    json_response = response.json()

    assert response.status_code == 201
    assert json_response["name"] == "Europe"
    assert json_response["description"] == "Visit europe in summer"


def test_create_invalid_project(test_client, default_user_token):
    response = test_client.post(
        "/projects",
        headers={"Authorization": "Bearer " + default_user_token},
        json={
            "name": "US",
            "start_date": "test"
        }
    )
    json_response = response.json()
    errors = json_response["detail"]

    assert response.status_code == 422
    assert json_response["detail"][0]["loc"] == ["body", "name"]
    assert json_response["detail"][1]["loc"] == ["body", "start_date"]
    assert any(error["loc"] for error in errors)


def test_get_lists_of_projects(test_client, default_user_token):
    response = test_client.get(
        "/projects",
        headers={"Authorization": "Bearer " + default_user_token}
    )
    assert response.status_code == 200


def test_get_no_project(test_client, default_user_token):
    response = test_client.get(
        "/projects/5",
        headers={"Authorization": "Bearer " + default_user_token}
    )
    assert response.status_code == 404


def test_no_access_to_projects(test_client,second_user_token):
    response = test_client.get(
        "/projects/1",
        headers={"Authorization": "Bearer " + second_user_token}
    )
    assert response.status_code == 404


def test_no_token(test_client, default_user_token):
    response = test_client.get(
        "/projects/1"
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_invalid_token(test_client, second_user_token):
    response = test_client.get(
        "/projects/1",
        headers={"Authorization": "Bearer " + "eyJhbGciOiJIUzI1NiIsInR5cCI6Ikp"
                                              "XVCJ9.eyJzdWIiOiIxIiwiZXhwIjoxNz"
                                              "c4Mzk5NTIxfQ.RdsOAZuppT8ZazDDOD4"
                                              "kOuEX_YAnF4YOqavnPMkYAn"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Couldn't validate credentials"


def test_update_project(test_client, default_user_token):
    response = test_client.patch(
        "/projects/1",
        headers={"Authorization": "Bearer " + default_user_token},
        json={
            "name": "USA2",
            "description": "USA is a shit"
        }
    )
    assert response.status_code == 200
    assert response.json()["name"] == "USA2"
    assert response.json()["description"] == "USA is a shit"


def test_update_no_project(test_client, default_user_token):
    response = test_client.patch(
        "/projects/2",
        headers={"Authorization": "Bearer " + default_user_token},
        json={
            "name": "USA2",
        }
    )
    assert response.status_code == 404


def test_update_invalid_token(test_client, second_user_token):
    response = test_client.patch(
        "/projects/2",
        headers={"Authorization": "Bearer " + "eyJhbGciOiJIUzI1NiIsInR5cCI6Ikp"
                                              "XVCJ9.eyJzdWIiOiIxIiwiZXhwIjoxNz"
                                              "c4Mzk5NTIxfQ.RdsOAZuppT8ZazDDOD4"
                                              "kOuEX_YAnF4YOqavnPMkYAn"},
        json={
            "name": "USA2",
        }
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Couldn't validate credentials"


def test_update_no_token(test_client, second_user_token):
    response = test_client.patch(
        "/projects/2"
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_full_flow(test_client, default_user_token):
    response = test_client.post(
        "/projects",
        headers={"Authorization": f"Bearer {default_user_token}"},
        json={
            "name": "Germany trip",
            "description": "Visit after war",
            "start_date": "2027-06-01"
        }
    )
    assert response.status_code == 201
    created_project_id = response.json()["id"]

    response_get = test_client.get(
        f"/projects/{created_project_id}",
        headers={"Authorization": f"Bearer {default_user_token}"}
    )
    assert response_get.status_code == 200

    response_get_list = test_client.get(
        "/projects",
        headers={"Authorization": f"Bearer {default_user_token}"}
    )
    assert response_get_list.status_code == 200

    response_patch = test_client.patch(
        f"/projects/{created_project_id}",
        headers={"Authorization": f"Bearer {default_user_token}"},
        json={"name": "Berlin"}
    )
    assert response_patch.status_code == 200

    response_place = test_client.post(
        f"/projects/{created_project_id}/places",
        headers={"Authorization": f"Bearer {default_user_token}"},
        json={
            "external_id": 23685
        }
    )
    response_place_id = response_place.json()["id"]
    json_response_place = response_place.json()

    assert response_place.status_code == 201
    assert json_response_place["title"] == "Ecce Homo"
    assert json_response_place["is_visited"] == False

    response_get_place = test_client.get(
        f"/projects/{created_project_id}/places/{response_place_id}",
        headers={"Authorization": f"Bearer {default_user_token}"}
    )
    assert response_get_place.status_code == 200

    response_patch_place = test_client.patch(
        f"/projects/{created_project_id}/places/{response_place_id}",
        headers={"Authorization": f"Bearer {default_user_token}"},
        json={
            "notes": "This trip was an excellent",
            "is_visited": True
        }
    )
    json_response_patched = response_patch_place.json()
    assert response_patch_place.status_code == 200
    assert json_response_patched["notes"] == "This trip was an excellent"
    assert json_response_patched["is_visited"] == True

    response_project_done = test_client.get(
        f"/projects/{created_project_id}",
        headers={"Authorization": f"Bearer {default_user_token}"}
    )
    json_response_done = response_project_done.json()
    assert response_project_done.status_code == 200
    assert json_response_done["is_completed"] == True

    response_delete = test_client.delete(
        f"/projects/{created_project_id}",
        headers={"Authorization": f"Bearer {default_user_token}"}
    )
    assert response_delete.status_code == 400
    assert response_delete.json()["detail"] == "Cannot delete project with visited places"

    response_delete_unvisited = test_client.delete(
        f"/projects/1",
        headers={"Authorization": f"Bearer {default_user_token}"}
    )
    assert response_delete_unvisited.status_code == 200
    assert response_delete_unvisited.json()["detail"] == "Project deleted"
