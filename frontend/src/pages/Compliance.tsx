import { useEffect, useState } from "react";
import { api } from "../services/api";
import type { ComplianceResult, User } from "../types";
import { Page, Loading, ErrorState, EmptyState } from "../components/Page";
import { ComplianceView } from "./BidderDetails";

function bidderIdFor(user: User) { return user.id === "frontend-preview" ? "BID-DEMO-001" : user.id; }

export function Compliance({ user }: { user: User }) {
  const [result, setResult] = useState<ComplianceResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const bidderId = bidderIdFor(user);

  useEffect(() => {
    setLoading(true); setError("");
    api.getComplianceResult(bidderId)
      .then(setResult)
      .catch((e) => setError(e instanceof Error ? e.message : "No compliance result available."))
      .finally(() => setLoading(false));
  }, [bidderId]);

  return <Page title="My Compliance" description="Your compliance is displayed exactly as returned by the verification backend.">
    {loading ? <Loading /> : error ? <ErrorState message={error} /> : result ? <ComplianceView result={result} /> : <EmptyState title="No compliance result" description="The backend has not returned a compliance result for this bidder." />}
  </Page>;
}
