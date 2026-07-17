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
  describe("populated evidence", () => {
    it("renders detector name and decision", () => {
      const detector = makeDetectorResult();
      render(<DetectorEvidencePanel detector={detector} />);

      fireEvent.click(screen.getByText("How this was detected"));

      expect(screen.getByText("FAQ Detector")).toBeInTheDocument();
      expect(screen.getByText("Decision: Detected")).toBeInTheDocument();
    });

    it("renders confidence as heuristic strength", () => {
      const detector = makeDetectorResult({ confidence: 0.85 });
      render(<DetectorEvidencePanel detector={detector} />);

      fireEvent.click(screen.getByText("How this was detected"));

      expect(screen.getByText(/Confidence: 0.85 \(heuristic strength\)/)).toBeInTheDocument();
    });

    it("renders duration in ms", () => {
      const detector = makeDetectorResult({ duration_ms: 2300 });
      render(<DetectorEvidencePanel detector={detector} />);

      fireEvent.click(screen.getByText("How this was detected"));

      expect(screen.getByText(/Duration: 2.3ms/)).toBeInTheDocument();
    });

    it("renders all evidence fields", () => {
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

    it("renders issues count when present", () => {
      const detector = makeDetectorResult({ issues: [{ type: "test" }] });
      render(<DetectorEvidencePanel detector={detector} />);

      fireEvent.click(screen.getByText("How this was detected"));

      expect(screen.getByText("Issues found: 1")).toBeInTheDocument();
    });
  });

  describe("partial evidence", () => {
    it("renders partial fields when some are missing", () => {
      const detector = makeDetectorResult({
        evidence: {
          fields: [
            { name: "Field 1", value: "Value 1" },
            { name: "Field 2", value: "" },
            { name: "Field 3", value: "Value 3" },
          ],
        },
      });
      render(<DetectorEvidencePanel detector={detector} />);

      fireEvent.click(screen.getByText("How this was detected"));

      expect(screen.getByText("Field 1")).toBeInTheDocument();
      expect(screen.getByText("Value 1")).toBeInTheDocument();
      expect(screen.getByText("Field 3")).toBeInTheDocument();
      expect(screen.getByText("Value 3")).toBeInTheDocument();
      expect(screen.queryByText("Field 2")).not.toBeInTheDocument();
    });

    it("renders fields with zero values", () => {
      const detector = makeDetectorResult({
        evidence: {
          fields: [
            { name: "Count", value: 0 },
          ],
        },
      });
      render(<DetectorEvidencePanel detector={detector} />);

      fireEvent.click(screen.getByText("How this was detected"));

      expect(screen.getByText("Count")).toBeInTheDocument();
      const values = screen.getAllByText("0");
      expect(values.length).toBeGreaterThanOrEqual(1);
    });
  });

  describe("empty evidence", () => {
    it("shows no evidence message when fields are empty", () => {
      const detector = makeDetectorResult({
        evidence: { fields: [] },
      });
      render(<DetectorEvidencePanel detector={detector} />);

      fireEvent.click(screen.getByText("How this was detected"));

      expect(screen.getByText("No evidence available")).toBeInTheDocument();
    });

    it("shows no evidence message when all fields have empty values", () => {
      const detector = makeDetectorResult({
        evidence: {
          fields: [
            { name: "Field 1", value: "" },
            { name: "Field 2", value: null as unknown as string },
          ],
        },
      });
      render(<DetectorEvidencePanel detector={detector} />);

      fireEvent.click(screen.getByText("How this was detected"));

      expect(screen.getByText("No evidence available")).toBeInTheDocument();
    });
  });

  describe("skipped detector", () => {
    it("renders skipped reason", () => {
      const detector = makeDetectorResult({
        decision: "skipped",
        skipped_reason: "Page quality too low",
        evidence: { fields: [] },
      });
      render(<DetectorEvidencePanel detector={detector} />);

      fireEvent.click(screen.getByText("How this was detected"));

      expect(screen.getByText(/Page quality too low/)).toBeInTheDocument();
    });

    it("renders skipped without reason", () => {
      const detector = makeDetectorResult({
        decision: "skipped",
        skipped_reason: undefined,
        evidence: { fields: [] },
      });
      render(<DetectorEvidencePanel detector={detector} />);

      fireEvent.click(screen.getByText("How this was detected"));

      expect(screen.getByText("Decision: Skipped")).toBeInTheDocument();
      expect(screen.queryByText(/Skipped:/)).not.toBeInTheDocument();
    });
  });

  describe("array truncation", () => {
    it("renders short arrays without truncation", () => {
      const detector = makeDetectorResult({
        evidence: {
          fields: [
            { name: "Keywords", value: ["faq", "faqs"] },
          ],
        },
      });
      render(<DetectorEvidencePanel detector={detector} />);

      fireEvent.click(screen.getByText("How this was detected"));

      expect(screen.getByText("faq, faqs")).toBeInTheDocument();
      expect(screen.queryByText(/more/)).not.toBeInTheDocument();
    });

    it("truncates long arrays with expansion option", () => {
      const detector = makeDetectorResult({
        evidence: {
          fields: [
            { name: "Keywords", value: ["a", "b", "c", "d", "e", "f", "g"] },
          ],
        },
      });
      render(<DetectorEvidencePanel detector={detector} />);

      fireEvent.click(screen.getByText("How this was detected"));

      expect(screen.getByText(/a, b, c, d, e/)).toBeInTheDocument();
      expect(screen.getByText(/and 2 more/)).toBeInTheDocument();
    });

    it("expands truncated array on click", () => {
      const detector = makeDetectorResult({
        evidence: {
          fields: [
            { name: "Keywords", value: ["a", "b", "c", "d", "e", "f", "g"] },
          ],
        },
      });
      render(<DetectorEvidencePanel detector={detector} />);

      fireEvent.click(screen.getByText("How this was detected"));
      fireEvent.click(screen.getByText(/and 2 more/));

      expect(screen.getByText("a, b, c, d, e, f, g")).toBeInTheDocument();
      expect(screen.getByText("Show less")).toBeInTheDocument();
    });

    it("collapses expanded array on click", () => {
      const detector = makeDetectorResult({
        evidence: {
          fields: [
            { name: "Keywords", value: ["a", "b", "c", "d", "e", "f", "g"] },
          ],
        },
      });
      render(<DetectorEvidencePanel detector={detector} />);

      fireEvent.click(screen.getByText("How this was detected"));
      fireEvent.click(screen.getByText(/and 2 more/));
      fireEvent.click(screen.getByText("Show less"));

      expect(screen.getByText(/a, b, c, d, e/)).toBeInTheDocument();
      expect(screen.getByText(/and 2 more/)).toBeInTheDocument();
    });
  });

  describe("safe escaping", () => {
    it("escapes HTML in evidence values", () => {
      const detector = makeDetectorResult({
        evidence: {
          fields: [
            { name: "Input", value: "<script>alert('xss')</script>" },
          ],
        },
      });
      render(<DetectorEvidencePanel detector={detector} />);

      fireEvent.click(screen.getByText("How this was detected"));

      expect(screen.getByText(/<script>/)).toBeInTheDocument();
      expect(screen.queryByText("alert('xss')")).not.toBeInTheDocument();
    });
  });

  describe("accessibility", () => {
    it("has proper aria attributes", () => {
      const detector = makeDetectorResult();
      render(<DetectorEvidencePanel detector={detector} />);

      const button = screen.getByRole("button");
      expect(button).toHaveAttribute("aria-expanded", "false");
      expect(button).toHaveAttribute("aria-controls", "evidence-faq_detector");
    });

    it("toggles aria-expanded on click", () => {
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

  describe("null detector", () => {
    it("returns null for undefined detector", () => {
      const { container } = render(
        <DetectorEvidencePanel detector={undefined as unknown as DetectorResult} />,
      );

      expect(container.firstChild).toBeNull();
    });
  });
});