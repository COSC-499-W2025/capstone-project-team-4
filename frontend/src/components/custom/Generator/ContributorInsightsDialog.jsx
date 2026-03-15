import React, { useEffect, useMemo, useState } from "react";
import axios from "axios";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { FolderTree, GitCommitHorizontal, Users } from "lucide-react";

const ContributorInsightsDialog = ({ open, onOpenChange, project }) => {
  const [contributorsData, setContributorsData] = useState(null);
  const [contributorsLoading, setContributorsLoading] = useState(false);
  const [contributorsError, setContributorsError] = useState(null);
  const [selectedContributorId, setSelectedContributorId] = useState(null);
  const [analysisData, setAnalysisData] = useState(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [analysisError, setAnalysisError] = useState(null);
  const [directoriesData, setDirectoriesData] = useState(null);
  const [directoriesLoading, setDirectoriesLoading] = useState(false);
  const [directoriesError, setDirectoriesError] = useState(null);

  const contributors = contributorsData?.contributors ?? [];
  const selectedContributor = useMemo(
    () =>
      contributors.find(
        (contributor) => contributor.id === selectedContributorId,
      ) ?? null,
    [contributors, selectedContributorId],
  );

  useEffect(() => {
    if (!open || !project?.projectId) {
      return;
    }

    let active = true;

    const loadContributors = async () => {
      setContributorsLoading(true);
      setContributorsError(null);
      setContributorsData(null);
      setSelectedContributorId(null);
      setAnalysisData(null);
      setAnalysisError(null);
      setDirectoriesData(null);
      setDirectoriesError(null);

      try {
        const response = await axios.get(
          `/api/projects/${project.projectId}/contributors`,
        );
        if (!active) {
          return;
        }

        setContributorsData(response.data);

        const firstContributor = response.data?.contributors?.[0] ?? null;
        setSelectedContributorId(firstContributor?.id ?? null);
      } catch (error) {
        if (!active) {
          return;
        }

        setContributorsError(
          error.response?.data?.detail ||
            error.message ||
            "Failed to load contributors",
        );
      } finally {
        if (active) {
          setContributorsLoading(false);
        }
      }
    };

    loadContributors();

    return () => {
      active = false;
    };
  }, [open, project?.projectId]);

  useEffect(() => {
    if (!open || !project?.projectId || !selectedContributorId) {
      return;
    }

    let active = true;

    const loadContributorInsights = async () => {
      setAnalysisLoading(true);
      setDirectoriesLoading(true);
      setAnalysisError(null);
      setDirectoriesError(null);
      setAnalysisData(null);
      setDirectoriesData(null);

      const baseUrl = `/api/projects/${project.projectId}/contributors/${selectedContributorId}`;
      const [analysisResult, directoriesResult] = await Promise.allSettled([
        axios.get(`${baseUrl}/analysis`),
        axios.get(`${baseUrl}/directories`),
      ]);

      if (!active) {
        return;
      }

      if (analysisResult.status === "fulfilled") {
        setAnalysisData(analysisResult.value.data);
      } else {
        setAnalysisError(
          analysisResult.reason?.response?.data?.detail ||
            analysisResult.reason?.message ||
            "Failed to load contributor analysis",
        );
      }

      if (directoriesResult.status === "fulfilled") {
        setDirectoriesData(directoriesResult.value.data);
      } else {
        setDirectoriesError(
          directoriesResult.reason?.response?.data?.detail ||
            directoriesResult.reason?.message ||
            "Failed to load contributor directories",
        );
      }

      setAnalysisLoading(false);
      setDirectoriesLoading(false);
    };

    loadContributorInsights();

    return () => {
      active = false;
    };
  }, [open, project?.projectId, selectedContributorId]);

  const formatNumber = (num) => {
    if (num >= 1000000) {
      return `${(num / 1000000).toFixed(1)}M`;
    }
    if (num >= 1000) {
      return `${(num / 1000).toFixed(1)}K`;
    }
    return `${num ?? 0}`;
  };

  const formatPercent = (share) => `${Math.round((share ?? 0) * 100)}%`;

  const renderStateBlock = (message) => (
    <div className="rounded-lg border border-dashed p-4 text-sm text-gray-500">
      {message}
    </div>
  );

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-[95vw] xl:max-w-7xl overflow-hidden p-0 h-[88vh]">
        <div className="flex h-full flex-col">
          <DialogHeader className="border-b px-6 py-4">
            <DialogTitle className="flex items-center gap-2">
              <Users className="h-5 w-5 text-blue-500" />
              Contributor Insights - {project?.name}
            </DialogTitle>
            <DialogDescription>
              Browse contributors and inspect their top areas, files, and
              directories.
            </DialogDescription>
          </DialogHeader>

          <div className="grid min-h-0 flex-1 overflow-hidden md:grid-cols-[300px_minmax(0,1fr)]">
            <div className="flex flex-col border-b p-4 md:border-b-0 md:border-r overflow-y-auto">
              <div className="mb-3 flex items-center justify-between">
                <h3 className="text-sm font-semibold text-gray-900">
                  Contributors
                </h3>
                {contributorsData && (
                  <Badge variant="secondary">
                    {contributorsData.total_contributors}
                  </Badge>
                )}
              </div>

              {contributorsLoading && (
                <div className="flex items-center gap-2 text-sm text-gray-500">
                  <Spinner className="size-4" />
                  Loading contributors...
                </div>
              )}

              {contributorsError && renderStateBlock(contributorsError)}

              {!contributorsLoading &&
                !contributorsError &&
                contributors.length === 0 &&
                renderStateBlock("No contributors found for this project.")}

              <div className="space-y-2">
                {contributors.map((contributor) => {
                  const isSelected = contributor.id === selectedContributorId;
                  return (
                    <button
                      key={contributor.id}
                      type="button"
                      onClick={() => setSelectedContributorId(contributor.id)}
                      className={[
                        "w-full rounded-lg border p-3 text-left transition-colors",
                        isSelected
                          ? "border-blue-300 bg-blue-50"
                          : "hover:bg-gray-50",
                      ].join(" ")}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0">
                          <p className="truncate font-medium text-gray-900">
                            {contributor.name ||
                              contributor.github_username ||
                              contributor.email ||
                              "Unknown"}
                          </p>
                          <p className="truncate text-xs text-gray-500">
                            {contributor.github_username ||
                              contributor.email ||
                              "No identity details"}
                          </p>
                        </div>
                        <Badge variant="outline">
                          {contributor.commits} commits
                        </Badge>
                      </div>
                      <div className="mt-2 text-xs text-gray-600">
                        {formatNumber(
                          contributor.changes?.total_lines_changed ?? 0,
                        )}{" "}
                        lines changed
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="min-h-0 overflow-y-auto p-6">
              {!selectedContributor &&
                !contributorsLoading &&
                !contributorsError &&
                renderStateBlock(
                  "Select a contributor to inspect individual analysis results.",
                )}

              {selectedContributor && (
                <div className="space-y-6">
                  <div className="grid gap-3 sm:grid-cols-3">
                    <div className="rounded-lg border p-4">
                      <div className="text-xs text-gray-500">Contributor</div>
                      <div className="mt-1 font-semibold text-gray-900">
                        {selectedContributor.name ||
                          selectedContributor.github_username ||
                          "Unknown"}
                      </div>
                    </div>
                    <div className="rounded-lg border p-4">
                      <div className="text-xs text-gray-500">Commits</div>
                      <div className="mt-1 flex items-center gap-2 font-semibold text-gray-900">
                        <GitCommitHorizontal className="h-4 w-4 text-blue-500" />
                        {selectedContributor.commits}
                      </div>
                    </div>
                    <div className="rounded-lg border p-4">
                      <div className="text-xs text-gray-500">Files Changed</div>
                      <div className="mt-1 flex items-center gap-2 font-semibold text-gray-900">
                        <FolderTree className="h-4 w-4 text-emerald-500" />
                        {selectedContributor.changes?.files_changed ?? 0}
                      </div>
                    </div>
                  </div>

                  <section className="space-y-3">
                    <div>
                      <h3 className="font-semibold text-gray-900">Top Areas</h3>
                      <p className="text-sm text-gray-500">
                        Where this contributor spent the most effort.
                      </p>
                    </div>

                    {analysisLoading && (
                      <div className="flex items-center gap-2 text-sm text-gray-500">
                        <Spinner className="size-4" />
                        Loading contributor analysis...
                      </div>
                    )}

                    {analysisError && renderStateBlock(analysisError)}

                    {!analysisLoading &&
                      !analysisError &&
                      (analysisData?.contributor?.summary?.top_areas?.length ??
                        0) === 0 &&
                      renderStateBlock(
                        "No area breakdown is available for this contributor yet.",
                      )}

                    <div className="space-y-2">
                      {analysisData?.contributor?.summary?.top_areas?.map(
                        (area) => (
                          <div
                            key={area.area}
                            className="rounded-lg border p-3"
                          >
                            <div className="mb-2 flex items-center justify-between text-sm">
                              <span className="font-medium text-gray-900">
                                {area.area}
                              </span>
                              <span className="text-gray-500">
                                {formatPercent(area.share)}
                              </span>
                            </div>
                            <div className="h-2 rounded-full bg-gray-100">
                              <div
                                className="h-2 rounded-full bg-blue-500"
                                style={{ width: formatPercent(area.share) }}
                              />
                            </div>
                          </div>
                        ),
                      )}
                    </div>
                  </section>

                  <section className="space-y-6">
                    <div className="space-y-3">
                      <div>
                        <h3 className="font-semibold text-gray-900">
                          Top Files
                        </h3>
                        <p className="text-sm text-gray-500">
                          Files with the highest amount of change.
                        </p>
                      </div>

                      {analysisLoading && !analysisData && (
                        <div className="flex items-center gap-2 text-sm text-gray-500">
                          <Spinner className="size-4" />
                          Loading file breakdown...
                        </div>
                      )}

                      {!analysisLoading &&
                        !analysisError &&
                        (analysisData?.contributor?.summary?.top_files
                          ?.length ?? 0) === 0 &&
                        renderStateBlock(
                          "No file-level contribution data is available.",
                        )}

                      <div className="space-y-2">
                        {analysisData?.contributor?.summary?.top_files?.map(
                          (file) => (
                            <div
                              key={file.file}
                              className="rounded-lg border p-3"
                            >
                              <div className="break-all text-sm font-medium text-gray-900">
                                {file.file}
                              </div>
                              <div className="mt-1 text-xs text-gray-500">
                                {formatNumber(file.lines_changed)} lines changed
                              </div>
                            </div>
                          ),
                        )}
                      </div>
                    </div>

                    <div className="space-y-3">
                      <div>
                        <h3 className="font-semibold text-gray-900">
                          Top Directories
                        </h3>
                        <p className="text-sm text-gray-500">
                          Directories where the contributor concentrated work.
                        </p>
                      </div>

                      {directoriesLoading && (
                        <div className="flex items-center gap-2 text-sm text-gray-500">
                          <Spinner className="size-4" />
                          Loading directory breakdown...
                        </div>
                      )}

                      {directoriesError && renderStateBlock(directoriesError)}

                      {!directoriesLoading &&
                        !directoriesError &&
                        (directoriesData?.top_directories?.length ?? 0) === 0 &&
                        renderStateBlock(
                          "No directory-level contribution data is available.",
                        )}

                      <div className="space-y-2">
                        {directoriesData?.top_directories?.map((directory) => (
                          <div
                            key={directory.directory}
                            className="rounded-lg border p-3"
                          >
                            <div className="mb-2 flex items-start justify-between gap-2 text-sm">
                              <span className="break-all font-medium text-gray-900">
                                {directory.directory}
                              </span>
                              <span className="text-gray-500">
                                {formatPercent(directory.share)}
                              </span>
                            </div>
                            <div className="mb-2 h-2 rounded-full bg-gray-100">
                              <div
                                className="h-2 rounded-full bg-emerald-500"
                                style={{
                                  width: formatPercent(directory.share),
                                }}
                              />
                            </div>
                            <div className="flex items-center justify-between text-xs text-gray-500">
                              <span>
                                {formatNumber(directory.lines_changed)} lines
                                changed
                              </span>
                              <span>{directory.files_count} files</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </section>
                </div>
              )}
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default ContributorInsightsDialog;
