import React from "react";
import Dropzone from "@/components/custom/Home/Dropzone";

const UploadSection = ({ onFileDrop }) => {
  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <h2 className="text-xl font-semibold mb-4">Step 1: Upload Projects</h2>
      <Dropzone
        onDrop={onFileDrop}
        accept={{ "application/zip": [".zip"] }}
        multiple={true}
      />
    </div>
  );
};

export default UploadSection;
