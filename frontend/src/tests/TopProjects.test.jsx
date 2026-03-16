import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import TopProjects from "@/components/custom/Portfolio/TopProjects";

const makePortfolio = (projects) => ({
  content: { projects },
});

const fakeProjects = [
  {
    name: "Project Alpha",
    languages: ["Python", "SQL"],
    frameworks: ["FastAPI"],
    resume_highlights: ["Built REST API", "Improved performance by 30%"],
    total_lines_of_code: 3000,
  },
  {
    name: "Project Beta",
    languages: ["JavaScript"],
    frameworks: ["React"],
    resume_highlights: ["Developed frontend dashboard"],
    total_lines_of_code: 2000,
  },
  {
    name: "Project Gamma",
    languages: ["Java"],
    frameworks: [],
    resume_highlights: [],
    total_lines_of_code: 1000,
  },
  {
    name: "Project Delta",
    languages: ["TypeScript"],
    frameworks: [],
    resume_highlights: [],
    total_lines_of_code: 500,
  },
];

describe("TopProjects", () => {

  // Test 1: section heading renders
  it("renders the Projects heading", () => {
    render(<TopProjects portfolio={makePortfolio(fakeProjects)} />);
    expect(screen.getByText("Projects")).toBeInTheDocument();
  });

  // Test 2: empty state when no projects
  it("shows empty state when projects list is empty", () => {
    render(<TopProjects portfolio={makePortfolio([])} />);
    expect(screen.getByText("No projects found. Upload a project to get started.")).toBeInTheDocument();
  });

  // Test 3: only top 3 shown, 4th is excluded
  it("only renders the top 3 projects and not the 4th", () => {
    render(<TopProjects portfolio={makePortfolio(fakeProjects)} />);
    expect(screen.getByText("Project Alpha")).toBeInTheDocument();
    expect(screen.getByText("Project Beta")).toBeInTheDocument();
    expect(screen.getByText("Project Gamma")).toBeInTheDocument();
    expect(screen.queryByText("Project Delta")).not.toBeInTheDocument();
  });

  // Test 4: rank badges show
  it("displays rank badges #1 #2 #3", () => {
    render(<TopProjects portfolio={makePortfolio(fakeProjects)} />);
    expect(screen.getByText("#1")).toBeInTheDocument();
    expect(screen.getByText("#2")).toBeInTheDocument();
    expect(screen.getByText("#3")).toBeInTheDocument();
  });

  // Test 5: language tags render correctly
  it("renders language tags for each project", () => {
    render(<TopProjects portfolio={makePortfolio(fakeProjects)} />);
    expect(screen.getByText("Python")).toBeInTheDocument();
    expect(screen.getByText("SQL")).toBeInTheDocument();
    expect(screen.getByText("JavaScript")).toBeInTheDocument();
  });

  // Test 6: resume highlights show up
  it("renders resume highlights", () => {
    render(<TopProjects portfolio={makePortfolio(fakeProjects)} />);
    expect(screen.getByText("Built REST API")).toBeInTheDocument();
    expect(screen.getByText("Improved performance by 30%")).toBeInTheDocument();
  });

  // Test 7: custom_name overrides name
  it("displays custom_name instead of name when set", () => {
    const projects = [{
      name: "raw-name",
      custom_name: "My Custom Project",
      languages: [],
      frameworks: [],
      resume_highlights: [],
      total_lines_of_code: 100,
    }];
    render(<TopProjects portfolio={makePortfolio(projects)} />);
    expect(screen.getByText("My Custom Project")).toBeInTheDocument();
    expect(screen.queryByText("raw-name")).not.toBeInTheDocument();
  });

  // Test 8: live demo link renders when url is provided
  it("renders a live demo link when live_demo_url is set", () => {
    const projects = [{
      name: "Demo Project",
      languages: [],
      frameworks: [],
      resume_highlights: [],
      total_lines_of_code: 100,
      live_demo_url: "https://example.com",
    }];
    render(<TopProjects portfolio={makePortfolio(projects)} />);
    const link = screen.getByRole("link");
    expect(link).toHaveAttribute("href", "https://example.com");
  });
});
