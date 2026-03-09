import React, { useCallback, useState } from 'react';
import { Upload, FileArchive } from 'lucide-react';

const Dropzone = ({ onDrop, accept = {}, multiple = true }) => {
  const [isDragging, setIsDragging] = useState(false);

  const handleDragEnter = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = Array.from(e.dataTransfer.files);
    
    // Filter files based on accept prop
    const acceptedFiles = files.filter((file) => {
      if (Object.keys(accept).length === 0) return true;
      
      for (const [mimeType, extensions] of Object.entries(accept)) {
        if (file.type === mimeType || extensions.some(ext => file.name.endsWith(ext))) {
          return true;
        }
      }
      return false;
    });

    if (onDrop && acceptedFiles.length > 0) {
      onDrop(acceptedFiles);
    }
  }, [accept, onDrop]);

  const handleFileInput = useCallback((e) => {
    const files = Array.from(e.target.files || []);
    
    if (onDrop && files.length > 0) {
      onDrop(files);
    }
    
    e.target.value = '';
  }, [onDrop]);

  const acceptString = Object.entries(accept)
    .flatMap(([mimeType, extensions]) => [mimeType, ...extensions])
    .join(',');

  return (
    <div
      onDragEnter={handleDragEnter}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={`
        relative border-2 border-dashed rounded-lg p-12 text-center cursor-pointer
        transition-all duration-200 ease-in-out
        ${isDragging 
          ? 'border-blue-500 bg-blue-50' 
          : 'border-gray-300 bg-gray-50 hover:border-blue-400 hover:bg-blue-50/50'
        }
      `}
    >
      <input
        type="file"
        multiple={multiple}
        accept={acceptString}
        onChange={handleFileInput}
        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
      />
      
      <div className="flex flex-col items-center space-y-4 pointer-events-none">
        <div className={`
          p-4 rounded-full transition-colors duration-200
          ${isDragging ? 'bg-blue-100' : 'bg-gray-100'}
        `}>
          {isDragging ? (
            <FileArchive className="w-12 h-12 text-blue-500" />
          ) : (
            <Upload className="w-12 h-12 text-gray-400" />
          )}
        </div>
        
        <div>
          <p className="text-lg font-semibold text-gray-700">
            {isDragging ? 'Drop files here' : 'Drag & drop files/folders here'}
          </p>
          <p className="text-sm text-gray-500 mt-1">
            or click to browse
          </p>
        </div>
        
        {Object.keys(accept).length > 0 && (
          <div className="text-xs text-gray-400">
            Accepted: {Object.values(accept).flat().join(', ')}
          </div>
        )}
      </div>
    </div>
  );
};

export default Dropzone;