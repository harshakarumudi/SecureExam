import React, { useState, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "../services/api";
import { AttemptStartResponse, StudentAnswerSubmission } from "../types";
import { TimerDisplay } from "../components/TimerDisplay";
import { QuestionPalette } from "../components/QuestionPalette";
import { Modal } from "../components/Modal";
import { Shield, AlertCircle, ArrowLeft, ArrowRight, CheckCircle2, RotateCcw } from "lucide-react";

export const ExamTakingPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [attemptData, setAttemptData] = useState<AttemptStartResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Active question index
  const [currentIndex, setCurrentIndex] = useState<number>(0);

  // Selected answers: map of question_id -> selected_option_id
  const [answers, setAnswers] = useState<Record<number, number | null>>({});

  // Submission modal
  const [showSubmitModal, setShowSubmitModal] = useState<boolean>(false);
  const [submitting, setSubmitting] = useState<boolean>(false);

  // Flag to prevent double submission
  const isSubmittedRef = useRef(false);

  useEffect(() => {
    const initAttempt = async () => {
      if (!id) return;
      try {
        const data = await api.startAttempt(parseInt(id, 10));
        setAttemptData(data);
      } catch (err: any) {
        setError(err.message || "Failed to initialize examination session.");
      } finally {
        setLoading(false);
      }
    };
    initAttempt();
  }, [id]);

  const handleSelectOption = (questionId: number, optionId: number) => {
    setAnswers((prev) => ({
      ...prev,
      [questionId]: optionId,
    }));
  };

  const handleClearOption = (questionId: number) => {
    setAnswers((prev) => ({
      ...prev,
      [questionId]: null,
    }));
  };

  const handleSubmitExam = async () => {
    if (!attemptData || isSubmittedRef.current) return;
    isSubmittedRef.current = true;
    setSubmitting(true);

    try {
      const payload: StudentAnswerSubmission[] = Object.entries(answers).map(([qId, optId]) => ({
        question_id: parseInt(qId, 10),
        selected_option_id: optId,
      }));

      const result = await api.submitAttempt(attemptData.attempt_id, payload);
      navigate(`/student/results?highlight=${result.id}`);
    } catch (err: any) {
      setError(err.message || "Failed to submit examination.");
      isSubmittedRef.current = false;
    } finally {
      setSubmitting(false);
      setShowSubmitModal(false);
    }
  };

  const handleTimerExpire = () => {
    if (!isSubmittedRef.current) {
      handleSubmitExam();
    }
  };

  if (loading) {
    return (
      <div className="min-h-[70vh] flex flex-col items-center justify-center space-y-3">
        <div className="w-10 h-10 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-sm font-semibold text-slate-600">Initializing Authoritative Security Session...</p>
      </div>
    );
  }

  if (error || !attemptData) {
    return (
      <div className="max-w-xl mx-auto my-12 p-6 bg-white rounded-2xl border border-rose-200 shadow-sm text-center space-y-4">
        <AlertCircle className="w-12 h-12 text-rose-500 mx-auto" />
        <h3 className="text-xl font-bold text-slate-800">Examination Session Error</h3>
        <p className="text-sm text-slate-600">{error || "Unable to start session."}</p>
        <button
          onClick={() => navigate("/student")}
          className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-sm font-medium transition"
        >
          Return to Dashboard
        </button>
      </div>
    );
  }

  const questions = attemptData.questions;
  const currentQuestion = questions[currentIndex];

  // Set of indices that have been answered
  const answeredIndices = new Set<number>();
  questions.forEach((q, idx) => {
    if (answers[q.id] !== undefined && answers[q.id] !== null) {
      answeredIndices.add(idx);
    }
  });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      {/* Active Exam Header Bar */}
      <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="bg-indigo-50 text-indigo-600 p-2.5 rounded-xl">
            <Shield className="w-5 h-5" />
          </div>
          <div>
            <span className="text-xs font-semibold text-indigo-600 uppercase tracking-wider">Active Test Environment</span>
            <h2 className="text-lg font-bold text-slate-900">{attemptData.exam_title}</h2>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <TimerDisplay expiresAt={attemptData.expires_at} onExpire={handleTimerExpire} />
          <button
            onClick={() => setShowSubmitModal(true)}
            className="bg-emerald-600 hover:bg-emerald-700 text-white font-medium px-4 py-2 rounded-xl text-xs shadow-sm transition flex items-center space-x-1.5"
          >
            <CheckCircle2 className="w-4 h-4" />
            <span>Finish & Submit</span>
          </button>
        </div>
      </div>

      {/* Main Examination Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Left / Center 3 Columns: Active Question Card */}
        <div className="lg:col-span-3 bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-sm flex flex-col justify-between min-h-[500px]">
          {currentQuestion ? (
            <div className="space-y-6">
              {/* Question Meta Header */}
              <div className="flex items-center justify-between border-b border-slate-100 pb-4">
                <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                  Question {currentIndex + 1} of {questions.length}
                </span>
                <span className="bg-slate-100 text-slate-700 text-xs px-2.5 py-1 rounded-lg font-semibold">
                  {currentQuestion.marks} {currentQuestion.marks === 1 ? "Mark" : "Marks"}
                </span>
              </div>

              {/* Question Text */}
              <div className="text-base sm:text-lg font-medium text-slate-900 leading-relaxed">
                {currentQuestion.question_text}
              </div>

              {/* Options List (Single Choice Radio) */}
              <div className="space-y-3 pt-2">
                {currentQuestion.options.map((opt, optIdx) => {
                  const isSelected = answers[currentQuestion.id] === opt.id;
                  const letter = String.fromCharCode(65 + optIdx); // A, B, C, D

                  return (
                    <label
                      key={opt.id}
                      onClick={() => handleSelectOption(currentQuestion.id, opt.id)}
                      className={`flex items-start space-x-3.5 p-4 rounded-xl border cursor-pointer transition-all ${
                        isSelected
                          ? "bg-indigo-50/70 border-indigo-500 text-indigo-950 ring-1 ring-indigo-500 shadow-sm"
                          : "bg-white border-slate-200 text-slate-800 hover:bg-slate-50"
                      }`}
                    >
                      <div
                        className={`w-6 h-6 rounded-full font-bold text-xs flex items-center justify-center flex-shrink-0 mt-0.5 border ${
                          isSelected
                            ? "bg-indigo-600 text-white border-indigo-600"
                            : "bg-slate-100 text-slate-600 border-slate-300"
                        }`}
                      >
                        {letter}
                      </div>
                      <div className="text-sm font-medium leading-normal pt-0.5">{opt.option_text}</div>
                    </label>
                  );
                })}
              </div>
            </div>
          ) : (
            <div className="text-center py-20 text-slate-400">No questions available in this test.</div>
          )}

          {/* Navigation Controls Footer */}
          <div className="mt-8 pt-4 border-t border-slate-100 flex items-center justify-between">
            <button
              onClick={() => setCurrentIndex((prev) => Math.max(0, prev - 1))}
              disabled={currentIndex === 0}
              className="px-4 py-2 rounded-xl border border-slate-300 text-slate-700 font-medium text-xs hover:bg-slate-50 disabled:opacity-40 disabled:hover:bg-transparent transition flex items-center space-x-1.5"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Previous Question</span>
            </button>

            {currentQuestion && answers[currentQuestion.id] !== null && answers[currentQuestion.id] !== undefined && (
              <button
                onClick={() => handleClearOption(currentQuestion.id)}
                className="text-xs text-slate-500 hover:text-slate-800 font-medium flex items-center space-x-1"
              >
                <RotateCcw className="w-3 h-3" />
                <span>Clear Selection</span>
              </button>
            )}

            {currentIndex < questions.length - 1 ? (
              <button
                onClick={() => setCurrentIndex((prev) => Math.min(questions.length - 1, prev + 1))}
                className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-xs shadow-sm transition flex items-center space-x-1.5"
              >
                <span>Next Question</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            ) : (
              <button
                onClick={() => setShowSubmitModal(true)}
                className="px-5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-medium text-xs shadow-sm transition flex items-center space-x-1.5"
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Review & Submit</span>
              </button>
            )}
          </div>
        </div>

        {/* Right 1 Column: Question Navigation Matrix */}
        <div className="space-y-6">
          <QuestionPalette
            totalQuestions={questions.length}
            currentIndex={currentIndex}
            answeredIndices={answeredIndices}
            onSelectQuestion={(idx) => setCurrentIndex(idx)}
          />

          <div className="bg-slate-100/70 border border-slate-200/80 rounded-xl p-4 text-xs text-slate-600 space-y-2">
            <div className="font-bold text-slate-700">Security Guarantee:</div>
            <p className="leading-relaxed">
              Your selections are temporarily held in client memory until final submission. Evaluation takes place strictly
              on the server backend upon submission.
            </p>
          </div>
        </div>
      </div>

      {/* Submission Confirmation Modal */}
      <Modal
        isOpen={showSubmitModal}
        onClose={() => setShowSubmitModal(false)}
        title="Confirm Examination Submission"
      >
        <div className="space-y-4 text-sm text-slate-600">
          <p>
            You are about to submit your examination answers for official grading.
          </p>

          <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-1 text-xs">
            <div className="flex justify-between">
              <span className="text-slate-500">Total Questions:</span>
              <span className="font-semibold text-slate-800">{questions.length}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Answered Questions:</span>
              <span className="font-semibold text-emerald-700">{answeredIndices.size}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Unanswered Questions:</span>
              <span className="font-semibold text-amber-700">{questions.length - answeredIndices.size}</span>
            </div>
          </div>

          <div className="text-xs text-rose-600 font-medium">
            Warning: Once confirmed, your answers will be permanently evaluated and sealed. You cannot reopen or retake this exam.
          </div>

          <div className="pt-4 border-t border-slate-100 flex justify-end space-x-3">
            <button
              onClick={() => setShowSubmitModal(false)}
              disabled={submitting}
              className="px-4 py-2 rounded-xl border border-slate-300 text-xs font-medium text-slate-700 hover:bg-slate-50"
            >
              Continue Test
            </button>
            <button
              onClick={handleSubmitExam}
              disabled={submitting}
              className="px-5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-xs font-medium text-white shadow-sm flex items-center space-x-1.5"
            >
              <span>{submitting ? "Grading..." : "Confirm & Submit"}</span>
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

