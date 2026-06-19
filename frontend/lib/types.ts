// Types mirroring the FastAPI backend responses.

export type Role = "admin" | "reviewer" | "viewer";

export interface Me {
  id: string;
  email: string;
  full_name: string | null;
  role: Role;
  tenant_id: string;
}

export interface Tokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export type DocStatus = "pending" | "processing" | "ready" | "failed";
export type FileType = "pdf" | "email" | "slack" | "audio" | "text" | "other";

export interface Document {
  id: string;
  name: string;
  file_type: FileType;
  status: DocStatus;
  size_bytes: number | null;
  page_count: number | null;
  error_message: string | null;
  uploaded_by: string | null;
  created_at: string;
}

export type CaseStatus = "open" | "pending_review" | "closed";
export type RiskTier = "critical" | "high" | "medium" | "low";
export type Severity = "critical" | "high" | "medium" | "low";
export type ReviewStatus = "pending" | "confirmed" | "dismissed";

export interface Violation {
  id: string;
  violation_type: string;
  severity: Severity;
  policy_ref: string;
  doc_excerpt: string;
  clause_text: string;
  reasoning: string;
  confidence: number;
  review_status: ReviewStatus;
  review_note: string | null;
  reviewed_at: string | null;
}

export interface Case {
  id: string;
  document_id: string;
  status: CaseStatus;
  risk_score: number | null;
  risk_tier: RiskTier | null;
  regulations_checked: string[];
  violation_count: number;
  created_at: string;
}

export interface CaseDetail extends Case {
  report_json: Record<string, unknown> | null;
  violations: Violation[];
}

export interface HumanReview {
  id: string;
  violation_id: string | null;
  decision: "confirmed" | "dismissed" | "escalated";
  note: string | null;
  reviewer_id: string | null;
  reviewed_at: string;
}

export interface Policy {
  id: string;
  regulation: string;
  title: string;
  jurisdiction: string | null;
  source: string | null;
  clause_count: number;
  is_active: boolean;
  scope: "global" | "tenant";
}

export interface PolicyMatch {
  regulation: string;
  section: string;
  citation: string;
  text: string;
  score: number;
}

export interface TenantInfo {
  id: string;
  name: string;
  slug: string;
  settings: Record<string, unknown>;
  is_active: boolean;
}

export interface UserRow {
  id: string;
  email: string;
  full_name: string | null;
  role: Role;
  is_active: boolean;
  tenant_id: string;
}

export interface AuditEntry {
  id: string;
  action: string;
  entity_type: string;
  entity_id: string | null;
  user_id: string | null;
  extra_data: Record<string, unknown>;
  ip_address: string | null;
  created_at: string;
}

export interface NotificationConfig {
  enabled: boolean;
  email_enabled: boolean;
  email_recipients: string[];
  events: string[] | null;
  smtp_configured: boolean;
}

export interface DownloadInfo {
  url: string;
  expires_seconds: number;
}
