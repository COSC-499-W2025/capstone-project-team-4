import { useState, useEffect } from "react";
import axios from "axios";

export const useFileUpload = () => {
  // Initialize state from localStorage if available
  const [uploadedFiles, setUploadedFiles] = useState(() => {
    const saved = localStorage.getItem("uploadedFiles");
    return saved ? JSON.parse(saved) : [];
  });

  const [projectData, setProjectData] = useState(() => {
    const saved = localStorage.getItem("projectData");
    return saved ? JSON.parse(saved) : null;
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
      // Process each file separately since your API takes one file at a time
      const results = [];

      for (const file of uploadedFiles) {
        const formData = new FormData();
        formData.append("file", file);

        // Use axios as it's much cleaner than fetch.
        const response = await axios.post(
          "/api/projects/analyze/upload",
          formData,
        );
        const data = response.data;

        // Transform the API response to match our display format
        results.push({
          name: data.project_name || file.name.replace(".zip", ""),
          contributions: data.files_analyzed || 0,
          date: new Date().toISOString(), // Set date when analyzed
          description: `Languages: ${data.languages?.join(", ") || "N/A"}`,
          languages: data.languages || [],
          frameworks: data.frameworks || [],
          skills: data.skills || [],
          complexity: data.complexity_metrics || {},
        });
      }

      setProjectData(results);
    } catch (error) {
      console.error("Error processing files:", error);
      setError(error.message);
      alert(
        `Error: ${error.message}\n\nPlease check that your backend server is running.`,
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleConsentAccept = () => {
    setConsentGiven(true);
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
        // Keep complexity metrics (not editable in UI)
        complexity: originalProject.complexity,
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
