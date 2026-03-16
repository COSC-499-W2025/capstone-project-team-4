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
import { Users, GitCommitHorizontal, FolderTree, Loader2 } from "lucide-react";

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

  const selectedContributor = useMemo(() => {
    return (
      contributors.find(
        (contributor) => contributor.id === selectedContributorId,
      ) || null
    );
  }, [contributors, selectedContributorId]);

  const resetDetailState = () => {
    setAnalysisData(null);
    setAnalysisError(null);
    setDirectoriesData(null);
    setDirectoriesError(null);
  };

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
      resetDetailState();

      try {
        const response = await axios.get(
          `/api/projects/${project.projectId}/contributors`,
        );

        if (!active) {
          return;
        }

        setContributorsData(response.data);

        const firstContributor = response.data?.contributors?.[0] || null;
        setSelectedContributorId(firstContributor?.id || null);
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

    const loadDetails = async () => {
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

    loadDetails();

    return () => {
      active = false;
    };
  }, [open, project?.projectId, selectedContributorId]);

  const formatNumber = (value) => {
    if (!value) {
      return "0";
    }
    if (value >= 1000000) {
      return `${(value / 1000000).toFixed(1)}M`;
    }
    if (value >= 1000) {
      return `${(value / 1000).toFixed(1)}K`;
    }
    return String(value);
  };

  const formatPercent = (value) => `${Math.round((value || 0) * 100)}%`;

  const messageBox = (message) => (
    <div className="rounded-lg border border-dashed p-3 text-sm text-gray-500">
      {message}
    </div>
  );

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="flex h-[86vh] max-w-[95vw] flex-col overflow-hidden xl:max-w-6xl">
        <DialogHeader className="border-b pb-4">
          <DialogTitle className="flex items-center gap-2">
            <Users className="h-5 w-5 text-blue-500" />
            Contributor Insights - {project?.name}
          </DialogTitle>
          <DialogDescription>
            Browse contributors and inspect their top areas, files, and
            directories.
          </DialogDescription>
        </DialogHeader>

        <div className="flex min-h-0 flex-1 gap-0 overflow-hidden">
          <div className="w-[280px] flex-none overflow-y-auto border-r pr-4">
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
                <Loader2 className="h-4 w-4 animate-spin" />
                Loading contributors...
              </div>
            )}

            {contributorsError && messageBox(contributorsError)}

            {!contributorsLoading &&
              !contributorsError &&
              contributors.length === 0 &&
              messageBox("No contributors found for this project.")}

            <div className="space-y-2">
              {contributors.map((contributor) => {
                const selected = contributor.id === selectedContributorId;

                return (
                  <button
                    key={contributor.id}
                    type="button"
                    className={[
                      "w-full rounded-lg border p-3 text-left transition-colors",
                      selected
                        ? "border-blue-300 bg-blue-50"
                        : "hover:bg-gray-50",
                    ].join(" ")}
                    onClick={() => setSelectedContributorId(contributor.id)}
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
                    <p className="mt-2 text-xs text-gray-600">
                      {formatNumber(
                        contributor.changes?.total_lines_changed || 0,
                      )}{" "}
                      lines changed
                    </p>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="min-h-0 flex-1 overflow-y-auto pl-5 pr-1">
            {!selectedContributor &&
              !contributorsLoading &&
              !contributorsError &&
              messageBox("Select a contributor to inspect detailed analysis.")}

            {selectedContributor && (
              <div className="space-y-5 pb-2">
                <div className="grid gap-3 sm:grid-cols-3">
                  <div className="rounded-lg border p-3">
                    <p className="text-xs text-gray-500">Contributor</p>
                    <p className="mt-1 font-semibold text-gray-900">
                      {selectedContributor.name ||
                        selectedContributor.github_username ||
                        "Unknown"}
                    </p>
                  </div>
                  <div className="rounded-lg border p-3">
                    <p className="text-xs text-gray-500">Commits</p>
                    <p className="mt-1 flex items-center gap-2 font-semibold text-gray-900">
                      <GitCommitHorizontal className="h-4 w-4 text-blue-500" />
                      {selectedContributor.commits}
                    </p>
                  </div>
                  <div className="rounded-lg border p-3">
                    <p className="text-xs text-gray-500">Files Changed</p>
                    <p className="mt-1 flex items-center gap-2 font-semibold text-gray-900">
                      <FolderTree className="h-4 w-4 text-emerald-500" />
                      {selectedContributor.changes?.files_changed || 0}
                    </p>
                  </div>
                </div>

                <section className="space-y-2">
                  <h3 className="font-semibold text-gray-900">Top Areas</h3>

                  {analysisLoading && (
                    <div className="flex items-center gap-2 text-sm text-gray-500">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Loading area breakdown...
                    </div>
                  )}

                  {analysisError && messageBox(analysisError)}

                  {!analysisLoading &&
                    !analysisError &&
                    (analysisData?.contributor?.summary?.top_areas?.length ||
                      0) === 0 &&
                    messageBox(
                      "No area breakdown is available for this contributor yet.",
                    )}

                  <div className="space-y-2">
                    {analysisData?.contributor?.summary?.top_areas?.map(
                      (area) => (
                        <div key={area.area} className="rounded-lg border p-3">
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

                <section className="grid gap-5 lg:grid-cols-2">
                  <div className="space-y-2">
                    <h3 className="font-semibold text-gray-900">Top Files</h3>

                    {!analysisLoading &&
                      !analysisError &&
                      (analysisData?.contributor?.summary?.top_files?.length ||
                        0) === 0 &&
                      messageBox(
                        "No file-level contribution data is available.",
                      )}

                    <div className="space-y-2">
                      {analysisData?.contributor?.summary?.top_files?.map(
                        (file) => (
                          <div
                            key={file.file}
                            className="rounded-lg border p-3"
                          >
                            <p className="break-all text-sm font-medium text-gray-900">
                              {file.file}
                            </p>
                            <p className="mt-1 text-xs text-gray-500">
                              {formatNumber(file.lines_changed)} lines changed
                            </p>
                          </div>
                        ),
                      )}
                    </div>
                  </div>

                  <div className="space-y-2">
                    <h3 className="font-semibold text-gray-900">
                      Top Directories
                    </h3>

                    {directoriesLoading && (
                      <div className="flex items-center gap-2 text-sm text-gray-500">
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Loading directory breakdown...
                      </div>
                    )}

                    {directoriesError && messageBox(directoriesError)}

                    {!directoriesLoading &&
                      !directoriesError &&
                      (directoriesData?.top_directories?.length || 0) === 0 &&
                      messageBox(
                        "No directory-level contribution data is available.",
                      )}

                    <div className="space-y-2">
                      {directoriesData?.top_directories?.map((directory) => (
                        <div
                          key={directory.directory}
                          className="rounded-lg border p-3"
                        >
                          <div className="mb-1 flex items-start justify-between gap-2 text-sm">
                            <span className="break-all font-medium text-gray-900">
                              {directory.directory}
                            </span>
                            <span className="text-gray-500">
                              {formatPercent(directory.share)}
                            </span>
                          </div>
                          <p className="text-xs text-gray-500">
                            {formatNumber(directory.lines_changed)} lines
                            changed ・ {directory.files_count} files
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                </section>
              </div>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default ContributorInsightsDialog;
