import {
  User,
  Exam,
  ExamAssignment,
  AttemptStartResponse,
  StudentAnswerSubmission,
  Result,
  AuditLog,
  UserRole,
} from "../types";

const API_BASE = "/api/v1";

class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem("token");
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail = `Request failed with status ${response.status}`;
    try {
      const errJson = await response.json();
      if (errJson.detail) {
        errorDetail = typeof errJson.detail === "string" ? errJson.detail : JSON.stringify(errJson.detail);
      }
    } catch {
      // ignore
    }
    throw new ApiError(errorDetail, response.status);
  }

  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

export const api = {
  // Auth
  login: (email: string, password: string) =>
    request<{ access_token: string; token_type: string; user: User }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  register: (email: string, full_name: string, password: string, role?: UserRole) =>
    request<User>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, full_name, password, role }),
    }),

  getMe: () => request<User>("/auth/me"),

  logout: () =>
    request<{ message: string }>("/auth/logout", {
      method: "POST",
    }),

  // Exams
  getExams: () => request<Exam[]>("/exams/"),

  getAvailableExams: () => request<Exam[]>("/exams/available"),

  getExam: (id: number) => request<Exam>(`/exams/${id}`),

  createExam: (exam: {
    title: string;
    description?: string;
    duration_minutes: number;
    total_marks: number;
    passing_marks: number;
    start_time?: string;
    end_time?: string;
  }) =>
    request<Exam>("/exams/", {
      method: "POST",
      body: JSON.stringify(exam),
    }),

  updateExam: (id: number, exam: Partial<Exam>) =>
    request<Exam>(`/exams/${id}`, {
      method: "PUT",
      body: JSON.stringify(exam),
    }),

  deleteExam: (id: number) =>
    request<void>(`/exams/${id}`, {
      method: "DELETE",
    }),

  addQuestion: (
    examId: number,
    question: {
      question_text: string;
      marks: number;
      negative_marks?: number;
      explanation?: string;
      order_index: number;
      options: { option_text: string; is_correct: boolean; order_index: number }[];
    }
  ) =>
    request<any>(`/exams/${examId}/questions`, {
      method: "POST",
      body: JSON.stringify(question),
    }),

  deleteQuestion: (questionId: number) =>
    request<void>(`/exams/questions/${questionId}`, {
      method: "DELETE",
    }),

  // Exam Assignments
  getExamAssignments: (examId: number) =>
    request<ExamAssignment[]>(`/exams/${examId}/assignments`),

  assignStudentsToExam: (examId: number, studentIds: number[]) =>
    request<ExamAssignment[]>(`/exams/${examId}/assignments`, {
      method: "POST",
      body: JSON.stringify({ student_ids: studentIds }),
    }),

  getStudents: () => request<User[]>("/users/students"),

  // Attempts
  startAttempt: (examId: number) =>
    request<AttemptStartResponse>(`/attempts/start/${examId}`, {
      method: "POST",
    }),

  saveAnswer: (
    attemptId: number,
    questionId: number,
    selectedOptionId: number | null,
    isMarkedForReview: boolean = false
  ) =>
    request<import("../types").AnswerAutoSaveResponse>(`/attempts/${attemptId}/save-answer`, {
      method: "POST",
      body: JSON.stringify({
        question_id: questionId,
        selected_option_id: selectedOptionId,
        is_marked_for_review: isMarkedForReview,
      }),
    }),

  recordViolation: (
    attemptId: number,
    eventType: string,
    details?: string
  ) =>
    request<import("../types").ExamViolationResponse>(`/attempts/${attemptId}/violation`, {
      method: "POST",
      body: JSON.stringify({
        event_type: eventType,
        details,
      }),
    }),

  getAttemptStatus: (attemptId: number) =>
    request<import("../types").AttemptStatusResponse>(`/attempts/${attemptId}/status`),

  getAttemptViolations: (attemptId: number) =>
    request<import("../types").ExamViolationItem[]>(`/attempts/${attemptId}/violations`),

  getExamAttempts: (examId: number) =>
    request<import("../types").ExamAttemptMonitor[]>(`/exams/${examId}/attempts`),

  submitAttempt: (attemptId: number, answers: StudentAnswerSubmission[]) =>
    request<Result>(`/attempts/${attemptId}/submit`, {
      method: "POST",
      body: JSON.stringify({ answers }),
    }),

  getAttempt: (attemptId: number) => request<any>(`/attempts/${attemptId}`),

  // Results
  getAttemptResult: (attemptId: number) => request<Result>(`/results/attempt/${attemptId}`),

  getMyResults: () => request<Result[]>("/results/my"),

  getExamResults: (examId: number) => request<Result[]>(`/results/exam/${examId}`),

  // Admin
  getUsers: () => request<User[]>("/users/"),

  updateUserRole: (id: number, role: UserRole) =>
    request<User>(`/users/${id}/role`, {
      method: "PUT",
      body: JSON.stringify({ role }),
    }),

  toggleUserStatus: (id: number, is_active: boolean) =>
    request<User>(`/users/${id}/status`, {
      method: "PUT",
      body: JSON.stringify({ is_active }),
    }),

  getAuditLogs: (limit = 50, action?: string) => {
    const params = new URLSearchParams();
    params.set("limit", limit.toString());
    if (action) params.set("action", action);
    return request<AuditLog[]>(`/audit/?${params.toString()}`);
  },
};
