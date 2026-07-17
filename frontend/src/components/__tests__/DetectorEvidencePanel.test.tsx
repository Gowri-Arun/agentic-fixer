import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { DetectorEvidencePanel } from "../DetectorEvidencePanel";
import type { DetectorResult } from "../../types/audit";

function makeDetectorResult(overrides: Partial<DetectorResult> = {}): DetectorResult {
  return {
    detector_id: "faq_detector",
    display_name: "FAQ Detector",
    decision: "detected",
    issues: [],
    evidence: {
      fields: [
        { name: "FAQ indicators found", value: "faq, faqs" },
        { name: "Heading count", value: 3 },
        { name: "Has FAQ schema", value: false },
      ],
    },
    confidence: 0.85,
    duration_ms: 2300,
    version: "1.0.0",
    ...overrides,
  };
}

describe("DetectorEvidencePanel", () => {
  it("renders detector name", () => {
    const detector = makeDetectorResult();
    render(<DetectorEvidencePanel detector={detector} />);

    expect(screen.getByText("How this was detected")).toBeInTheDocument();
  });

  it("expands to show details", () => {
    const detector = makeDetectorResult();
    render(<DetectorEvidencePanel detector={detector} />);

    fireEvent.click(screen.getByText("How this was detected"));

    expect(screen.getByText("FAQ Detector")).toBeInTheDocument();
    expect(screen.getByText("Decision: Detected")).toBeInTheDocument();
  });

  it("renders confidence as heuristic", () => {
    const detector = makeDetectorResult({ confidence: 0.85 });
    render(<DetectorEvidencePanel detector={detector} />);

    fireEvent.click(screen.getByText("How this was detected"));

    expect(screen.getByText(/Confidence: 0.85/)).toBeInTheDocument();
  });

  it("renders duration in ms", () => {
    const detector = makeDetectorResult({ duration_ms: 2300 });
    render(<DetectorEvidencePanel detector={detector} />);

    fireEvent.click(screen.getByText("How this was detected"));

    expect(screen.getByText(/Duration: 2.3ms/)).toBeInTheDocument();
  });

  it("renders evidence fields", () => {
    const detector = makeDetectorResult();
    render(<DetectorEvidencePanel detector={detector} />);

    fireEvent.click(screen.getByText("How this was detected"));

    expect(screen.getByText("FAQ indicators found")).toBeInTheDocument();
    expect(screen.getByText("faq, faqs")).toBeInTheDocument();
    expect(screen.getByText("Heading count")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
  });

  it("renders boolean values as Yes/No", () => {
    const detector = makeDetectorResult();
    render(<DetectorEvidencePanel detector={detector} />);

    fireEvent.click(screen.getByText("How this was detected"));

    expect(screen.getByText("Has FAQ schema")).toBeInTheDocument();
    expect(screen.getByText("No")).toBeInTheDocument();
  });

  it("renders skipped reason", () => {
    const detector = makeDetectorResult({
      decision: "skipped",
      skipped_reason: "Page quality too low",
    });
    render(<DetectorEvidencePanel detector={detector} />);

    fireEvent.click(screen.getByText("How this was detected"));

    expect(screen.getByText("Skipped: Page quality too low")).toBeInTheDocument();
  });

  it("handles missing detector_results", () => {
    const { container } = render(
      <DetectorEvidencePanel detector={undefined as unknown as DetectorResult} />,
    );

    expect(container.firstChild).toBeNull();
  });

  it("collapse/expand toggle", () => {
    const detector = makeDetectorResult();
    render(<DetectorEvidencePanel detector={detector} />);

    const button = screen.getByRole("button");
    expect(button).toHaveAttribute("aria-expanded", "false");

    fireEvent.click(button);
    expect(button).toHaveAttribute("aria-expanded", "true");

    fireEvent.click(button);
    expect(button).toHaveAttribute("aria-expanded", "false");
  });
});