import React from 'react';
import ProjectSummary from '@/components/custom/Generator/ProjectSummary';

const SummarySection = ({ projectData, onUpdateProject }) => {
  if (!projectData) return null;

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <ProjectSummary 
        projects={projectData} 
        onUpdateProject={onUpdateProject}
      />
    </div>
  );
};

export default SummarySection;