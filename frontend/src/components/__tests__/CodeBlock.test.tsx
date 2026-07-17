import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, act } from "@testing-library/react";
import { CodeBlock } from "../CodeBlock";
import * as clipboard from "../../utils/clipboard";

vi.mock("../../utils/clipboard", () => ({
  copyToClipboard: vi.fn(),
}));

const SAMPLE_CODE = `function greet(name) {
  return "Hello, " + name;
}`;

describe("CodeBlock", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  function getCodeContent(container: HTMLElement): string {
    const codeEl = container.querySelector("code");
    if (!codeEl) throw new Error("No code element found");
    return codeEl.textContent ?? "";
  }

  describe("code preservation", () => {
    it("renders code content exactly", () => {
      const { container } = render(<CodeBlock code={SAMPLE_CODE} />);
      expect(getCodeContent(container)).toBe(SAMPLE_CODE);
    });

    it("preserves whitespace in code", () => {
      const spacedCode = "    indented code\n        double indented";
      const { container } = render(<CodeBlock code={spacedCode} />);
      expect(getCodeContent(container)).toBe(spacedCode);
      const codeEl = container.querySelector("code");
      expect(codeEl).toBeInTheDocument();
      expect(codeEl!.tagName).toBe("CODE");
    });

    it("preserves special characters", () => {
      const specialCode = 'const x = "hello <world> & \\"friends\\"";';
      const { container } = render(<CodeBlock code={specialCode} />);
      expect(getCodeContent(container)).toBe(specialCode);
    });
  });

  describe("language label", () => {
    it("displays default language as html", () => {
      render(<CodeBlock code="test" />);
      expect(screen.getByText("html")).toBeInTheDocument();
    });

    it("displays custom language", () => {
      render(<CodeBlock code="test" language="typescript" />);
      expect(screen.getByText("typescript")).toBeInTheDocument();
    });
  });

  describe("file path hint", () => {
    it("does not show file path when not provided", () => {
      render(<CodeBlock code="test" />);
      expect(screen.queryByText(/components/)).not.toBeInTheDocument();
    });

    it("shows file path when provided", () => {
      render(<CodeBlock code="test" filePath="src/components/Button.tsx" />);
      expect(
        screen.getByText("src/components/Button.tsx"),
      ).toBeInTheDocument();
    });
  });

  describe("expand/collapse", () => {
    it("shows code by default", () => {
      const { container } = render(<CodeBlock code={SAMPLE_CODE} />);
      expect(getCodeContent(container)).toBe(SAMPLE_CODE);
      expect(screen.getByText("Hide code")).toBeInTheDocument();
    });

    it("hides code when defaultCollapsed is true", () => {
      const { container } = render(
        <CodeBlock code={SAMPLE_CODE} defaultCollapsed />,
      );
      const pre = container.querySelector("pre");
      expect(pre).toHaveAttribute("hidden");
      expect(screen.getByText("Show code")).toBeInTheDocument();
    });

    it("toggles code visibility on button click", () => {
      const { container } = render(<CodeBlock code={SAMPLE_CODE} />);
      const toggle = screen.getByText("Hide code");

      fireEvent.click(toggle);
      const pre = container.querySelector("pre");
      expect(pre).toHaveAttribute("hidden");
      expect(screen.getByText("Show code")).toBeInTheDocument();

      fireEvent.click(screen.getByText("Show code"));
      expect(pre).not.toHaveAttribute("hidden");
      expect(screen.getByText("Hide code")).toBeInTheDocument();
    });

    it("has correct aria-expanded attribute", () => {
      render(<CodeBlock code={SAMPLE_CODE} />);
      const toggle = screen.getByText("Hide code");
      expect(toggle).toHaveAttribute("aria-expanded", "true");

      fireEvent.click(toggle);
      expect(screen.getByText("Show code")).toHaveAttribute(
        "aria-expanded",
        "false",
      );
    });
  });

  describe("copy functionality", () => {
    it("copies code to clipboard on click", async () => {
      vi.mocked(clipboard.copyToClipboard).mockResolvedValue(undefined);
      render(<CodeBlock code={SAMPLE_CODE} />);

      await act(async () => {
        fireEvent.click(screen.getByText("Copy"));
      });

      expect(clipboard.copyToClipboard).toHaveBeenCalledWith(SAMPLE_CODE);
    });

    it("shows copied confirmation then resets", async () => {
      vi.mocked(clipboard.copyToClipboard).mockResolvedValue(undefined);
      render(<CodeBlock code={SAMPLE_CODE} />);

      await act(async () => {
        fireEvent.click(screen.getByText("Copy"));
      });

      expect(screen.getByText("Copied")).toBeInTheDocument();

      act(() => {
        vi.advanceTimersByTime(2000);
      });

      expect(screen.getByText("Copy")).toBeInTheDocument();
    });

    it("shows failed state on clipboard error", async () => {
      vi.mocked(clipboard.copyToClipboard).mockRejectedValue(
        new Error("Not allowed"),
      );
      render(<CodeBlock code={SAMPLE_CODE} />);

      await act(async () => {
        fireEvent.click(screen.getByText("Copy"));
      });

      expect(screen.getByText("Failed")).toBeInTheDocument();

      act(() => {
        vi.advanceTimersByTime(2000);
      });

      expect(screen.getByText("Copy")).toBeInTheDocument();
    });

    it("disables copy button while copy is in progress", async () => {
      let resolvePromise: () => void;
      vi.mocked(clipboard.copyToClipboard).mockImplementation(
        () =>
          new Promise<void>((resolve) => {
            resolvePromise = resolve;
          }),
      );
      render(<CodeBlock code={SAMPLE_CODE} />);

      const button = screen.getByText("Copy");

      await act(async () => {
        fireEvent.click(button);
      });

      expect(button).toBeDisabled();

      await act(async () => {
        resolvePromise!();
      });
    });

    it("has descriptive aria-label for copy button", () => {
      render(<CodeBlock code="test" language="python" />);
      expect(
        screen.getByRole("button", { name: /Copy python code/ }),
      ).toBeInTheDocument();
    });

    it("includes file path in copy aria-label when provided", () => {
      render(
        <CodeBlock code="test" language="python" filePath="app/main.py" />,
      );
      expect(
        screen.getByRole("button", {
          name: /Copy python code from app\/main\.py/,
        }),
      ).toBeInTheDocument();
    });
  });

  describe("keyboard accessibility", () => {
    it("toggle button is keyboard focusable", () => {
      render(<CodeBlock code={SAMPLE_CODE} />);
      const toggle = screen.getByText("Hide code");
      toggle.focus();
      expect(toggle).toHaveFocus();
    });

    it("copy button is keyboard focusable", () => {
      render(<CodeBlock code={SAMPLE_CODE} />);
      const copyBtn = screen.getByText("Copy");
      copyBtn.focus();
      expect(copyBtn).toHaveFocus();
    });
  });
});
