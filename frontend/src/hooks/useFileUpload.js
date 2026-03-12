import { useState, useEffect } from "react";
import axios from "axios";
import { getAccessToken } from "@/lib/auth";

function getAuthHeaders() {
  const token = getAccessToken();
  if (!token) {
    return {};
  }

  return {
    Authorization: `Bearer ${token}`,
  };
}

export const useFileUpload = () => {
  // Initialize state from localStorage if available
  const [uploadedFiles, setUploadedFiles] = useState(() => {
    try {
      const saved = localStorage.getItem("uploadedFiles");
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  const [projectData, setProjectData] = useState(() => {
    try {
      const saved = localStorage.getItem("projectData");
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });

  const [isLoading, setIsLoading] = useState(false);
  const [showConsent, setShowConsent] = useState(false);
  const [consentGiven, setConsentGiven] = useState(() => {
    const saved = localStorage.getItem("consentGiven");
    return saved === "true";
  });

  const [error, setError] = useState(null);

  // Save to localStorage whenever state changes
  useEffect(() => {
    localStorage.setItem("uploadedFiles", JSON.stringify(uploadedFiles));
  }, [uploadedFiles]);

  useEffect(() => {
    localStorage.setItem("projectData", JSON.stringify(projectData));
  }, [projectData]);

  useEffect(() => {
    localStorage.setItem("consentGiven", consentGiven.toString());
  }, [consentGiven]);

  const handleFileDrop = (acceptedFiles) => {
    // Filter only .zip files
    const zipFiles = acceptedFiles.filter(
      (file) => file.name.endsWith(".zip") || file.type === "application/zip",
    );

    if (zipFiles.length < acceptedFiles.length) {
      alert("Only ZIP files are allowed. Other files have been filtered out.");
    }

    setUploadedFiles((prev) => [...prev, ...zipFiles]);
  };

  const handleDeleteFile = (index) => {
    setUploadedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  function handleDeleteAll() {
    if (confirm("Are you sure you want to delete all files?")) {
      setUploadedFiles([]);
    }
  }

  const handleSubmit = async (processFilesFn) => {
    if (uploadedFiles.length === 0) {
      alert("Please upload at least one ZIP file.");
      return;
    }

    if (!consentGiven) {
      setShowConsent(true);
      return;
    }

    await processFilesFn();
  };

  const processFiles = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const results = [];

      for (const file of uploadedFiles) {
        const formData = new FormData();
        formData.append("file", file);

        const response = await axios.post("/api/projects/analyze/upload", formData, {
          headers: {
            ...getAuthHeaders(),
          },
        });

        const payload = response.data;
        const items = Array.isArray(payload) ? payload : [payload];

        // Filter out empty/root “outer zip” result so it doesn’t render as a card
        const filteredItems = items.filter((p) => {
          if (!p) return false;

          const hasName = typeof p.project_name === "string" && p.project_name.trim().length > 0;

          const hasContent =
            (p.file_count ?? 0) > 0 ||
            (p.total_lines_of_code ?? 0) > 0 ||
            (p.languages?.length ?? 0) > 0 ||
            (p.frameworks?.length ?? 0) > 0 ||
            (p.libraries?.length ?? 0) > 0 ||
            (p.tools_and_technologies?.length ?? 0) > 0;

          // If backend returns a “root project” summary for the outer zip, it often has no name or no content.
          return hasName && hasContent;
        });

        for (const data of filteredItems) {
          let contributorDetails = null;

          if (data.project_id) {
            try {
              const contributorResponse = await axios.get(
                `/api/projects/${data.project_id}/contributors/default-branch-stats`,
                {
                  headers: {
                    ...getAuthHeaders(),
                  },
                },
              );
              contributorDetails = contributorResponse.data;
            } catch (contributorError) {
              console.warn("Could not fetch contributor details:", contributorError);
            }
          }

          results.push({
          
            name: data.project_name,
            contributions: data.file_count || 0,
            date: data.zip_uploaded_at || new Date().toISOString(),
            projectStartedAt: data.project_started_at || null,
            firstCommitDate: data.first_commit_date || null,
            firstFileCreated: data.first_file_created || null,
            description: `Languages: ${data.languages?.join(", ") || "N/A"}`,
            languages: data.languages || [],
            frameworks: data.frameworks || [],
            skills: data.contextual_skills || data.skills || [],
            complexity: data.complexity_summary || {},
            contributorCount: data.contributor_count || 0,
            contributorDetails,
            projectId: data.project_id,
            totalLinesOfCode: data.total_lines_of_code || 0,
            libraryCount: data.library_count || 0,
            toolCount: data.tool_count || 0,
            libraries: data.libraries || [],
            toolsAndTechnologies: data.tools_and_technologies || [],
          });
        }
      }

      setProjectData((prev) => [...(prev || []), ...results]);
      setUploadedFiles([]);
    } catch (error) {
      console.error("Error processing files:", error);
      setError(error.message);
      const status = error?.response?.status;
      const details =
        error?.response?.data?.detail || error?.response?.data?.message || error.message;

      if (status === 401) {
        alert(
          `Error: ${details}\n\nYour session is missing or expired. Please log in and try again.`,
        );
        return;
      }

      alert(
        `Error: ${details}\n\nPlease check that your backend server is running.`,
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleConsentAccept = async () => {
    setConsentGiven(true);
    // Saves the consent to backend privacy settings
    try {
      const token = getAccessToken();
      if (token) {
        const userRes = await axios.get("/api/auth/me", {
          headers: { Authorization: `Bearer ${token}` },
        });
        await axios.put(`/api/privacy-settings/${userRes.data.id}`, {
          allow_data_collection: true,
        }, {
          headers: { Authorization: `Bearer ${token}` },
        });
      }
    } catch (error) {
      console.error("Failed to load privacy settings:", error);
    }
    processFiles();
  };

  // Update a specific project - NOW allows date to be updated
  const handleUpdateProject = (index, updatedProject) => {
    setProjectData((prev) => {
      const newData = [...prev];
      const originalProject = newData[index];

      // Merge updates, now including date
      newData[index] = {
        ...originalProject,
        ...updatedProject,
        // Keep complexity metrics and contributor details (not editable in UI)
        complexity: originalProject.complexity,
        contributorDetails: originalProject.contributorDetails,
      };

      return newData;
    });
  };

  // Clear all data (optional - call this when user wants to start fresh)
  const clearAllData = () => {
    setUploadedFiles([]);
    setProjectData(null);
    setConsentGiven(false);
    localStorage.removeItem("uploadedFiles");
    localStorage.removeItem("projectData");
    localStorage.removeItem("consentGiven");
  };

  return {
    uploadedFiles,
    projectData,
    isLoading,
    showConsent,
    setShowConsent,
    handleFileDrop,
    handleDeleteFile,
    handleSubmit,
    handleConsentAccept,
    processFiles,
    error,
    clearAllData,
    handleUpdateProject,
    handleDeleteAll,
  };
};
