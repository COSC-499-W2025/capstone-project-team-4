import React from 'react';
import { Link } from 'react-router-dom';
import ProjectSummary from '@/components/custom/Generator/ProjectSummary';

const SummarySection = ({ projectData, onUpdateProject, onDeleteProject, hasMore, totalCount }) => {
  if (!projectData) return null;

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <ProjectSummary
        projects={projectData}
        onUpdateProject={onUpdateProject}
        onDeleteProject={onDeleteProject}
      />
      {hasMore && (
        <div className="mt-4 text-center text-sm text-slate-500">
          Showing 4 of {totalCount} projects &middot;{' '}
          <Link to="/history" className="text-blue-600 hover:underline font-medium">
            View full history →
          </Link>
        </div>
      )}
    </div>
  );
};

export default SummarySection;