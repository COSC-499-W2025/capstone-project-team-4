import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@/components/ui/tooltip";
import { useLayoutEffect, useMemo, useRef, useState } from "react";

const CHIP_AREA_MAX_HEIGHT = 56; // roughly 2 wrapped chip rows
const LOAD_MORE_BATCH_SIZE = 8;

function SkillChip({ skillEntry }) {
    return (
        <Tooltip>
            <TooltipTrigger asChild>
                <span className="inline-flex cursor-default items-center rounded-full border border-border bg-secondary px-3 py-1 text-xs font-medium text-secondary-foreground transition-colors hover:bg-secondary/80">
                    {skillEntry.skill}
                    {skillEntry.count > 1 && (
                        <span className="ml-1 text-[11px] text-muted-foreground">
                            ×{skillEntry.count}
                        </span>
                    )}
                </span>
            </TooltipTrigger>

            <TooltipContent side="top" align="start" className="max-w-xs">
                <div className="space-y-1">
                    <p className="text-sm font-semibold">{skillEntry.skill}</p>
                </div>
            </TooltipContent>
        </Tooltip>
    );
}

export default function SkillTimelineDateRow({ skills }) {
    const measureContainerRef = useRef(null);

    const allSkills = skills;
    const measuredSkills = useMemo(() => skills, [skills]);

    const [baseVisibleCount, setBaseVisibleCount] = useState(skills.length);
    const [expandedCount, setExpandedCount] = useState(0);

    useLayoutEffect(() => {
        const container = measureContainerRef.current;
        if (!container) return;

        const calculateBaseVisibleCount = () => {
            const chipNodes = Array.from(
                container.querySelectorAll("[data-skill-chip='true']")
            );

            if (!chipNodes.length) {
                setBaseVisibleCount(0);
                setExpandedCount(0);
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
            if (hiddenCount > 0 && fitCount > 0) {
                fitCount -= 1;
            }

            const nextBaseCount = Math.max(fitCount, 0);
            setBaseVisibleCount(nextBaseCount);

            // Reset progressive expansion when layout changes significantly
            setExpandedCount((prev) => {
                const maxExpandable = Math.max(allSkills.length - nextBaseCount, 0);
                return Math.min(prev, maxExpandable);
            });
        };

        calculateBaseVisibleCount();

        const resizeObserver = new ResizeObserver(() => {
            calculateBaseVisibleCount();
        });

        resizeObserver.observe(container);
        window.addEventListener("resize", calculateBaseVisibleCount);

        return () => {
            resizeObserver.disconnect();
            window.removeEventListener("resize", calculateBaseVisibleCount);
        };
    }, [allSkills]);

    useLayoutEffect(() => {
        setExpandedCount(0);
    }, [allSkills]);

    const totalVisibleCount = Math.min(
        baseVisibleCount + expandedCount,
        allSkills.length
    );

    const visibleSkills = allSkills.slice(0, totalVisibleCount);
    const remainingCount = Math.max(allSkills.length - totalVisibleCount, 0);

    const handleLoadMore = () => {
        setExpandedCount((prev) =>
            Math.min(prev + LOAD_MORE_BATCH_SIZE, allSkills.length - baseVisibleCount)
        );
    };

    return (
        <TooltipProvider delayDuration={150}>
            <div className="relative">
                <div className="flex flex-wrap gap-2">
                    {visibleSkills.map((skillEntry) => (
                        <SkillChip key={skillEntry.skill} skillEntry={skillEntry} />
                    ))}

                    {remainingCount > 0 && (
                        <button
                            type="button"
                            onClick={handleLoadMore}
                            className="inline-flex items-center rounded-full border border-dashed border-border px-3 py-1 text-xs text-muted-foreground transition-colors hover:bg-muted"
                        >
                            +{remainingCount} more
                        </button>
                    )}
                </div>

                <div
                    ref={measureContainerRef}
                    aria-hidden="true"
                    className="pointer-events-none absolute left-0 top-0 -z-10 invisible flex w-full flex-wrap gap-2"
                    style={{ maxHeight: CHIP_AREA_MAX_HEIGHT }}
                >
                    {measuredSkills.map((skillEntry) => (
                        <span
                            key={`measure-${skillEntry.skill}`}
                            data-skill-chip="true"
                            className="inline-flex items-center rounded-full border border-border bg-secondary px-3 py-1 text-xs font-medium"
                        >
                            {skillEntry.skill}
                            {skillEntry.count > 1 ? ` ×${skillEntry.count}` : ""}
                        </span>
                    ))}
                </div>
            </div>
        </TooltipProvider>
    );
}