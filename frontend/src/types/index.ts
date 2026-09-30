export type Role = "ADMIN" | "BIDDER" | "TENDER";
export type VerificationStatus = "VERIFIED" | "REVIEW" | "INVALID" | "MISSING";
export type RequirementStatus = "PASS" | "FAIL" | "REVIEW" | "MISSING";

export interface User {
  id: string;
  name: string;
  email: string;
  role: Role;
  mobileNumber?: string;
  businessName?: string;
  businessType?: string;
  bidderId?: string;
}

export interface Tender {
  id: string;
  reference: string;
  title: string;
  organization: string;
  category: string;
  tenderValue: number | string;
  deadline: string;
  bidderType: string;
  status: string;
  bidderCount?: number;
  description?: string;
  location?: string;
  publishDate?: string;
  requirements?: TenderRequirement[];
}

export interface TenderRequirement {
  id: string;
  requirement: string;
  operator?: string;
  requiredValue?: string | number | boolean | null;
  condition?: string;
  mandatory?: boolean;
  fieldToCheck?: string | null;
  verificationSource?: string | null;
  category?: string;
  description?: string;
}

export interface Bidder {
  id: string;
  name: string;
  businessName: string;
  email: string;
  mobile?: string;
  appliedTenders?: number;
  verificationStatus?: VerificationStatus;
  complianceStatus?: string;
  status?: string;
}

export interface DocumentRecord {
  id?: string;
  type: string;
  required?: boolean;
  fileName?: string;
  status: VerificationStatus | "UPLOADED" | "EXTRACTING" | "VERIFYING";
  uploadedAt?: string;
  storagePath?: string;
  mimeType?: string;
  fileSize?: number;
}

export interface ComplianceResult {
  percentage?: number;
  overallStatus?: string;
  compliance_percentage?: number;
  overall_status?: string;
  company_name?: string;
  tender_id?: string;
  summary?: {
    pass?: number;
    fail?: number;
    review?: number;
    missing?: number;
    total_requirements?: number;
  };
  requirements?: RequirementResult[];
  stage1?: {
    verified?: number;
    review?: number;
    invalid?: number;
    missing?: number;
    items?: VerificationItem[];
  };
  stage2?: {
    pass?: number;
    fail?: number;
    review?: number;
    missing?: number;
    items?: RequirementResult[];
  };
  failedRequirements?: RequirementResult[];
  reviewItems?: RequirementResult[];
}

export interface VerificationItem {
  id?: string;
  name: string;
  status: VerificationStatus;
  result?: string;
  reason?: string;
  evidence?: string;
}

export interface RequirementResult {
  id?: string;
  requirement_id?: string;
  requirement: string;
  requirement_name?: string;
  category?: string;
  mandatory?: boolean;
  verification_source?: string | null;
  status: RequirementStatus;
  reason?: string;
  evidence?: string;
  extracted_value?: unknown;
  required_value?: unknown;
  government_value?: unknown;
}

export interface AuditEvent {
  id: string;
  user: string;
  action: string;
  timestamp: string;
  relatedEntity?: string;
  details?: string;
}

export interface CreateBidderPayload {
  name: string;
  businessName: string;
  email: string;
  mobile: string;
  password: string;
}

export const DOCUMENT_TYPES = [
  "Udyam Registration Certificate",
  "GST Registration Certificate",
  "GST Return Filing Record",
  "PAN Card",
  "Income Tax Return (ITR) Acknowledgement",
  "Make in India / Local Content Declaration",
  "EPFO Registration & Compliance Record",
  "ESIC Registration & Compliance Record",
  "DPIIT Startup Recognition Certificate",
  "NSIC Registration Certificate",
  "OEM Authorization Certificate/Letter",
  "DigiLocker Document Verification Record",
  "Blacklisting/Debarment Declaration",
  "Tender/Bid Compliance Declaration",
  "Certificate of Incorporation / Business Registration Certificate",
] as const;
