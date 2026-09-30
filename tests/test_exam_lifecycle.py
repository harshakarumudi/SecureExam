import pytest


@pytest.mark.asyncio
async def test_full_exam_lifecycle(client, faculty1_headers, student1_headers):
    # 1. Faculty creates exam
    exam_payload = {
        "title": "Computer Networks Midterm",
        "description": "Comprehensive assessment on OSI and TCP/IP models",
        "duration_minutes": 20,
        "total_marks": 10.0,
        "passing_marks": 5.0
    }
    create_resp = await client.post("/api/v1/exams/", json=exam_payload, headers=faculty1_headers)
    assert create_resp.status_code == 201
    exam = create_resp.json()
    exam_id = exam["id"]
    assert exam["status"] == "DRAFT"

    # 2. Faculty adds questions
    q1_payload = {
        "question_text": "Which layer of the OSI model provides end-to-end communication?",
        "marks": 5.0,
        "explanation": "Transport layer provides end-to-end communication services.",
        "options": [
            {"option_text": "Physical Layer", "is_correct": False},
            {"option_text": "Data Link Layer", "is_correct": False},
            {"option_text": "Transport Layer", "is_correct": True},
            {"option_text": "Session Layer", "is_correct": False}
        ]
    }
    q1_resp = await client.post(f"/api/v1/exams/{exam_id}/questions", json=q1_payload, headers=faculty1_headers)
    assert q1_resp.status_code == 201
    q1_data = q1_resp.json()
    q1_id = q1_data["id"]
    q1_correct_opt = next(opt["id"] for opt in q1_data["options"] if opt["is_correct"])

    q2_payload = {
        "question_text": "What protocol is used for secure shell remote login?",
        "marks": 5.0,
        "explanation": "SSH runs on port 22 and encrypts traffic.",
        "options": [
            {"option_text": "Telnet", "is_correct": False},
            {"option_text": "SSH", "is_correct": True},
            {"option_text": "FTP", "is_correct": False},
            {"option_text": "HTTP", "is_correct": False}
        ]
    }
    q2_resp = await client.post(f"/api/v1/exams/{exam_id}/questions", json=q2_payload, headers=faculty1_headers)
    assert q2_resp.status_code == 201
    q2_data = q2_resp.json()
    q2_id = q2_data["id"]
    q2_incorrect_opt = next(opt["id"] for opt in q2_data["options"] if not opt["is_correct"])

    # 3. Faculty publishes exam
    pub_resp = await client.put(f"/api/v1/exams/{exam_id}", json={"status": "PUBLISHED"}, headers=faculty1_headers)
    assert pub_resp.status_code == 200
    assert pub_resp.json()["status"] == "PUBLISHED"

    # 4. Student discovers published exam
    exams_resp = await client.get("/api/v1/exams/", headers=student1_headers)
    assert exams_resp.status_code == 200
    published_exams = exams_resp.json()
    found = any(e["id"] == exam_id for e in published_exams)
    assert found is True

    # 5. Student starts attempt
    start_resp = await client.post(f"/api/v1/attempts/start/{exam_id}", headers=student1_headers)
    assert start_resp.status_code == 201
    attempt_data = start_resp.json()
    attempt_id = attempt_data["attempt_id"]
    assert "expires_at" in attempt_data

    # Verify student question view has zero answer leakage
    questions = attempt_data["questions"]
    assert len(questions) == 2
    for q in questions:
        for opt in q["options"]:
            assert "is_correct" not in opt
        assert "explanation" not in q

    # 6. Student submits answers (Q1 correct: 5 marks, Q2 wrong: 0 marks)
    submission_payload = {
        "answers": [
            {"question_id": q1_id, "selected_option_id": q1_correct_opt},
            {"question_id": q2_id, "selected_option_id": q2_incorrect_opt}
        ]
    }
    submit_resp = await client.post(f"/api/v1/attempts/{attempt_id}/submit", json=submission_payload, headers=student1_headers)
    assert submit_resp.status_code == 200
    res_data = submit_resp.json()
    assert res_data["total_score"] == 5.0
    assert res_data["max_score"] == 10.0
    assert res_data["percentage"] == 50.0
    assert res_data["passed"] is True

    # 7. Student retrieves stored result
    result_resp = await client.get(f"/api/v1/results/attempt/{attempt_id}", headers=student1_headers)
    assert result_resp.status_code == 200
    stored_result = result_resp.json()
    assert stored_result["total_score"] == 5.0
    assert stored_result["attempt_id"] == attempt_id

    # 8. Faculty views exam attempts / results
    faculty_attempts_resp = await client.get(f"/api/v1/results/exam/{exam_id}", headers=faculty1_headers)
    assert faculty_attempts_resp.status_code == 200
    results_list = faculty_attempts_resp.json()
    assert len(results_list) >= 1
    assert any(r["attempt_id"] == attempt_id for r in results_list)
