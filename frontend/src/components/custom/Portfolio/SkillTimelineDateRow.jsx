import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@/components/ui/tooltip";
import { useLayoutEffect, useMemo, useRef, useState } from "react";

const CHIP_AREA_MAX_HEIGHT = 56; // roughly 2 wrapped chip rows

function SkillChip({ skillEntry }) {
    return (
        <Tooltip>
            <TooltipTrigger asChild>
                <span className="inline-flex cursor-default items-center rounded-full border border-border bg-secondary px-3 py-1 text-xs font-medium text-secondary-foreground transition-colors hover:bg-secondary/80">
                    {skillEntry.skill}
                </span>
            </TooltipTrigger>

            <TooltipContent side="top" align="start" className="max-w-xs">
                <div className="space-y-1">
                    <p className="text-sm font-semibold">{skillEntry.skill}</p>
                    <p className="text-xs text-muted-foreground">Used in:</p>
                    <div className="space-y-1">
                        {skillEntry.projects.map((project) => (
                            <p key={project.projectId} className="text-xs">
                                • {project.projectName}
                            </p>
                        ))}
                    </div>
                </div>
            </TooltipContent>
        </Tooltip>
    );
}

export default function SkillTimelineDateRow({ group }) {
    const measureContainerRef = useRef(null);
    const [visibleCount, setVisibleCount] = useState(group.skills.length);

    const allSkills = group.skills;

    const measuredSkills = useMemo(() => group.skills, [group.skills]);

    useLayoutEffect(() => {
        const container = measureContainerRef.current;
        if (!container) return;

        const calculateVisibleCount = () => {
            const chipNodes = Array.from(
                container.querySelectorAll("[data-skill-chip='true']")
            );

            if (!chipNodes.length) {
                setVisibleCount(0);
                return;
            }

            let fitCount = 0;

            for (const node of chipNodes) {
                const bottom = node.offsetTop + node.offsetHeight;
                if (bottom <= CHIP_AREA_MAX_HEIGHT) {
                    fitCount += 1;
                } else {
                    break;
                }
            }

            const hiddenCount = allSkills.length - fitCount;

            // Reserve room for the +N more badge if overflow exists.
            // This is a practical compact-layout heuristic.
            if (hiddenCount > 0 && fitCount > 0) {
                fitCount -= 1;
            }

            setVisibleCount(Math.max(fitCount, 0));
        };

        calculateVisibleCount();

        const resizeObserver = new ResizeObserver(() => {
            calculateVisibleCount();
        });

        resizeObserver.observe(container);

        window.addEventListener("resize", calculateVisibleCount);

        return () => {
            resizeObserver.disconnect();
            window.removeEventListener("resize", calculateVisibleCount);
        };
    }, [allSkills]);

    const visibleSkills = allSkills.slice(0, visibleCount);
    const hiddenCount = Math.max(allSkills.length - visibleSkills.length, 0);

    return (
        <TooltipProvider delayDuration={150}>
            <div className="relative rounded-xl border border-border/60 bg-background/50 p-4">
                <div className="mb-3">
                    <p className="text-sm font-semibold text-foreground">
                        {group.formattedDate}
                    </p>
                </div>

                <div className="flex flex-wrap gap-2">
                    {visibleSkills.map((skillEntry) => (
                        <SkillChip
                            key={`${group.date}-${skillEntry.skill}`}
                            skillEntry={skillEntry}
                        />
                    ))}

                    {hiddenCount > 0 && (
                        <span className="inline-flex items-center rounded-full border border-dashed border-border px-3 py-1 text-xs text-muted-foreground">
                            +{hiddenCount} more
                        </span>
                    )}
                </div>

                {/* Hidden measurement layer */}
                <div
                    ref={measureContainerRef}
                    aria-hidden="true"
                    className="pointer-events-none absolute left-0 top-0 -z-10 invisible flex w-full flex-wrap gap-2"
                    style={{ maxHeight: CHIP_AREA_MAX_HEIGHT }}
                >
                    {measuredSkills.map((skillEntry) => (
                        <span
                            key={`measure-${group.date}-${skillEntry.skill}`}
                            data-skill-chip="true"
                            className="inline-flex items-center rounded-full border border-border bg-secondary px-3 py-1 text-xs font-medium"
                        >
                            {skillEntry.skill}
                        </span>
                    ))}
                </div>
            </div>
        </TooltipProvider>
    );
}
