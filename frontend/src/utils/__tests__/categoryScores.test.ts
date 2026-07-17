import { describe, it, expect } from "vitest";
import { computeCategoryScores } from "../categoryScores";
import type { Issue } from "../../types/audit";

function makeIssue(overrides: Partial<Issue> = {}): Issue {
  return {
    id: "test-issue",
    severity: "medium",
    category: "structured_data",
    location: "body",
    description: "Test issue",
    ...overrides,
  };
}

describe("computeCategoryScores", () => {
  it("returns 100 for all categories when no issues", () => {
    const scores = computeCategoryScores([]);
    expect(scores).toHaveLength(3);
    expect(scores.every((s) => s.score === 100)).toBe(true);
  });

  it("deducts severity-based penalties for single category", () => {
    const issues = [
      makeIssue({ category: "structured_data", severity: "high" }),
    ];
    const scores = computeCategoryScores(issues);
    const structured = scores.find((s) => s.category === "structured_data");
    expect(structured?.score).toBe(80);
  });

  it("handles multiple categories independently", () => {
    const issues = [
      makeIssue({ category: "structured_data", severity: "medium" }),
      makeIssue({ category: "commercial_trust", severity: "low" }),
    ];
    const scores = computeCategoryScores(issues);
    const structured = scores.find((s) => s.category === "structured_data");
    const trust = scores.find((s) => s.category === "commercial_trust");
    expect(structured?.score).toBe(88);
    expect(trust?.score).toBe(94);
  });

  it("clamps to 0 when penalties exceed 100", () => {
    const issues = [
      makeIssue({ category: "structured_data", severity: "high" }),
      makeIssue({ category: "structured_data", severity: "high" }),
      makeIssue({ category: "structured_data", severity: "high" }),
      makeIssue({ category: "structured_data", severity: "high" }),
      makeIssue({ category: "structured_data", severity: "high" }),
      makeIssue({ category: "structured_data", severity: "high" }),
    ];
    const scores = computeCategoryScores(issues);
    const structured = scores.find((s) => s.category === "structured_data");
    expect(structured?.score).toBe(0);
  });

  it("returns score of 1 when 99 points deducted", () => {
    const issues = [
      makeIssue({ category: "structured_data", severity: "high" }),
      makeIssue({ category: "structured_data", severity: "high" }),
      makeIssue({ category: "structured_data", severity: "high" }),
      makeIssue({ category: "structured_data", severity: "high" }),
      makeIssue({ category: "structured_data", severity: "medium" }),
      makeIssue({ category: "structured_data", severity: "low" }),
    ];
    const scores = computeCategoryScores(issues);
    const structured = scores.find((s) => s.category === "structured_data");
    // 4*20 + 12 + 6 = 98, so score = 2
    expect(structured?.score).toBe(2);
  });

  it("returns score of 49 at boundary", () => {
    const issues = [
      makeIssue({ category: "structured_data", severity: "high" }),
      makeIssue({ category: "structured_data", severity: "high" }),
      makeIssue({ category: "structured_data", severity: "high" }),
      makeIssue({ category: "structured_data", severity: "medium" }),
    ];
    const scores = computeCategoryScores(issues);
    const structured = scores.find((s) => s.category === "structured_data");
    // 3*20 + 12 = 72, so score = 28
    expect(structured?.score).toBe(28);
  });

  it("returns score of 50 at boundary", () => {
    const issues = [
      makeIssue({ category: "structured_data", severity: "high" }),
      makeIssue({ category: "structured_data", severity: "high" }),
      makeIssue({ category: "structured_data", severity: "high" }),
    ];
    const scores = computeCategoryScores(issues);
    const structured = scores.find((s) => s.category === "structured_data");
    // 3*20 = 60, so score = 40
    expect(structured?.score).toBe(40);
  });

  it("returns score of 79 at boundary", () => {
    const issues = [
      makeIssue({ category: "structured_data", severity: "high" }),
      makeIssue({ category: "structured_data", severity: "low" }),
    ];
    const scores = computeCategoryScores(issues);
    const structured = scores.find((s) => s.category === "structured_data");
    // 20 + 6 = 26, so score = 74
    expect(structured?.score).toBe(74);
  });

  it("returns score of 80 at boundary", () => {
    const issues = [
      makeIssue({ category: "structured_data", severity: "high" }),
    ];
    const scores = computeCategoryScores(issues);
    const structured = scores.find((s) => s.category === "structured_data");
    // 20, so score = 80
    expect(structured?.score).toBe(80);
  });

  it("returns score of 99 with single low issue", () => {
    const issues = [
      makeIssue({ category: "structured_data", severity: "low" }),
    ];
    const scores = computeCategoryScores(issues);
    const structured = scores.find((s) => s.category === "structured_data");
    // 6, so score = 94
    expect(structured?.score).toBe(94);
  });

  it("returns score of 100 with no issues", () => {
    const scores = computeCategoryScores([]);
    const structured = scores.find((s) => s.category === "structured_data");
    expect(structured?.score).toBe(100);
  });

  it("tracks maxSeverity correctly", () => {
    const issues = [
      makeIssue({ category: "structured_data", severity: "low" }),
      makeIssue({ category: "structured_data", severity: "high" }),
    ];
    const scores = computeCategoryScores(issues);
    const structured = scores.find((s) => s.category === "structured_data");
    expect(structured?.maxSeverity).toBe("high");
  });

  it("returns null maxSeverity when no issues", () => {
    const scores = computeCategoryScores([]);
    const structured = scores.find((s) => s.category === "structured_data");
    expect(structured?.maxSeverity).toBeNull();
  });

  it("counts issues per category", () => {
    const issues = [
      makeIssue({ category: "structured_data", severity: "medium" }),
      makeIssue({ category: "structured_data", severity: "low" }),
      makeIssue({ category: "commercial_trust", severity: "high" }),
    ];
    const scores = computeCategoryScores(issues);
    const structured = scores.find((s) => s.category === "structured_data");
    const trust = scores.find((s) => s.category === "commercial_trust");
    expect(structured?.issueCount).toBe(2);
    expect(trust?.issueCount).toBe(1);
  });
});