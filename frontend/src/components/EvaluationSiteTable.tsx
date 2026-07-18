import { useState, useMemo } from "react";
import type { SiteResult } from "../types/evaluation";

type SortField = "name" | "page_type" | "status" | "score" | "duration" | "issues";
type SortDirection = "asc" | "desc";
type FilterStatus = "all" | "success" | "failure";
type FilterPageType = "all" | "pricing" | "faq" | "ecommerce" | "service" | "general";
type FilterWarnings = "all" | "with_warnings" | "without_warnings";

interface EvaluationSiteTableProps {
  results: SiteResult[];
  onInspect?: (site: SiteResult) => void;
}

function getDomain(url: string): string {
  try {
    return new URL(url).hostname;
  } catch {
    return url;
  }
}

function formatDuration(ms: number): string {
  if (ms < 1000) return `${Math.round(ms)}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

function getScoreClass(score: number): string {
  if (score >= 80) return "score-high";
  if (score >= 50) return "score-medium";
  return "score-low";
}

export function EvaluationSiteTable({ results, onInspect }: EvaluationSiteTableProps) {
  const [search, setSearch] = useState("");
  const [sortField, setSortField] = useState<SortField>("name");
  const [sortDirection, setSortDirection] = useState<SortDirection>("asc");
  const [filterStatus, setFilterStatus] = useState<FilterStatus>("all");
  const [filterPageType, setFilterPageType] = useState<FilterPageType>("all");
  const [filterWarnings, setFilterWarnings] = useState<FilterWarnings>("all");

  const filteredResults = useMemo(() => {
    let filtered = results;

    // Search filter
    if (search.trim()) {
      const searchLower = search.toLowerCase();
      filtered = filtered.filter(
        (site) =>
          site.name.toLowerCase().includes(searchLower) ||
          getDomain(site.url).toLowerCase().includes(searchLower)
      );
    }

    // Status filter
    if (filterStatus !== "all") {
      filtered = filtered.filter((site) => site.status === filterStatus);
    }

    // Page type filter
    if (filterPageType !== "all") {
      filtered = filtered.filter((site) => site.page_type === filterPageType);
    }

    // Warnings filter
    if (filterWarnings === "with_warnings") {
      filtered = filtered.filter(
        (site) =>
          site.status === "failure" ||
          (site.status === "success" && site.issue_count > 0)
      );
    } else if (filterWarnings === "without_warnings") {
      filtered = filtered.filter(
        (site) =>
          site.status === "success" && site.issue_count === 0
      );
    }

    // Sorting
    return [...filtered].sort((a, b) => {
      let comparison = 0;
      switch (sortField) {
        case "name":
          comparison = a.name.localeCompare(b.name);
          break;
        case "page_type":
          comparison = a.page_type.localeCompare(b.page_type);
          break;
        case "status":
          comparison = a.status.localeCompare(b.status);
          break;
        case "score":
          comparison =
            (a.status === "success" ? a.score : 0) -
            (b.status === "success" ? b.score : 0);
          break;
        case "duration":
          comparison = a.duration_ms - b.duration_ms;
          break;
        case "issues":
          comparison =
            (a.status === "success" ? a.issue_count : 1) -
            (b.status === "success" ? b.issue_count : 1);
          break;
      }
      return sortDirection === "asc" ? comparison : -comparison;
    });
  }, [results, search, sortField, sortDirection, filterStatus, filterPageType, filterWarnings]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDirection("asc");
    }
  };

  const getSortIndicator = (field: SortField) => {
    if (sortField !== field) return "↕";
    return sortDirection === "asc" ? "↑" : "↓";
  };

  if (results.length === 0) {
    return (
      <div className="site-table-empty" role="status">
        No evaluation results available
      </div>
    );
  }

  return (
    <div className="site-table-container">
      <div className="site-table-filters">
        <div className="site-table-search">
          <label htmlFor="site-search">Search</label>
          <input
            id="site-search"
            type="search"
            placeholder="Search by name or domain..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            aria-label="Search sites by name or domain"
          />
        </div>
        <div className="site-table-filter">
          <label htmlFor="filter-status">Status</label>
          <select
            id="filter-status"
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value as FilterStatus)}
            aria-label="Filter by status"
          >
            <option value="all">All Status</option>
            <option value="success">Success</option>
            <option value="failure">Failure</option>
          </select>
        </div>
        <div className="site-table-filter">
          <label htmlFor="filter-page-type">Page Type</label>
          <select
            id="filter-page-type"
            value={filterPageType}
            onChange={(e) => setFilterPageType(e.target.value as FilterPageType)}
            aria-label="Filter by page type"
          >
            <option value="all">All Types</option>
            <option value="pricing">Pricing</option>
            <option value="faq">FAQ</option>
            <option value="ecommerce">E-commerce</option>
            <option value="service">Service</option>
            <option value="general">General</option>
          </select>
        </div>
        <div className="site-table-filter">
          <label htmlFor="filter-warnings">Warnings</label>
          <select
            id="filter-warnings"
            value={filterWarnings}
            onChange={(e) => setFilterWarnings(e.target.value as FilterWarnings)}
            aria-label="Filter by warning presence"
          >
            <option value="all">All</option>
            <option value="with_warnings">With Warnings</option>
            <option value="without_warnings">Without Warnings</option>
          </select>
        </div>
      </div>

      {filteredResults.length === 0 ? (
        <div className="site-table-empty" role="status">
          No results match your filters
        </div>
      ) : (
        <div className="site-table-scroll">
          <table className="site-table" aria-label="Evaluation results">
            <thead>
              <tr>
                <th scope="col">
                  <button
                    type="button"
                    className="sort-button"
                    onClick={() => handleSort("name")}
                    aria-label={`Sort by name ${getSortIndicator("name")}`}
                  >
                    Name {getSortIndicator("name")}
                  </button>
                </th>
                <th scope="col">URL</th>
                <th scope="col">
                  <button
                    type="button"
                    className="sort-button"
                    onClick={() => handleSort("page_type")}
                    aria-label={`Sort by page type ${getSortIndicator("page_type")}`}
                  >
                    Page Type {getSortIndicator("page_type")}
                  </button>
                </th>
                <th scope="col">
                  <button
                    type="button"
                    className="sort-button"
                    onClick={() => handleSort("status")}
                    aria-label={`Sort by status ${getSortIndicator("status")}`}
                  >
                    Status {getSortIndicator("status")}
                  </button>
                </th>
                <th scope="col">
                  <button
                    type="button"
                    className="sort-button"
                    onClick={() => handleSort("score")}
                    aria-label={`Sort by score ${getSortIndicator("score")}`}
                  >
                    Score {getSortIndicator("score")}
                  </button>
                </th>
                <th scope="col">
                  <button
                    type="button"
                    className="sort-button"
                    onClick={() => handleSort("issues")}
                    aria-label={`Sort by issues ${getSortIndicator("issues")}`}
                  >
                    Issues {getSortIndicator("issues")}
                  </button>
                </th>
                <th scope="col">
                  <button
                    type="button"
                    className="sort-button"
                    onClick={() => handleSort("duration")}
                    aria-label={`Sort by duration ${getSortIndicator("duration")}`}
                  >
                    Duration {getSortIndicator("duration")}
                  </button>
                </th>
                <th scope="col">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredResults.map((site) => {
                const isFailure = site.status === "failure";
                const successSite = site.status === "success" ? site : null;
                return (
                  <tr
                    key={site.url}
                    className={isFailure ? "row-failure" : "row-success"}
                  >
                    <td data-label="Name">{site.name}</td>
                    <td data-label="URL">
                      <a
                        href={site.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="site-url-link"
                      >
                        {getDomain(site.url)}
                        <span className="sr-only">(opens in new tab)</span>
                      </a>
                    </td>
                    <td data-label="Page Type">
                      <span className="badge badge-type">{site.page_type}</span>
                    </td>
                    <td data-label="Status">
                      <span
                        className={`badge ${
                          isFailure ? "badge-failure" : "badge-success"
                        }`}
                      >
                        {site.status}
                      </span>
                    </td>
                    <td data-label="Score">
                      {isFailure ? (
                        <span className="score-na">N/A</span>
                      ) : (
                        <span className={`score ${getScoreClass(successSite!.score)}`}>
                          {successSite!.score}
                        </span>
                      )}
                    </td>
                    <td data-label="Issues">
                      {isFailure ? (
                        <span className="error-category">{site.error_category}</span>
                      ) : (
                        <span className="issue-count">{successSite!.issue_count}</span>
                      )}
                    </td>
                    <td data-label="Duration">{formatDuration(site.duration_ms)}</td>
                    <td data-label="Actions">
                      {onInspect && (
                        <button
                          type="button"
                          className="inspect-button"
                          onClick={() => onInspect(site)}
                          aria-label={`Inspect audit data for ${site.name}`}
                        >
                          Inspect
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      <div className="site-table-count" aria-live="polite">
        Showing {filteredResults.length} of {results.length} sites
      </div>
    </div>
  );
}
