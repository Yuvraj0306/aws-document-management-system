import json
import importlib
import os
import sys
from unittest.mock import Mock, patch

from werkzeug.security import generate_password_hash

# Add the project root to Python's import path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)


def load_app():
    secrets_client = Mock()
    secrets_client.get_secret_value.return_value = {
        "SecretString": json.dumps({
            "FLASK_SECRET_KEY": "test-secret-key",
            "USER_PASSWORD_HASH": generate_password_hash("test-password")
        })
    }

    s3_client = Mock()

    def fake_boto3_client(service_name, *args, **kwargs):
        if service_name == "secretsmanager":
            return secrets_client
        if service_name == "s3":
            return s3_client
        raise ValueError(f"Unexpected AWS service: {service_name}")

    sys.modules.pop("app", None)

    with patch("boto3.client", side_effect=fake_boto3_client):
        app_module = importlib.import_module("app")

    return app_module


def test_login_page_loads():
    app_module = load_app()
    client = app_module.app.test_client()

    response = client.get("/login")

    assert response.status_code == 200


def test_unauthenticated_user_is_redirected():
    app_module = load_app()
    client = app_module.app.test_client()

    response = client.get("/")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_unauthenticated_download_is_rejected():
    app_module = load_app()
    client = app_module.app.test_client()

    response = client.get("/download/test.txt")

    assert response.status_code == 401


def test_wrong_password_is_rejected():
    app_module = load_app()
    client = app_module.app.test_client()

    response = client.post(
        "/login",
        data={
            "username": "yuvraj",
            "password": "wrong-password"
        }
    )

    assert response.status_code == 401


def test_correct_login_succeeds():
    app_module = load_app()
    client = app_module.app.test_client()

    response = client.post(
        "/login",
        data={
            "username": "yuvraj",
            "password": "test-password"
        }
    )

    assert response.status_code == 302
    assert "/" in response.headers["Location"]


def test_logout_succeeds():
    app_module = load_app()
    client = app_module.app.test_client()

    client.post(
        "/login",
        data={
            "username": "yuvraj",
            "password": "test-password"
        }
    )

    response = client.get("/logout")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]