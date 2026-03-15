import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

vi.mock("axios", () => ({
  default: { get: vi.fn() },
}));

vi.mock("@/components/custom/Generator/EditProjectModal", () => ({
  default: ({ isOpen, onClose, onSave, project }) =>
    isOpen ? (
      <div data-testid="edit-modal">
        <button onClick={onClose}>Close</button>
        <button onClick={() => onSave({ ...project, name: "Edited Name" })}>
          Save
        </button>
      </div>
    ) : null,
}));

import axios from "axios";
import ProjectSummary from "@/components/custom/Generator/ProjectSummary";

const makeContributorsResponse = () => ({
  project_id: 5,
  project_name: "Test Project",
  total_contributors: 2,
  total_commits: 18,
  contributors: [
    {
      id: 11,
      name: "Alice",
      email: "alice@example.com",
      github_username: "alicehub",
      commits: 12,
      changes: {
        total_lines_changed: 120,
        files_changed: 5,
      },
    },
    {
      id: 22,
      name: "Bob",
      email: "bob@example.com",
      github_username: "bobhub",
      commits: 6,
      changes: {
        total_lines_changed: 60,
        files_changed: 3,
      },
    },
  ],
});

const makeAnalysisResponse = (overrides = {}) => ({
  contributor: {
    contributor_id: 11,
    name: "Alice",
    summary: {
      top_areas: [
        { area: "backend", share: 0.75 },
        { area: "frontend", share: 0.25 },
      ],
      top_files: [
        {
          file: "backend/src/services/contributor_analysis_service.py",
          lines_changed: 420,
        },
        { file: "frontend/src/pages/Dashboard.jsx", lines_changed: 180 },
      ],
    },
  },
  ...overrides,
});

const makeDirectoriesResponse = (overrides = {}) => ({
  contributor_id: 11,
  top_directories: [
    {
      directory: "backend/src/services",
      lines_changed: 420,
      share: 0.7,
      files_count: 5,
    },
    {
      directory: "frontend/src/components",
      lines_changed: 180,
      share: 0.3,
      files_count: 3,
    },
  ],
  ...overrides,
});

const makeProject = (overrides = {}) => ({
  projectId: 1,
  name: "Test Project",
  contributions: 42,
  contributorCount: 3,
  date: "2026-03-08T00:00:00Z",
  projectStartedAt: "2025-01-01T00:00:00Z",
  totalLinesOfCode: 1500,
  languages: ["JavaScript", "Python"],
  frameworks: ["React"],
  skills: ["Frontend"],
  toolsAndTechnologies: ["Docker"],
  description: "A test project",
  complexity: {
    total_functions: 10,
    avg_complexity: 2.5,
    max_complexity: 8,
    high_complexity_count: 1,
  },
  ...overrides,
});

describe("ProjectSummary", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders nothing when projects is null", () => {
    const { container } = render(<ProjectSummary projects={null} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders nothing when projects is empty", () => {
    const { container } = render(<ProjectSummary projects={[]} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders the project name", () => {
    render(<ProjectSummary projects={[makeProject()]} />);
    expect(screen.getByText("Test Project")).toBeInTheDocument();
  });

  it("displays files analyzed count", () => {
    render(<ProjectSummary projects={[makeProject({ contributions: 99 })]} />);
    expect(screen.getByText("99")).toBeInTheDocument();
  });

  it("displays contributor count", () => {
    render(
      <ProjectSummary projects={[makeProject({ contributorCount: 5 })]} />,
    );
    expect(screen.getByText("5")).toBeInTheDocument();
  });

  it("shows total lines of code when > 0", () => {
    render(
      <ProjectSummary projects={[makeProject({ totalLinesOfCode: 1500 })]} />,
    );
    expect(screen.getByText("1,500")).toBeInTheDocument();
  });

  it("hides lines of code section when totalLinesOfCode is 0", () => {
    render(
      <ProjectSummary projects={[makeProject({ totalLinesOfCode: 0 })]} />,
    );
    expect(screen.queryByText("Total Lines of Code")).not.toBeInTheDocument();
  });

  it("hides lines of code section when totalLinesOfCode is missing", () => {
    render(
      <ProjectSummary
        projects={[makeProject({ totalLinesOfCode: undefined })]}
      />,
    );
    expect(screen.queryByText("Total Lines of Code")).not.toBeInTheDocument();
  });

  it("renders language badges", () => {
    render(
      <ProjectSummary
        projects={[makeProject({ languages: ["Java", "XML"] })]}
      />,
    );
    expect(screen.getByText("Java")).toBeInTheDocument();
    expect(screen.getByText("XML")).toBeInTheDocument();
  });

  it("hides languages section when languages array is empty", () => {
    render(<ProjectSummary projects={[makeProject({ languages: [] })]} />);
    expect(screen.queryByText("Languages:")).not.toBeInTheDocument();
  });

  it("renders complexity metrics", () => {
    render(<ProjectSummary projects={[makeProject()]} />);
    expect(screen.getByText("Total Functions:")).toBeInTheDocument();
    expect(screen.getByText("10")).toBeInTheDocument();
    expect(screen.getByText("Avg Complexity:")).toBeInTheDocument();
    expect(screen.getByText("2.50")).toBeInTheDocument();
    expect(screen.getByText("Max Complexity:")).toBeInTheDocument();
    expect(screen.getByText("8")).toBeInTheDocument();
  });

  it("shows high complexity count when > 0", () => {
    render(
      <ProjectSummary
        projects={[
          makeProject({
            complexity: {
              high_complexity_count: 7,
              total_functions: 10,
              avg_complexity: 2,
              max_complexity: 5,
            },
          }),
        ]}
      />,
    );
    expect(screen.getByText("High Complexity Functions:")).toBeInTheDocument();
    expect(screen.getByText("7")).toBeInTheDocument();
  });

  it("hides high complexity count when 0", () => {
    render(
      <ProjectSummary
        projects={[
          makeProject({
            complexity: {
              high_complexity_count: 0,
              total_functions: 5,
              avg_complexity: 1,
              max_complexity: 2,
            },
          }),
        ]}
      />,
    );
    expect(
      screen.queryByText("High Complexity Functions:"),
    ).not.toBeInTheDocument();
  });

  it("hides complexity section when complexity is empty", () => {
    render(<ProjectSummary projects={[makeProject({ complexity: {} })]} />);
    expect(screen.queryByText("Complexity Metrics:")).not.toBeInTheDocument();
  });

  it("shows N/A for missing dates", () => {
    render(
      <ProjectSummary
        projects={[makeProject({ date: null, projectStartedAt: null })]}
      />,
    );
    const naElements = screen.getAllByText("N/A");
    expect(naElements.length).toBeGreaterThanOrEqual(2);
  });

  it("renders the description", () => {
    render(
      <ProjectSummary
        projects={[makeProject({ description: "A cool project" })]}
      />,
    );
    expect(screen.getByText("A cool project")).toBeInTheDocument();
  });

  it("hides description when not provided", () => {
    render(<ProjectSummary projects={[makeProject({ description: null })]} />);
    expect(screen.queryByText("Description:")).not.toBeInTheDocument();
  });

  it("renders frameworks and tools badges", () => {
    render(<ProjectSummary projects={[makeProject()]} />);
    expect(screen.getByText("React")).toBeInTheDocument();
    expect(screen.getByText("Docker")).toBeInTheDocument();
  });

  it("shows +N more badge when languages exceed 8", () => {
    const manyLanguages = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"];
    render(
      <ProjectSummary projects={[makeProject({ languages: manyLanguages })]} />,
    );
    expect(screen.getByText("+2 more")).toBeInTheDocument();
  });

  it("expands language list when clicking +N more", () => {
    const manyLanguages = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"];
    render(
      <ProjectSummary projects={[makeProject({ languages: manyLanguages })]} />,
    );
    fireEvent.click(screen.getByText("+2 more"));
    expect(screen.getByText("I")).toBeInTheDocument();
    expect(screen.getByText("J")).toBeInTheDocument();
  });

  it("sorts by date by default (newest first)", () => {
    const projects = [
      makeProject({
        projectId: 1,
        name: "Older",
        date: "2025-01-01T00:00:00Z",
      }),
      makeProject({
        projectId: 2,
        name: "Newer",
        date: "2026-01-01T00:00:00Z",
      }),
    ];
    render(<ProjectSummary projects={projects} />);
    const cards = screen.getAllByText(/Older|Newer/);
    expect(cards[0].textContent).toBe("Newer");
    expect(cards[1].textContent).toBe("Older");
  });

  it("renders multiple project cards", () => {
    const projects = [
      makeProject({ projectId: 1, name: "Project Alpha" }),
      makeProject({ projectId: 2, name: "Project Beta" }),
    ];
    render(<ProjectSummary projects={projects} />);
    expect(screen.getByText("Project Alpha")).toBeInTheDocument();
    expect(screen.getByText("Project Beta")).toBeInTheDocument();
  });

  it("opens edit modal when edit button is clicked", () => {
    render(<ProjectSummary projects={[makeProject()]} />);
    const editButtons = screen
      .getAllByRole("button")
      .filter((b) => b.querySelector("svg"));
    fireEvent.click(editButtons[0]);
    expect(screen.getByTestId("edit-modal")).toBeInTheDocument();
  });

  it("closes edit modal when onClose is called", () => {
    render(<ProjectSummary projects={[makeProject()]} />);
    const editButtons = screen
      .getAllByRole("button")
      .filter((b) => b.querySelector("svg"));
    fireEvent.click(editButtons[0]);
    expect(screen.getByTestId("edit-modal")).toBeInTheDocument();
    fireEvent.click(screen.getByText("Close"));
    expect(screen.queryByTestId("edit-modal")).not.toBeInTheDocument();
  });

  it("calls onUpdateProject with updated data when saving", () => {
    const onUpdateProject = vi.fn();
    render(
      <ProjectSummary
        projects={[makeProject()]}
        onUpdateProject={onUpdateProject}
      />,
    );
    const editButtons = screen
      .getAllByRole("button")
      .filter((b) => b.querySelector("svg"));
    fireEvent.click(editButtons[0]);
    fireEvent.click(screen.getByText("Save"));
    expect(onUpdateProject).toHaveBeenCalledWith(
      0,
      expect.objectContaining({ name: "Edited Name" }),
    );
  });

  it("opens contributor modal and loads the first contributor insights", async () => {
    axios.get
      .mockResolvedValueOnce({ data: makeContributorsResponse() })
      .mockResolvedValueOnce({ data: makeAnalysisResponse() })
      .mockResolvedValueOnce({ data: makeDirectoriesResponse() });

    render(
      <ProjectSummary
        projects={[makeProject({ projectId: 5, contributorCount: 2 })]}
      />,
    );
    fireEvent.click(screen.getByText("2"));

    await waitFor(() => {
      expect(
        screen.getByText(
          "Browse contributors and inspect their top areas, files, and directories.",
        ),
      ).toBeInTheDocument();
    });
    await waitFor(() => {
      expect(
        screen.getByText(
          "backend/src/services/contributor_analysis_service.py",
        ),
      ).toBeInTheDocument();
    });
    expect(screen.getAllByText("Alice").length).toBeGreaterThan(0);
    expect(screen.getByText("backend/src/services")).toBeInTheDocument();
    expect(axios.get).toHaveBeenNthCalledWith(
      1,
      "/api/projects/5/contributors",
    );
    expect(axios.get).toHaveBeenNthCalledWith(
      2,
      "/api/projects/5/contributors/11/analysis",
    );
    expect(axios.get).toHaveBeenNthCalledWith(
      3,
      "/api/projects/5/contributors/11/directories",
    );
  });

  it("loads another contributor when selected from the list", async () => {
    axios.get
      .mockResolvedValueOnce({ data: makeContributorsResponse() })
      .mockResolvedValueOnce({ data: makeAnalysisResponse() })
      .mockResolvedValueOnce({ data: makeDirectoriesResponse() })
      .mockResolvedValueOnce({
        data: makeAnalysisResponse({
          contributor: {
            contributor_id: 22,
            name: "Bob",
            summary: {
              top_areas: [{ area: "frontend", share: 1 }],
              top_files: [{ file: "frontend/src/App.jsx", lines_changed: 50 }],
            },
          },
        }),
      })
      .mockResolvedValueOnce({
        data: makeDirectoriesResponse({
          contributor_id: 22,
          top_directories: [
            {
              directory: "frontend/src",
              lines_changed: 50,
              share: 1,
              files_count: 2,
            },
          ],
        }),
      });

    render(
      <ProjectSummary
        projects={[makeProject({ projectId: 5, contributorCount: 2 })]}
      />,
    );
    fireEvent.click(screen.getByText("2"));

    await waitFor(() => {
      expect(screen.getByText("Bob")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /Bob/i }));

    await waitFor(() => {
      expect(screen.getByText("frontend/src/App.jsx")).toBeInTheDocument();
    });

    expect(axios.get).toHaveBeenNthCalledWith(
      4,
      "/api/projects/5/contributors/22/analysis",
    );
    expect(axios.get).toHaveBeenNthCalledWith(
      5,
      "/api/projects/5/contributors/22/directories",
    );
  });

  it("shows error message when contributor list fetch fails", async () => {
    axios.get.mockRejectedValue({ message: "Network Error" });

    render(
      <ProjectSummary
        projects={[makeProject({ projectId: 5, contributorCount: 2 })]}
      />,
    );
    fireEvent.click(screen.getByText("2"));

    await waitFor(() => {
      expect(screen.getByText("Network Error")).toBeInTheDocument();
    });
  });

  it("shows directory error while still rendering analysis data", async () => {
    axios.get
      .mockResolvedValueOnce({ data: makeContributorsResponse() })
      .mockResolvedValueOnce({ data: makeAnalysisResponse() })
      .mockRejectedValueOnce({ message: "Directory fetch failed" });

    render(
      <ProjectSummary
        projects={[makeProject({ projectId: 5, contributorCount: 2 })]}
      />,
    );
    fireEvent.click(screen.getByText("2"));

    await waitFor(() => {
      expect(screen.getByText("backend")).toBeInTheDocument();
    });

    expect(screen.getByText("Directory fetch failed")).toBeInTheDocument();
    expect(
      screen.getByText("backend/src/services/contributor_analysis_service.py"),
    ).toBeInTheDocument();
  });
});
