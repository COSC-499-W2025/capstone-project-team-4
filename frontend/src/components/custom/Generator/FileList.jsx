import React from "react";
import { X } from "lucide-react";
import { Button } from "@/components/ui/button";

// Helper function to format bytes automatically
const formatFileSize = (bytes) => {
  if (bytes === 0) return "0 Bytes";
  if (!bytes || isNaN(bytes)) return "Unknown Size"; // Handle the NaN case gracefully

  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB", "TB"];

  // Calculate which unit to use (0 = Bytes, 1 = KB, 2 = MB, etc.)
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
};

const FileList = ({ files, onDelete }) => {
  if (files.length === 0) return null;

  return (
    <div className="w-full max-w-2xl mt-6 mx-auto">
      <h3 className="text-lg font-semibold mb-3 text-center">Uploaded Files</h3>
      <div className="space-y-2">
        {files.map((file, index) => (
          <div
            key={`${file.name}-${index}`}
            className="flex items-center justify-between p-3 bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition-shadow"
          >
            <div className="flex items-center space-x-3 flex-1">
              <div className="flex-shrink-0 w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                <span className="text-blue-600 font-semibold text-sm">ZIP</span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {file.name}
                </p>
                {/* Use the helper function here */}
                <p className="text-xs text-gray-500">
                  {formatFileSize(file.size)}
                </p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onDelete(index)}
              className="ml-2 hover:bg-red-50 hover:text-red-600"
              aria-label={`Delete ${file.name}`}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        ))}
      </div>
    </div>
  );
};

export default FileList;
