import { getAccessToken } from "@/lib/auth";
import axios from "axios";
import { useEffect, useMemo, useRef, useState } from "react";


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

function ProjectSnapshotCard({ projectGroup, onViewTimeline }) {
    return (
        <div className="rounded-xl border border-border/60 bg-background/50 p-4">
            <div className="mb-4 flex items-center justify-between gap-4">
                <h3 className="text-sm font-semibold text-foreground">
                    {projectGroup.projectName}
                </h3>

                <button
                    type="button"
                    className="shrink-0 text-xs font-medium text-primary hover:underline"
                    onClick={() => onViewTimeline(projectGroup.projectId)}
                >
                    View Chronological Timeline
                </button>
            </div>

            {projectGroup.skills.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                    No skill snapshot data available for this project.
                </p>
            ) : (
                <div className="flex flex-wrap gap-2">
                    {projectGroup.skills.map((skill) => (
                        <span
                            key={skill}
                            className="rounded-full border border-border/60 bg-background px-3 py-1 text-xs text-foreground"
                        >
                            {skill}
                        </span>
                    ))}
                </div>
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

    const [selectedProjectId, setSelectedProjectId] = useState(null);
    const [isDialogOpen, setIsDialogOpen] = useState(false);
    const [timelineData, setTimelineData] = useState(null);
    const [timelineLoading, setTimelineLoading] = useState(false);
    const [timelineError, setTimelineError] = useState("");

    const scrollContentRef = useRef(null);

    const authHeader = useMemo(() => {
        const token = getAccessToken();
        return token ? { Authorization: `Bearer ${token}` } : null;
    }, []);

    useEffect(() => {
        let isCancelled = false;

        async function loadSnapshots() {
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
                            `/api/projects/${project.project_id ?? project.id}/skills`,
                            { headers: authHeader }
                        )
                    )
                );

                if (isCancelled) return;

                const failedResponses = results.filter(
                    (result) => result.status === "rejected"
                );

                if (failedResponses.length > 0) {
                    setPartialError(results.some((result) => result.status === "fulfilled"));
                }

                const snapshots = results
                    .map((result, index) => {
                        if (result.status !== "fulfilled") return null;

                        const project = topThreeProjects[index];
                        const data = result.value.data;

                        return {
                            projectId: project.project_id ?? project.id,
                            projectName:
                                data?.project_name || project.name || `Project ${project.project_id ?? project.id}`,
                            skills: Array.isArray(data?.skills) ? data.skills : [],
                        };
                    })
                    .filter(Boolean);

                if (snapshots.length === 0) {
                    const firstError = failedResponses[0]?.reason;
                    const detail =
                        firstError?.response?.data?.detail ||
                        firstError?.message ||
                        "Failed to load skill snapshot data.";
                    setError(detail);
                    setProjectSnapshots([]);
                    return;
                }

                setProjectSnapshots(snapshots);
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

        loadSnapshots();

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

    async function handleViewTimeline(projectId) {
        if (!authHeader) {
            setTimelineError("You must be logged in to view the chronological timeline.");
            setIsDialogOpen(true);
            return;
        }

        setSelectedProjectId(projectId);
        setIsDialogOpen(true);
        setTimelineLoading(true);
        setTimelineError("");
        setTimelineData(null);

        try {
            const res = await axios.post(
                `/api/projects/${projectId}/skills/timeline/build`,
                {},
                { headers: authHeader }
            );
            setTimelineData(res.data);
        } catch (err) {
            setTimelineError(
                err?.response?.data?.detail ||
                err?.message ||
                "Failed to load chronological timeline."
            );
        } finally {
            setTimelineLoading(false);
        }
    }

    function closeDialog() {
        setIsDialogOpen(false);
        setSelectedProjectId(null);
        setTimelineData(null);
        setTimelineError("");
        setTimelineLoading(false);
    }

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
                                        onViewTimeline={handleViewTimeline}
                                    />
                                ))}
                            </>
                        )}
                    </div>
                </div>
            </section>

            {isDialogOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
                    <div className="w-full max-w-2xl rounded-2xl border border-border bg-card p-6 shadow-xl">
                        <div className="mb-4 flex items-center justify-between gap-4">
                            <div>
                                <h3 className="text-lg font-semibold text-foreground">
                                    Chronological Timeline
                                </h3>
                                {selectedProjectId && (
                                    <p className="text-sm text-muted-foreground">
                                        Project ID: {selectedProjectId}
                                    </p>
                                )}
                            </div>

                            <button
                                type="button"
                                className="text-sm text-muted-foreground hover:text-foreground"
                                onClick={closeDialog}
                            >
                                Close
                            </button>
                        </div>

                        <div className="max-h-[60vh] overflow-y-auto pr-1">
                            {timelineLoading ? (
                                <p className="text-sm text-muted-foreground">
                                    Loading chronological timeline...
                                </p>
                            ) : timelineError ? (
                                <p className="text-sm text-destructive">{timelineError}</p>
                            ) : !timelineData?.timeline?.length ? (
                                <p className="text-sm text-muted-foreground">
                                    No chronological timeline data available yet.
                                </p>
                            ) : (
                                <div className="space-y-3">
                                    {timelineData.timeline.map((entry, index) => (
                                        <div
                                            key={`${entry.skill}-${entry.date}-${index}`}
                                            className="rounded-xl border border-border/60 bg-background/50 p-4"
                                        >
                                            <div className="flex items-center justify-between gap-4">
                                                <span className="text-sm font-medium text-foreground">
                                                    {entry.skill}
                                                </span>
                                                <span className="text-xs text-muted-foreground">
                                                    {entry.date}
                                                </span>
                                            </div>
                                            <p className="mt-2 text-xs text-muted-foreground">
                                                Count: {entry.count}
                                            </p>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </section>
    );
}