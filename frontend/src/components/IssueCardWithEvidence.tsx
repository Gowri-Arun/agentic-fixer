import type { Issue, DetectorResult } from "../types/audit";
import { IssueCard } from "./IssueCard";
import { DetectorEvidencePanel } from "./DetectorEvidencePanel";

interface IssueCardWithEvidenceProps {
  issue: Issue;
  detectorResults?: DetectorResult[];
}

const ISSUE_TO_DETECTOR: Record<string, string> = {
  missing_faq_schema: "faq_detector",
  missing_product_or_service_schema: "pricing_detector",
  invalid_json_ld: "structured_data_detector",
  missing_policy_surface: "policy_detector",
  missing_h1: "heading_detector",
  multiple_h1: "heading_detector",
  heading_hierarchy_jump: "heading_detector",
};

export function IssueCardWithEvidence({
  issue,
  detectorResults,
}: IssueCardWithEvidenceProps) {
  const detectorId = ISSUE_TO_DETECTOR[issue.id];
  const detector = detectorResults?.find((d) => d.detector_id === detectorId);

  return (
    <div className="issue-with-evidence">
      <IssueCard issue={issue} />
      {detector && <DetectorEvidencePanel detector={detector} />}
    </div>
  );
}