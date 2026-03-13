import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, it, expect, vi, beforeEach } from "vitest";

vi.mock("axios", () => ({
  default: {
    post: vi.fn(),
  },
}));

vi.mock("@/lib/auth", () => ({
  getAccessToken: () => "fake-token",
}));

vi.mock("@/components/Navigation", () => ({
  default: () => <nav>Navigation</nav>,
}));

vi.mock("@/components/custom/Portfolio/TopProjects", () => ({
  default: () => <div data-testid="top-projects" />,
}));

vi.mock("@/components/custom/Portfolio/SkillTimeline", () => ({
  default: () => <div data-testid="skill-timeline" />,
}));

vi.mock("@/components/custom/Portfolio/ActivityHeatmap", () => ({
  default: () => <div data-testid="activity-heatmap" />,
}));

vi.mock("@/components/custom/Portfolio/PrivateModeEditor", () => ({
  default: () => <div data-testid="private-mode-editor" />,
}));

vi.mock("@/components/custom/Portfolio/PublicModeView", () => ({
  default: () => <div data-testid="public-mode-view" />,
}));

import axios from "axios";
import PortfolioPage from "@/pages/Portfolio";

const fakePortfolio = {
  id: 1,
  title: "Full-Stack Software Engineer",
  summary: "A developer with experience across multiple projects.",
  content: {
    projects: [
      { name: "Project A", languages: ["Python"], frameworks: [], resume_highlights: ["Built X"] },
      { name: "Project B", languages: ["JavaScript"], frameworks: ["React"], resume_highlights: [] },
    ],
    skills: ["Backend Development", "Frontend Development"],
  },
};

describe("PortfolioPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // Test 1: loading spinner shows while fetching
  it("shows loading spinner on mount", () => {
    axios.post.mockResolvedValueOnce({ data: fakePortfolio });
    render(
      <MemoryRouter>
        <PortfolioPage />
      </MemoryRouter>
    );
    expect(screen.getByText("Generating your portfolio...")).toBeInTheDocument();
  });

  // Test 2: portfolio title and summary show up after load
  it("displays portfolio title and summary after load", async () => {
    axios.post.mockResolvedValueOnce({ data: fakePortfolio });
    render(
      <MemoryRouter>
        <PortfolioPage />
      </MemoryRouter>
    );
    await waitFor(() => {
      expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Full-Stack Software Engineer");
      expect(screen.getByText("A developer with experience across multiple projects.")).toBeInTheDocument();
    });
  });

  // Test 3: stat cards show correct labels
  it("displays Projects, Skills, and Languages stat card labels", async () => {
    axios.post.mockResolvedValueOnce({ data: fakePortfolio });
    render(
      <MemoryRouter>
        <PortfolioPage />
      </MemoryRouter>
    );
    await waitFor(() => {
      expect(screen.getByText("Projects")).toBeInTheDocument();
      expect(screen.getByText("Skills")).toBeInTheDocument();
      expect(screen.getByText("Languages")).toBeInTheDocument();
    });
  });

  // Test 4: error message shows when API fails
  it("shows error message when portfolio generation fails", async () => {
    axios.post.mockRejectedValueOnce({ message: "Network Error" });
    render(
      <MemoryRouter>
        <PortfolioPage />
      </MemoryRouter>
    );
    await waitFor(() => {
      expect(screen.getByText("Network Error")).toBeInTheDocument();
    });
  });

  // Test 5: private mode is default
  it("renders private mode view by default", async () => {
    axios.post.mockResolvedValueOnce({ data: fakePortfolio });
    render(
      <MemoryRouter>
        <PortfolioPage />
      </MemoryRouter>
    );
    await waitFor(() => {
      expect(screen.getByTestId("top-projects")).toBeInTheDocument();
      expect(screen.getByTestId("private-mode-editor")).toBeInTheDocument();
      expect(screen.queryByTestId("public-mode-view")).not.toBeInTheDocument();
    });
  });

  // Test 6: clicking public switches view
  it("switches to public view when Public button is clicked", async () => {
    axios.post.mockResolvedValueOnce({ data: fakePortfolio });
    render(
      <MemoryRouter>
        <PortfolioPage />
      </MemoryRouter>
    );
    await waitFor(() => screen.getByText("🌐 Public"));
    fireEvent.click(screen.getByText("🌐 Public"));
    expect(screen.getByTestId("public-mode-view")).toBeInTheDocument();
    expect(screen.queryByTestId("top-projects")).not.toBeInTheDocument();
  });

  // Test 7: clicking private switches back
  it("switches back to private view when Private button is clicked", async () => {
    axios.post.mockResolvedValueOnce({ data: fakePortfolio });
    render(
      <MemoryRouter>
        <PortfolioPage />
      </MemoryRouter>
    );
    await waitFor(() => screen.getByText("🌐 Public"));
    fireEvent.click(screen.getByText("🌐 Public"));
    fireEvent.click(screen.getByText("🔒 Private"));
    expect(screen.getByTestId("top-projects")).toBeInTheDocument();
    expect(screen.queryByTestId("public-mode-view")).not.toBeInTheDocument();
  });
});
