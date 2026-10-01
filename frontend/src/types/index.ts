export type UserRole = "STUDENT" | "FACULTY" | "ADMIN";

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export type ExamStatus = "DRAFT" | "PUBLISHED" | "CLOSED";

export type AttemptStatus =
  | "NOT_STARTED"
  | "IN_PROGRESS"
  | "SUBMITTED"
  | "AUTO_SUBMITTED"
  | "TERMINATED_FOR_VIOLATION"
  | "EXPIRED";

export interface QuestionOption {
  id: number;
  question_id: number;
  option_text: string;
  is_correct?: boolean;
  order_index: number;
}

export interface Question {
  id: number;
  exam_id: number;
  question_text: string;
  marks: number;
  negative_marks?: number;
  explanation?: string;
  order_index: number;
  options: QuestionOption[];
}

export interface Exam {
  id: number;
  title: string;
  description?: string;
  duration_minutes: number;
  total_marks: number;
  passing_marks: number;
  enable_negative_marking?: boolean;
  status: ExamStatus;
  created_by: number;
  start_time?: string;
  end_time?: string;
  created_at: string;
  updated_at: string;
  question_count?: number;
  questions?: Question[];
}

export interface SavedAnswerItem {
  question_id: number;
  selected_option_id: number | null;
  is_marked_for_review: boolean;
}

export interface AttemptStartResponse {
  attempt_id: number;
  exam_id: number;
  exam_title: string;
  duration_minutes: number;
  total_marks?: number;
  enable_negative_marking?: boolean;
  started_at: string;
  expires_at: string;
  remaining_seconds: number;
  violation_count?: number;
  status?: AttemptStatus;
  questions: Question[];
  saved_answers?: SavedAnswerItem[];
}

export interface StudentAnswerSubmission {
  question_id: number;
  selected_option_id: number | null;
}

export interface AnswerAutoSaveResponse {
  status: string;
  question_id: number;
  selected_option_id: number | null;
  is_marked_for_review: boolean;
  recorded_at: string;
}

export interface ExamViolationResponse {
  violation_count: number;
  warning_level: number;
  message: string;
  is_terminated: boolean;
  termination_reason?: string;
  timestamp: string;
}

export interface AttemptStatusResponse {
  attempt_id: number;
  status: AttemptStatus;
  remaining_seconds: number;
  violation_count: number;
  is_terminated: boolean;
  termination_reason?: string;
  expires_at: string;
}

export interface ExamViolationItem {
  id: number;
  attempt_id: number;
  student_id: number;
  student_name?: string;
  event_type: string;
  warning_number?: number;
  details?: string;
  ip_address?: string;
  timestamp: string;
}

export interface ExamAttemptMonitor {
  id: number;
  student_id: number;
  student_name: string;
  student_email: string;
  status: AttemptStatus;
  started_at: string;
  submitted_at?: string;
  terminated_at?: string;
  termination_reason?: string;
  violation_count: number;
  score?: number;
  max_score?: number;
  percentage?: number;
  passed?: boolean;
}

export interface Result {
  id: number;
  attempt_id: number;
  student_id: number;
  exam_id: number;
  total_score: number;
  max_score: number;
  percentage: number;
  passed: boolean;
  evaluated_at: string;
  student_name?: string;
  student_email?: string;
  exam_title?: string;
}

export interface AuditLog {
  id: number;
  timestamp: string;
  actor_id?: number;
  actor_role?: string;
  action: string;
  resource_id?: string;
  ip_address?: string;
  status: string;
  details?: string;
}

export interface ExamAssignment {
  id: number;
  exam_id: number;
  student_id: number;
  student_name: string;
  student_email: string;
  assigned_at: string;
}
