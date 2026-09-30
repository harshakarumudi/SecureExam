import React, { useState, useEffect } from "react";
import { Exam, Result } from "../types";
import { api } from "../services/api";
import { Modal } from "../components/Modal";
import {
  Layers,
  Plus,
  Eye,
  Trash2,
  Users,
  AlertCircle,
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

  // Active selected exam
  const [activeExam, setActiveExam] = useState<Exam | null>(null);
  const [submissions, setSubmissions] = useState<Result[]>([]);

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
    </div>
  );
};

