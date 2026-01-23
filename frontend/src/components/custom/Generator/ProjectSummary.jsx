import React, { useState } from 'react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Pencil } from 'lucide-react';
import EditProjectModal from '@/components/custom/Generator/EditProjectModal';

const ProjectSummary = ({ projects, onUpdateProject }) => {
  const [sortBy, setSortBy] = useState('contributions');
  const [editingProject, setEditingProject] = useState(null);
  const [editingIndex, setEditingIndex] = useState(null);

  if (!projects || projects.length === 0) return null;

  const sortedProjects = [...projects].sort((a, b) => {
    if (sortBy === 'contributions') {
      return (b.contributions || 0) - (a.contributions || 0);
    } else if (sortBy === 'date') {
      return new Date(b.date || 0) - new Date(a.date || 0);
    }
    return 0;
  });

  const handleEdit = (project, index) => {
    setEditingProject(project);
    setEditingIndex(index);
  };

  const handleSave = (updatedProject) => {
    if (onUpdateProject) {
      onUpdateProject(editingIndex, updatedProject);
    }
    setEditingProject(null);
    setEditingIndex(null);
  };

  return (
    <div className="w-full max-w-4xl mt-8">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold">Project Summary</h2>
        <div className="flex items-center space-x-2">
          <label htmlFor="sort-select" className="text-sm font-medium">
            Sort by:
          </label>
          <Select value={sortBy} onValueChange={setSortBy}>
            <SelectTrigger id="sort-select" className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="contributions">Contributions</SelectItem>
              <SelectItem value="date">Date</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {sortedProjects.map((project, index) => (
          <Card key={index} className="hover:shadow-lg transition-shadow relative">
            {/* Edit Button */}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleEdit(project, index)}
              className="absolute top-2 right-2 h-8 w-8 p-0 hover:bg-blue-50"
            >
              <Pencil className="h-4 w-4 text-gray-500 hover:text-blue-600" />
            </Button>

            <CardHeader>
              <CardTitle className="text-lg pr-8">{project.name}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 text-sm">
                {/* Files Analyzed */}
                <div className="flex justify-between">
                  <span className="text-gray-600">Files Analyzed:</span>
                  <span className="font-semibold">{project.contributions || 0}</span>
                </div>

                {/* Last Updated */}
                <div className="flex justify-between">
                  <span className="text-gray-600">Analyzed:</span>
                  <span className="font-semibold">
                    {project.date
                      ? new Date(project.date).toLocaleDateString()
                      : 'N/A'}
                  </span>
                </div>

                {/* Description */}
                {project.description && (
                  <div>
                    <span className="text-gray-600 block mb-1">Description:</span>
                    <p className="text-gray-700 text-xs">{project.description}</p>
                  </div>
                )}

                {/* Languages */}
                {project.languages && project.languages.length > 0 && (
                  <div>
                    <span className="text-gray-600 block mb-2">Languages:</span>
                    <div className="flex flex-wrap gap-1">
                      {project.languages.map((lang, i) => (
                        <Badge key={i} variant="secondary" className="text-xs">
                          {lang}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                {/* Frameworks */}
                {project.frameworks && project.frameworks.length > 0 && (
                  <div>
                    <span className="text-gray-600 block mb-2">Frameworks:</span>
                    <div className="flex flex-wrap gap-1">
                      {project.frameworks.map((fw, i) => (
                        <Badge key={i} variant="outline" className="text-xs">
                          {fw}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                {/* Skills */}
                {project.skills && project.skills.length > 0 && (
                  <div>
                    <span className="text-gray-600 block mb-2">Skills:</span>
                    <div className="flex flex-wrap gap-1">
                      {project.skills.slice(0, 5).map((skill, i) => (
                        <Badge key={i} className="text-xs bg-blue-100 text-blue-800">
                          {skill}
                        </Badge>
                      ))}
                      {project.skills.length > 5 && (
                        <Badge className="text-xs bg-gray-100 text-gray-600">
                          +{project.skills.length - 5} more
                        </Badge>
                      )}
                    </div>
                  </div>
                )}

                {/* Complexity Metrics */}
                {project.complexity && Object.keys(project.complexity).length > 0 && (
                  <div className="pt-2 border-t">
                    <span className="text-gray-600 block mb-1 text-xs">
                      Complexity Metrics:
                    </span>
                    <div className="text-xs text-gray-500 space-y-1">
                      {Object.entries(project.complexity).slice(0, 3).map(([key, value]) => (
                        <div key={key} className="flex justify-between">
                          <span>{key}:</span>
                          <span className="font-mono">
                            {typeof value === 'number' ? value.toFixed(2) : value}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Edit Modal */}
      {editingProject && (
        <EditProjectModal
          isOpen={!!editingProject}
          onClose={() => {
            setEditingProject(null);
            setEditingIndex(null);
          }}
          project={editingProject}
          onSave={handleSave}
        />
      )}
    </div>
  );
};

export default ProjectSummary;