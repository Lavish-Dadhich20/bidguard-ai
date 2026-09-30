import type {
  AuditEvent, Bidder, ComplianceResult, CreateBidderPayload, DocumentRecord, Tender, TenderRequirement, User
} from "../types";

const BASE_URL = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");
export const FRONTEND_ONLY = !BASE_URL;

function normalizeTender(raw: any): Tender {
  return {
    id: String(raw.id ?? ""),
    reference: raw.reference ?? raw.tender_reference ?? raw.id ?? "—",
    title: raw.title ?? "—",
    organization: raw.organization ?? "—",
    category: raw.category ?? "—",
    tenderValue: raw.tender_value ?? raw.tenderValue ?? raw.value ?? "—",
    deadline: raw.deadline ?? raw.submission_deadline ?? "—",
    bidderType: raw.bidder_type ?? raw.bidderType ?? "—",
    status: raw.status ?? "—",
    bidderCount: raw.bidder_count ?? raw.bidderCount ?? 0,
    description: raw.description ?? "",
    location: raw.location ?? "",
    publishDate: raw.publish_date ?? raw.publishDate ?? "",
    requirements: Array.isArray(raw.requirements)
      ? raw.requirements.map(normalizeRequirement)
      : undefined,
  };
}

function normalizeRequirement(raw: any): TenderRequirement {
  return {
    id: String(raw.id ?? raw.requirement_id ?? crypto.randomUUID()),
    requirement: raw.requirement ?? raw.requirement_name ?? raw.name ?? "Requirement",
    operator: raw.operator ?? "",
    requiredValue: raw.requiredValue ?? raw.required_value ?? raw.value ?? "",
    condition: raw.condition ?? "",
    mandatory: raw.mandatory ?? true,
    fieldToCheck: raw.fieldToCheck ?? raw.field_to_check ?? null,
    verificationSource: raw.verificationSource ?? raw.verification_source ?? null,
    category: raw.category ?? "GENERAL",
    description: raw.description ?? "",
  };
}

function normalizeBidder(raw: any): Bidder {
  return {
    id: String(raw.id ?? ""),
    name: raw.contact_person ?? raw.name ?? raw.company_name ?? "—",
    businessName: raw.company_name ?? raw.businessName ?? raw.name ?? "—",
    email: raw.email ?? "—",
    mobile: raw.phone ?? raw.mobile ?? "",
    appliedTenders: raw.applied_tenders ?? raw.appliedTenders,
    verificationStatus: raw.verification_status ?? raw.verificationStatus,
    complianceStatus: raw.compliance_status ?? raw.complianceStatus,
    status: raw.status,
  };
}

function normalizeAudit(raw: any, index: number): AuditEvent {
  const details = raw.details;
  let detailText = "—";
  if (details !== undefined && details !== null) {
    detailText = typeof details === "string" ? details : JSON.stringify(details);
  }

  const rawUser = raw.user ?? raw.username ?? raw.user_id ?? "System";
  return {
    id: String(raw.id ?? `${raw.action ?? "AUDIT"}-${index}`),
    user: typeof rawUser === "string" ? rawUser : JSON.stringify(rawUser),
    action: typeof raw.action === "string" ? raw.action : JSON.stringify(raw.action ?? "—"),
    timestamp: raw.created_at ?? raw.timestamp ?? "—",
    relatedEntity: raw.entity_id ?? raw.related_entity ?? raw.entity_type,
    details: detailText,
  };
}

function getErrorMessage(detail: unknown): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((item) => {
      if (typeof item === "string") return item;
      if (item && typeof item === "object") {
        const value = item as Record<string, unknown>;
        return String(value.msg ?? value.message ?? JSON.stringify(value));
      }
      return String(item);
    }).join("; ");
  }
  if (detail && typeof detail === "object") return JSON.stringify(detail);
  return "";
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  if (!BASE_URL) {
    throw new Error("API base URL is not configured. Set VITE_API_BASE_URL in your environment.");
  }

  const response = await fetch(`${BASE_URL}${path}`, {
    credentials: "include",
    ...options,
    headers: {
      ...(options.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...(options.headers || {}),
    },
  });

  if (response.status === 401) throw new Error("Your session has expired. Please sign in again.");
  if (response.status === 403) throw new Error("You are not authorized to perform this action.");
  if (!response.ok) {
    let detail = "";
    try {
      const body = await response.json();
      detail = getErrorMessage(body?.detail ?? body?.message);
    } catch {}
    throw new Error(detail || `Request failed with status ${response.status}.`);
  }
  if (response.status === 204) return undefined as T;
  return response.json();
}

export const api = {
  login: (payload: { username: string; password: string }) =>
    request<User>("/auth/login", { method: "POST", body: JSON.stringify(payload) }),
  logout: () => request<void>("/auth/logout", { method: "POST" }),
  getCurrentUser: () => request<User>("/auth/me"),
  changePassword: (payload: { currentPassword: string; newPassword: string }) =>
    request<void>("/auth/change-password", { method: "POST", body: JSON.stringify(payload) }),
  deleteAccount: (password: string) =>
    request<void>("/auth/account", { method: "DELETE", body: JSON.stringify({ password }) }),

  getTenders: async () => {
    if (FRONTEND_ONLY) return [] as Tender[];
    const data = await request<any[]>("/tenders");
    return (data || []).map(normalizeTender);
  },
  getTender: async (id: string) => normalizeTender(await request<any>(`/tenders/${encodeURIComponent(id)}`)),
  createTender: async (payload: Omit<Tender, "status" | "bidderCount">) => {
    const raw = await request<any>("/tenders", {
      method: "POST",
      body: JSON.stringify({
        id: payload.id,
        reference: payload.reference,
        title: payload.title,
        organization: payload.organization,
        category: payload.category,
        tender_value: payload.tenderValue,
        deadline: payload.deadline,
        bidder_type: payload.bidderType,
        description: payload.description,
        location: payload.location,
        publish_date: payload.publishDate,
        requirements: (payload.requirements || []).map((item, index) => ({
          requirement_id: item.id || `REQ-${String(index + 1).padStart(3, "0")}`,
          requirement_name: item.requirement,
          category: item.category || "GENERAL",
          mandatory: item.mandatory !== false,
          field_to_check: item.fieldToCheck ?? null,
          operator: item.operator || "==",
          value: item.requiredValue ?? null,
          verification_source: item.verificationSource ?? null,
          description: item.description || item.condition || "",
        })),
      }),
    });
    return normalizeTender(raw);
  },
  applyForTender: (tenderId: string, bidderId: string) => {
    const form = new FormData();
    form.append("bidder_id", bidderId);
    return request<any>(`/tenders/${encodeURIComponent(tenderId)}/apply`, {
      method: "POST",
      body: form,
    });
  },

  getBidders: async () => {
    if (FRONTEND_ONLY) return [] as Bidder[];
    const data = await request<any[]>("/bidders");
    return (data || []).map(normalizeBidder);
  },
  getBidder: async (id: string) => normalizeBidder(await request<any>(`/bidders/${encodeURIComponent(id)}`)),
  createBidder: async (payload: CreateBidderPayload) => {
    const raw = await request<any>("/bidders", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    return normalizeBidder(raw);
  },

  registerBidder: async (payload: CreateBidderPayload) => {
    const raw = await request<any>("/bidders", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    return normalizeBidder(raw);
  },

  getDocuments: (bidderId: string, tenderId?: string) =>
    FRONTEND_ONLY ? Promise.resolve([] as DocumentRecord[]) : request<DocumentRecord[]>(
      `/bidders/${encodeURIComponent(bidderId)}/documents${tenderId ? `?tender_id=${encodeURIComponent(tenderId)}` : ""}`
    ),
  uploadDocument: (bidderId: string, type: string, file: File, tenderId?: string) => {
    const form = new FormData();
    form.append("document_type", type);
    form.append("file", file);
    if (tenderId) form.append("tender_id", tenderId);
    return request<DocumentRecord>(`/bidders/${encodeURIComponent(bidderId)}/documents`, {
      method: "POST", body: form
    });
  },
  replaceDocument: (documentId: string, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<DocumentRecord>(`/documents/${encodeURIComponent(documentId)}`, {
      method: "PUT", body: form
    });
  },
  removeDocument: (documentId: string) =>
    request<void>(`/documents/${encodeURIComponent(documentId)}`, { method: "DELETE" }),

  verifyBidder: (bidderId: string, tenderId?: string) =>
    request<ComplianceResult>(`/bidders/${encodeURIComponent(bidderId)}/verify`, {
      method: "POST",
      body: JSON.stringify(tenderId ? { tender_id: tenderId } : {})
    }),
  getVerificationResult: (bidderId: string, tenderId?: string) =>
    request<ComplianceResult>(
      `/bidders/${encodeURIComponent(bidderId)}/verification${tenderId ? `?tender_id=${encodeURIComponent(tenderId)}` : ""}`
    ),
  getComplianceResult: (bidderId: string, tenderId?: string) =>
    request<ComplianceResult>(
      `/bidders/${encodeURIComponent(bidderId)}/compliance${tenderId ? `?tender_id=${encodeURIComponent(tenderId)}` : ""}`
    ),
  getTenderCompliance: (tenderId: string) =>
    request<{ bidder: Bidder; compliance: ComplianceResult }[]>(
      `/tenders/${encodeURIComponent(tenderId)}/compliance`
    ),

  getReports: (params?: { bidderId?: string; tenderId?: string }) => {
    if (FRONTEND_ONLY) return Promise.resolve([] as any[]);
    const query = new URLSearchParams();
    if (params?.bidderId) query.set("bidder_id", params.bidderId);
    if (params?.tenderId) query.set("tender_id", params.tenderId);
    return request<any[]>(`/reports${query.toString() ? `?${query}` : ""}`);
  },
  getAuditTrail: async () => {
    if (FRONTEND_ONLY) return [] as AuditEvent[];
    const data = await request<any[]>("/audit-trail");
    return (data || []).map(normalizeAudit);
  },
};
