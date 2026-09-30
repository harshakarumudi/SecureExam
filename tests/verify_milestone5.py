import asyncio
import time
from httpx import AsyncClient, ASGITransport
from backend.main import app

async def run_e2e_verification():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        ts = int(time.time())
        student_email = f"student_{ts}@secureexam.edu"

        print("=== 1. TEST REGISTRATION & AUTHENTICATION ===")
        reg_res = await client.post("/api/v1/auth/register", json={
            "email": student_email,
            "full_name": "Jane Doe",
            "password": "CandidateSecure123!@#",
            "role": "STUDENT"
        })
        print("Register status:", reg_res.status_code)
        assert reg_res.status_code == 201

        # Login as student
        s_login = await client.post("/api/v1/auth/login", json={
            "email": student_email,
            "password": "CandidateSecure123!@#"
        })
        assert s_login.status_code == 200
        student_token = s_login.json()["access_token"]
        s_headers = {"Authorization": f"Bearer {student_token}"}
        print("Student login successful")

        print("=== 2. TEST FACULTY EXAM & QUESTION AUTHORING ===")
        f_login = await client.post("/api/v1/auth/login", json={
            "email": "faculty@secureexam.edu",
            "password": "FacultyPass123!@#"
        })
        assert f_login.status_code == 200
        faculty_token = f_login.json()["access_token"]
        f_headers = {"Authorization": f"Bearer {faculty_token}"}

        # Create exam
        exam_res = await client.post("/api/v1/exams/", headers=f_headers, json={
            "title": f"Secure Software Architecture {ts}",
            "description": "Mandatory midterm covering OWASP, STRIDE, and Cryptography",
            "duration_minutes": 45,
            "total_marks": 10.0,
            "passing_marks": 5.0
        })
        assert exam_res.status_code == 201
        exam_id = exam_res.json()["id"]
        status_val = exam_res.json()["status"]
        print(f"Exam created with ID: {exam_id}, Status: {status_val}")

        # Add question 1
        q1_res = await client.post(f"/api/v1/exams/{exam_id}/questions", headers=f_headers, json={
            "question_text": "Which memory-hard algorithm is recommended for password hashing?",
            "marks": 5.0,
            "negative_marks": 0.0,
            "explanation": "Argon2id won the Password Hashing Competition and resists GPU/ASIC attacks.",
            "order_index": 1,
            "options": [
                {"option_text": "MD5", "is_correct": False, "order_index": 1},
                {"option_text": "SHA-1", "is_correct": False, "order_index": 2},
                {"option_text": "Argon2id", "is_correct": True, "order_index": 3},
                {"option_text": "DES", "is_correct": False, "order_index": 4}
            ]
        })
        assert q1_res.status_code == 201
        q1_id = q1_res.json()["id"]

        # Add question 2
        q2_res = await client.post(f"/api/v1/exams/{exam_id}/questions", headers=f_headers, json={
            "question_text": "What category in STRIDE corresponds to unauthorized tampering of database records?",
            "marks": 5.0,
            "negative_marks": 0.0,
            "explanation": "T in STRIDE stands for Tampering with data.",
            "order_index": 2,
            "options": [
                {"option_text": "Spoofing", "is_correct": False, "order_index": 1},
                {"option_text": "Tampering", "is_correct": True, "order_index": 2},
                {"option_text": "Repudiation", "is_correct": False, "order_index": 3},
                {"option_text": "Denial of Service", "is_correct": False, "order_index": 4}
            ]
        })
        assert q2_res.status_code == 201
        q2_id = q2_res.json()["id"]
        print(f"Authored 2 questions: Q1 ID {q1_id}, Q2 ID {q2_id}")

        # Publish exam
        pub_res = await client.put(f"/api/v1/exams/{exam_id}", headers=f_headers, json={"status": "PUBLISHED"})
        assert pub_res.status_code == 200
        assert pub_res.json()["status"] == "PUBLISHED"
        print("Exam published successfully")

        print("=== 3. TEST STUDENT ATTEMPT & AUTHORITATIVE TIMER ===")
        # Student starts exam
        attempt_res = await client.post(f"/api/v1/attempts/start/{exam_id}", headers=s_headers)
        assert attempt_res.status_code == 201
        attempt_data = attempt_res.json()
        attempt_id = attempt_data["attempt_id"]
        print(f"Attempt started: #{attempt_id}, Expires at: {attempt_data['expires_at']}")

        # Verify question data sent to student is sanitized
        received_q1 = attempt_data["questions"][0]
        assert "is_correct" not in received_q1["options"][0]
        assert "explanation" not in received_q1
        print("Verified: Student question payload is confidential (keys hidden)")

        # Find option IDs
        opt_q1_correct = [o["id"] for o in received_q1["options"] if o["option_text"] == "Argon2id"][0]
        received_q2 = attempt_data["questions"][1]
        opt_q2_wrong = [o["id"] for o in received_q2["options"] if o["option_text"] == "Spoofing"][0]

        # Submit answers
        sub_res = await client.post(f"/api/v1/attempts/{attempt_id}/submit", headers=s_headers, json={
            "answers": [
                {"question_id": q1_id, "selected_option_id": opt_q1_correct},
                {"question_id": q2_id, "selected_option_id": opt_q2_wrong}
            ]
        })
        assert sub_res.status_code == 200
        result_data = sub_res.json()
        print("Evaluated score:", result_data["total_score"], "/", result_data["max_score"])
        print("Percentage:", result_data["percentage"], "Passed:", result_data["passed"])
        assert result_data["total_score"] == 5.0
        assert result_data["max_score"] == 10.0
        assert result_data["percentage"] == 50.0
        assert result_data["passed"] is True

        print("=== 4. TEST SECURITY: RBAC, BOLA/IDOR & REJECTION ===")
        # Student tries to create exam -> HTTP 403
        bad_exam = await client.post("/api/v1/exams/", headers=s_headers, json={"title": "Hacked Exam", "duration_minutes": 10})
        assert bad_exam.status_code == 403
        print("Verified: Student blocked from faculty endpoint (403)")

        # Student tries to submit again -> HTTP 400
        dup_sub = await client.post(f"/api/v1/attempts/{attempt_id}/submit", headers=s_headers, json={"answers": []})
        assert dup_sub.status_code == 400
        print("Verified: Resubmission blocked (400)")

        # Second student tries to read first student's result -> HTTP 403
        s2_login = await client.post("/api/v1/auth/login", json={"email": "student@secureexam.edu", "password": "StudentPass123!@#"})
        s2_headers = {"Authorization": f"Bearer {s2_login.json()['access_token']}"}
        idor_res = await client.get(f"/api/v1/results/attempt/{attempt_id}", headers=s2_headers)
        assert idor_res.status_code == 403
        print("Verified: BOLA/IDOR prevented when accessing another candidate result (403)")

        print("=== 5. TEST ADMIN GOVERNANCE & AUDIT LOGS ===")
        admin_login = await client.post("/api/v1/auth/login", json={"email": "admin@secureexam.edu", "password": "AdminPass123!@#"})
        a_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}
        audit_res = await client.get("/api/v1/audit/", headers=a_headers)
        assert audit_res.status_code == 200
        logs = audit_res.json()
        print(f"Total audit logs generated: {len(logs)}")
        actions = [l["action"] for l in logs]
        assert "USER_REGISTERED" in actions
        assert "EXAM_CREATED" in actions
        assert "ATTEMPT_STARTED" in actions
        assert "ATTEMPT_SUBMITTED" in actions

        print("\n*** MILESTONE 5 COMPLETE WORKING WEBSITE VERIFIED 100% ***")

if __name__ == "__main__":
    asyncio.run(run_e2e_verification())
