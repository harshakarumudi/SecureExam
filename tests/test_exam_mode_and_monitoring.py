from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient

from backend.app.models.attempt import ExamAttempt
from tests.conftest import TestSessionLocal


@pytest.mark.asyncio
async def test_exam_monitoring_violations_and_termination(
    client: AsyncClient,
    faculty1_headers: dict[str, str],
    student1_headers: dict[str, str],
    student2_headers: dict[str, str]
):
    # 1. Faculty creates and publishes an exam
    exam_payload = {
        "title": "Security & Architecture Midterm",
        "description": "High-stakes proctored test with strict tab-switch and fullscreen policies",
        "duration_minutes": 30,
        "total_marks": 10.0,
        "passing_marks": 5.0,
        "enable_negative_marking": True
    }
    create_resp = await client.post("/api/v1/exams/", json=exam_payload, headers=faculty1_headers)
    assert create_resp.status_code == 201
    exam_id = create_resp.json()["id"]

    # Add question
    q_payload = {
        "question_text": "What type of attack does Content Security Policy (CSP) primarily mitigate?",
        "marks": 10.0,
        "explanation": "CSP is an effective defense against Cross-Site Scripting (XSS).",
        "options": [
            {"option_text": "SQL Injection", "is_correct": False},
            {"option_text": "Cross-Site Scripting (XSS)", "is_correct": True},
            {"option_text": "Buffer Overflow", "is_correct": False},
            {"option_text": "ARP Spoofing", "is_correct": False}
        ]
    }
    q_resp = await client.post(f"/api/v1/exams/{exam_id}/questions", json=q_payload, headers=faculty1_headers)
    assert q_resp.status_code == 201
    q_data = q_resp.json()
    q_id = q_data["id"]
    correct_opt_id = next(o["id"] for o in q_data["options"] if o["is_correct"])

    # Publish exam
    pub_resp = await client.put(f"/api/v1/exams/{exam_id}", json={"status": "PUBLISHED"}, headers=faculty1_headers)
    assert pub_resp.status_code == 200

    # 2. Student starts attempt
    start_resp = await client.post(f"/api/v1/attempts/start/{exam_id}", headers=student1_headers)
    assert start_resp.status_code == 201
    attempt_info = start_resp.json()
    attempt_id = attempt_info["attempt_id"]
    assert attempt_info["violation_count"] == 0
    assert attempt_info["status"] == "IN_PROGRESS"
    assert len(attempt_info["saved_answers"]) == 0

    # 3. Student answers question and marks for review (Auto-save)
    save_resp = await client.post(
        f"/api/v1/attempts/{attempt_id}/save-answer",
        json={"question_id": q_id, "selected_option_id": correct_opt_id, "is_marked_for_review": True},
        headers=student1_headers
    )
    assert save_resp.status_code == 200
    save_data = save_resp.json()
    assert save_data["status"] == "saved"
    assert save_data["selected_option_id"] == correct_opt_id
    assert save_data["is_marked_for_review"] is True

    # 4. Student resumes attempt (e.g. after refresh) -> verify saved answers restored
    resume_resp = await client.post(f"/api/v1/attempts/start/{exam_id}", headers=student1_headers)
    assert resume_resp.status_code in [200, 201]
    resume_info = resume_resp.json()
    assert resume_info["attempt_id"] == attempt_id
    assert len(resume_info["saved_answers"]) == 1
    assert resume_info["saved_answers"][0]["selected_option_id"] == correct_opt_id
    assert resume_info["saved_answers"][0]["is_marked_for_review"] is True

    # 5. Anti-IDOR: Peer student cannot save answers to this attempt
    peer_save = await client.post(
        f"/api/v1/attempts/{attempt_id}/save-answer",
        json={"question_id": q_id, "selected_option_id": correct_opt_id, "is_marked_for_review": False},
        headers=student2_headers
    )
    assert peer_save.status_code == 403

    # 6. Tab Switch & Fullscreen Violations Escalation
    # Violation 1: Tab switch
    v1_resp = await client.post(
        f"/api/v1/attempts/{attempt_id}/violation",
        json={"event_type": "TAB_SWITCH", "details": "Candidate switched browser tab"},
        headers=student1_headers
    )
    assert v1_resp.status_code == 200
    v1_data = v1_resp.json()
    assert v1_data["violation_count"] == 1
    assert v1_data["warning_level"] == 1
    assert v1_data["is_terminated"] is False

    # Violation 2: Fullscreen exit
    v2_resp = await client.post(
        f"/api/v1/attempts/{attempt_id}/violation",
        json={"event_type": "FULLSCREEN_EXIT", "details": "Candidate pressed ESC to exit fullscreen"},
        headers=student1_headers
    )
    assert v2_resp.status_code == 200
    v2_data = v2_resp.json()
    assert v2_data["violation_count"] == 2
    assert v2_data["warning_level"] == 2
    assert v2_data["is_terminated"] is False

    # Violation 3: Window blur
    v3_resp = await client.post(
        f"/api/v1/attempts/{attempt_id}/violation",
        json={"event_type": "WINDOW_BLUR", "details": "Window lost focus"},
        headers=student1_headers
    )
    assert v3_resp.status_code == 200
    v3_data = v3_resp.json()
    assert v3_data["violation_count"] == 3
    assert v3_data["warning_level"] == 3
    assert v3_data["is_terminated"] is False

    # Check status endpoint at warning 3
    status_resp = await client.get(f"/api/v1/attempts/{attempt_id}/status", headers=student1_headers)
    assert status_resp.status_code == 200
    assert status_resp.json()["violation_count"] == 3
    assert status_resp.json()["is_terminated"] is False

    # Violation 4: 4th infraction -> Exam Termination!
    v4_resp = await client.post(
        f"/api/v1/attempts/{attempt_id}/violation",
        json={"event_type": "TAB_SWITCH", "details": "Candidate switched tabs after final warning"},
        headers=student1_headers
    )
    assert v4_resp.status_code == 200
    v4_data = v4_resp.json()
    assert v4_data["violation_count"] == 4
    assert v4_data["warning_level"] == 4
    assert v4_data["is_terminated"] is True
    assert "Terminated" in v4_data["message"]

    # Verify attempt status is now TERMINATED_FOR_VIOLATION
    term_status = await client.get(f"/api/v1/attempts/{attempt_id}/status", headers=student1_headers)
    assert term_status.status_code == 200
    assert term_status.json()["status"] == "TERMINATED_FOR_VIOLATION"
    assert term_status.json()["is_terminated"] is True

    # 7. Verify Result record was automatically sealed with saved answers
    res_resp = await client.get(f"/api/v1/results/attempt/{attempt_id}", headers=student1_headers)
    assert res_resp.status_code == 200
    res_data = res_resp.json()
    assert res_data["total_score"] == 10.0
    assert res_data["passed"] is True

    # 8. Retake Prevention: Student CANNOT start another attempt after termination
    retake_resp = await client.post(f"/api/v1/attempts/start/{exam_id}", headers=student1_headers)
    assert retake_resp.status_code == 400
    assert "prohibited" in retake_resp.json()["detail"].lower() or "terminated" in retake_resp.json()["detail"].lower()

    # 9. Faculty Monitoring
    attempts_mon_resp = await client.get(f"/api/v1/exams/{exam_id}/attempts", headers=faculty1_headers)
    assert attempts_mon_resp.status_code == 200
    mon_list = attempts_mon_resp.json()
    assert len(mon_list) >= 1
    found_att = next(a for a in mon_list if a["id"] == attempt_id)
    assert found_att["status"] == "TERMINATED_FOR_VIOLATION"
    assert found_att["violation_count"] == 4
    assert found_att["score"] == 10.0

    violations_resp = await client.get(f"/api/v1/attempts/{attempt_id}/violations", headers=faculty1_headers)
    assert violations_resp.status_code == 200
    events = violations_resp.json()
    assert len(events) >= 5
    event_types = [e["event_type"] for e in events]
    assert "EXAM_STARTED" in event_types
    assert "TAB_SWITCH" in event_types
    assert "FULLSCREEN_EXIT" in event_types
    assert "WINDOW_BLUR" in event_types


@pytest.mark.asyncio
async def test_attempt_idor_and_unauthorized_access(
    client: AsyncClient,
    faculty1_headers: dict[str, str],
    faculty2_headers: dict[str, str],
    student1_headers: dict[str, str],
    student2_headers: dict[str, str],
    admin_headers: dict[str, str]
):
    # Faculty 1 creates exam
    exam_resp = await client.post("/api/v1/exams/", json={
        "title": "IDOR Proctored Test",
        "description": "Strict isolation test",
        "duration_minutes": 25,
        "total_marks": 5.0,
        "passing_marks": 2.5
    }, headers=faculty1_headers)
    exam_id = exam_resp.json()["id"]

    await client.put(f"/api/v1/exams/{exam_id}", json={"status": "PUBLISHED"}, headers=faculty1_headers)

    # Student 1 starts attempt
    start_resp = await client.post(f"/api/v1/attempts/start/{exam_id}", headers=student1_headers)
    attempt_id = start_resp.json()["attempt_id"]

    # Student 2 cannot read Student 1's attempt violations
    viol_resp = await client.get(f"/api/v1/attempts/{attempt_id}/violations", headers=student2_headers)
    assert viol_resp.status_code == 403

    # Student 2 cannot read Student 1's attempt status
    status_resp = await client.get(f"/api/v1/attempts/{attempt_id}/status", headers=student2_headers)
    assert status_resp.status_code == 403

    # Faculty 2 (not creator) cannot read exam attempts
    f2_resp = await client.get(f"/api/v1/exams/{exam_id}/attempts", headers=faculty2_headers)
    assert f2_resp.status_code == 403

    # Admin CAN read exam attempts
    admin_resp = await client.get(f"/api/v1/exams/{exam_id}/attempts", headers=admin_headers)
    assert admin_resp.status_code == 200

    # Student 1 CAN read their own attempt details and status
    s1_status = await client.get(f"/api/v1/attempts/{attempt_id}/status", headers=student1_headers)
    assert s1_status.status_code == 200
    assert s1_status.json()["status"] == "IN_PROGRESS"


@pytest.mark.asyncio
async def test_auto_submit_on_expiration(
    client: AsyncClient,
    faculty1_headers: dict[str, str],
    student1_headers: dict[str, str]
):
    # Create and publish exam
    exam_resp = await client.post("/api/v1/exams/", json={
        "title": "Auto-Submit Timeout Test",
        "description": "Testing automatic sealing on time expiration",
        "duration_minutes": 1,
        "total_marks": 5.0,
        "passing_marks": 2.5
    }, headers=faculty1_headers)
    exam_id = exam_resp.json()["id"]
    await client.put(f"/api/v1/exams/{exam_id}", json={"status": "PUBLISHED"}, headers=faculty1_headers)

    # Student starts attempt
    start_resp = await client.post(f"/api/v1/attempts/start/{exam_id}", headers=student1_headers)
    attempt_id = start_resp.json()["attempt_id"]

    # Force expiration in database to past time
    async with TestSessionLocal() as db:
        attempt = await db.get(ExamAttempt, attempt_id)
        past_time = datetime.now(UTC) - timedelta(minutes=5)
        attempt.expires_at = past_time
        await db.commit()

    # Status heartbeat triggers AUTO_SUBMITTED
    sync_resp = await client.get(f"/api/v1/attempts/{attempt_id}/status", headers=student1_headers)
    assert sync_resp.status_code == 200
    assert sync_resp.json()["status"] == "AUTO_SUBMITTED"

    # Retake blocked after auto-submission
    retake_resp = await client.post(f"/api/v1/attempts/start/{exam_id}", headers=student1_headers)
    assert retake_resp.status_code == 400


@pytest.mark.asyncio
async def test_database_initialization_and_seeding():
    from backend.app.db.init_db import init_db
    # Execute database initialization and idempotent migrations
    await init_db()


@pytest.mark.asyncio
async def test_get_attempt_endpoint_authorization(
    client: AsyncClient,
    faculty1_headers: dict[str, str],
    student1_headers: dict[str, str],
    student2_headers: dict[str, str],
    admin_headers: dict[str, str]
):
    # Create and publish exam
    exam_resp = await client.post("/api/v1/exams/", json={
        "title": "Attempt Lookup Test",
        "description": "Testing attempt endpoint",
        "duration_minutes": 15,
        "total_marks": 5.0,
        "passing_marks": 2.5
    }, headers=faculty1_headers)
    exam_id = exam_resp.json()["id"]
    await client.put(f"/api/v1/exams/{exam_id}", json={"status": "PUBLISHED"}, headers=faculty1_headers)

    start_resp = await client.post(f"/api/v1/attempts/start/{exam_id}", headers=student1_headers)
    attempt_id = start_resp.json()["attempt_id"]

    # Student 1 can access own attempt
    s1_resp = await client.get(f"/api/v1/attempts/{attempt_id}", headers=student1_headers)
    assert s1_resp.status_code == 200
    assert s1_resp.json()["id"] == attempt_id

    # Admin can access student's attempt
    adm_resp = await client.get(f"/api/v1/attempts/{attempt_id}", headers=admin_headers)
    assert adm_resp.status_code == 200

    # Peer student 2 is blocked from student 1's attempt (IDOR Defense)
    s2_resp = await client.get(f"/api/v1/attempts/{attempt_id}", headers=student2_headers)
    assert s2_resp.status_code == 403

