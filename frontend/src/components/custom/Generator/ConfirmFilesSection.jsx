import React from 'react';
import { Button } from '@/components/ui/button';
import FileList from '@/components/custom/Generator/FileList';

const ConfirmFilesSection = ({ files, onDelete, onSubmit, isLoading }) => {
  if (files.length === 0) return null;

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <h2 className="text-xl font-semibold mb-4">Step 2: Confirm Files</h2>
      <FileList files={files} onDelete={onDelete} />
      
      <div className="mt-6 flex justify-center">
        <Button
          onClick={onSubmit}
          disabled={isLoading || files.length === 0}
          className="px-8 py-2"
        >
          {isLoading ? 'Processing...' : 'Submit & Analyze'}
        </Button>
      </div>
    </div>
  );
};

export default ConfirmFilesSection;