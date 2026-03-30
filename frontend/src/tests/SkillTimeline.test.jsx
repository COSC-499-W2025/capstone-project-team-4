// frontend/src/tests/SkillTimeline.test.jsx
import "@testing-library/jest-dom";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import axios from "axios";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import SkillTimeline from "@/components/custom/Portfolio/SkillTimeline";
import SkillTimelineDateRow from "@/components/custom/Portfolio/SkillTimelineDateRow";
import { buildSkillSnapshots } from "@/components/custom/Portfolio/utils/skillTimeline";

vi.mock("axios");
vi.mock("@/lib/auth", () => ({
    getAccessToken: vi.fn(),
}));

import { getAccessToken } from "@/lib/auth";

const resizeObserverInstances = [];

class ResizeObserverMock {
    constructor(callback) {
        this.callback = callback;
        resizeObserverInstances.push(this);
    }

    observe() { }
    disconnect() { }
    unobserve() { }
}

function triggerAllResizeObservers() {
    act(() => {
        resizeObserverInstances.forEach((instance) => {
            instance.callback();
        });
    });
}

describe("Skill timeline feature", () => {
    beforeEach(() => {
        vi.clearAllMocks();
        resizeObserverInstances.length = 0;

        global.ResizeObserver = ResizeObserverMock;

        Object.defineProperty(window, "matchMedia", {
            writable: true,
            value: vi.fn().mockImplementation((query) => ({
                matches: false,
                media: query,
                onchange: null,
                addListener: vi.fn(),
                removeListener: vi.fn(),
                addEventListener: vi.fn(),
                removeEventListener: vi.fn(),
                dispatchEvent: vi.fn(),
            })),
        });

        getAccessToken.mockReturnValue("fake-token");

        axios.get.mockImplementation((url) => {
            if (url === "/api/projects") {
                return Promise.resolve({
                    data: [
                        { id: 1, name: "Older Project", created_at: "2026-03-01T10:00:00Z" },
                        { id: 2, name: "Newest Project", created_at: "2026-03-15T10:00:00Z" },
                        { id: 3, name: "Second Project", created_at: "2026-03-14T10:00:00Z" },
                        { id: 4, name: "Third Project", created_at: "2026-03-13T10:00:00Z" },
                    ],
                });
            }

            if (url === "/api/projects/2/skills/timeline") {
                return Promise.resolve({
                    data: {
                        project_id: 2,
                        timeline: [
                            { skill: "React", count: 2 },
                            { skill: "Tailwind", count: 1 },
                        ],
                    },
                });
            }

            if (url === "/api/projects/3/skills/timeline") {
                return Promise.resolve({
                    data: {
                        project_id: 3,
                        timeline: [
                            { skill: "JavaScript", count: 3 },
                            { skill: "React", count: 1 },
                        ],
                    },
                });
            }

            if (url === "/api/projects/4/skills/timeline") {
                return Promise.resolve({
                    data: {
                        project_id: 4,
                        timeline: [{ skill: "Python", count: 1 }],
                    },
                });
            }

            return Promise.reject(new Error(`Unhandled URL: ${url}`));
        });
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    describe("buildSkillSnapshots", () => {
        it("aggregates skills per project and sorts projects by created_at descending", () => {
            const projects = [
                { id: 10, name: "Project A", created_at: "2026-03-10T00:00:00Z" },
                { id: 11, name: "Project B", created_at: "2026-03-12T00:00:00Z" },
            ];

            const timelineResponses = [
                {
                    project_id: 10,
                    timeline: [
                        { skill: "React", count: 2 },
                        { skill: "React", count: 1 },
                        { skill: "CSS", count: 1 },
                    ],
                },
                {
                    project_id: 11,
                    timeline: [
                        { skill: "Python", count: 1 },
                        { skill: "Algorithms", count: 4 },
                    ],
                },
            ];

            const result = buildSkillSnapshots(projects, timelineResponses);

            expect(result).toHaveLength(2);

            expect(result[0]).toMatchObject({
                projectId: 11,
                projectName: "Project B",
            });

            expect(result[1]).toMatchObject({
                projectId: 10,
                projectName: "Project A",
            });

            expect(result[1].skills).toEqual([
                { skill: "React", count: 3 },
                { skill: "CSS", count: 1 },
            ]);

            expect(result[0].skills).toEqual([
                { skill: "Algorithms", count: 4 },
                { skill: "Python", count: 1 },
            ]);
        });

        it("ignores invalid responses and unknown projects", () => {
            const projects = [{ id: 5, name: "Known", created_at: "2026-03-10T00:00:00Z" }];

            const timelineResponses = [
                null,
                { project_id: 999, timeline: [{ skill: "Ghost", count: 1 }] },
                { project_id: 5, timeline: [{ skill: "React", count: 2 }] },
            ];

            const result = buildSkillSnapshots(projects, timelineResponses);

            expect(result).toEqual([
                {
                    projectId: 5,
                    projectName: "Known",
                    createdAt: "2026-03-10T00:00:00Z",
                    skills: [{ skill: "React", count: 2 }],
                },
            ]);
        });
    });

    describe("SkillTimelineDateRow", () => {
        it("reveals more skills in batches while the button shows remaining hidden count", async () => {
            const skills = Array.from({ length: 12 }, (_, index) => ({
                skill: `Skill ${index + 1}`,
                count: 1,
            }));

            render(<SkillTimelineDateRow skills={skills} />);

            const measureNodes = document.querySelectorAll("[data-skill-chip='true']");
            expect(measureNodes.length).toBe(12);

            measureNodes.forEach((node, index) => {
                Object.defineProperty(node, "offsetHeight", {
                    configurable: true,
                    get: () => 20,
                });

                Object.defineProperty(node, "offsetTop", {
                    configurable: true,
                    get: () => (index < 4 ? 0 : 60),
                });
            });

            triggerAllResizeObservers();

            await waitFor(() => {
                expect(screen.getByRole("button", { name: "+9 more" })).toBeInTheDocument();
            });

            fireEvent.click(screen.getByRole("button", { name: "+9 more" }));

            await waitFor(() => {
                expect(screen.getByRole("button", { name: "+1 more" })).toBeInTheDocument();
            });

            fireEvent.click(screen.getByRole("button", { name: "+1 more" }));

            await waitFor(() => {
                expect(screen.queryByRole("button", { name: /\+\d+ more/i })).not.toBeInTheDocument();
            });

            expect(screen.getAllByText("Skill 12").length).toBeGreaterThan(0);
        });
    });

    describe("SkillTimeline component", () => {
        it("shows auth error when user is not logged in", async () => {
            getAccessToken.mockReturnValue(null);

            render(<SkillTimeline />);

            expect(
                await screen.findByText("You must be logged in to view the skill snapshot.")
            ).toBeInTheDocument();

            expect(axios.get).not.toHaveBeenCalled();
        });

        it("loads only the top 3 most recent projects and renders their skills", async () => {
            render(<SkillTimeline />);

            expect(await screen.findByText("Newest Project")).toBeInTheDocument();
            expect(screen.getByText("Second Project")).toBeInTheDocument();
            expect(screen.getByText("Third Project")).toBeInTheDocument();

            expect(screen.queryByText("Older Project")).not.toBeInTheDocument();

            expect(screen.getAllByText("React").length).toBeGreaterThan(0);
            expect(screen.getAllByText("JavaScript").length).toBeGreaterThan(0);
            expect(screen.getAllByText("Python").length).toBeGreaterThan(0);

            expect(axios.get).toHaveBeenCalledWith("/api/projects", {
                headers: { Authorization: "Bearer fake-token" },
            });

            expect(axios.get).toHaveBeenCalledWith("/api/projects/2/skills/timeline", {
                headers: { Authorization: "Bearer fake-token" },
            });
            expect(axios.get).toHaveBeenCalledWith("/api/projects/3/skills/timeline", {
                headers: { Authorization: "Bearer fake-token" },
            });
            expect(axios.get).toHaveBeenCalledWith("/api/projects/4/skills/timeline", {
                headers: { Authorization: "Bearer fake-token" },
            });

            expect(axios.get).not.toHaveBeenCalledWith(
                "/api/projects/1/skills/timeline",
                expect.anything()
            );
        });

        it("shows a helpful message when no projects exist", async () => {
            axios.get.mockResolvedValueOnce({ data: [] });

            render(<SkillTimeline />);

            expect(
                await screen.findByText("No projects found for the current account.")
            ).toBeInTheDocument();
        });

        it("shows partial error message when some timeline requests fail but some succeed", async () => {
            axios.get.mockImplementation((url) => {
                if (url === "/api/projects") {
                    return Promise.resolve({
                        data: [
                            { id: 2, name: "Newest Project", created_at: "2026-03-15T10:00:00Z" },
                            { id: 3, name: "Second Project", created_at: "2026-03-14T10:00:00Z" },
                            { id: 4, name: "Third Project", created_at: "2026-03-13T10:00:00Z" },
                        ],
                    });
                }

                if (url === "/api/projects/2/skills/timeline") {
                    return Promise.resolve({
                        data: {
                            project_id: 2,
                            timeline: [{ skill: "React", count: 2 }],
                        },
                    });
                }

                if (url === "/api/projects/3/skills/timeline") {
                    return Promise.reject({
                        response: { status: 404, data: { detail: "Project not found" } },
                        message: "Request failed",
                    });
                }

                if (url === "/api/projects/4/skills/timeline") {
                    return Promise.resolve({
                        data: {
                            project_id: 4,
                            timeline: [{ skill: "Python", count: 1 }],
                        },
                    });
                }

                return Promise.reject(new Error(`Unhandled URL: ${url}`));
            });

            render(<SkillTimeline />);

            expect(await screen.findByText("Newest Project")).toBeInTheDocument();
            expect(screen.getByText("Third Project")).toBeInTheDocument();

            expect(
                screen.getByText("Some project snapshot data could not be loaded.")
            ).toBeInTheDocument();
        });

        it("shows final error when all timeline requests fail", async () => {
            axios.get.mockImplementation((url) => {
                if (url === "/api/projects") {
                    return Promise.resolve({
                        data: [
                            { id: 2, name: "Newest Project", created_at: "2026-03-15T10:00:00Z" },
                            { id: 3, name: "Second Project", created_at: "2026-03-14T10:00:00Z" },
                            { id: 4, name: "Third Project", created_at: "2026-03-13T10:00:00Z" },
                        ],
                    });
                }

                return Promise.reject({
                    response: { data: { detail: "Failed to load skill snapshot data." } },
                    message: "Request failed",
                });
            });

            render(<SkillTimeline />);

            expect(
                await screen.findByText("Failed to load skill snapshot data.")
            ).toBeInTheDocument();
        });
    });
});