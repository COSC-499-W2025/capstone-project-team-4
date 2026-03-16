import { getAccessToken } from "@/lib/auth";
import axios from "axios";
import { useEffect, useMemo, useRef, useState } from "react";

import SkillTimelineDateRow from "./SkillTimelineDateRow";
import { buildSkillSnapshots } from "./utils/skillTimeline";

const SCROLL_MAX_HEIGHT = 420;

function SkillTimelineSkeleton() {
    return (
        <div className="space-y-5">
            {[1, 2, 3].map((item) => (
                <div
                    key={item}
                    className="rounded-xl border border-border/60 bg-background/50 p-4"
                >
                    <div className="mb-3 h-5 w-40 animate-pulse rounded bg-muted" />
                    <div className="flex flex-wrap gap-2">
                        {[1, 2, 3, 4, 5].map((chip) => (
                            <div
                                key={chip}
                                className="h-7 w-24 animate-pulse rounded-full bg-muted"
                            />
                        ))}
                    </div>
                </div>
            ))}
        </div>
    );
}

function ProjectSnapshotCard({ projectGroup }) {
    return (
        <div className="rounded-xl border border-border/60 bg-background/50 p-4">
            <div className="mb-4">
                <h3 className="text-sm font-semibold text-foreground">
                    {projectGroup.projectName}
                </h3>
            </div>

            {projectGroup.skills.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                    No skill snapshot data available for this project.
                </p>
            ) : (
                <SkillTimelineDateRow skills={projectGroup.skills} />
            )}
        </div>
    );
}

export default function SkillTimeline() {
    const [projectSnapshots, setProjectSnapshots] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState("");
    const [partialError, setPartialError] = useState(false);
    const [isScrollable, setIsScrollable] = useState(false);

    const scrollContentRef = useRef(null);

    const authHeader = useMemo(() => {
        const token = getAccessToken();
        return token ? { Authorization: `Bearer ${token}` } : null;
    }, []);

    useEffect(() => {
        let isCancelled = false;

        async function loadTimeline() {
            setIsLoading(true);
            setError("");
            setPartialError(false);

            if (!authHeader) {
                setError("You must be logged in to view the skill snapshot.");
                setIsLoading(false);
                return;
            }

            try {
                const projectsRes = await axios.get("/api/projects", {
                    headers: authHeader,
                });

                const allProjects = Array.isArray(projectsRes.data)
                    ? projectsRes.data
                    : Array.isArray(projectsRes.data?.projects)
                        ? projectsRes.data.projects
                        : Array.isArray(projectsRes.data?.items)
                            ? projectsRes.data.items
                            : Array.isArray(projectsRes.data?.data)
                                ? projectsRes.data.data
                                : [];

                const topThreeProjects = [...allProjects]
                    .sort((a, b) => (b.total_lines_of_code || 0) - (a.total_lines_of_code || 0))
                    .slice(0, 3);

                if (topThreeProjects.length === 0) {
                    setError("No projects found for the current account.");
                    setProjectSnapshots([]);
                    return;
                }

                const results = await Promise.allSettled(
                    topThreeProjects.map((project) =>
                        axios.get(
                            `/api/projects/${project.project_id ?? project.id}/skills/timeline`,
                            {
                                headers: authHeader,
                            }
                        )
                    )
                );

                if (isCancelled) return;

                const successfulResponses = results
                    .filter((result) => result.status === "fulfilled")
                    .map((result) => result.value.data);

                const failedResponses = results.filter(
                    (result) => result.status === "rejected"
                );

                if (failedResponses.length > 0) {
                    setPartialError(successfulResponses.length > 0);
                }

                if (successfulResponses.length === 0) {
                    const firstError = failedResponses[0]?.reason;
                    const detail =
                        firstError?.response?.data?.detail ||
                        firstError?.message ||
                        "Failed to load skill snapshot data.";
                    setError(detail);
                    setProjectSnapshots([]);
                    return;
                }

                const grouped = buildSkillSnapshots(topThreeProjects, successfulResponses);
                setProjectSnapshots(grouped);
            } catch (err) {
                if (!isCancelled) {
                    setError(
                        err?.response?.data?.detail ||
                        err?.message ||
                        "Failed to load skill snapshot data."
                    );
                    setProjectSnapshots([]);
                }
            } finally {
                if (!isCancelled) {
                    setIsLoading(false);
                }
            }
        }

        loadTimeline();

        return () => {
            isCancelled = true;
        };
    }, [authHeader]);

    useEffect(() => {
        const content = scrollContentRef.current;
        if (!content) return;

        const updateScrollable = () => {
            const visibleHeight = content.getBoundingClientRect().height;
            setIsScrollable(visibleHeight > SCROLL_MAX_HEIGHT);
        };

        updateScrollable();

        const resizeObserver = new ResizeObserver(() => {
            updateScrollable();
        });

        resizeObserver.observe(content);
        window.addEventListener("resize", updateScrollable);

        return () => {
            resizeObserver.disconnect();
            window.removeEventListener("resize", updateScrollable);
        };
    }, [isLoading, error, partialError, projectSnapshots]);

    return (
        <section>
            <h2 className="pf-section-title">Skills</h2>
            <div className="pf-divider" />

            <section
                className="rounded-2xl border border-border bg-card p-5 shadow-sm"
                style={{ marginTop: 36 }}
            >
                <div className="mb-4">
                    <p className="text-sm text-muted-foreground">
                        Skills demonstrated across top 3 projects
                    </p>
                </div>

                <div
                    className={isScrollable ? "max-h-[420px] overflow-y-auto pr-1" : "pr-1"}
                >
                    <div ref={scrollContentRef} className="space-y-4">
                        {isLoading ? (
                            <SkillTimelineSkeleton />
                        ) : error ? (
                            <p className="text-sm text-destructive">{error}</p>
                        ) : projectSnapshots.length === 0 ? (
                            <p className="text-sm text-muted-foreground">
                                No skill snapshot data available for the selected projects.
                            </p>
                        ) : (
                            <>
                                {partialError && (
                                    <p className="text-sm text-muted-foreground">
                                        Some project snapshot data could not be loaded.
                                    </p>
                                )}

                                {projectSnapshots.map((projectGroup) => (
                                    <ProjectSnapshotCard
                                        key={projectGroup.projectId}
                                        projectGroup={projectGroup}
                                    />
                                ))}
                            </>
                        )}
                    </div>
                </div>
            </section>
        </section>
    );
}
