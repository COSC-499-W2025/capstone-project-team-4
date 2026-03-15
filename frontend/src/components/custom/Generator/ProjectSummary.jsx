import React, { useState } from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Pencil,
  Users,
  Calendar,
  Code,
  FileText,
  ChevronRight,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import EditProjectModal from "@/components/custom/Generator/EditProjectModal";
import ContributorInsightsDialog from "@/components/custom/Generator/ContributorInsightsDialog";

const ProjectSummary = ({ projects, onUpdateProject }) => {
  const [sortBy, setSortBy] = useState("date");
  const [editingProject, setEditingProject] = useState(null);
  const [editingIndex, setEditingIndex] = useState(null);
  const [contributorModalOpen, setContributorModalOpen] = useState(false);
  const [selectedProjectForContributors, setSelectedProjectForContributors] =
    useState(null);
  const [expandedSections, setExpandedSections] = useState({});

  if (!projects || projects.length === 0) return null;

  const sortedProjects = [...projects].sort((a, b) => {
    if (sortBy === "contributions") {
      return (b.contributions || 0) - (a.contributions || 0);
    }
    if (sortBy === "date") {
      return new Date(b.date || 0) - new Date(a.date || 0);
    }
    if (sortBy === "contributors") {
      return (b.contributorCount || 0) - (a.contributorCount || 0);
    }
    if (sortBy === "projectStart") {
      const dateA = a.projectStartedAt
        ? new Date(a.projectStartedAt)
        : new Date(0);
      const dateB = b.projectStartedAt
        ? new Date(b.projectStartedAt)
        : new Date(0);
      return dateB - dateA;
    }
    return 0;
  });

  const handleEdit = (project, index) => {
    setEditingProject(project);
    setEditingIndex(index);
  };

  const handleSave = (updatedProject) => {
    if (onUpdateProject) {
      onUpdateProject(editingIndex, updatedProject);
    }
    setEditingProject(null);
    setEditingIndex(null);
  };

  const toggleExpanded = (projectIndex, sectionType) => {
    const key = `${projectIndex}-${sectionType}`;
    setExpandedSections((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  const isExpanded = (projectIndex, sectionType) => {
    return expandedSections[`${projectIndex}-${sectionType}`] || false;
  };

  const formatDate = (dateString) => {
    if (!dateString) return "N/A";
    try {
      return new Date(dateString).toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
      });
    } catch {
      return "N/A";
    }
  };

  const handleContributorClick = (project) => {
    if (!project.projectId) {
      console.error("No projectId available for this project");
      return;
    }

    setSelectedProjectForContributors(project);
    setContributorModalOpen(true);
  };

  const renderExpandableBadges = (
    items,
    projectIndex,
    sectionType,
    maxItems = 5,
    badgeProps = {},
  ) => {
    if (!items || items.length === 0) return null;

    const expanded = isExpanded(projectIndex, sectionType);
    const displayItems = expanded ? items : items.slice(0, maxItems);
    const hasMore = items.length > maxItems;

    return (
      <div className="flex flex-wrap gap-1">
        {displayItems.map((item, itemIndex) => (
          <Badge key={`${sectionType}-${itemIndex}-${item}`} {...badgeProps}>
            {item}
          </Badge>
        ))}
        {hasMore && (
          <Badge
            className="cursor-pointer bg-gray-100 text-xs text-gray-600 transition-colors hover:bg-gray-200"
            onClick={() => toggleExpanded(projectIndex, sectionType)}
          >
            {expanded ? (
              <>
                <ChevronUp className="mr-1 h-3 w-3" />
                Show less
              </>
            ) : (
              <>
                <ChevronDown className="mr-1 h-3 w-3" />+
                {items.length - maxItems} more
              </>
            )}
          </Badge>
        )}
      </div>
    );
  };

  return (
    <div className="mt-8 w-full max-w-4xl">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-2xl font-bold">Project Summary</h2>
        <div className="flex items-center space-x-2">
          <label htmlFor="sort-select" className="text-sm font-medium">
            Sort by:
          </label>
          <Select value={sortBy} onValueChange={setSortBy}>
            <SelectTrigger id="sort-select" className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="contributions">Files Analyzed</SelectItem>
              <SelectItem value="contributors">Contributors</SelectItem>
              <SelectItem value="date">Date Analyzed</SelectItem>
              <SelectItem value="projectStart">Project Start</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {sortedProjects.map((project, index) => (
          <Card
            key={project.projectId || index}
            className="relative transition-shadow hover:shadow-lg"
          >
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleEdit(project, index)}
              className="absolute top-2 right-2 h-8 w-8 p-0 hover:bg-blue-50"
            >
              <Pencil className="h-4 w-4 text-gray-500 hover:text-blue-600" />
            </Button>

            <CardHeader>
              <CardTitle className="pr-8 text-lg">{project.name}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 text-sm">
                <div className="grid grid-cols-2 gap-3 border-b pb-3">
                  <div className="flex items-center gap-2">
                    <FileText className="h-4 w-4 text-gray-500" />
                    <div>
                      <span className="block text-xs text-gray-600">
                        Files Analyzed
                      </span>
                      <span className="font-semibold">
                        {project.contributions || 0}
                      </span>
                    </div>
                  </div>

                  <div
                    className={`-m-2 flex items-center gap-2 rounded-lg p-2 transition-all ${
                      project.projectId
                        ? "group cursor-pointer hover:bg-blue-50"
                        : ""
                    }`}
                    onClick={() =>
                      project.projectId && handleContributorClick(project)
                    }
                    role={project.projectId ? "button" : undefined}
                    tabIndex={project.projectId ? 0 : undefined}
                    onKeyDown={(e) => {
                      if (
                        project.projectId &&
                        (e.key === "Enter" || e.key === " ")
                      ) {
                        handleContributorClick(project);
                      }
                    }}
                    title={
                      project.projectId
                        ? "Click to view contributor details"
                        : undefined
                    }
                  >
                    <Users className="h-4 w-4 text-blue-500" />
                    <div className="flex-1">
                      <span className="block text-xs text-gray-600">
                        Contributors
                      </span>
                      <span
                        className={`font-semibold ${project.projectId ? "text-blue-600 group-hover:underline" : "text-blue-600"}`}
                      >
                        {project.contributorCount || 0}
                      </span>
                    </div>
                    {project.projectId && (
                      <ChevronRight className="h-4 w-4 text-blue-400 opacity-0 transition-opacity group-hover:opacity-100" />
                    )}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3 border-b pb-3">
                  <div className="flex items-center gap-2">
                    <Calendar className="h-4 w-4 text-green-500" />
                    <div>
                      <span className="block text-xs text-gray-600">
                        Project Started
                      </span>
                      <span className="font-semibold text-green-600">
                        {formatDate(project.projectStartedAt)}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <Calendar className="h-4 w-4 text-gray-500" />
                    <div>
                      <span className="block text-xs text-gray-600">
                        Analyzed
                      </span>
                      <span className="font-semibold">
                        {formatDate(project.date)}
                      </span>
                    </div>
                  </div>
                </div>

                {project.totalLinesOfCode > 0 && (
                  <div className="flex items-center gap-2 border-b pb-3">
                    <Code className="h-4 w-4 text-purple-500" />
                    <div>
                      <span className="block text-xs text-gray-600">
                        Total Lines of Code
                      </span>
                      <span className="font-semibold text-purple-600">
                        {project.totalLinesOfCode.toLocaleString()}
                      </span>
                    </div>
                  </div>
                )}

                {project.description && (
                  <div>
                    <span className="mb-1 block text-gray-600">
                      Description:
                    </span>
                    <p className="text-xs text-gray-700">
                      {project.description}
                    </p>
                  </div>
                )}

                {project.languages?.length > 0 && (
                  <div>
                    <span className="mb-2 block text-gray-600">Languages:</span>
                    {renderExpandableBadges(
                      project.languages,
                      index,
                      "languages",
                      8,
                      {
                        variant: "secondary",
                        className: "text-xs",
                      },
                    )}
                  </div>
                )}

                {project.frameworks?.length > 0 && (
                  <div>
                    <span className="mb-2 block text-gray-600">
                      Frameworks:
                    </span>
                    {renderExpandableBadges(
                      project.frameworks,
                      index,
                      "frameworks",
                      5,
                      {
                        variant: "outline",
                        className: "text-xs",
                      },
                    )}
                  </div>
                )}

                {project.skills?.length > 0 && (
                  <div>
                    <span className="mb-2 block text-gray-600">Skills:</span>
                    {renderExpandableBadges(
                      project.skills,
                      index,
                      "skills",
                      5,
                      {
                        className: "bg-blue-100 text-xs text-blue-800",
                      },
                    )}
                  </div>
                )}

                {project.toolsAndTechnologies?.length > 0 && (
                  <div>
                    <span className="mb-2 block text-gray-600">
                      Tools & Technologies:
                    </span>
                    {renderExpandableBadges(
                      project.toolsAndTechnologies,
                      index,
                      "tools",
                      5,
                      {
                        variant: "outline",
                        className:
                          "border-orange-200 bg-orange-50 text-xs text-orange-700",
                      },
                    )}
                  </div>
                )}

                {project.complexity &&
                  Object.keys(project.complexity).length > 0 && (
                    <div className="border-t pt-2">
                      <span className="mb-1 block text-xs text-gray-600">
                        Complexity Metrics:
                      </span>
                      <div className="space-y-1 text-xs text-gray-500">
                        {project.complexity.total_functions !== undefined && (
                          <div className="flex justify-between">
                            <span>Total Functions:</span>
                            <span className="font-mono">
                              {project.complexity.total_functions}
                            </span>
                          </div>
                        )}
                        {project.complexity.avg_complexity !== undefined && (
                          <div className="flex justify-between">
                            <span>Avg Complexity:</span>
                            <span className="font-mono">
                              {project.complexity.avg_complexity.toFixed(2)}
                            </span>
                          </div>
                        )}
                        {project.complexity.max_complexity !== undefined && (
                          <div className="flex justify-between">
                            <span>Max Complexity:</span>
                            <span className="font-mono">
                              {project.complexity.max_complexity}
                            </span>
                          </div>
                        )}
                        {project.complexity.high_complexity_count !==
                          undefined &&
                          project.complexity.high_complexity_count > 0 && (
                            <div className="flex justify-between">
                              <span>High Complexity Functions:</span>
                              <span className="font-mono text-amber-600">
                                {project.complexity.high_complexity_count}
                              </span>
                            </div>
                          )}
                      </div>
                    </div>
                  )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {editingProject && (
        <EditProjectModal
          isOpen={!!editingProject}
          onClose={() => {
            setEditingProject(null);
            setEditingIndex(null);
          }}
          project={editingProject}
          onSave={handleSave}
        />
      )}

      <ContributorInsightsDialog
        open={contributorModalOpen}
        onOpenChange={setContributorModalOpen}
        project={selectedProjectForContributors}
      />
    </div>
  );
};

export default ProjectSummary;
