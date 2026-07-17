export interface CategoryConfig {
  id: string;
  label: string;
  description: string;
}

export const CATEGORIES: CategoryConfig[] = [
  {
    id: "structured_data",
    label: "Structured Data",
    description: "Schema markup and structured data issues",
  },
  {
    id: "commercial_trust",
    label: "Trust & Policy",
    description: "Trust signals and policy surface issues",
  },
  {
    id: "document_structure",
    label: "Document Structure",
    description: "Heading hierarchy and document structure issues",
  },
];

export const UNCATORIZED_CATEGORY: CategoryConfig = {
  id: "other",
  label: "Other",
  description: "Uncategorised issues",
};

export const SEVERITY_ORDER: Record<string, number> = {
  high: 0,
  medium: 1,
  low: 2,
};

export const SEVERITY_LABELS: Record<string, string> = {
  high: "High",
  medium: "Medium",
  low: "Low",
};