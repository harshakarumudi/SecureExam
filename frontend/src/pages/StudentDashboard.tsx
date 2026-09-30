import React, { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Exam } from "../types";
import { api } from "../services/api";
import { Modal } from "../components/Modal";
import { BookOpen, Clock, Award, AlertCircle, ArrowRight, FileText } from "lucide-react";

export const StudentDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [exams, setExams] = useState<Exam[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Instructions Modal state
  const [selectedExam, setSelectedExam] = useState<Exam | null>(null);

  useEffect(() => {
    const fetchAvailableExams = async () => {
      try {
        const data = await api.getAvailableExams();
        setExams(data);
      } catch (err: any) {
        setError(err.message || "Failed to load available examinations.");
      } finally {
        setLoading(false);
      }
    };
    fetchAvailableExams();
  }, []);

  const handleStartExam = (examId: number) => {
    navigate(`/student/exam/${examId}`);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Top Banner */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-indigo-600 font-semibold text-xs uppercase tracking-wider mb-1">
            <BookOpen className="w-4 h-4" />
            <span>Candidate Examination Portal</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900">Available Examinations</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Active, published tests available for formal evaluation
          </p>
        </div>

        <div>
          <Link
            to="/student/results"
            className="inline-flex items-center space-x-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium px-4 py-2.5 rounded-xl text-sm transition"
          >
            <Award className="w-4 h-4 text-indigo-600" />
            <span>View My Past Results</span>
          </Link>
        </div>
      </div>

      {error && (
        <div className="bg-rose-50 border border-rose-200 text-rose-800 p-4 rounded-xl flex items-center space-x-3 text-sm">
          <AlertCircle className="w-5 h-5 text-rose-500" />
          <span>{error}</span>
        </div>
      )}

      {loading ? (
        <div className="text-center py-16 text-slate-400">Loading active examinations...</div>
      ) : exams.length === 0 ? (
        <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center max-w-lg mx-auto">
          <FileText className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <h3 className="text-lg font-bold text-slate-800">No Examinations Available</h3>
          <p className="text-sm text-slate-500 mt-1">
            There are currently no published examinations open for testing. Please check back later.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {exams.map((exam) => (
            <div
              key={exam.id}
              className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm hover:shadow-md transition flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-semibold bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded-full uppercase tracking-wider">
                    Published & Active
                  </span>
                  <div className="flex items-center space-x-1 text-slate-500 text-xs font-mono font-medium">
                    <Clock className="w-3.5 h-3.5" />
                    <span>{exam.duration_minutes} Mins</span>
                  </div>
                </div>

                <h3 className="text-lg font-bold text-slate-900 line-clamp-1">{exam.title}</h3>
                <p className="text-xs text-slate-500 line-clamp-2">
                  {exam.description || "No specific instructions provided."}
                </p>

                <div className="pt-2 border-t border-slate-100 grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <span className="text-slate-400">Total Marks:</span>
                    <span className="ml-1 font-semibold text-slate-700">{exam.total_marks}</span>
                  </div>
                  <div>
                    <span className="text-slate-400">Passing Threshold:</span>
                    <span className="ml-1 font-semibold text-slate-700">{exam.passing_marks}</span>
                  </div>
                </div>
              </div>

              <div className="mt-6 pt-4 border-t border-slate-100 flex items-center space-x-3">
                <button
                  onClick={() => setSelectedExam(exam)}
                  className="flex-1 bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium py-2 rounded-xl text-xs transition"
                >
                  Instructions
                </button>
                <button
                  onClick={() => handleStartExam(exam.id)}
                  className="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-2 rounded-xl text-xs shadow-sm transition flex items-center justify-center space-x-1"
                >
                  <span>Start Exam</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Exam Instructions Modal */}
      {selectedExam && (
        <Modal
          isOpen={!!selectedExam}
          onClose={() => setSelectedExam(null)}
          title={`Exam Instructions: ${selectedExam.title}`}
        >
          <div className="space-y-4 text-sm text-slate-600">
            <div className="bg-amber-50 border border-amber-200 text-amber-900 p-4 rounded-xl text-xs space-y-1">
              <div className="font-bold flex items-center space-x-1.5">
                <AlertCircle className="w-4 h-4 text-amber-600 flex-shrink-0" />
                <span>Authoritative Security Policy Notice</span>
              </div>
              <p>
                Once initiated, your examination session will be locked to an authoritative server-side countdown timer.
                Submissions received after the hard expiration window will be rejected.
              </p>
            </div>

            <div>
              <h4 className="font-semibold text-slate-800 mb-1">Key Examination Parameters:</h4>
              <ul className="list-disc list-inside space-y-1 text-xs text-slate-600">
                <li>Duration: <strong>{selectedExam.duration_minutes} minutes</strong></li>
                <li>Total Available Points: <strong>{selectedExam.total_marks}</strong></li>
                <li>Passing Requirement: <strong>{selectedExam.passing_marks} points</strong></li>
                <li>Question Format: Single Answer Multiple Choice (MCQ)</li>
              </ul>
            </div>

            <div>
              <h4 className="font-semibold text-slate-800 mb-1">Integrity Rules:</h4>
              <p className="text-xs leading-relaxed text-slate-500">
                Do not navigate away from the testing room or attempt client-side script manipulation. All transactions,
                selections, and submission timestamps are logged in an immutable security audit trail.
              </p>
            </div>

            <div className="pt-4 border-t border-slate-100 flex justify-end space-x-3">
              <button
                onClick={() => setSelectedExam(null)}
                className="px-4 py-2 rounded-xl border border-slate-300 text-xs font-medium text-slate-700 hover:bg-slate-50"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  const id = selectedExam.id;
                  setSelectedExam(null);
                  handleStartExam(id);
                }}
                className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-xs font-medium text-white shadow-sm"
              >
                Acknowledge & Begin Exam
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};

