import React from 'react';
import { X } from 'lucide-react';
import { Button } from '@/components/ui/button';

const FileList = ({ files, onDelete }) => {
  if (files.length === 0) return null;

  return (
    <div className="w-full max-w-2xl mt-6">
      <h3 className="text-lg font-semibold mb-3">Uploaded Files</h3>
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
                <p className="text-xs text-gray-500">
                  {(file.size / 1024).toFixed(2)} KB
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
