from abc import ABC, abstractmethod

from backend.app.models.question import Question


class EvaluationStrategy(ABC):
    """
    Abstract Evaluation Strategy interface.
    Follows the Strategy Pattern (GoF) to encapsulate scoring algorithms,
    decoupling question-level score computation from the orchestrating EvaluationService.
    """

    @abstractmethod
    def evaluate_question(self, question: Question, selected_option_id: int | None) -> float:
        """
        Calculates the earned marks for a single question response.
        :param question: The Question model instance with correct option data and marks.
        :param selected_option_id: The option ID chosen by the student (or None if unanswered).
        :return: Earned score (positive, zero, or negative).
        """
        pass


class StandardEvaluationStrategy(EvaluationStrategy):
    """
    Standard Positive-Only Scoring Strategy (V1.0 Baseline):
    - Correct answer: +marks
    - Incorrect answer: 0
    - Unanswered: 0
    """

    def evaluate_question(self, question: Question, selected_option_id: int | None) -> float:
        if selected_option_id is None:
            return 0.0

        correct_opt = next((opt for opt in question.options if opt.is_correct), None)
        if correct_opt and selected_option_id == correct_opt.id:
            return float(question.marks)
        return 0.0


class NegativeMarkingStrategy(EvaluationStrategy):
    """
    Configurable Negative Marking Strategy (Client Change Request CR-2026-004):
    - Correct answer: +marks
    - Incorrect answer: -negative_marks (configured penalty)
    - Unanswered: 0 (No penalty for unanswered questions)
    """

    def evaluate_question(self, question: Question, selected_option_id: int | None) -> float:
        if selected_option_id is None:
            # Explicit rule: Unanswered questions incur zero penalty
            return 0.0

        correct_opt = next((opt for opt in question.options if opt.is_correct), None)
        if correct_opt and selected_option_id == correct_opt.id:
            return float(question.marks)
        # Deduct configured negative penalty for wrong choice
        penalty = float(question.negative_marks)
        return -abs(penalty)


class EvaluationStrategyFactory:
    """Factory resolving appropriate EvaluationStrategy instance based on exam configuration."""

    @staticmethod
    def get_strategy(enable_negative_marking: bool) -> EvaluationStrategy:
        if enable_negative_marking:
            return NegativeMarkingStrategy()
        return StandardEvaluationStrategy()
