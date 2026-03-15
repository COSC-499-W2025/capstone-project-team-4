import { getAccessToken } from "@/lib/auth";
import axios from "axios";
import { useEffect, useMemo, useState } from "react";

import SkillTimelineDateRow from "./SkillTimelineDateRow";
import { mergeSkillTimelines } from "./utils/skillTimeline";

function SkillTimelineSkeleton() {
    return (
        <div className="space-y-4">
            {[1, 2, 3].map((item) => (
                <div
                    key={item}
                    className="rounded-xl border border-border/60 bg-background/50 p-4"
                >
                    <div className="mb-3 h-4 w-28 animate-pulse rounded bg-muted" />
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

export default function SkillTimeline() {
    const [groupedTimeline, setGroupedTimeline] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState("");
    const [partialError, setPartialError] = useState(false);

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
                setError("You must be logged in to view the skill timeline.");
                setIsLoading(false);
                return;
            }

            try {
                const projectsRes = await axios.get("/api/projects", {
                    headers: authHeader,
                });

                console.log("Projects API response:", projectsRes.data);

                const allProjects = Array.isArray(projectsRes.data)
                    ? projectsRes.data
                    : Array.isArray(projectsRes.data?.projects)
                        ? projectsRes.data.projects
                        : Array.isArray(projectsRes.data?.items)
                            ? projectsRes.data.items
                            : Array.isArray(projectsRes.data?.data)
                                ? projectsRes.data.data
                                : [];

                console.log("All projects:", allProjects);

                const topThreeProjects = [...allProjects]
                    .sort(
                        (a, b) =>
                            (b.total_lines_of_code || 0) - (a.total_lines_of_code || 0)
                    )
                    .slice(0, 3);

                console.log("Top three projects:", topThreeProjects);

                if (topThreeProjects.length === 0) {
                    console.log("No top projects found from /api/projects");
                    setError("No projects found for the current account.");
                    setGroupedTimeline([]);
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

                console.log("Timeline results:", results);

                if (isCancelled) return;

                const successfulResponses = results
                    .filter((result) => result.status === "fulfilled")
                    .map((result) => result.value.data);

                const failedResponses = results.filter(
                    (result) => result.status === "rejected"
                );

                console.log("Successful timeline responses:", successfulResponses);

                if (failedResponses.length > 0) {
                    console.error(
                        "Timeline request failures:",
                        failedResponses.map((result) => ({
                            status: result.reason?.response?.status,
                            data: result.reason?.response?.data,
                            url: result.reason?.config?.url,
                            message: result.reason?.message,
                        }))
                    );
                    setPartialError(successfulResponses.length > 0);
                }

                if (successfulResponses.length === 0) {
                    const firstError = failedResponses[0]?.reason;
                    const detail =
                        firstError?.response?.data?.detail ||
                        firstError?.message ||
                        "Failed to load skill timeline data.";
                    setError(detail);
                    setGroupedTimeline([]);
                    return;
                }

                const merged = mergeSkillTimelines(
                    topThreeProjects,
                    successfulResponses
                );

                console.log("Merged grouped timeline:", merged);

                setGroupedTimeline(merged);
            } catch (err) {
                console.error("SkillTimeline load error:", err);
                if (!isCancelled) {
                    setError(
                        err?.response?.data?.detail ||
                        err?.message ||
                        "Failed to load skill timeline data."
                    );
                    setGroupedTimeline([]);
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

    return (
        <section className="rounded-2xl border border-border bg-card p-5 shadow-sm">
            <div className="mb-4">
                <h2 className="text-lg font-semibold">Skill Timeline</h2>
                <p className="text-sm text-muted-foreground">
                    Skills demonstrated across top 3 projects
                </p>
            </div>

            <div className="max-h-[420px] space-y-4 overflow-y-auto pr-1">
                {isLoading ? (
                    <SkillTimelineSkeleton />
                ) : error ? (
                    <p className="text-sm text-destructive">{error}</p>
                ) : groupedTimeline.length === 0 ? (
                    <p className="text-sm text-muted-foreground">
                        No skill timeline data available for the selected projects.
                    </p>
                ) : (
                    <>
                        {partialError && (
                            <p className="text-sm text-muted-foreground">
                                Some timeline data could not be loaded.
                            </p>
                        )}

                        {groupedTimeline.map((group) => (
                            <SkillTimelineDateRow key={group.date} group={group} />
                        ))}
                    </>
                )}
            </div>
        </section>
    );
}
