import React, { useState } from 'react';
import axios from 'axios';
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
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { 
  Pencil,
  Users,
  Calendar,
  Code,
  FileText,
  ChevronRight,
  Plus,
  Minus,
  Loader2,
  ChevronDown,
  ChevronUp,
  GitCompare
} from 'lucide-react';
import EditProjectModal from '@/components/custom/Generator/EditProjectModal';
import ContributorInsightsDialog from '@/components/custom/Generator/ContributorInsightsDialog';
import SnapshotComparisonModal from '@/components/custom/Generator/SnapshotComparisonModal';

const ProjectSummary = ({ projects, onUpdateProject }) => {
  const [sortBy, setSortBy] = useState('date');
  const [editingProject, setEditingProject] = useState(null);
  const [editingIndex, setEditingIndex] = useState(null);
  
  // Contributor modal state
  const [contributorModalOpen, setContributorModalOpen] = useState(false);
  const [contributorInsightsOpen, setContributorInsightsOpen] = useState(false);
  const [selectedProjectForContributors, setSelectedProjectForContributors] = useState(null);
  const [contributorData, setContributorData] = useState(null);
  const [contributorLoading, setContributorLoading] = useState(false);
  const [contributorError, setContributorError] = useState(null);

  // Snapshot comparison modal state
  const [snapshotProject, setSnapshotProject] = useState(null);

  // Expanded sections state - track which project indices have expanded sections
  const [expandedSections, setExpandedSections] = useState({});

  if (!projects || projects.length === 0) return null;

  const sortedProjects = [...projects].sort((a, b) => {
    if (sortBy === 'contributions') {
      return (b.contributions || 0) - (a.contributions || 0);
    } else if (sortBy === 'date') {
      return new Date(b.date || 0) - new Date(a.date || 0);
    } else if (sortBy === 'contributors') {
      return (b.contributorCount || 0) - (a.contributorCount || 0);
    } else if (sortBy === 'projectStart') {
      const dateA = a.projectStartedAt ? new Date(a.projectStartedAt) : new Date(0);
      const dateB = b.projectStartedAt ? new Date(b.projectStartedAt) : new Date(0);
      return dateB - dateA;
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

  // Toggle expanded section for a specific project and section type
  const toggleExpanded = (projectIndex, sectionType) => {
    const key = `${projectIndex}-${sectionType}`;
    setExpandedSections(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const isExpanded = (projectIndex, sectionType) => {
    return expandedSections[`${projectIndex}-${sectionType}`] || false;
  };

  // Format date for display
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      });
    } catch {
      return 'N/A';
    }
  };

  // Format large numbers
  const formatNumber = (num) => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K';
    }
    return num.toLocaleString();
  };

  // Parse author string to extract name
  const parseAuthorName = (authorString) => {
    if (!authorString) return 'Unknown';
    const match = authorString.match(/^([^<]+)/);
    return match ? match[1].trim() : authorString;
  };

  // Handle clicking on contributor count
  const handleContributorClick = async (project) => {
    // Make sure we have a valid projectId
    if (!project.projectId) {
      console.error('No projectId available for this project');
      return;
    }

    setSelectedProjectForContributors(project);
    setContributorModalOpen(true);
    setContributorLoading(true);
    setContributorError(null);
    setContributorData(null);

    try {
      // Fetch contributor details using THIS project's specific projectId
      const response = await axios.get(
        `/api/projects/${project.projectId}/contributors/default-branch-stats`
      );
      setContributorData(response.data);
    } catch (error) {
      console.error('Error fetching contributor data:', error);
      setContributorError(
        error.response?.data?.detail || 
        error.message || 
        'Failed to load contributor details'
      );
    } finally {
      setContributorLoading(false);
    }
  };

  const handleContributorInsightsClick = (project) => {
    if (!project.projectId) {
      console.error('No projectId available for this project');
      return;
    }

    setSelectedProjectForContributors(project);
    setContributorInsightsOpen(true);
  };

  // Render expandable badge list
  const renderExpandableBadges = (items, projectIndex, sectionType, maxItems = 5, badgeProps = {}) => {
    if (!items || items.length === 0) return null;

    const expanded = isExpanded(projectIndex, sectionType);
    const displayItems = expanded ? items : items.slice(0, maxItems);
    const hasMore = items.length > maxItems;

    return (
      <div className="flex flex-wrap gap-1">
        {displayItems.map((item, i) => (
          <Badge key={i} {...badgeProps}>
            {item}
          </Badge>
        ))}
        {hasMore && (
          <Badge 
            className="text-xs bg-gray-100 text-gray-600 cursor-pointer hover:bg-gray-200 transition-colors"
            onClick={() => toggleExpanded(projectIndex, sectionType)}
          >
            {expanded ? (
              <>
                <ChevronUp className="h-3 w-3 mr-1" />
                Show less
              </>
            ) : (
              <>
                <ChevronDown className="h-3 w-3 mr-1" />
                +{items.length - maxItems} more
              </>
            )}
          </Badge>
        )}
      </div>
    );
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
              <SelectItem value="contributions">Files Analyzed</SelectItem>
              <SelectItem value="contributors">Contributors</SelectItem>
              <SelectItem value="date">Date Analyzed</SelectItem>
              <SelectItem value="projectStart">Project Start</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {sortedProjects.map((project, index) => (
          <Card key={project.projectId || index} className="hover:shadow-lg transition-shadow relative">
            {/* Action Buttons */}
            <div className="absolute top-2 right-2 flex items-center gap-1">
              {project.projectId && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setSnapshotProject(project)}
                  className="h-8 w-8 p-0 hover:bg-indigo-50"
                  title="View project progress"
                >
                  <GitCompare className="h-4 w-4 text-gray-500 hover:text-indigo-600" />
                </Button>
              )}
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleEdit(project, index)}
                className="h-8 w-8 p-0 hover:bg-blue-50"
              >
                <Pencil className="h-4 w-4 text-gray-500 hover:text-blue-600" />
              </Button>
            </div>

            <CardHeader>
              <CardTitle className="text-lg pr-8">{project.name}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 text-sm">
                {/* Key Metrics Row */}
                <div className="grid grid-cols-2 gap-3 pb-3 border-b">
                  {/* Files Analyzed */}
                  <div className="flex items-center gap-2">
                    <FileText className="h-4 w-4 text-gray-500" />
                    <div>
                      <span className="text-gray-600 text-xs block">Files Analyzed</span>
                      <span className="font-semibold">{project.contributions || 0}</span>
                    </div>
                  </div>

                  {/* Contributors - CLICKABLE */}
                  <div>
                    <div 
                      className={`flex items-center gap-2 p-2 -m-2 rounded-lg transition-all ${
                        project.projectId 
                          ? 'cursor-pointer hover:bg-blue-50 group' 
                          : ''
                      }`}
                      onClick={() => project.projectId && handleContributorClick(project)}
                      role={project.projectId ? "button" : undefined}
                      tabIndex={project.projectId ? 0 : undefined}
                      onKeyDown={(e) => {
                        if (project.projectId && (e.key === 'Enter' || e.key === ' ')) {
                          handleContributorClick(project);
                        }
                      }}
                      title={project.projectId ? "Click to view contributor details" : undefined}
                    >
                      <Users className="h-4 w-4 text-blue-500" />
                      <div className="flex-1">
                        <span className="text-gray-600 text-xs block">Contributors</span>
                        <span className={`font-semibold ${project.projectId ? 'text-blue-600 group-hover:underline' : 'text-blue-600'}`}>
                          {project.contributorCount || 0}
                        </span>
                      </div>
                      {project.projectId && (
                        <ChevronRight className="h-4 w-4 text-blue-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                      )}
                    </div>

                    {project.projectId && (
                      <Button
                        type="button"
                        size="default"
                        variant="outline"
                        className="mt-3 min-h-11 w-full whitespace-normal border-2 border-gray-300 bg-gray-100 px-3 py-2 text-sm font-semibold leading-tight text-gray-800 shadow-sm transition-colors hover:bg-gray-200"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleContributorInsightsClick(project);
                        }}
                      >
                        Open Contributor Insights
                      </Button>
                    )}
                  </div>
                </div>

                {/* Dates Row */}
                <div className="grid grid-cols-2 gap-3 pb-3 border-b">
                  {/* Project Started */}
                  <div className="flex items-center gap-2">
                    <Calendar className="h-4 w-4 text-green-500" />
                    <div>
                      <span className="text-gray-600 text-xs block">Project Started</span>
                      <span className="font-semibold text-green-600">
                        {formatDate(project.projectStartedAt)}
                      </span>
                    </div>
                  </div>

                  {/* Analyzed Date */}
                  <div className="flex items-center gap-2">
                    <Calendar className="h-4 w-4 text-gray-500" />
                    <div>
                      <span className="text-gray-600 text-xs block">Analyzed</span>
                      <span className="font-semibold">
                        {formatDate(project.date)}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Lines of Code (if available) */}
                {project.totalLinesOfCode > 0 && (
                  <div className="flex items-center gap-2 pb-3 border-b">
                    <Code className="h-4 w-4 text-purple-500" />
                    <div>
                      <span className="text-gray-600 text-xs block">Total Lines of Code</span>
                      <span className="font-semibold text-purple-600">
                        {project.totalLinesOfCode.toLocaleString()}
                      </span>
                    </div>
                  </div>
                )}

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
                    {renderExpandableBadges(
                      project.languages, 
                      index, 
                      'languages', 
                      8,
                      { variant: "secondary", className: "text-xs" }
                    )}
                  </div>
                )}

                {/* Frameworks */}
                {project.frameworks && project.frameworks.length > 0 && (
                  <div>
                    <span className="text-gray-600 block mb-2">Frameworks:</span>
                    {renderExpandableBadges(
                      project.frameworks, 
                      index, 
                      'frameworks', 
                      5,
                      { variant: "outline", className: "text-xs" }
                    )}
                  </div>
                )}

                {/* Skills */}
                {project.skills && project.skills.length > 0 && (
                  <div>
                    <span className="text-gray-600 block mb-2">Skills:</span>
                    {renderExpandableBadges(
                      project.skills, 
                      index, 
                      'skills', 
                      5,
                      { className: "text-xs bg-blue-100 text-blue-800" }
                    )}
                  </div>
                )}

                {/* Tools & Technologies */}
                {project.toolsAndTechnologies && project.toolsAndTechnologies.length > 0 && (
                  <div>
                    <span className="text-gray-600 block mb-2">Tools & Technologies:</span>
                    {renderExpandableBadges(
                      project.toolsAndTechnologies, 
                      index, 
                      'tools', 
                      5,
                      { variant: "outline", className: "text-xs bg-orange-50 text-orange-700 border-orange-200" }
                    )}
                  </div>
                )}

                {/* Complexity Metrics */}
                {project.complexity && Object.keys(project.complexity).length > 0 && (
                  <div className="pt-2 border-t">
                    <span className="text-gray-600 block mb-1 text-xs">
                      Complexity Metrics:
                    </span>
                    <div className="text-xs text-gray-500 space-y-1">
                      {project.complexity.total_functions !== undefined && (
                        <div className="flex justify-between">
                          <span>Total Functions:</span>
                          <span className="font-mono">{project.complexity.total_functions}</span>
                        </div>
                      )}
                      {project.complexity.avg_complexity !== undefined && (
                        <div className="flex justify-between">
                          <span>Avg Complexity:</span>
                          <span className="font-mono">{project.complexity.avg_complexity.toFixed(2)}</span>
                        </div>
                      )}
                      {project.complexity.max_complexity !== undefined && (
                        <div className="flex justify-between">
                          <span>Max Complexity:</span>
                          <span className="font-mono">{project.complexity.max_complexity}</span>
                        </div>
                      )}
                      {project.complexity.high_complexity_count !== undefined && project.complexity.high_complexity_count > 0 && (
                        <div className="flex justify-between">
                          <span>High Complexity Functions:</span>
                          <span className="font-mono text-amber-600">{project.complexity.high_complexity_count}</span>
                        </div>
                      )}
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

      {/* Snapshot Comparison Modal */}
      <SnapshotComparisonModal
        isOpen={!!snapshotProject}
        onClose={() => setSnapshotProject(null)}
        project={snapshotProject}
      />

      {/* Contributors Detail Modal */}
      <Dialog open={contributorModalOpen} onOpenChange={setContributorModalOpen}>
        <DialogContent className="sm:max-w-2xl max-h-[80vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Users className="h-5 w-5 text-blue-500" />
              Contributors - {selectedProjectForContributors?.name}
            </DialogTitle>
            <DialogDescription>
              Contribution statistics from git history on the default branch
            </DialogDescription>
          </DialogHeader>

          <div className="flex-1 overflow-y-auto mt-4">
            {contributorLoading && (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
                <span className="ml-2 text-gray-600">Loading contributors...</span>
              </div>
            )}

            {contributorError && (
              <div className="text-center py-12">
                <p className="text-red-500 mb-2">Failed to load contributors</p>
                <p className="text-sm text-gray-500">{contributorError}</p>
              </div>
            )}

            {contributorData && !contributorLoading && (
              <div className="space-y-3">
                {/* Summary Stats */}
                <div className="bg-gray-50 rounded-lg p-3 mb-4">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">Total Contributors:</span>
                    <span className="font-semibold">{contributorData.total_contributors}</span>
                  </div>
                </div>

                {/* Contributor List */}
                <div className="space-y-2">
                  {contributorData.items?.map((contributor, idx) => (
                    <div 
                      key={idx}
                      className="border rounded-lg p-3 hover:bg-gray-50 transition-colors"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-gray-900 truncate">
                            {parseAuthorName(contributor.author)}
                          </p>
                          <p className="text-xs text-gray-500 truncate">
                            {contributor.author}
                          </p>
                        </div>
                        <div className="text-right ml-4">
                          <p className="text-sm font-semibold text-gray-700">
                            {formatNumber(contributor.total_lines_changed)} lines
                          </p>
                        </div>
                      </div>
                      
                      {/* Line Stats */}
                      <div className="mt-2 flex items-center gap-4 text-xs">
                        <div className="flex items-center gap-1 text-green-600">
                          <Plus className="h-3 w-3" />
                          <span>{formatNumber(contributor.total_lines_added)} added</span>
                        </div>
                        <div className="flex items-center gap-1 text-red-500">
                          <Minus className="h-3 w-3" />
                          <span>{formatNumber(contributor.total_lines_deleted)} deleted</span>
                        </div>
                      </div>

                      {/* Progress bar showing contribution proportion */}
                      {contributorData.items.length > 0 && contributorData.items[0].total_lines_changed > 0 && (
                        <div className="mt-2">
                          <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-blue-500 rounded-full transition-all"
                              style={{
                                width: `${Math.min(
                                  (contributor.total_lines_changed /
                                    contributorData.items[0].total_lines_changed) * 100,
                                  100
                                )}%`
                              }}
                            />
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>

                {contributorData.items?.length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    No contributor data available
                  </div>
                )}
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>

      <ContributorInsightsDialog
        open={contributorInsightsOpen}
        onOpenChange={setContributorInsightsOpen}
        project={selectedProjectForContributors}
      />
    </div>
  );
};

export default ProjectSummary;