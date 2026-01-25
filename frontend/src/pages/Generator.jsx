import React from "react";
import { useFileUpload } from "@/hooks/useFileUpload";
import Navigation from "@/components/Navigation";
import { Button } from "@/components/ui/button";
import { RotateCcw } from "lucide-react";
import PageHeader from "@/components/custom/Generator/PageHeader";
import UploadSection from "@/components/custom/Generator/UploadSection";
import ConfirmFilesSection from "@/components/custom/Generator/ConfirmFilesSection";
import SummarySection from "@/components/custom/Generator/SummarySection";
import DataPrivacyConsent from "@/components/custom/Generator/DataPrivacyConsent";

const Generator = () => {
  const {
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
    clearAllData,
    handleUpdateProject,
    handleDeleteAll,
  } = useFileUpload();

  const handleReset = () => {
    if (confirm("Are you sure you want to clear all data and restart?")) {
      clearAllData();
    }
  };

  return (
    <div>
      <Navigation />

      <div className="min-h-screen bg-gradient-to-b from-gray-50 to-gray-100 py-12 px-4">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-8">
            <PageHeader
              title="Resume Generator"
              subtitle="Upload your project ZIP files to generate a comprehensive resume"
            />

            {/* Reset Button - Shows only if there's data */}
            {(uploadedFiles.length > 0 || projectData) && (
              <div className="mt-4">
                <Button
                  variant="outline"
                  onClick={handleReset}
                  className="text-red-600 hover:text-red-700 hover:bg-red-50"
                >
                  <RotateCcw className="h-4 w-4 mr-2" />
                  Restart
                </Button>
              </div>
            )}
          </div>

          <UploadSection onFileDrop={handleFileDrop} />

          <ConfirmFilesSection
            files={uploadedFiles}
            onDelete={handleDeleteFile}
            onDeleteAll={handleDeleteAll}
            onSubmit={() => handleSubmit(processFiles)}
            isLoading={isLoading}
          />

          <SummarySection
            projectData={projectData}
            onUpdateProject={handleUpdateProject}
          />

          <DataPrivacyConsent
            isOpen={showConsent}
            onClose={() => setShowConsent(false)}
            onAccept={handleConsentAccept}
          />
        </div>
      </div>
    </div>
  );
};

export default Generator;
