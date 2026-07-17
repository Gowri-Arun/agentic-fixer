import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ScoreBreakdown } from "../ScoreBreakdown";
import type { CategoryScore } from "../../utils/categoryScores";

function makeCategoryScore(overrides: Partial<CategoryScore> = {}): CategoryScore {
  return {
    category: "structured_data",
    label: "Structured Data",
    score: 80,
    issueCount: 0,
    maxSeverity: null,
    ...overrides,
  };
}

describe("ScoreBreakdown", () => {
  describe("overall score rendering", () => {
    it("renders overall score and grade", () => {
      render(
        <ScoreBreakdown
          overallScore={85}
          overallGrade="Good"
          categoryScores={[]}
        />,
      );

      expect(screen.getByText("Overall: Good")).toBeInTheDocument();
      expect(screen.getByText("85/100")).toBeInTheDocument();
    });

    it("renders overall score with Excellent grade", () => {
      render(
        <ScoreBreakdown
          overallScore={100}
          overallGrade="Excellent"
          categoryScores={[]}
        />,
      );

      expect(screen.getByText("Overall: Excellent")).toBeInTheDocument();
      expect(screen.getByText("100/100")).toBeInTheDocument();
    });
  });

  describe("boundary value tests", () => {
    it("renders score of 0", () => {
      render(
        <ScoreBreakdown
          overallScore={0}
          overallGrade="Poor"
          categoryScores={[makeCategoryScore({ score: 0, category: "commercial_trust", label: "Trust" })]}
        />,
      );

      const values = screen.getAllByText("0/100");
      expect(values.length).toBe(2);
      const progressbars = screen.getAllByRole("progressbar");
      expect(progressbars[0]).toHaveAttribute("aria-valuenow", "0");
    });

    it("renders score of 1", () => {
      render(
        <ScoreBreakdown
          overallScore={1}
          overallGrade="Poor"
          categoryScores={[makeCategoryScore({ score: 1, category: "commercial_trust", label: "Trust" })]}
        />,
      );

      const values = screen.getAllByText("1/100");
      expect(values.length).toBe(2);
      const progressbars = screen.getAllByRole("progressbar");
      expect(progressbars[0]).toHaveAttribute("aria-valuenow", "1");
    });

    it("renders score of 49", () => {
      render(
        <ScoreBreakdown
          overallScore={49}
          overallGrade="Needs Work"
          categoryScores={[makeCategoryScore({ score: 49, category: "commercial_trust", label: "Trust" })]}
        />,
      );

      const values = screen.getAllByText("49/100");
      expect(values.length).toBe(2);
      const progressbars = screen.getAllByRole("progressbar");
      expect(progressbars[0]).toHaveAttribute("aria-valuenow", "49");
    });

    it("renders score of 50", () => {
      render(
        <ScoreBreakdown
          overallScore={50}
          overallGrade="Good"
          categoryScores={[makeCategoryScore({ score: 50, category: "commercial_trust", label: "Trust" })]}
        />,
      );

      const values = screen.getAllByText("50/100");
      expect(values.length).toBe(2);
      const progressbars = screen.getAllByRole("progressbar");
      expect(progressbars[0]).toHaveAttribute("aria-valuenow", "50");
    });

    it("renders score of 79", () => {
      render(
        <ScoreBreakdown
          overallScore={79}
          overallGrade="Needs Work"
          categoryScores={[makeCategoryScore({ score: 79, category: "commercial_trust", label: "Trust" })]}
        />,
      );

      const values = screen.getAllByText("79/100");
      expect(values.length).toBe(2);
      const progressbars = screen.getAllByRole("progressbar");
      expect(progressbars[0]).toHaveAttribute("aria-valuenow", "79");
    });

    it("renders score of 80", () => {
      render(
        <ScoreBreakdown
          overallScore={80}
          overallGrade="Good"
          categoryScores={[makeCategoryScore({ score: 80, category: "commercial_trust", label: "Trust" })]}
        />,
      );

      const values = screen.getAllByText("80/100");
      expect(values.length).toBe(2);
      const progressbars = screen.getAllByRole("progressbar");
      expect(progressbars[0]).toHaveAttribute("aria-valuenow", "80");
    });

    it("renders score of 99", () => {
      render(
        <ScoreBreakdown
          overallScore={99}
          overallGrade="Excellent"
          categoryScores={[makeCategoryScore({ score: 99, category: "commercial_trust", label: "Trust" })]}
        />,
      );

      const values = screen.getAllByText("99/100");
      expect(values.length).toBe(2);
      const progressbars = screen.getAllByRole("progressbar");
      expect(progressbars[0]).toHaveAttribute("aria-valuenow", "99");
    });

    it("renders score of 100", () => {
      render(
        <ScoreBreakdown
          overallScore={100}
          overallGrade="Excellent"
          categoryScores={[makeCategoryScore({ score: 100, category: "commercial_trust", label: "Trust" })]}
        />,
      );

      const values = screen.getAllByText("100/100");
      expect(values.length).toBe(2);
      const progressbars = screen.getAllByRole("progressbar");
      expect(progressbars[0]).toHaveAttribute("aria-valuenow", "100");
    });
  });

  describe("category scores", () => {
    it("renders all category bars", () => {
      const categoryScores = [
        makeCategoryScore({ category: "structured_data", label: "Structured Data", score: 78 }),
        makeCategoryScore({ category: "commercial_trust", label: "Trust", score: 100 }),
        makeCategoryScore({ category: "document_structure", label: "Document Structure", score: 88 }),
      ];

      render(
        <ScoreBreakdown
          overallScore={85}
          overallGrade="Good"
          categoryScores={categoryScores}
        />,
      );

      expect(screen.getByText("Structured Data")).toBeInTheDocument();
      expect(screen.getByText("Trust")).toBeInTheDocument();
      expect(screen.getByText("Document Structure")).toBeInTheDocument();
    });

    it("shows numeric values for each category", () => {
      const categoryScores = [
        makeCategoryScore({ category: "structured_data", label: "Structured Data", score: 78 }),
        makeCategoryScore({ category: "commercial_trust", label: "Trust", score: 100 }),
        makeCategoryScore({ category: "document_structure", label: "Document Structure", score: 88 }),
      ];

      render(
        <ScoreBreakdown
          overallScore={85}
          overallGrade="Good"
          categoryScores={categoryScores}
        />,
      );

      expect(screen.getByText("78/100")).toBeInTheDocument();
      expect(screen.getByText("100/100")).toBeInTheDocument();
      expect(screen.getByText("88/100")).toBeInTheDocument();
    });

    it("handles empty categories", () => {
      render(
        <ScoreBreakdown
          overallScore={100}
          overallGrade="Excellent"
          categoryScores={[]}
        />,
      );

      expect(screen.getByText("Overall: Excellent")).toBeInTheDocument();
      expect(screen.getByText("100/100")).toBeInTheDocument();
      expect(screen.queryByText("Structured Data")).not.toBeInTheDocument();
    });
  });

  describe("accessibility", () => {
    it("has accessible progressbar elements", () => {
      const categoryScores = [
        makeCategoryScore({ category: "structured_data", label: "Structured Data", score: 78 }),
      ];

      render(
        <ScoreBreakdown
          overallScore={85}
          overallGrade="Good"
          categoryScores={categoryScores}
        />,
      );

      const progressbars = screen.getAllByRole("progressbar");
      expect(progressbars).toHaveLength(2);

      expect(progressbars[0]).toHaveAttribute("aria-label", "Overall score: 85 out of 100, Good");
      expect(progressbars[0]).toHaveAttribute("aria-valuenow", "85");
      expect(progressbars[0]).toHaveAttribute("aria-valuemin", "0");
      expect(progressbars[0]).toHaveAttribute("aria-valuemax", "100");

      expect(progressbars[1]).toHaveAttribute("aria-label", "Structured Data score: 78 out of 100, Needs Work");
      expect(progressbars[1]).toHaveAttribute("aria-valuenow", "78");
    });

    it("provides accessible description for each score", () => {
      const categoryScores = [
        makeCategoryScore({ category: "commercial_trust", label: "Trust", score: 92 }),
      ];

      render(
        <ScoreBreakdown
          overallScore={85}
          overallGrade="Good"
          categoryScores={categoryScores}
        />,
      );

      expect(screen.getByRole("progressbar", { name: /Overall score: 85/ })).toBeInTheDocument();
      expect(screen.getByRole("progressbar", { name: /Trust score: 92/ })).toBeInTheDocument();
    });

    it("has region landmark", () => {
      render(
        <ScoreBreakdown
          overallScore={85}
          overallGrade="Good"
          categoryScores={[]}
        />,
      );

      expect(screen.getByRole("region", { name: /Score breakdown/ })).toBeInTheDocument();
    });
  });

  describe("score color classes", () => {
    it("applies score-high class for scores >= 80", () => {
      render(
        <ScoreBreakdown
          overallScore={85}
          overallGrade="Good"
          categoryScores={[makeCategoryScore({ score: 85 })]}
        />,
      );

      const fillElements = document.querySelectorAll(".score-bar-fill");
      expect(fillElements[0]).toHaveClass("score-high");
    });

    it("applies score-medium class for scores 50-79", () => {
      render(
        <ScoreBreakdown
          overallScore={65}
          overallGrade="Needs Work"
          categoryScores={[makeCategoryScore({ score: 65 })]}
        />,
      );

      const fillElements = document.querySelectorAll(".score-bar-fill");
      expect(fillElements[0]).toHaveClass("score-medium");
    });

    it("applies score-low class for scores < 50", () => {
      render(
        <ScoreBreakdown
          overallScore={30}
          overallGrade="Poor"
          categoryScores={[makeCategoryScore({ score: 30 })]}
        />,
      );

      const fillElements = document.querySelectorAll(".score-bar-fill");
      expect(fillElements[0]).toHaveClass("score-low");
    });
  });
});