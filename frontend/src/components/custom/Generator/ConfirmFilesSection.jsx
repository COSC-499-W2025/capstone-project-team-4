import React from "react";
import { Button } from "@/components/ui/button";
import FileList from "@/components/custom/Generator/FileList";
// Cool icons!!
import { Send, Trash2 } from "lucide-react";

const ConfirmFilesSection = ({
  files,
  projectNames,
  onProjectNameChange,
  onDelete,
  onDeleteAll,
  onSubmit,
  isLoading,
}) => {
  if (files.length === 0) return null;

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <h2 className="text-xl font-semibold mb-4 text-center">
        Step 2: Confirm Files
      </h2>
      <FileList
        files={files}
        projectNames={projectNames}
        onProjectNameChange={onProjectNameChange}
        onDelete={onDelete}
      />

      <div className="mt-6 flex justify-center gap-8">
        <Button
          onClick={onSubmit}
          disabled={isLoading || files.length === 0}
          className="px-4 py-2 hover:cursor-pointer"
        >
          <Send />
          {isLoading ? "Processing..." : "Submit & Analyze"}
        </Button>
        <Button
          onClick={onDeleteAll}
          className="px-4 py-2 hover:cursor-pointer"
        >
          <Trash2 />
          Delete All
        </Button>
      </div>
    </div>
  );
};

export default ConfirmFilesSection;
