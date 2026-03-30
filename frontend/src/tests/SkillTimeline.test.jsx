import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import axios from "axios";
import { beforeEach, describe, expect, it, vi } from "vitest";

import SkillTimeline from "../components/custom/Portfolio/SkillTimeline";

vi.mock("axios");
vi.mock("@/lib/auth", () => ({
    getAccessToken: () => "test-token",
}));

describe("SkillTimeline", () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it("loads snapshot skills and builds chronological timeline on button click", async () => {
        axios.get.mockImplementation((url) => {
            if (url === "/api/projects") {
                return Promise.resolve({
                    data: [
                        {
                            id: 8,
                            name: "TicketApprentice - Website",
                            total_lines_of_code: 1000,
                        },
                        {
                            id: 9,
                            name: "gstack-main",
                            total_lines_of_code: 900,
                        },
                    ],
                });
            }

            if (url === "/api/projects/8/skills") {
                return Promise.resolve({
                    data: {
                        project_name: "TicketApprentice - Website",
                        skills: ["JavaScript", "Unit Testing", "Node.js"],
                    },
                });
            }

            if (url === "/api/projects/9/skills") {
                return Promise.resolve({
                    data: {
                        project_name: "gstack-main",
                        skills: ["Automation", "CI/CD"],
                    },
                });
            }

            return Promise.reject(new Error(`Unexpected GET ${url}`));
        });

        axios.post.mockImplementation((url) => {
            if (url === "/api/projects/8/skills/timeline/build") {
                return Promise.resolve({
                    data: {
                        project_id: 8,
                        timeline: [
                            {
                                skill: "JavaScript",
                                date: "2023-05-20T12:00:00",
                                count: 3,
                            },
                            {
                                skill: "Unit Testing",
                                date: "2023-05-20T12:00:00",
                                count: 1,
                            },
                        ],
                    },
                });
            }

            return Promise.reject(new Error(`Unexpected POST ${url}`));
        });

        render(<SkillTimeline />);

        expect(
            await screen.findByText("Skills demonstrated across top 3 projects")
        ).toBeInTheDocument();

        expect(await screen.findByText("JavaScript")).toBeInTheDocument();
        expect(screen.getByText("Unit Testing")).toBeInTheDocument();
        expect(screen.getByText("Node.js")).toBeInTheDocument();

        const buttons = await screen.findAllByRole("button", {
            name: /view chronological timeline/i,
        });

        fireEvent.click(buttons[0]);

        await waitFor(() => {
            expect(axios.post).toHaveBeenCalledWith(
                "/api/projects/8/skills/timeline/build",
                {},
                {
                    headers: {
                        Authorization: "Bearer test-token",
                    },
                }
            );
        });

        expect(
            await screen.findByText("Chronological Timeline")
        ).toBeInTheDocument();
        expect(
            await screen.findByText("Chronological Timeline")
        ).toBeInTheDocument();

        const timelineDates = await screen.findAllByText("2023-05-20T12:00:00");
        expect(timelineDates.length).toBeGreaterThan(0);

        expect(screen.getByText("Count: 3")).toBeInTheDocument();
        expect(screen.getByText("Count: 1")).toBeInTheDocument();
    });
});