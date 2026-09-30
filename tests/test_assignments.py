import pytest


@pytest.mark.asyncio
async def test_exam_assignment_flow_and_rbac(client, faculty1_headers, faculty2_headers, student1_headers, student2_headers):
    # 1. Faculty 1 creates an exam
    exam_payload = {
        "title": "Restricted Cryptography Exam",
        "description": "Exam assigned exclusively to student 1",
        "duration_minutes": 30,
        "total_marks": 20.0,
        "passing_marks": 10.0,
    }
    create_resp = await client.post("/api/v1/exams/", json=exam_payload, headers=faculty1_headers)
    assert create_resp.status_code == 201
    exam = create_resp.json()
    exam_id = exam["id"]

    # Add question to make exam valid
    q_payload = {
        "question_text": "What is RSA?",
        "marks": 20.0,
        "options": [
            {"option_text": "Asymmetric Cryptosystem", "is_correct": True},
            {"option_text": "Symmetric Cipher", "is_correct": False},
        ],
    }
    q_resp = await client.post(f"/api/v1/exams/{exam_id}/questions", json=q_payload, headers=faculty1_headers)
    assert q_resp.status_code == 201

    # Publish exam
    pub_resp = await client.put(f"/api/v1/exams/{exam_id}", json={"status": "PUBLISHED"}, headers=faculty1_headers)
    assert pub_resp.status_code == 200

    # 2. Faculty 1 lists enrolled students
    students_resp = await client.get("/api/v1/users/students", headers=faculty1_headers)
    assert students_resp.status_code == 200
    students = students_resp.json()
    assert len(students) >= 2
    student1_obj = next(s for s in students if s["email"] == "student1@test.edu")
    student2_obj = next(s for s in students if s["email"] == "student2@test.edu")

    # 3. Faculty 1 assigns exam ONLY to Student 1
    assign_resp = await client.post(
        f"/api/v1/exams/{exam_id}/assignments",
        json={"student_ids": [student1_obj["id"]]},
        headers=faculty1_headers,
    )
    assert assign_resp.status_code == 200
    assignments = assign_resp.json()
    assert len(assignments) == 1
    assert assignments[0]["student_id"] == student1_obj["id"]

    # 4. Student 1 checks available exams: MUST see the restricted exam
    s1_exams_resp = await client.get("/api/v1/exams/available", headers=student1_headers)
    assert s1_exams_resp.status_code == 200
    s1_exam_ids = [e["id"] for e in s1_exams_resp.json()]
    assert exam_id in s1_exam_ids

    # 5. Student 2 checks available exams: MUST NOT see the restricted exam
    s2_exams_resp = await client.get("/api/v1/exams/available", headers=student2_headers)
    assert s2_exams_resp.status_code == 200
    s2_exam_ids = [e["id"] for e in s2_exams_resp.json()]
    assert exam_id not in s2_exam_ids

    # 6. Student 2 attempts to start attempt via direct IDOR URL -> 403 FORBIDDEN
    s2_attempt_resp = await client.post(f"/api/v1/attempts/start/{exam_id}", headers=student2_headers)
    assert s2_attempt_resp.status_code == 403
    assert "not assigned" in s2_attempt_resp.json()["detail"].lower()

    # 7. Student 1 starts attempt -> 201 CREATED
    s1_attempt_resp = await client.post(f"/api/v1/attempts/start/{exam_id}", headers=student1_headers)
    assert s1_attempt_resp.status_code == 201

    # 8. Cross-faculty IDOR: Faculty 2 tries to reassign Faculty 1's exam -> 403 FORBIDDEN
    f2_assign_resp = await client.post(
        f"/api/v1/exams/{exam_id}/assignments",
        json={"student_ids": [student2_obj["id"]]},
        headers=faculty2_headers,
    )
    assert f2_assign_resp.status_code == 403
