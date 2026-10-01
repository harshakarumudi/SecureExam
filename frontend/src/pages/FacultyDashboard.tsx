import React, { useState, useEffect } from "react";
import { Exam, ExamAttemptMonitor, ExamViolationItem, Result, User } from "../types";
import { api } from "../services/api";
import { Modal } from "../components/Modal";
import {
  Layers,
  Plus,
  Eye,
  Trash2,
  Users,
  AlertCircle,
  UserCheck,
  ShieldAlert,
} from "lucide-react";

export const FacultyDashboard: React.FC = () => {
  const [exams, setExams] = useState<Exam[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modal controls
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showQuestionModal, setShowQuestionModal] = useState(false);
  const [showPreviewModal, setShowPreviewModal] = useState(false);
  const [showSubmissionsModal, setShowSubmissionsModal] = useState(false);
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [showAttemptsModal, setShowAttemptsModal] = useState(false);
  const [showActivityLogModal, setShowActivityLogModal] = useState(false);

  // Active selected exam
  const [activeExam, setActiveExam] = useState<Exam | null>(null);
  const [submissions, setSubmissions] = useState<Result[]>([]);

  // Attempts & Proctoring Monitor State
  const [attemptsList, setAttemptsList] = useState<ExamAttemptMonitor[]>([]);
  const [attemptsLoading, setAttemptsLoading] = useState(false);
  const [selectedAttemptViolations, setSelectedAttemptViolations] = useState<ExamViolationItem[]>([]);
  const [selectedAttemptInfo, setSelectedAttemptInfo] = useState<ExamAttemptMonitor | null>(null);
  const [activityLoading, setActivityLoading] = useState(false);

  // Student Assignment State
  const [students, setStudents] = useState<User[]>([]);
  const [selectedStudentIds, setSelectedStudentIds] = useState<number[]>([]);
  const [studentSearch, setStudentSearch] = useState("");
  const [assignLoading, setAssignLoading] = useState(false);

  // Create Exam Form state
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [durationMinutes, setDurationMinutes] = useState(60);
  const [totalMarks, setTotalMarks] = useState(100);
  const [passingMarks, setPassingMarks] = useState(40);

  // Add Question Form state
  const [qText, setQText] = useState("");
  const [qMarks, setQMarks] = useState(1);
  const [qExplanation, setQExplanation] = useState("");
  const [options, setOptions] = useState([
    { text: "", isCorrect: true },
    { text: "", isCorrect: false },
    { text: "", isCorrect: false },
    { text: "", isCorrect: false },
  ]);

  const fetchExams = async () => {
    try {
      const data = await api.getExams();
      setExams(data);
    } catch (err: any) {
      setError(err.message || "Failed to load examinations.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExams();
  }, []);

  const handleCreateExam = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createExam({
        title,
        description,
        duration_minutes: durationMinutes,
        total_marks: totalMarks,
        passing_marks: passingMarks,
      });
      setShowCreateModal(false);
      setTitle("");
      setDescription("");
      fetchExams();
    } catch (err: any) {
      alert(err.message || "Failed to create examination.");
    }
  };

  const handleTogglePublish = async (exam: Exam) => {
    const newStatus = exam.status === "PUBLISHED" ? "DRAFT" : "PUBLISHED";
    try {
      await api.updateExam(exam.id, { status: newStatus });
      fetchExams();
    } catch (err: any) {
      alert(err.message || "Failed to toggle publication status.");
    }
  };

  const handleDeleteExam = async (examId: number) => {
    if (!window.confirm("Are you sure you want to delete this examination?")) return;
    try {
      await api.deleteExam(examId);
      fetchExams();
    } catch (err: any) {
      alert(err.message || "Failed to delete examination.");
    }
  };

  const openQuestionManager = async (exam: Exam) => {
    try {
      const detailed = await api.getExam(exam.id);
      setActiveExam(detailed);
      setShowQuestionModal(true);
    } catch (err: any) {
      alert(err.message);
    }
  };

  const openPreview = async (exam: Exam) => {
    try {
      const detailed = await api.getExam(exam.id);
      setActiveExam(detailed);
      setShowPreviewModal(true);
    } catch (err: any) {
      alert(err.message);
    }
  };

  const openSubmissions = async (exam: Exam) => {
    try {
      setActiveExam(exam);
      const data = await api.getExamResults(exam.id);
      setSubmissions(data);
      setShowSubmissionsModal(true);
    } catch (err: any) {
      alert(err.message);
    }
  };

  const openAssignModal = async (exam: Exam) => {
    try {
      setActiveExam(exam);
      setAssignLoading(true);
      setShowAssignModal(true);
      const [allStuds, currentAssignments] = await Promise.all([
        api.getStudents(),
        api.getExamAssignments(exam.id),
      ]);
      setStudents(allStuds);
      setSelectedStudentIds(currentAssignments.map((a) => a.student_id));
    } catch (err: any) {
      alert(err.message || "Failed to load student assignments.");
    } finally {
      setAssignLoading(false);
    }
  };

  const openAttemptsMonitor = async (exam: Exam) => {
    try {
      setActiveExam(exam);
      setAttemptsLoading(true);
      setShowAttemptsModal(true);
      const data = await api.getExamAttempts(exam.id);
      setAttemptsList(data);
    } catch (err: any) {
      alert(err.message || "Failed to load examination attempts.");
    } finally {
      setAttemptsLoading(false);
    }
  };

  const openActivityLog = async (attempt: ExamAttemptMonitor) => {
    try {
      setSelectedAttemptInfo(attempt);
      setActivityLoading(true);
      setShowActivityLogModal(true);
      const data = await api.getAttemptViolations(attempt.id);
      setSelectedAttemptViolations(data);
    } catch (err: any) {
      alert(err.message || "Failed to load attempt violations.");
    } finally {
      setActivityLoading(false);
    }
  };

  const handleSaveAssignments = async () => {
    if (!activeExam) return;
    try {
      setAssignLoading(true);
      await api.assignStudentsToExam(activeExam.id, selectedStudentIds);
      setShowAssignModal(false);
      fetchExams();
    } catch (err: any) {
      alert(err.message || "Failed to save student assignments.");
    } finally {
      setAssignLoading(false);
    }
  };

  const handleAddQuestion = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeExam) return;

    try {
      await api.addQuestion(activeExam.id, {
        question_text: qText,
        marks: qMarks,
        explanation: qExplanation,
        order_index: (activeExam.questions?.length || 0) + 1,
        options: options.map((o, idx) => ({
          option_text: o.text,
          is_correct: o.isCorrect,
          order_index: idx + 1,
        })),
      });

      // Reset question inputs
      setQText("");
      setQExplanation("");
      setOptions([
        { text: "", isCorrect: true },
        { text: "", isCorrect: false },
        { text: "", isCorrect: false },
        { text: "", isCorrect: false },
      ]);

      // Refresh active exam questions
      const detailed = await api.getExam(activeExam.id);
      setActiveExam(detailed);
      fetchExams();
    } catch (err: any) {
      alert(err.message || "Failed to add question.");
    }
  };

  const handleDeleteQuestion = async (questionId: number) => {
    if (!activeExam) return;
    try {
      await api.deleteQuestion(questionId);
      const detailed = await api.getExam(activeExam.id);
      setActiveExam(detailed);
      fetchExams();
    } catch (err: any) {
      alert(err.message);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Top Header */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-indigo-600 font-semibold text-xs uppercase tracking-wider mb-1">
            <Layers className="w-4 h-4" />
            <span>Faculty Authoring & Assessment Studio</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900">Examination Management</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Create exams, author questions with secure option keys, configure duration, and review submissions
          </p>
        </div>

        <button
          onClick={() => setShowCreateModal(true)}
          className="inline-flex items-center space-x-2 bg-indigo-600 hover:bg-indigo-700 text-white font-medium px-4 py-2.5 rounded-xl text-sm shadow-sm transition"
        >
          <Plus className="w-4 h-4" />
          <span>New Examination</span>
        </button>
      </div>

      {error && (
        <div className="bg-rose-50 border border-rose-200 text-rose-800 p-4 rounded-xl flex items-center space-x-2 text-sm">
          <AlertCircle className="w-5 h-5 text-rose-500" />
          <span>{error}</span>
        </div>
      )}

      {loading ? (
        <div className="text-center py-16 text-slate-400">Loading authored examinations...</div>
      ) : exams.length === 0 ? (
        <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center max-w-lg mx-auto">
          <Layers className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <h3 className="text-lg font-bold text-slate-800">No Examinations Created Yet</h3>
          <p className="text-sm text-slate-500 mt-1">
            Click the "New Examination" button to author your first secure test paper.
          </p>
        </div>
      ) : (
        <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
          <table className="w-full text-left border-collapse text-sm">
            <thead>
              <tr className="bg-slate-50/80 border-b border-slate-200 text-xs font-bold text-slate-500 uppercase tracking-wider">
                <th className="py-4 px-6">Examination Title</th>
                <th className="py-4 px-6">Duration</th>
                <th className="py-4 px-6">Questions</th>
                <th className="py-4 px-6">Marks (Pass / Total)</th>
                <th className="py-4 px-6">Status</th>
                <th className="py-4 px-6 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {exams.map((exam) => (
                <tr key={exam.id} className="hover:bg-slate-50/50 transition">
                  <td className="py-4 px-6 font-semibold text-slate-900">{exam.title}</td>
                  <td className="py-4 px-6 text-slate-600 font-mono text-xs">{exam.duration_minutes} Mins</td>
                  <td className="py-4 px-6 text-slate-600 font-medium">{exam.question_count || 0}</td>
                  <td className="py-4 px-6 text-slate-600 text-xs">
                    <span className="font-semibold text-slate-800">{exam.passing_marks}</span> / {exam.total_marks}
                  </td>
                  <td className="py-4 px-6">
                    <button
                      onClick={() => handleTogglePublish(exam)}
                      className={`text-xs px-2.5 py-1 rounded-full font-semibold transition ${
                        exam.status === "PUBLISHED"
                          ? "bg-emerald-100 text-emerald-800 hover:bg-emerald-200"
                          : "bg-amber-100 text-amber-800 hover:bg-amber-200"
                      }`}
                    >
                      {exam.status === "PUBLISHED" ? "PUBLISHED" : "DRAFT"}
                    </button>
                  </td>
                  <td className="py-4 px-6 text-right space-x-2">
                    <button
                      onClick={() => openQuestionManager(exam)}
                      title="Manage Questions"
                      className="p-1.5 text-slate-600 hover:text-indigo-600 hover:bg-slate-100 rounded-lg transition"
                    >
                      <Plus className="w-4 h-4 inline" /> Questions
                    </button>
                    <button
                      onClick={() => openPreview(exam)}
                      title="Preview Paper"
                      className="p-1.5 text-slate-600 hover:text-indigo-600 hover:bg-slate-100 rounded-lg transition"
                    >
                      <Eye className="w-4 h-4 inline" /> Preview
                    </button>
                    <button
                      onClick={() => openSubmissions(exam)}
                      title="Candidate Submissions"
                      className="p-1.5 text-slate-600 hover:text-indigo-600 hover:bg-slate-100 rounded-lg transition"
                    >
                      <Users className="w-4 h-4 inline" /> Submissions
                    </button>
                    <button
                      onClick={() => openAttemptsMonitor(exam)}
                      title="Attempts & Proctoring Violations"
                      className="p-1.5 text-slate-600 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition"
                    >
                      <ShieldAlert className="w-4 h-4 inline" /> Proctoring
                    </button>
                    <button
                      onClick={() => openAssignModal(exam)}
                      title="Assign Exam to Students"
                      className="p-1.5 text-slate-600 hover:text-emerald-600 hover:bg-emerald-50 rounded-lg transition"
                    >
                      <UserCheck className="w-4 h-4 inline" /> Assign Students
                    </button>
                    <button
                      onClick={() => handleDeleteExam(exam.id)}
                      title="Delete Exam"
                      className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition"
                    >
                      <Trash2 className="w-4 h-4 inline" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Create Exam Modal */}
      <Modal isOpen={showCreateModal} onClose={() => setShowCreateModal(false)} title="Create New Examination">
        <form onSubmit={handleCreateExam} className="space-y-4 text-sm">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Examination Title
            </label>
            <input
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. CS601: Secure Software Engineering Midterm"
              className="w-full px-3 py-2 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Description & Instructions
            </label>
            <textarea
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Provide instructions regarding duration, negative marking, or topics covered..."
              className="w-full px-3 py-2 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
            />
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Duration (Mins)
              </label>
              <input
                type="number"
                min={1}
                max={360}
                required
                value={durationMinutes}
                onChange={(e) => setDurationMinutes(parseInt(e.target.value, 10))}
                className="w-full px-3 py-2 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Total Marks
              </label>
              <input
                type="number"
                min={1}
                required
                value={totalMarks}
                onChange={(e) => setTotalMarks(parseFloat(e.target.value))}
                className="w-full px-3 py-2 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Passing Marks
              </label>
              <input
                type="number"
                min={0}
                required
                value={passingMarks}
                onChange={(e) => setPassingMarks(parseFloat(e.target.value))}
                className="w-full px-3 py-2 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
              />
            </div>
          </div>

          <div className="pt-4 border-t border-slate-100 flex justify-end space-x-3">
            <button
              type="button"
              onClick={() => setShowCreateModal(false)}
              className="px-4 py-2 rounded-xl border border-slate-300 text-xs font-medium text-slate-700 hover:bg-slate-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-xs font-medium text-white shadow-sm"
            >
              Save Examination
            </button>
          </div>
        </form>
      </Modal>

      {/* Question Management Modal */}
      {activeExam && (
        <Modal
          isOpen={showQuestionModal}
          onClose={() => setShowQuestionModal(false)}
          title={`Question Management: ${activeExam.title}`}
          maxWidth="max-w-3xl"
        >
          <div className="space-y-6 text-sm max-h-[80vh] overflow-y-auto pr-1">
            {/* Existing Questions List */}
            <div className="space-y-3">
              <h4 className="font-bold text-slate-800 text-xs uppercase tracking-wider">
                Existing Questions ({activeExam.questions?.length || 0})
              </h4>
              {(!activeExam.questions || activeExam.questions.length === 0) ? (
                <p className="text-xs text-slate-400 italic">No questions added yet. Author your first question below.</p>
              ) : (
                <div className="space-y-2">
                  {activeExam.questions.map((q, idx) => (
                    <div key={q.id} className="p-3.5 rounded-xl border border-slate-200 bg-slate-50/50 flex items-start justify-between">
                      <div className="space-y-1.5 flex-1 pr-4">
                        <div className="font-semibold text-slate-900 text-xs">
                          {idx + 1}. {q.question_text}
                        </div>
                        <div className="text-[11px] text-slate-500 flex items-center space-x-2">
                          <span className="font-medium text-indigo-600">{q.marks} Mark(s)</span>
                          <span>•</span>
                          <span>{q.options.length} Choices</span>
                        </div>
                      </div>
                      <button
                        onClick={() => handleDeleteQuestion(q.id)}
                        className="text-slate-400 hover:text-rose-600 p-1"
                        title="Delete question"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Author New Question Form */}
            <form onSubmit={handleAddQuestion} className="bg-slate-50 p-5 rounded-xl border border-slate-200 space-y-4">
              <h4 className="font-bold text-slate-800 text-xs uppercase tracking-wider flex items-center space-x-1.5">
                <Plus className="w-3.5 h-3.5 text-indigo-600" />
                <span>Author New Multiple Choice Question</span>
              </h4>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Question Prompt Text
                </label>
                <textarea
                  required
                  rows={2}
                  value={qText}
                  onChange={(e) => setQText(e.target.value)}
                  placeholder="Which cryptographic algorithm provides memory-hard hashing resistant to GPU cracking?"
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-xs"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                    Question Weight (Marks)
                  </label>
                  <input
                    type="number"
                    min={0.1}
                    step={0.5}
                    required
                    value={qMarks}
                    onChange={(e) => setQMarks(parseFloat(e.target.value))}
                    className="w-full px-3 py-1.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-xs"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                    Explanation (Optional)
                  </label>
                  <input
                    type="text"
                    value={qExplanation}
                    onChange={(e) => setQExplanation(e.target.value)}
                    placeholder="Pedagogical solution explanation..."
                    className="w-full px-3 py-1.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-xs"
                  />
                </div>
              </div>

              {/* Options */}
              <div className="space-y-2">
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider">
                  Options (Select exactly one correct option)
                </label>
                {options.map((opt, i) => (
                  <div key={i} className="flex items-center space-x-2">
                    <input
                      type="radio"
                      name="correct_option"
                      checked={opt.isCorrect}
                      onChange={() => {
                        const updated = options.map((o, idx) => ({ ...o, isCorrect: idx === i }));
                        setOptions(updated);
                      }}
                      className="w-4 h-4 text-indigo-600 focus:ring-indigo-500"
                    />
                    <input
                      type="text"
                      required
                      placeholder={`Choice ${String.fromCharCode(65 + i)}`}
                      value={opt.text}
                      onChange={(e) => {
                        const updated = [...options];
                        updated[i].text = e.target.value;
                        setOptions(updated);
                      }}
                      className="flex-1 px-3 py-1.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-xs"
                    />
                  </div>
                ))}
              </div>

              <div className="pt-2 flex justify-end">
                <button
                  type="submit"
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-medium shadow-sm transition"
                >
                  Add Question to Examination
                </button>
              </div>
            </form>
          </div>
        </Modal>
      )}

      {/* Exam Preview Modal */}
      {activeExam && (
        <Modal
          isOpen={showPreviewModal}
          onClose={() => setShowPreviewModal(false)}
          title={`Exam Preview: ${activeExam.title}`}
          maxWidth="max-w-3xl"
        >
          <div className="space-y-6 text-sm max-h-[75vh] overflow-y-auto pr-1">
            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 flex items-center justify-between text-xs">
              <div>
                <span className="text-slate-500">Duration:</span>{" "}
                <span className="font-semibold text-slate-800">{activeExam.duration_minutes} Mins</span>
              </div>
              <div>
                <span className="text-slate-500">Total Marks:</span>{" "}
                <span className="font-semibold text-slate-800">{activeExam.total_marks}</span>
              </div>
              <div>
                <span className="text-slate-500">Passing Threshold:</span>{" "}
                <span className="font-semibold text-slate-800">{activeExam.passing_marks}</span>
              </div>
            </div>

            {(!activeExam.questions || activeExam.questions.length === 0) ? (
              <p className="text-center py-8 text-slate-400">No questions available to preview.</p>
            ) : (
              <div className="space-y-6">
                {activeExam.questions.map((q, idx) => (
                  <div key={q.id} className="p-4 rounded-xl border border-slate-200 bg-white space-y-3">
                    <div className="flex justify-between items-start">
                      <span className="font-bold text-slate-800 text-sm">
                        {idx + 1}. {q.question_text}
                      </span>
                      <span className="bg-slate-100 text-slate-600 text-[11px] px-2 py-0.5 rounded font-mono font-medium">
                        {q.marks} Mark(s)
                      </span>
                    </div>

                    <div className="space-y-1.5 pl-2">
                      {q.options.map((opt, optIdx) => (
                        <div
                          key={opt.id}
                          className={`text-xs p-2 rounded-lg border ${
                            opt.is_correct
                              ? "bg-emerald-50 border-emerald-300 text-emerald-900 font-semibold"
                              : "bg-slate-50 border-slate-200 text-slate-700"
                          }`}
                        >
                          {String.fromCharCode(65 + optIdx)}. {opt.option_text}{" "}
                          {opt.is_correct && <span className="text-emerald-600 text-[10px] ml-1">(Correct Answer)</span>}
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </Modal>
      )}

      {/* Submissions Modal */}
      {activeExam && (
        <Modal
          isOpen={showSubmissionsModal}
          onClose={() => setShowSubmissionsModal(false)}
          title={`Candidate Submissions: ${activeExam.title}`}
          maxWidth="max-w-4xl"
        >
          <div className="space-y-4 max-h-[75vh] overflow-y-auto">
            {submissions.length === 0 ? (
              <p className="text-center py-8 text-slate-400">No candidates have submitted attempts for this exam yet.</p>
            ) : (
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold uppercase tracking-wider">
                    <th className="py-3 px-4">Candidate Name</th>
                    <th className="py-3 px-4">Email</th>
                    <th className="py-3 px-4">Score</th>
                    <th className="py-3 px-4">Percentage</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4">Submission Time</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {submissions.map((sub) => (
                    <tr key={sub.id} className="hover:bg-slate-50/50">
                      <td className="py-3 px-4 font-semibold text-slate-900">{sub.student_name}</td>
                      <td className="py-3 px-4 text-slate-500">{sub.student_email}</td>
                      <td className="py-3 px-4 font-bold text-slate-800">
                        {sub.total_score} / {sub.max_score}
                      </td>
                      <td className="py-3 px-4 font-mono font-semibold text-indigo-600">
                        {sub.percentage.toFixed(1)}%
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 rounded-full font-bold text-[10px] ${
                            sub.passed ? "bg-emerald-100 text-emerald-800" : "bg-rose-100 text-rose-800"
                          }`}
                        >
                          {sub.passed ? "PASSED" : "FAILED"}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-400">
                        {new Date(sub.evaluated_at).toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </Modal>
      )}

      {/* Assign Students Modal */}
      {showAssignModal && activeExam && (
        <Modal
          isOpen={showAssignModal}
          onClose={() => setShowAssignModal(false)}
          title={`Assign Students: ${activeExam.title}`}
          maxWidth="max-w-2xl"
        >
          <div className="space-y-4">
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-3 text-xs text-amber-800 flex items-center justify-between">
              <div>
                <span className="font-bold">Assignment Policy: </span>
                {selectedStudentIds.length === 0 ? (
                  <span>No specific students selected. Exam is <strong>open to all students</strong>.</span>
                ) : (
                  <span>Restricted to <strong>{selectedStudentIds.length}</strong> assigned student(s).</span>
                )}
              </div>
              <div className="space-x-2">
                <button
                  type="button"
                  onClick={() => setSelectedStudentIds(students.map((s) => s.id))}
                  className="px-2 py-1 bg-white border border-amber-300 rounded font-semibold text-amber-800 hover:bg-amber-100 text-xs transition"
                >
                  Select All
                </button>
                <button
                  type="button"
                  onClick={() => setSelectedStudentIds([])}
                  className="px-2 py-1 bg-white border border-amber-300 rounded font-semibold text-amber-800 hover:bg-amber-100 text-xs transition"
                >
                  Clear All
                </button>
              </div>
            </div>

            <div>
              <input
                type="text"
                placeholder="Search students by name or email..."
                value={studentSearch}
                onChange={(e) => setStudentSearch(e.target.value)}
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div className="max-h-[300px] overflow-y-auto border border-slate-200 rounded-xl divide-y divide-slate-100">
              {students.length === 0 ? (
                <p className="p-4 text-center text-xs text-slate-400">Loading enrolled students...</p>
              ) : (
                students
                  .filter(
                    (s) =>
                      s.full_name.toLowerCase().includes(studentSearch.toLowerCase()) ||
                      s.email.toLowerCase().includes(studentSearch.toLowerCase())
                  )
                  .map((student) => {
                    const isChecked = selectedStudentIds.includes(student.id);
                    return (
                      <label
                        key={student.id}
                        className={`flex items-center justify-between px-4 py-3 cursor-pointer transition ${
                          isChecked ? "bg-indigo-50/60" : "hover:bg-slate-50"
                        }`}
                      >
                        <div className="flex items-center space-x-3">
                          <input
                            type="checkbox"
                            checked={isChecked}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setSelectedStudentIds([...selectedStudentIds, student.id]);
                              } else {
                                setSelectedStudentIds(selectedStudentIds.filter((id) => id !== student.id));
                              }
                            }}
                            className="w-4 h-4 rounded text-indigo-600 focus:ring-indigo-500"
                          />
                          <div>
                            <p className="font-semibold text-xs text-slate-900">{student.full_name}</p>
                            <p className="text-[11px] text-slate-500">{student.email}</p>
                          </div>
                        </div>
                        <span
                          className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                            isChecked ? "bg-emerald-100 text-emerald-800" : "bg-slate-100 text-slate-500"
                          }`}
                        >
                          {isChecked ? "ASSIGNED" : "UNASSIGNED"}
                        </span>
                      </label>
                    );
                  })
              )}
            </div>

            <div className="flex justify-end space-x-3 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setShowAssignModal(false)}
                className="px-4 py-2 border border-slate-300 text-slate-700 rounded-xl text-xs font-semibold hover:bg-slate-50 transition"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={assignLoading}
                onClick={handleSaveAssignments}
                className="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold shadow-sm transition disabled:opacity-50"
              >
                {assignLoading ? "Saving..." : "Save Assignments"}
              </button>
            </div>
          </div>
        </Modal>
      )}

      {/* Proctoring & Attempts Monitor Modal */}
      {showAttemptsModal && activeExam && (
        <Modal
          isOpen={showAttemptsModal}
          onClose={() => setShowAttemptsModal(false)}
          title={`Proctoring & Attempts Monitor — ${activeExam.title}`}
        >
          <div className="space-y-4 max-w-4xl w-full">
            <div className="flex items-center justify-between text-xs text-slate-500 bg-slate-50 p-3 rounded-xl border border-slate-200">
              <div>
                <strong>Authoritative Monitor:</strong> Live attempt statuses and anti-cheating violations tracked on the server.
              </div>
              <div className="font-semibold text-slate-700">
                Total Attempts: {attemptsList.length}
              </div>
            </div>

            {attemptsLoading ? (
              <div className="text-center py-12 text-slate-400">Loading student attempts...</div>
            ) : attemptsList.length === 0 ? (
              <div className="text-center py-12 text-slate-400">No attempts recorded for this examination yet.</div>
            ) : (
              <div className="max-h-96 overflow-y-auto border border-slate-200 rounded-xl overflow-hidden">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="bg-slate-100/80 border-b border-slate-200 text-slate-600 font-bold uppercase tracking-wider">
                      <th className="py-3 px-4">Student</th>
                      <th className="py-3 px-4">Attempt ID</th>
                      <th className="py-3 px-4">Status</th>
                      <th className="py-3 px-4">Score</th>
                      <th className="py-3 px-4">Violations</th>
                      <th className="py-3 px-4">Activity Log</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {attemptsList.map((att) => {
                      let badgeColor = "bg-slate-100 text-slate-700";
                      if (att.status === "SUBMITTED") badgeColor = "bg-emerald-100 text-emerald-800";
                      if (att.status === "AUTO_SUBMITTED") badgeColor = "bg-blue-100 text-blue-800";
                      if (att.status === "IN_PROGRESS") badgeColor = "bg-amber-100 text-amber-800";
                      if (att.status === "TERMINATED_FOR_VIOLATION") badgeColor = "bg-rose-100 text-rose-800 font-bold";
                      if (att.status === "EXPIRED") badgeColor = "bg-gray-100 text-gray-700";

                      return (
                        <tr key={att.id} className="hover:bg-slate-50/70 transition">
                          <td className="py-3 px-4">
                            <div className="font-semibold text-slate-900">{att.student_name}</div>
                            <div className="text-[11px] text-slate-400">{att.student_email}</div>
                          </td>
                          <td className="py-3 px-4 font-mono font-medium text-slate-600">#{att.id}</td>
                          <td className="py-3 px-4">
                            <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold ${badgeColor}`}>
                              {att.status}
                            </span>
                          </td>
                          <td className="py-3 px-4 font-semibold text-slate-800">
                            {att.score !== null && att.score !== undefined
                              ? `${att.score} / ${att.max_score} (${att.percentage?.toFixed(1)}%)`
                              : "—"}
                          </td>
                          <td className="py-3 px-4">
                            <span
                              className={`px-2 py-0.5 rounded-md font-bold text-xs ${
                                att.violation_count > 0 ? "bg-rose-100 text-rose-700" : "bg-slate-100 text-slate-500"
                              }`}
                            >
                              {att.violation_count} {att.violation_count === 1 ? "alert" : "alerts"}
                            </span>
                          </td>
                          <td className="py-3 px-4">
                            <button
                              onClick={() => openActivityLog(att)}
                              className="px-2.5 py-1 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-semibold rounded-lg text-[11px] transition"
                            >
                              View Logs
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setShowAttemptsModal(false)}
                className="px-4 py-2 border border-slate-300 rounded-xl text-xs font-semibold text-slate-700 hover:bg-slate-50 transition"
              >
                Close
              </button>
            </div>
          </div>
        </Modal>
      )}

      {/* Attempt Activity & Violation Log Stream Modal */}
      {showActivityLogModal && selectedAttemptInfo && (
        <Modal
          isOpen={showActivityLogModal}
          onClose={() => setShowActivityLogModal(false)}
          title={`Security & Violation Audit: ${selectedAttemptInfo.student_name}`}
        >
          <div className="space-y-4 max-w-2xl w-full">
            <div className="bg-slate-50 border border-slate-200 p-3 rounded-xl text-xs space-y-1 text-slate-600">
              <div className="flex justify-between">
                <span>Attempt ID: <strong>#{selectedAttemptInfo.id}</strong></span>
                <span>Violations Recorded: <strong className="text-rose-600">{selectedAttemptInfo.violation_count}</strong></span>
              </div>
              <div className="flex justify-between">
                <span>Current Status: <strong className="text-slate-800">{selectedAttemptInfo.status}</strong></span>
                {selectedAttemptInfo.termination_reason && (
                  <span className="text-rose-600 font-medium truncate max-w-xs">{selectedAttemptInfo.termination_reason}</span>
                )}
              </div>
            </div>

            {activityLoading ? (
              <div className="text-center py-8 text-slate-400">Loading activity stream...</div>
            ) : selectedAttemptViolations.length === 0 ? (
              <div className="text-center py-8 text-slate-400">No security violations recorded for this attempt.</div>
            ) : (
              <div className="space-y-2.5 max-h-80 overflow-y-auto pr-1">
                {selectedAttemptViolations.map((v) => {
                  let alertBadge = "bg-slate-100 text-slate-700 border-slate-200";
                  if (v.event_type.includes("TERMINATED")) {
                    alertBadge = "bg-rose-50 text-rose-800 border-rose-200 font-bold";
                  } else if (v.event_type.includes("SWITCH") || v.event_type.includes("BLUR") || v.event_type.includes("FULLSCREEN")) {
                    alertBadge = "bg-amber-50 text-amber-800 border-amber-200";
                  } else if (v.event_type.includes("STARTED")) {
                    alertBadge = "bg-emerald-50 text-emerald-800 border-emerald-200";
                  }

                  const timeStr = new Date(v.timestamp).toLocaleTimeString();

                  return (
                    <div
                      key={v.id}
                      className={`p-3 rounded-xl border text-xs flex items-start justify-between space-x-3 ${alertBadge}`}
                    >
                      <div className="space-y-0.5">
                        <div className="flex items-center space-x-2">
                          <span className="font-mono font-bold">{v.event_type}</span>
                          {v.warning_number && v.warning_number > 0 && (
                            <span className="text-[10px] px-1.5 py-0.5 bg-white/70 rounded border font-semibold">
                              Warning #{v.warning_number}
                            </span>
                          )}
                        </div>
                        <p className="text-[11px] text-slate-600 leading-relaxed">{v.details || "Telemetry logged."}</p>
                      </div>
                      <div className="text-right flex-shrink-0 text-[10px] text-slate-400 font-mono">
                        <div>{timeStr}</div>
                        {v.ip_address && <div>IP: {v.ip_address}</div>}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setShowActivityLogModal(false)}
                className="px-4 py-2 border border-slate-300 rounded-xl text-xs font-semibold text-slate-700 hover:bg-slate-50 transition"
              >
                Close Audit
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};

export default FacultyDashboard;

