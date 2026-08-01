import pytest

from tests.server.conftest import TEST_PASSWORD, TEST_USERNAME


def test_visitors_can_view_results_without_signing_in(anonymous_client):
    status = anonymous_client.get("/auth/status")
    weeks = anonymous_client.get("/artifacts/weeks")
    models = anonymous_client.get("/config/models")

    assert status.status_code == 200
    assert status.get_json() == {
        "authenticated": False,
        "configured": True,
        "username": None,
    }
    assert weeks.status_code == 200
    assert models.status_code == 200


@pytest.mark.parametrize(
    ("path", "body"),
    [
        ("/stages/almanac", {}),
        ("/stages/technical", {}),
        ("/stages/macro", {}),
        ("/stages/evidence", {}),
        ("/stages/delta", {}),
        ("/stages/llm", {}),
        ("/stages/human", {}),
        ("/artifacts/human-score", {}),
        ("/artifacts/final-prediction", {}),
        ("/export", {}),
    ],
)
def test_visitors_cannot_change_data(anonymous_client, path, body):
    response = anonymous_client.post(path, json=body)

    assert response.status_code == 401
    assert response.get_json()["error"] == "Authentication required."


def test_admin_can_sign_in_and_sign_out(anonymous_client):
    wrong = anonymous_client.post(
        "/auth/login",
        json={"username": TEST_USERNAME, "password": "wrong"},
    )
    assert wrong.status_code == 401

    logged_in = anonymous_client.post(
        "/auth/login",
        json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
    )
    assert logged_in.status_code == 200

    status = anonymous_client.get("/auth/status")
    assert status.get_json() == {
        "authenticated": True,
        "configured": True,
        "username": TEST_USERNAME,
    }

    protected = anonymous_client.post("/stages/almanac", json={})
    assert protected.status_code == 400

    logged_out = anonymous_client.post("/auth/logout")
    assert logged_out.status_code == 200
    protected_again = anonymous_client.post("/stages/almanac", json={})
    assert protected_again.status_code == 401


def test_write_routes_fail_closed_without_auth_configuration(app):
    app.config.update(
        SECRET_KEY=None,
        AUTH_USERNAME=None,
        AUTH_PASSWORD=None,
    )
    with app.test_client() as client:
        login = client.post(
            "/auth/login",
            json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
        )
        write = client.post("/export", json={})

    assert login.status_code == 503
    assert write.status_code == 503
