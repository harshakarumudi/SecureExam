import pytest


@pytest.mark.asyncio
async def test_unauthenticated_requests_blocked(client):
    endpoints = [
        ("GET", "/api/v1/auth/me"),
        ("GET", "/api/v1/users/"),
        ("POST", "/api/v1/exams/"),
        ("GET", "/api/v1/audit/"),
    ]
    for method, path in endpoints:
        if method == "GET":
            resp = await client.get(path)
        else:
            resp = await client.post(path, json={})
        assert resp.status_code == 401, f"Expected 401 for {method} {path}, got {resp.status_code}"

@pytest.mark.asyncio
async def test_student_blocked_from_faculty_exam_creation(client, student1_headers):
    payload = {
        "title": "Unauthorized Exam by Student",
        "description": "Should fail with 403",
        "duration_minutes": 30,
        "total_marks": 100.0,
        "pass_marks": 40.0
    }
    resp = await client.post("/api/v1/exams/", json=payload, headers=student1_headers)
    assert resp.status_code == 403
    assert "forbidden" in resp.json()["detail"].lower()

@pytest.mark.asyncio
async def test_student_blocked_from_admin_audit_logs(client, student1_headers):
    resp = await client.get("/api/v1/audit/", headers=student1_headers)
    assert resp.status_code == 403

@pytest.mark.asyncio
async def test_student_blocked_from_admin_user_directory(client, student1_headers):
    resp = await client.get("/api/v1/users/", headers=student1_headers)
    assert resp.status_code == 403

@pytest.mark.asyncio
async def test_faculty_blocked_from_admin_audit_logs(client, faculty1_headers):
    resp = await client.get("/api/v1/audit/", headers=faculty1_headers)
    assert resp.status_code == 403

@pytest.mark.asyncio
async def test_cross_faculty_tampering_blocked(client, faculty1_headers, faculty2_headers):
    # 1. Faculty 1 creates an exam
    create_payload = {
        "title": "Faculty One Private Exam",
        "description": "Exclusive exam",
        "duration_minutes": 45,
        "total_marks": 50.0,
        "pass_marks": 25.0
    }
    create_resp = await client.post("/api/v1/exams/", json=create_payload, headers=faculty1_headers)
    assert create_resp.status_code == 201
    exam_id = create_resp.json()["id"]

    # 2. Faculty 2 attempts to modify Faculty 1's exam
    update_payload = {
        "title": "Tampered Exam Title",
        "description": "Malicious modification"
    }
    update_resp = await client.put(f"/api/v1/exams/{exam_id}", json=update_payload, headers=faculty2_headers)
    assert update_resp.status_code == 403
    assert "not authorized" in update_resp.json()["detail"].lower()

    # 3. Faculty 2 attempts to add question to Faculty 1's exam
    question_payload = {
        "question_text": "Injected question?",
        "marks": 5.0,
        "options": [
            {"option_text": "Opt A", "is_correct": True},
            {"option_text": "Opt B", "is_correct": False}
        ]
    }
    q_resp = await client.post(f"/api/v1/exams/{exam_id}/questions", json=question_payload, headers=faculty2_headers)
    assert q_resp.status_code == 403

@pytest.mark.asyncio
async def test_admin_access_allowed(client, admin_headers):
    audit_resp = await client.get("/api/v1/audit/", headers=admin_headers)
    assert audit_resp.status_code == 200

    users_resp = await client.get("/api/v1/users/", headers=admin_headers)
    assert users_resp.status_code == 200
    assert len(users_resp.json()) >= 5
