import React, { useState, useEffect, useRef, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "../services/api";
import {
  Exam,
  AttemptStartResponse,
  StudentAnswerSubmission,
  ExamViolationResponse,
} from "../types";
import { TimerDisplay } from "../components/TimerDisplay";
import { QuestionPalette } from "../components/QuestionPalette";
import { Modal } from "../components/Modal";
import {
  Shield,
  AlertCircle,
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  RotateCcw,
  Maximize2,
  Bookmark,
  Check,
  Loader2,
  Clock,
  BookOpen,
  Lock,
} from "lucide-react";

export const ExamTakingPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  // Mode: "INSTRUCTIONS" or "ACTIVE_EXAM"
  const [examMode, setExamMode] = useState<"INSTRUCTIONS" | "ACTIVE_EXAM">("INSTRUCTIONS");
  const [examMeta, setExamMeta] = useState<Exam | null>(null);
  const [rulesAccepted, setRulesAccepted] = useState<boolean>(false);

  // Active attempt state
  const [attemptData, setAttemptData] = useState<AttemptStartResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Active question index
  const [currentIndex, setCurrentIndex] = useState<number>(0);

  // Selected answers: map of question_id -> selected_option_id
  const [answers, setAnswers] = useState<Record<number, number | null>>({});

  // Marked for review: set of question_ids
  const [markedForReview, setMarkedForReview] = useState<Set<number>>(new Set());

  // Auto-save visual indicator: "saved" | "saving" | "error"
  const [saveStatus, setSaveStatus] = useState<"saved" | "saving" | "error">("saved");

  // Proctored Violation Modal State
  const [warningModalOpen, setWarningModalOpen] = useState<boolean>(false);
  const [currentWarning, setCurrentWarning] = useState<ExamViolationResponse | null>(null);

  // Termination State
  const [isTerminated, setIsTerminated] = useState<boolean>(false);
  const [terminationReason, setTerminationReason] = useState<string>("");

  // Submission modal
  const [showSubmitModal, setShowSubmitModal] = useState<boolean>(false);
  const [submitting, setSubmitting] = useState<boolean>(false);

  // Internal flags to prevent duplicate calls
  const isSubmittedRef = useRef(false);
  const isTerminatedRef = useRef(false);
  const lastViolationTimeRef = useRef<number>(0);

  // Load exam metadata or resume existing attempt
  useEffect(() => {
    const fetchExamInfo = async () => {
      if (!id) return;
      try {
        const examIdNum = parseInt(id, 10);
        // Pre-fetch exam metadata for the instructions page
        const meta = await api.getExam(examIdNum);
        setExamMeta(meta);

        // Attempt silent start or resume (if the student refreshed the page during an active attempt)
        try {
          const attempt = await api.startAttempt(examIdNum);
          if (attempt && attempt.questions && attempt.questions.length > 0) {
            // Restore attempt data
            setAttemptData(attempt);

            // Populate saved answers
            if (attempt.saved_answers && attempt.saved_answers.length > 0) {
              const restoredAnswers: Record<number, number | null> = {};
              const restoredMarked = new Set<number>();
              attempt.saved_answers.forEach((ans) => {
                restoredAnswers[ans.question_id] = ans.selected_option_id;
                if (ans.is_marked_for_review) {
                  restoredMarked.add(ans.question_id);
                }
              });
              setAnswers(restoredAnswers);
              setMarkedForReview(restoredMarked);
            }

            if (attempt.status === "TERMINATED_FOR_VIOLATION" || (attempt.violation_count ?? 0) >= 4) {
              isTerminatedRef.current = true;
              setIsTerminated(true);
              setTerminationReason("Exam terminated due to exceeding the maximum number of allowed violations.");
            } else {
              // If already in progress, switch directly to active exam mode
              setExamMode("ACTIVE_EXAM");
            }
          }
        } catch (attemptErr: any) {
          // If 400/403 with retakes prohibited or terminated
          if (attemptErr.message?.toLowerCase().includes("terminated")) {
            isTerminatedRef.current = true;
            setIsTerminated(true);
            setTerminationReason("Exam terminated due to exceeding the maximum number of allowed violations.");
          } else if (attemptErr.status === 400 || attemptErr.status === 403) {
            setError(attemptErr.message || "You cannot access this examination. Retakes are prohibited.");
          }
        }
      } catch (err: any) {
        setError(err.message || "Failed to load examination details.");
      } finally {
        setLoading(false);
      }
    };

    fetchExamInfo();
  }, [id]);

  // Helper to check if browser is currently in fullscreen
  const isFullscreenActive = () => {
    return !!(
      document.fullscreenElement ||
      (document as any).webkitFullscreenElement ||
      (document as any).mozFullScreenElement ||
      (document as any).msFullscreenElement
    );
  };

  const [isFullscreen, setIsFullscreen] = useState<boolean>(true);

  useEffect(() => {
    const updateFsState = () => {
      setIsFullscreen(isFullscreenActive());
    };
    document.addEventListener("fullscreenchange", updateFsState);
    document.addEventListener("webkitfullscreenchange", updateFsState);
    return () => {
      document.removeEventListener("fullscreenchange", updateFsState);
      document.removeEventListener("webkitfullscreenchange", updateFsState);
    };
  }, []);

  // Request Browser Fullscreen
  const requestFullScreen = async () => {
    try {
      const elem = document.documentElement;
      if (elem.requestFullscreen) {
        await elem.requestFullscreen();
      } else if ((elem as any).webkitRequestFullscreen) {
        await (elem as any).webkitRequestFullscreen();
      } else if ((elem as any).mozRequestFullScreen) {
        await (elem as any).mozRequestFullScreen();
      } else if ((elem as any).msRequestFullscreen) {
        await (elem as any).msRequestFullscreen();
      }
    } catch {
      // Browser may block automatic fullscreen if no direct gesture
    }
  };

  // Exit Fullscreen
  const exitFullScreen = () => {
    try {
      if (document.fullscreenElement && document.exitFullscreen) {
        document.exitFullscreen().catch(() => {});
      }
    } catch {
      // ignore
    }
  };

  // Start Exam Handler from Instructions Page
  const handleStartExam = async () => {
    if (!id || !rulesAccepted) return;

    // 1. Enter Fullscreen Mode directly from user gesture
    await requestFullScreen();

    setLoading(true);
    setError(null);

    try {
      // 2. Start / Initialize Authoritative Session
      const data = await api.startAttempt(parseInt(id, 10));
      setAttemptData(data);

      if (data.saved_answers && data.saved_answers.length > 0) {
        const restoredAnswers: Record<number, number | null> = {};
        const restoredMarked = new Set<number>();
        data.saved_answers.forEach((ans) => {
          restoredAnswers[ans.question_id] = ans.selected_option_id;
          if (ans.is_marked_for_review) {
            restoredMarked.add(ans.question_id);
          }
        });
        setAnswers(restoredAnswers);
        setMarkedForReview(restoredMarked);
      }

      setExamMode("ACTIVE_EXAM");
    } catch (err: any) {
      setError(err.message || "Unable to start examination session.");
    } finally {
      setLoading(false);
    }
  };

  // Centralized Violation Handler (A, B, C, D, E, F, G)
  const isProcessingViolationRef = useRef(false);
  const handleExamViolation = useCallback(
    async (type: "TAB_SWITCH" | "FULLSCREEN_EXIT") => {
      if (
        !attemptData ||
        isSubmittedRef.current ||
        isTerminatedRef.current ||
        examMode !== "ACTIVE_EXAM"
      ) {
        return;
      }

      if (isProcessingViolationRef.current) {
        return;
      }

      // Throttle violation triggers to at least 1.2s apart to prevent duplicate event cascades
      const now = Date.now();
      if (now - lastViolationTimeRef.current < 1200) {
        return;
      }
      lastViolationTimeRef.current = now;
      isProcessingViolationRef.current = true;

      try {
        const details =
          type === "FULLSCREEN_EXIT"
            ? "Candidate exited required full-screen mode."
            : "Candidate switched away from examination tab.";

        // Read server count, increment by 1, log audit event, return updated status
        const res = await api.recordViolation(attemptData.attempt_id, type, details);

        // Update local attempt data with authoritative violation count
        setAttemptData((prev) =>
          prev ? { ...prev, violation_count: res.violation_count } : null
        );

        if (res.is_terminated || res.violation_count >= 4) {
          isTerminatedRef.current = true;
          setIsTerminated(true);
          setTerminationReason(
            res.termination_reason ||
            res.message ||
            "Exam terminated due to exceeding the maximum number of allowed violations."
          );
          setWarningModalOpen(false);
          exitFullScreen();
        } else {
          setCurrentWarning(res);
          setWarningModalOpen(true);
        }
      } catch (err: any) {
        if (
          err?.message?.toLowerCase().includes("terminated") ||
          err?.status === 400 ||
          err?.status === 403
        ) {
          isTerminatedRef.current = true;
          setIsTerminated(true);
          setTerminationReason("Exam terminated due to exceeding the maximum number of allowed violations.");
          setWarningModalOpen(false);
          exitFullScreen();
        }
      } finally {
        isProcessingViolationRef.current = false;
      }
    },
    [attemptData, examMode]
  );

  // Monitoring Listeners: Visibility, Focus/Blur, and Fullscreen Change
  useEffect(() => {
    if (examMode !== "ACTIVE_EXAM" || isSubmittedRef.current || isTerminatedRef.current) return;

    // 1. Visibility Change (Tab Switch / Minimized)
    const handleVisibilityChange = () => {
      if (document.hidden || document.visibilityState === "hidden") {
        handleExamViolation("TAB_SWITCH");
      }
    };

    // 2. Window Blur (Focus Lost / Alt-Tab / App Switching)
    const handleWindowBlur = () => {
      handleExamViolation("TAB_SWITCH");
    };

    // 3. Fullscreen Exit Detection (ESC key or browser exit)
    const handleFullscreenChange = () => {
      if (!isFullscreenActive()) {
        handleExamViolation("FULLSCREEN_EXIT");
      }
    };

    // 4. Keyboard ESC listener for immediate signal
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" || e.code === "Escape") {
        handleExamViolation("FULLSCREEN_EXIT");
      }
    };

    // 5. Page BeforeUnload (Closing window or reloading)
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      e.preventDefault();
      e.returnValue = "Leaving this page will log an exam violation.";
      return e.returnValue;
    };

    document.addEventListener("visibilitychange", handleVisibilityChange);
    window.addEventListener("blur", handleWindowBlur);
    document.addEventListener("fullscreenchange", handleFullscreenChange);
    document.addEventListener("webkitfullscreenchange", handleFullscreenChange);
    window.addEventListener("keydown", handleKeyDown);
    window.addEventListener("beforeunload", handleBeforeUnload);

    return () => {
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      window.removeEventListener("blur", handleWindowBlur);
      document.removeEventListener("fullscreenchange", handleFullscreenChange);
      document.removeEventListener("webkitfullscreenchange", handleFullscreenChange);
      window.removeEventListener("keydown", handleKeyDown);
      window.removeEventListener("beforeunload", handleBeforeUnload);
    };
  }, [examMode, handleExamViolation]);

  // Periodic Heartbeat Sync with Backend (Every 15 Seconds)
  useEffect(() => {
    if (examMode !== "ACTIVE_EXAM" || !attemptData || isSubmittedRef.current || isTerminatedRef.current) return;

    const intervalId = setInterval(async () => {
      try {
        const statusData = await api.getAttemptStatus(attemptData.attempt_id);
        if (statusData.is_terminated || statusData.status === "TERMINATED_FOR_VIOLATION") {
          isTerminatedRef.current = true;
          setIsTerminated(true);
          setTerminationReason("Exam terminated due to exceeding the maximum number of allowed violations.");
          setWarningModalOpen(false);
          exitFullScreen();
        } else if (statusData.status === "AUTO_SUBMITTED" || statusData.remaining_seconds <= 0) {
          isSubmittedRef.current = true;
          exitFullScreen();
          navigate(`/student/results`);
        } else if (statusData.violation_count !== undefined) {
          setAttemptData((prev) => (prev ? { ...prev, violation_count: statusData.violation_count } : null));
        }
      } catch {
        // Network heartbeat retry handled quietly
      }
    }, 15000);

    return () => clearInterval(intervalId);
  }, [examMode, attemptData, navigate]);

  // Handle Option Selection with Real-Time Auto-Save
  const handleSelectOption = async (questionId: number, optionId: number) => {
    if (isTerminatedRef.current || isSubmittedRef.current || !attemptData) return;

    // Immediate optimistic local update
    setAnswers((prev) => ({
      ...prev,
      [questionId]: optionId,
    }));
    setSaveStatus("saving");

    try {
      const isMarked = markedForReview.has(questionId);
      await api.saveAnswer(attemptData.attempt_id, questionId, optionId, isMarked);
      setSaveStatus("saved");
    } catch {
      setSaveStatus("error");
    }
  };

  // Handle Clear Option Selection
  const handleClearOption = async (questionId: number) => {
    if (isTerminatedRef.current || isSubmittedRef.current || !attemptData) return;

    setAnswers((prev) => ({
      ...prev,
      [questionId]: null,
    }));
    setSaveStatus("saving");

    try {
      const isMarked = markedForReview.has(questionId);
      await api.saveAnswer(attemptData.attempt_id, questionId, null, isMarked);
      setSaveStatus("saved");
    } catch {
      setSaveStatus("error");
    }
  };

  // Toggle Mark for Review
  const handleToggleMarkForReview = async (questionId: number) => {
    if (isTerminatedRef.current || isSubmittedRef.current || !attemptData) return;

    const willBeMarked = !markedForReview.has(questionId);
    setMarkedForReview((prev) => {
      const updated = new Set(prev);
      if (willBeMarked) {
        updated.add(questionId);
      } else {
        updated.delete(questionId);
      }
      return updated;
    });

    setSaveStatus("saving");
    try {
      const currentOptId = answers[questionId] ?? null;
      await api.saveAnswer(attemptData.attempt_id, questionId, currentOptId, willBeMarked);
      setSaveStatus("saved");
    } catch {
      setSaveStatus("error");
    }
  };

  // Submit Exam
  const handleSubmitExam = async () => {
    if (!attemptData || isSubmittedRef.current || isTerminatedRef.current) return;
    isSubmittedRef.current = true;
    setSubmitting(true);

    try {
      const payload: StudentAnswerSubmission[] = Object.entries(answers).map(([qId, optId]) => ({
        question_id: parseInt(qId, 10),
        selected_option_id: optId,
      }));

      const result = await api.submitAttempt(attemptData.attempt_id, payload);
      exitFullScreen();
      navigate(`/student/results?highlight=${result.id}`);
    } catch (err: any) {
      setError(err.message || "Failed to submit examination.");
      isSubmittedRef.current = false;
    } finally {
      setSubmitting(false);
      setShowSubmitModal(false);
    }
  };

  // Handle Server-Authoritative Timer Expiry
  const handleTimerExpire = () => {
    if (!isSubmittedRef.current && !isTerminatedRef.current) {
      handleSubmitExam();
    }
  };

  // ==========================================
  // VIEW 1: LOADING STATE
  // ==========================================
  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex flex-col items-center justify-center space-y-4 text-white p-6">
        <div className="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-base font-semibold text-slate-300">Initializing Authoritative Security Session...</p>
        <span className="text-xs text-slate-500">Checking proctoring integrity and server clock synchronization</span>
      </div>
    );
  }

  // ==========================================
  // VIEW 2: ERROR OR LOCKOUT
  // ==========================================
  if (error) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center p-6">
        <div className="max-w-lg w-full bg-slate-800 border border-slate-700 rounded-3xl p-8 text-center space-y-5 shadow-2xl">
          <div className="w-16 h-16 bg-rose-500/10 border border-rose-500/20 text-rose-400 rounded-2xl flex items-center justify-center mx-auto">
            <AlertCircle className="w-8 h-8" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-white">Examination Access Blocked</h3>
            <p className="text-sm text-slate-400 mt-2 leading-relaxed">{error}</p>
          </div>
          <button
            onClick={() => navigate("/student")}
            className="w-full py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-sm font-semibold transition"
          >
            Return to Student Dashboard
          </button>
        </div>
      </div>
    );
  }

  // ==========================================
  // VIEW 3: TERMINATED FOR VIOLATIONS
  // ==========================================
  if (isTerminated) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center p-6">
        <div className="max-w-xl w-full bg-slate-900 border border-rose-600/40 rounded-3xl p-8 text-center space-y-6 shadow-2xl">
          <div className="w-20 h-20 bg-rose-600/20 border border-rose-500 text-rose-400 rounded-3xl flex items-center justify-center mx-auto animate-pulse">
            <Lock className="w-10 h-10" />
          </div>
          <div className="space-y-2">
            <span className="px-3 py-1 bg-rose-500/20 text-rose-400 border border-rose-500/30 rounded-full text-xs font-bold uppercase tracking-wider">
              Security Violation Lockout
            </span>
            <h2 className="text-2xl font-bold text-white">Examination Terminated</h2>
            <p className="text-sm text-slate-300 leading-relaxed max-w-md mx-auto">
              Exam terminated due to exceeding the maximum number of allowed violations.
            </p>
          </div>

          <div className="bg-slate-800/80 border border-slate-700 p-4 rounded-2xl text-left text-xs space-y-2 text-slate-300">
            <div className="font-semibold text-rose-400 uppercase tracking-wider text-[10px]">Official Record:</div>
            <div>
              <span className="text-slate-500">Reason:</span> {terminationReason || "Exam terminated due to exceeding the maximum number of allowed violations."}
            </div>
            <div>
              <span className="text-slate-500">Attempt Status:</span>{" "}
              <strong className="text-rose-400">TERMINATED_FOR_VIOLATION</strong>
            </div>
            <div>
              <span className="text-slate-500">Answers:</span> Automatically sealed and submitted for faculty audit. Retakes are prohibited.
            </div>
          </div>

          <button
            onClick={() => navigate("/student/results")}
            className="w-full py-3.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-sm font-semibold transition shadow-lg shadow-indigo-600/20"
          >
            View Evaluation & Results
          </button>
        </div>
      </div>
    );
  }

  // ==========================================
  // VIEW 4: EXAM INSTRUCTIONS PAGE
  // ==========================================
  if (examMode === "INSTRUCTIONS") {
    const meta = examMeta;
    return (
      <div className="min-h-screen bg-slate-900 text-slate-100 flex items-center justify-center p-4 sm:p-6 lg:p-8">
        <div className="max-w-3xl w-full bg-slate-800 border border-slate-700 rounded-3xl p-6 sm:p-10 shadow-2xl space-y-8">
          {/* Header */}
          <div className="flex items-start justify-between border-b border-slate-700/80 pb-6">
            <div className="space-y-1">
              <div className="flex items-center space-x-2 text-xs font-semibold text-indigo-400 uppercase tracking-wider">
                <Shield className="w-4 h-4" />
                <span>SecureExam &bull; Proctored Environment</span>
              </div>
              <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">{meta?.title || "Examination"}</h1>
              {meta?.description && <p className="text-sm text-slate-400 pt-1">{meta.description}</p>}
            </div>
            <button
              onClick={() => navigate("/student")}
              className="px-3.5 py-1.5 rounded-xl border border-slate-700 text-xs font-medium text-slate-400 hover:text-white hover:bg-slate-700/50 transition"
            >
              Exit
            </button>
          </div>

          {/* Exam Parameter Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
            <div className="bg-slate-900/70 border border-slate-700/60 p-4 rounded-2xl">
              <div className="flex items-center space-x-1.5 text-slate-400 text-xs mb-1">
                <Clock className="w-3.5 h-3.5 text-indigo-400" />
                <span>Duration</span>
              </div>
              <div className="text-lg font-bold text-white">{meta?.duration_minutes || 30} mins</div>
            </div>

            <div className="bg-slate-900/70 border border-slate-700/60 p-4 rounded-2xl">
              <div className="flex items-center space-x-1.5 text-slate-400 text-xs mb-1">
                <BookOpen className="w-3.5 h-3.5 text-indigo-400" />
                <span>Questions</span>
              </div>
              <div className="text-lg font-bold text-white">{meta?.question_count || meta?.questions?.length || 0} Questions</div>
            </div>

            <div className="bg-slate-900/70 border border-slate-700/60 p-4 rounded-2xl">
              <div className="flex items-center space-x-1.5 text-slate-400 text-xs mb-1">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                <span>Total Marks</span>
              </div>
              <div className="text-lg font-bold text-white">{meta?.total_marks || 100} Marks</div>
            </div>

            <div className="bg-slate-900/70 border border-slate-700/60 p-4 rounded-2xl">
              <div className="flex items-center space-x-1.5 text-slate-400 text-xs mb-1">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                <span>Negative Marking</span>
              </div>
              <div className="text-lg font-bold text-white">
                {meta?.enable_negative_marking ? (
                  <span className="text-rose-400">Active (-25%)</span>
                ) : (
                  <span className="text-emerald-400">None</span>
                )}
              </div>
            </div>
          </div>

          {/* Exam Rules & Anti-Cheating Checklist */}
          <div className="space-y-4">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-300">
              Mandatory Code of Conduct & Anti-Cheating Policy
            </h3>
            <div className="bg-slate-900/80 border border-slate-700/80 rounded-2xl p-5 space-y-3.5 text-xs text-slate-300 leading-relaxed">
              <div className="flex items-start space-x-3">
                <div className="w-5 h-5 rounded-full bg-indigo-500/20 text-indigo-400 flex items-center justify-center flex-shrink-0 mt-0.5 font-bold text-[10px]">
                  1
                </div>
                <div>
                  <strong className="text-white">Strict Full-Screen Requirement:</strong> The exam must be taken in dedicated
                  browser full-screen mode. Exiting full-screen is monitored and counts as a violation.
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <div className="w-5 h-5 rounded-full bg-indigo-500/20 text-indigo-400 flex items-center justify-center flex-shrink-0 mt-0.5 font-bold text-[10px]">
                  2
                </div>
                <div>
                  <strong className="text-white">Tab Switch & Window Focus Policy:</strong> Leaving the exam tab, switching
                  windows, or minimizing the browser generates immediate server-logged warnings. A maximum of{" "}
                  <strong className="text-amber-300">3 warnings</strong> are permitted. The 4th violation permanently terminates
                  your exam.
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <div className="w-5 h-5 rounded-full bg-indigo-500/20 text-indigo-400 flex items-center justify-center flex-shrink-0 mt-0.5 font-bold text-[10px]">
                  3
                </div>
                <div>
                  <strong className="text-white">Authoritative Server Timer:</strong> The countdown clock is managed by the backend
                  server. Refreshing or reopening your browser does not reset or pause the timer.
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <div className="w-5 h-5 rounded-full bg-indigo-500/20 text-indigo-400 flex items-center justify-center flex-shrink-0 mt-0.5 font-bold text-[10px]">
                  4
                </div>
                <div>
                  <strong className="text-white">Real-Time Auto-Save:</strong> All answers are immediately saved to the server as you
                  select them. If your network temporarily disconnects, your progress is preserved.
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <div className="w-5 h-5 rounded-full bg-indigo-500/20 text-indigo-400 flex items-center justify-center flex-shrink-0 mt-0.5 font-bold text-[10px]">
                  5
                </div>
                <div>
                  <strong className="text-white">Single Attempt Policy:</strong> Once submitted, auto-submitted, or terminated for
                  violations, the exam is locked permanently. No retakes are permitted.
                </div>
              </div>
            </div>
          </div>

          {/* Explicit Rules Acceptance Checkbox */}
          <div className="pt-2">
            <label className="flex items-start space-x-3 cursor-pointer group">
              <input
                type="checkbox"
                checked={rulesAccepted}
                onChange={(e) => setRulesAccepted(e.target.checked)}
                className="w-5 h-5 mt-0.5 rounded border-slate-600 bg-slate-900 text-indigo-600 focus:ring-indigo-500 focus:ring-offset-slate-800 transition cursor-pointer"
              />
              <span className="text-xs text-slate-300 group-hover:text-white transition leading-normal">
                I have read, understood, and accept all the examination rules and anti-cheating policies. I agree to enter
                full-screen proctored mode and accept server-authoritative termination in the event of repeated violations.
              </span>
            </label>
          </div>

          {/* Action Button */}
          <div className="pt-2 flex flex-col sm:flex-row items-center justify-between gap-4">
            <span className="text-xs text-slate-400">
              {rulesAccepted ? "Ready to begin proctored session." : "Accept rules to unlock start button."}
            </span>
            <button
              onClick={handleStartExam}
              disabled={!rulesAccepted}
              className="w-full sm:w-auto px-8 py-3.5 rounded-2xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:hover:bg-indigo-600 text-white font-bold text-sm shadow-xl shadow-indigo-600/30 transition flex items-center justify-center space-x-2"
            >
              <Maximize2 className="w-4 h-4" />
              <span>Enter Full-Screen & Start Exam</span>
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ==========================================
  // VIEW 5: ACTIVE PROCTORED EXAM ENVIRONMENT
  // ==========================================
  if (!attemptData) return null;

  const questions = attemptData.questions || [];
  const currentQuestion = questions[currentIndex];

  // Set of indices that have been answered
  const answeredIndices = new Set<number>();
  const markedIndices = new Set<number>();
  questions.forEach((q, idx) => {
    if (answers[q.id] !== undefined && answers[q.id] !== null) {
      answeredIndices.add(idx);
    }
    if (markedForReview.has(q.id)) {
      markedIndices.add(idx);
    }
  });

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Dedicated Exam Top Navigation Bar */}
      <header className="bg-slate-900/95 border-b border-slate-800 sticky top-0 z-30 px-4 sm:px-8 py-3.5 flex items-center justify-between shadow-md">
        <div className="flex items-center space-x-3.5">
          <div className="w-9 h-9 rounded-xl bg-indigo-600/20 border border-indigo-500/40 text-indigo-400 flex items-center justify-center">
            <Shield className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                Live Proctored
              </span>
              {attemptData.enable_negative_marking && (
                <span className="text-[10px] font-bold uppercase tracking-wider text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded-full border border-amber-500/20">
                  Negative Marking
                </span>
              )}
            </div>
            <h2 className="text-sm sm:text-base font-bold text-white truncate max-w-xs sm:max-w-md">
              {attemptData.exam_title}
            </h2>
          </div>
        </div>

        {/* Center: Live Auto-Save Status */}
        <div className="hidden sm:flex items-center space-x-2 text-xs px-3 py-1.5 rounded-xl bg-slate-800/80 border border-slate-700">
          {saveStatus === "saving" && (
            <>
              <Loader2 className="w-3.5 h-3.5 text-indigo-400 animate-spin" />
              <span className="text-slate-300">Saving...</span>
            </>
          )}
          {saveStatus === "saved" && (
            <>
              <Check className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-slate-300">Saved</span>
            </>
          )}
          {saveStatus === "error" && (
            <>
              <AlertCircle className="w-3.5 h-3.5 text-amber-400" />
              <span className="text-amber-300">Unable to save — retrying...</span>
            </>
          )}
        </div>

        {/* Right: Authoritative Timer & Fullscreen & Submit */}
        <div className="flex items-center space-x-2 sm:space-x-3">
          <TimerDisplay expiresAt={attemptData.expires_at} onExpire={handleTimerExpire} />

          <button
            onClick={requestFullScreen}
            title={isFullscreen ? "Full-screen Active" : "Enter Full-screen"}
            className={`p-2 rounded-xl border text-xs transition flex items-center space-x-1 ${
              isFullscreen
                ? "bg-slate-800 text-slate-400 border-slate-700 hover:text-white"
                : "bg-amber-500/20 text-amber-300 border-amber-500/40 hover:bg-amber-500/30 animate-pulse"
            }`}
          >
            <Maximize2 className="w-4 h-4" />
          </button>

          <button
            onClick={() => setShowSubmitModal(true)}
            className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow-md transition flex items-center space-x-1.5"
          >
            <CheckCircle2 className="w-4 h-4" />
            <span>Finish & Submit</span>
          </button>
        </div>
      </header>

      {/* Full-Screen Alert Banner if browser exits fullscreen */}
      {!isFullscreen && (
        <div className="bg-amber-500/10 border-b border-amber-500/30 px-4 sm:px-8 py-2.5 flex items-center justify-between text-xs text-amber-300">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0" />
            <span>Full-screen mode is required for this examination.</span>
          </div>
          <button
            onClick={requestFullScreen}
            className="px-3.5 py-1 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold rounded-lg transition text-xs flex items-center space-x-1 shadow-sm"
          >
            <Maximize2 className="w-3.5 h-3.5" />
            <span>Re-Enter Full-Screen</span>
          </button>
        </div>
      )}

      {/* Main Examination Grid */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8 grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Left 3 Columns: Active Question Card */}
        <div className="lg:col-span-3 bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-xl flex flex-col justify-between min-h-[540px]">
          {currentQuestion ? (
            <div className="space-y-6">
              {/* Question Header */}
              <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                    Question {currentIndex + 1} of {questions.length}
                  </span>
                  {markedForReview.has(currentQuestion.id) && (
                    <span className="flex items-center space-x-1 text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/40">
                      <Bookmark className="w-3 h-3" />
                      <span>Marked for Review</span>
                    </span>
                  )}
                </div>

                <span className="text-xs font-semibold px-2.5 py-1 rounded-xl bg-slate-800 text-slate-300 border border-slate-700">
                  {currentQuestion.marks} {currentQuestion.marks === 1 ? "Mark" : "Marks"}
                </span>
              </div>

              {/* Question Text */}
              <div className="text-base sm:text-lg font-medium text-slate-100 leading-relaxed">
                {currentQuestion.question_text}
              </div>

              {/* Options List */}
              <div className="space-y-3 pt-2">
                {currentQuestion.options.map((opt, optIdx) => {
                  const isSelected = answers[currentQuestion.id] === opt.id;
                  const letter = String.fromCharCode(65 + optIdx);

                  return (
                    <div
                      key={opt.id}
                      onClick={() => handleSelectOption(currentQuestion.id, opt.id)}
                      className={`flex items-start space-x-3.5 p-4 rounded-2xl border cursor-pointer transition-all ${
                        isSelected
                          ? "bg-indigo-600/20 border-indigo-500 text-white ring-1 ring-indigo-500 shadow-md"
                          : "bg-slate-800/70 border-slate-700/80 text-slate-300 hover:bg-slate-800 hover:border-slate-600"
                      }`}
                    >
                      <div
                        className={`w-7 h-7 rounded-xl font-bold text-xs flex items-center justify-center flex-shrink-0 mt-0.5 border ${
                          isSelected
                            ? "bg-indigo-600 text-white border-indigo-500"
                            : "bg-slate-700/60 text-slate-400 border-slate-600"
                        }`}
                      >
                        {letter}
                      </div>
                      <div className="text-sm font-medium leading-normal pt-1">{opt.option_text}</div>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : (
            <div className="text-center py-20 text-slate-500">No questions available in this test.</div>
          )}

          {/* Navigation and Action Bar */}
          <div className="mt-8 pt-4 border-t border-slate-800 flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setCurrentIndex((prev) => Math.max(0, prev - 1))}
                disabled={currentIndex === 0}
                className="px-4 py-2.5 rounded-xl border border-slate-700 text-slate-300 hover:bg-slate-800 disabled:opacity-40 disabled:hover:bg-transparent text-xs font-semibold transition flex items-center space-x-1.5"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>Previous</span>
              </button>

              {currentQuestion && (
                <button
                  onClick={() => handleToggleMarkForReview(currentQuestion.id)}
                  className={`px-4 py-2.5 rounded-xl border text-xs font-semibold transition flex items-center space-x-1.5 ${
                    markedForReview.has(currentQuestion.id)
                      ? "bg-purple-600/30 border-purple-500 text-purple-300"
                      : "border-slate-700 text-slate-400 hover:text-slate-200 hover:bg-slate-800"
                  }`}
                >
                  <Bookmark className="w-3.5 h-3.5" />
                  <span>{markedForReview.has(currentQuestion.id) ? "Unmark Review" : "Mark for Review"}</span>
                </button>
              )}

              {currentQuestion && answers[currentQuestion.id] !== null && answers[currentQuestion.id] !== undefined && (
                <button
                  onClick={() => handleClearOption(currentQuestion.id)}
                  className="px-3.5 py-2.5 rounded-xl text-xs font-medium text-slate-400 hover:text-slate-200 hover:bg-slate-800/80 transition flex items-center space-x-1"
                >
                  <RotateCcw className="w-3 h-3" />
                  <span>Clear Answer</span>
                </button>
              )}
            </div>

            <div>
              {currentIndex < questions.length - 1 ? (
                <button
                  onClick={() => setCurrentIndex((prev) => Math.min(questions.length - 1, prev + 1))}
                  className="px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow-md transition flex items-center space-x-1.5"
                >
                  <span>Next Question</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              ) : (
                <button
                  onClick={() => setShowSubmitModal(true)}
                  className="px-6 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow-md transition flex items-center space-x-1.5"
                >
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Review & Submit</span>
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Right 1 Column: Question Navigation Palette & Proctoring Status */}
        <div className="space-y-6">
          <QuestionPalette
            totalQuestions={questions.length}
            currentIndex={currentIndex}
            answeredIndices={answeredIndices}
            markedIndices={markedIndices}
            onSelectQuestion={(idx) => setCurrentIndex(idx)}
          />

          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 text-xs text-slate-400 space-y-3">
            <div className="flex items-center space-x-2 text-indigo-400 font-bold uppercase tracking-wider text-[11px]">
              <Shield className="w-4 h-4" />
              <span>Active Proctoring</span>
            </div>
            <p className="leading-relaxed">
              Full-screen status, window focus, and tab-switch telemetry are actively tracked and authoritative on the
              backend. Leaving this window counts toward policy violations.
            </p>
          </div>
        </div>
      </main>

      {/* Warning Violation Modal (Warnings 1, 2, 3) */}
      <Modal
        isOpen={warningModalOpen && !isTerminated}
        onClose={async () => {
          setWarningModalOpen(false);
          await requestFullScreen();
        }}
        title="Anti-Cheating Policy Warning"
      >
        <div className="space-y-4 text-slate-700">
          <div className="flex items-center space-x-3 bg-amber-50 border border-amber-200 p-3.5 rounded-2xl text-amber-800">
            <AlertTriangle className="w-6 h-6 flex-shrink-0 text-amber-600" />
            <div>
              <div className="font-bold text-sm">
                Security Warning {currentWarning?.warning_level || (attemptData?.violation_count ?? 1)} of 3
              </div>
              <div className="text-xs text-amber-700 mt-0.5">
                {currentWarning?.message || "You left the examination window or exited full-screen."}
              </div>
            </div>
          </div>

          <p className="text-xs text-slate-600 leading-relaxed">
            Examination rules require continuous focus in full-screen mode. This infraction has been logged immutably on the
            server. <strong>A total of 3 warnings are permitted. A 4th violation will immediately terminate your exam.</strong>
          </p>

          <div className="pt-2 flex justify-end">
            <button
              onClick={async () => {
                setWarningModalOpen(false);
                await requestFullScreen();
              }}
              className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold transition flex items-center space-x-1.5 shadow-md"
            >
              <Maximize2 className="w-3.5 h-3.5" />
              <span>Acknowledge & Return to Full-Screen</span>
            </button>
          </div>
        </div>
      </Modal>

      {/* Submission Confirmation Modal */}
      <Modal
        isOpen={showSubmitModal}
        onClose={() => setShowSubmitModal(false)}
        title="Confirm Examination Submission"
      >
        <div className="space-y-4 text-sm text-slate-700">
          <p className="text-slate-600">
            You are about to submit your examination answers for official grading. Please review your attempt summary:
          </p>

          <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200 space-y-2 text-xs">
            <div className="flex justify-between">
              <span className="text-slate-500">Total Questions:</span>
              <span className="font-bold text-slate-800">{questions.length}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Answered Questions:</span>
              <span className="font-bold text-emerald-700">{answeredIndices.size}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Marked for Review:</span>
              <span className="font-bold text-purple-700">{markedIndices.size}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Unanswered Questions:</span>
              <span className="font-bold text-amber-700">{questions.length - answeredIndices.size}</span>
            </div>
          </div>

          <div className="text-xs text-rose-600 font-semibold bg-rose-50 border border-rose-200 p-3 rounded-xl">
            Important: Once confirmed, your answers will be sealed and scored on the server. You cannot reopen or retake this examination.
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
              className="px-6 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-xs font-bold text-white rounded-xl shadow-md flex items-center space-x-1.5"
            >
              <span>{submitting ? "Sealing & Scoring..." : "Confirm & Submit"}</span>
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default ExamTakingPage;
