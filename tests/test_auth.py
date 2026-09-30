from datetime import timedelta

import pytest

from backend.app.core.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    validate_password_strength,
    verify_password,
)


@pytest.mark.asyncio
async def test_password_hashing_and_verification():
    raw_password = "SecurePassword@2026!"
    hashed = get_password_hash(raw_password)
    assert hashed != raw_password
    assert verify_password(raw_password, hashed) is True
    assert verify_password("WrongPassword@2026!", hashed) is False

@pytest.mark.asyncio
async def test_password_strength_validator():
    # Valid passwords
    valid, msg = validate_password_strength("StrongPass@123")
    assert valid is True
    assert msg == ""

    valid, msg = validate_password_strength("C0mplex#Secure!")
    assert valid is True
    assert msg == ""

    # Invalid: Too short (<10)
    valid, msg = validate_password_strength("Sh@1a")
    assert valid is False
    assert "at least 10 characters" in msg

    # Invalid: No uppercase
    valid, msg = validate_password_strength("lowercase@123")
    assert valid is False
    assert "uppercase" in msg

    # Invalid: No lowercase
    valid, msg = validate_password_strength("UPPERCASE@123")
    assert valid is False
    assert "lowercase" in msg

    # Invalid: No digit
    valid, msg = validate_password_strength("NoDigitsHere@!")
    assert valid is False
    assert "digit" in msg

    # Invalid: No special character
    valid, msg = validate_password_strength("NoSpecialChar123")
    assert valid is False
    assert "special character" in msg

@pytest.mark.asyncio
async def test_jwt_token_creation_and_verification():
    token = create_access_token(subject="testuser@secureexam.edu", role="STUDENT", expires_delta=timedelta(minutes=15))
    assert isinstance(token, str)
    assert len(token) > 20

    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded["sub"] == "testuser@secureexam.edu"
    assert decoded["role"] == "STUDENT"

@pytest.mark.asyncio
async def test_user_registration_success(client):
    reg_data = {
        "email": "newstudent@secureexam.edu",
        "full_name": "New Enrolled Student",
        "password": "SecurePassword@123",
        "role": "STUDENT"
    }
    resp = await client.post("/api/v1/auth/register", json=reg_data)
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "newstudent@secureexam.edu"
    assert data["role"] == "STUDENT"
    assert "id" in data
    assert "hashed_password" not in data

@pytest.mark.asyncio
async def test_user_registration_duplicate_email(client):
    # Already seeded in conftest
    reg_data = {
        "email": "student1@test.edu",
        "full_name": "Duplicate Student",
        "password": "SecurePassword@123",
        "role": "STUDENT"
    }
    resp = await client.post("/api/v1/auth/register", json=reg_data)
    assert resp.status_code == 400
    assert "already exists" in resp.json()["detail"].lower()

@pytest.mark.asyncio
async def test_user_login_success(client):
    login_data = {
        "email": "student1@test.edu",
        "password": "Student@123456"
    }
    resp = await client.post("/api/v1/auth/login", json=login_data)
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "student1@test.edu"
    assert data["user"]["role"] == "STUDENT"

@pytest.mark.asyncio
async def test_user_login_invalid_password(client):
    login_data = {
        "email": "student1@test.edu",
        "password": "WrongPassword@999"
    }
    resp = await client.post("/api/v1/auth/login", json=login_data)
    assert resp.status_code == 401
    # Check for generic authentication failure message
    assert "Invalid email or password" in resp.json()["detail"]

@pytest.mark.asyncio
async def test_user_login_nonexistent_user(client):
    login_data = {
        "email": "ghost@doesnotexist.edu",
        "password": "AnyPassword@123"
    }
    resp = await client.post("/api/v1/auth/login", json=login_data)
    assert resp.status_code == 401
    assert "Invalid email or password" in resp.json()["detail"]

@pytest.mark.asyncio
async def test_current_user_profile(client, student1_headers):
    resp = await client.get("/api/v1/auth/me", headers=student1_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "student1@test.edu"
    assert data["role"] == "STUDENT"
