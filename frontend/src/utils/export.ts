import type { Fix } from "../types/audit";

export function downloadTextFile(
  filename: string,
  content: string,
  mimeType: string,
): void {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export function buildJsonExportContent(value: unknown): string {
  return JSON.stringify(value, null, 2);
}

export function buildFixesExportContent(fixes: Fix[]): string {
  if (fixes.length === 0) {
    return "No fixes to export.";
  }

  let content = "# Agentic Fixer - Suggested Fixes\n\n";

  fixes.forEach((fix, index) => {
    content += `## ${index + 1}. ${fix.title}\n\n`;
    content += `**Issue ID:** ${fix.issue_id}\n`;
    content += `**Priority:** ${fix.priority}\n\n`;
    content += `### Why it matters\n\n${fix.why_it_matters}\n\n`;

    if (fix.instructions.length > 0) {
      content += `### Instructions\n\n`;
      fix.instructions.forEach((instruction, i) => {
        content += `${i + 1}. ${instruction}\n`;
      });
      content += "\n";
    }

    if (fix.code_snippet) {
      content += `### Code snippet\n\n\`\`\`html\n${fix.code_snippet}\n\`\`\`\n\n`;
    }

    content += "---\n\n";
  });

  return content;
}
