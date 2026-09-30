import pytest

from backend.app.models.question import Question, QuestionOption
from backend.app.services.evaluation_strategies import (
    EvaluationStrategyFactory,
    NegativeMarkingStrategy,
    StandardEvaluationStrategy,
)


def build_mock_question(marks=5.0, negative_marks=2.0):
    q = Question(
        id=101,
        exam_id=1,
        question_text="What is AES?",
        marks=marks,
        negative_marks=negative_marks
    )
    opt1 = QuestionOption(id=1, question_id=101, option_text="Symmetric cipher", is_correct=True)
    opt2 = QuestionOption(id=2, question_id=101, option_text="Hash function", is_correct=False)
    opt3 = QuestionOption(id=3, question_id=101, option_text="Asymmetric cipher", is_correct=False)
    q.options = [opt1, opt2, opt3]
    return q

def test_standard_evaluation_strategy_unit():
    strategy = StandardEvaluationStrategy()
    q = build_mock_question(marks=5.0, negative_marks=2.0)

    # Correct answer -> +5.0
    assert strategy.evaluate_question(q, 1) == 5.0
    # Incorrect answer -> 0.0 (no penalty in standard mode)
    assert strategy.evaluate_question(q, 2) == 0.0
    # Unanswered -> 0.0
    assert strategy.evaluate_question(q, None) == 0.0

def test_negative_marking_strategy_unit():
    strategy = NegativeMarkingStrategy()
    q = build_mock_question(marks=5.0, negative_marks=2.0)

    # Correct answer -> +5.0
    assert strategy.evaluate_question(q, 1) == 5.0
    # Incorrect answer -> -2.0 penalty
    assert strategy.evaluate_question(q, 2) == -2.0
    assert strategy.evaluate_question(q, 3) == -2.0
    # Unanswered -> 0.0 (No penalty for skipped questions)
    assert strategy.evaluate_question(q, None) == 0.0

def test_evaluation_strategy_factory():
    assert isinstance(EvaluationStrategyFactory.get_strategy(False), StandardEvaluationStrategy)
    assert isinstance(EvaluationStrategyFactory.get_strategy(True), NegativeMarkingStrategy)

@pytest.mark.asyncio
async def test_negative_marking_e2e_lifecycle(client, faculty1_headers, student1_headers):
    # 1. Faculty creates exam with negative marking enabled
    exam_payload = {
        "title": "GATE CS Competitive Exam",
        "description": "High-stakes entrance exam with 25% negative marking penalty",
        "duration_minutes": 30,
        "total_marks": 15.0,
        "passing_marks": 7.5,
        "enable_negative_marking": True
    }
    create_resp = await client.post("/api/v1/exams/", json=exam_payload, headers=faculty1_headers)
    assert create_resp.status_code == 201
    exam = create_resp.json()
    exam_id = exam["id"]
    assert exam["enable_negative_marking"] is True

    # 2. Add 3 questions (5 marks each, 1.5 negative marks)
    q_ids = []
    correct_opts = []
    wrong_opts = []

    for i in range(1, 4):
        q_payload = {
            "question_text": f"Competitive Question {i}",
            "marks": 5.0,
            "negative_marks": 1.5,
            "options": [
                {"option_text": "Option A (Correct)", "is_correct": True},
                {"option_text": "Option B (Wrong)", "is_correct": False},
                {"option_text": "Option C (Wrong)", "is_correct": False}
            ]
        }
        q_resp = await client.post(f"/api/v1/exams/{exam_id}/questions", json=q_payload, headers=faculty1_headers)
        assert q_resp.status_code == 201
        data = q_resp.json()
        q_ids.append(data["id"])
        correct_opts.append(next(o["id"] for o in data["options"] if o["is_correct"]))
        wrong_opts.append(next(o["id"] for o in data["options"] if not o["is_correct"]))

    # Publish exam
    await client.put(f"/api/v1/exams/{exam_id}", json={"status": "PUBLISHED"}, headers=faculty1_headers)

    # 3. Student starts attempt
    start_resp = await client.post(f"/api/v1/attempts/start/{exam_id}", headers=student1_headers)
    assert start_resp.status_code == 201
    attempt_id = start_resp.json()["attempt_id"]

    # 4. Student submits:
    # Q1: Correct (+5.0)
    # Q2: Wrong (-1.5)
    # Q3: Unanswered (0.0)
    submission_payload = {
        "answers": [
            {"question_id": q_ids[0], "selected_option_id": correct_opts[0]},
            {"question_id": q_ids[1], "selected_option_id": wrong_opts[1]}
            # Q3 omitted -> Unanswered
        ]
    }
    submit_resp = await client.post(f"/api/v1/attempts/{attempt_id}/submit", json=submission_payload, headers=student1_headers)
    assert submit_resp.status_code == 200
    res = submit_resp.json()

    # Net score: 5.0 - 1.5 + 0.0 = 3.5
    assert res["total_score"] == 3.5
    assert res["max_score"] == 15.0
    assert round(res["percentage"], 2) == 23.33
    assert res["passed"] is False

@pytest.mark.asyncio
async def test_negative_marking_underflow_protection(client, faculty1_headers, student1_headers):
    # Create exam with negative marking
    exam_resp = await client.post("/api/v1/exams/", json={
        "title": "Strict Math Olympiad",
        "description": "Testing score floor protection",
        "duration_minutes": 15,
        "total_marks": 10.0,
        "passing_marks": 5.0,
        "enable_negative_marking": True
    }, headers=faculty1_headers)
    exam_id = exam_resp.json()["id"]

    # Add 2 questions with heavy penalties (5 marks each, -4 marks penalty)
    q_ids = []
    wrong_opts = []
    for i in range(1, 3):
        q_resp = await client.post(f"/api/v1/exams/{exam_id}/questions", json={
            "question_text": f"Severe Question {i}",
            "marks": 5.0,
            "negative_marks": 4.0,
            "options": [
                {"option_text": "Correct", "is_correct": True},
                {"option_text": "Wrong", "is_correct": False}
            ]
        }, headers=faculty1_headers)
        q_data = q_resp.json()
        q_ids.append(q_data["id"])
        wrong_opts.append(next(o["id"] for o in q_data["options"] if not o["is_correct"]))

    await client.put(f"/api/v1/exams/{exam_id}", json={"status": "PUBLISHED"}, headers=faculty1_headers)

    start_resp = await client.post(f"/api/v1/attempts/start/{exam_id}", headers=student1_headers)
    attempt_id = start_resp.json()["attempt_id"]

    # Submit all incorrect answers: -4.0 + -4.0 = -8.0 mathematically
    # Must be bounded at 0.0 (score underflow protection)
    submission_payload = {
        "answers": [
            {"question_id": q_ids[0], "selected_option_id": wrong_opts[0]},
            {"question_id": q_ids[1], "selected_option_id": wrong_opts[1]}
        ]
    }
    submit_resp = await client.post(f"/api/v1/attempts/{attempt_id}/submit", json=submission_payload, headers=student1_headers)
    assert submit_resp.status_code == 200
    res = submit_resp.json()

    assert res["total_score"] == 0.0
    assert res["percentage"] == 0.0
    assert res["passed"] is False
