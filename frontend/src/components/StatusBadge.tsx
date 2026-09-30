import { CheckCircle2, CircleAlert, CircleX, Clock3, FileWarning } from "lucide-react";

const styles: Record<string, string> = {
  PASS: "status pass", VERIFIED: "status pass", COMPLIANT: "status pass",
  FAIL: "status fail", INVALID: "status fail", NON_COMPLIANT: "status fail",
  REVIEW: "status review", MISSING: "status missing",
  UPLOADED: "status info", EXTRACTING: "status info", VERIFYING: "status info",
};

export function StatusBadge({ value }: { value?: string }) {
  if (!value) return <span className="status status-missing">Not available</span>;
  const key = value.toUpperCase();
  const Icon = key === "PASS" || key === "VERIFIED" || key === "COMPLIANT"
    ? CheckCircle2
    : key === "FAIL" || key === "INVALID" || key === "NON_COMPLIANT"
      ? CircleX
      : key === "REVIEW"
        ? CircleAlert
        : key === "MISSING"
          ? FileWarning
          : Clock3;
  return <span className={styles[key] || "status status-info"}><Icon size={14} />{value}</span>;
}