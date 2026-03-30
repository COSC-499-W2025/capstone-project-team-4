import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Loader2, AlertCircle, Clock } from 'lucide-react';
import Navigation from '@/components/Navigation';
import ProjectSummary from '@/components/custom/Generator/ProjectSummary';
import { getAccessToken } from '@/lib/auth';
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationPrevious,
  PaginationNext,
  PaginationEllipsis,
} from '@/components/ui/pagination';

const PAGE_SIZE = 6;

function mapProjectDetail(d) {
  return {
    name: d.name,
    contributions: d.file_count || 0,
    date: d.zip_uploaded_at || d.created_at,
    projectStartedAt: d.project_started_at || null,
    firstCommitDate: d.first_commit_date || null,
    firstFileCreated: d.first_file_created || null,
    description: `Languages: ${d.languages?.join(', ') || 'N/A'}`,
    languages: d.languages || [],
    frameworks: d.frameworks || [],
    skills: [],
    complexity: {
      avg_complexity: d.avg_complexity || 0,
      max_complexity: d.max_complexity || 0,
    },
    contributorCount: d.contributor_count || 0,
    contributorDetails: null,
    projectId: d.id,
    totalLinesOfCode: d.total_lines_of_code || 0,
    libraryCount: d.library_count || 0,
    toolCount: d.tool_count || 0,
    libraries: d.libraries || [],
    toolsAndTechnologies: d.tools || [],
  };
}

function getPageNumbers(currentPage, totalPages) {
  if (totalPages <= 7) {
    return Array.from({ length: totalPages }, (_, i) => i + 1);
  }

  const pages = new Set([1, totalPages, currentPage]);
  if (currentPage > 1) pages.add(currentPage - 1);
  if (currentPage < totalPages) pages.add(currentPage + 1);

  const sorted = Array.from(pages).sort((a, b) => a - b);
  const result = [];

  for (let i = 0; i < sorted.length; i++) {
    if (i > 0 && sorted[i] - sorted[i - 1] > 1) {
      result.push('ellipsis');
    }
    result.push(sorted[i]);
  }

  return result;
}

export default function HistoryPage() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);

  useEffect(() => {
    const load = async () => {
      const token = getAccessToken();
      const headers = token ? { Authorization: `Bearer ${token}` } : {};

      try {
        const listRes = await axios.get('/api/projects?page=1&page_size=100', { headers });
        const items = listRes.data.items ?? [];

        if (items.length === 0) {
          setProjects([]);
          return;
        }

        const detailResults = await Promise.all(
          items.map((p) =>
            axios
              .get(`/api/projects/${p.id}`, { headers })
              .then((r) => r.data)
              .catch(() => null)
          )
        );

        setProjects(detailResults.filter(Boolean).map(mapProjectDetail));
      } catch (err) {
        setError(err?.response?.data?.detail || err?.message || 'Failed to load projects.');
      } finally {
        setLoading(false);
      }
    };

    load();
  }, []);

  const handleDeleteProject = async (projectId) => {
    const token = getAccessToken();
    try {
      await axios.delete(`/api/projects/${projectId}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      setProjects((prev) => {
        const next = prev.filter((p) => p.projectId !== projectId);
        // If deleting the last item on a non-first page, go back one page
        const newTotalPages = Math.ceil(next.length / PAGE_SIZE);
        if (currentPage > newTotalPages && newTotalPages > 0) {
          setCurrentPage(newTotalPages);
        }
        return next;
      });
    } catch (err) {
      alert(err?.response?.data?.detail || err?.message || 'Failed to delete project.');
    }
  };

  const totalPages = Math.ceil(projects.length / PAGE_SIZE);
  const pagedProjects = projects.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE);
  const pageNumbers = getPageNumbers(currentPage, totalPages);

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-gray-100">
      <Navigation />

      <div className="max-w-4xl mx-auto px-4 py-10">
        <div className="flex items-center gap-3 mb-6">
          <Clock className="h-6 w-6 text-slate-500" />
          <h1 className="text-3xl font-bold text-slate-900">Project History</h1>
          {!loading && !error && (
            <span className="ml-1 rounded-full bg-slate-100 px-2.5 py-0.5 text-sm font-medium text-slate-600">
              {projects.length}
            </span>
          )}
        </div>

        {loading && (
          <div className="flex items-center gap-2 text-slate-500 py-12 justify-center">
            <Loader2 className="h-5 w-5 animate-spin" />
            <span>Loading your projects...</span>
          </div>
        )}

        {!loading && error && (
          <div className="flex items-center gap-2 text-red-600 py-12 justify-center">
            <AlertCircle className="h-5 w-5" />
            <span>{error}</span>
          </div>
        )}

        {!loading && !error && projects.length === 0 && (
          <div className="text-center py-20 text-slate-400">
            <Clock className="h-12 w-12 mx-auto mb-3 opacity-30" />
            <p className="text-lg font-medium">No projects yet</p>
            <p className="text-sm mt-1">Upload and analyze a project to see it here.</p>
          </div>
        )}

        {!loading && !error && projects.length > 0 && (
          <>
            <div className="bg-white rounded-lg shadow-md p-6">
              <ProjectSummary
                projects={pagedProjects}
                onDeleteProject={handleDeleteProject}
              />
            </div>

            {totalPages > 1 && (
              <div className="mt-6">
                <Pagination>
                  <PaginationContent>
                    <PaginationItem>
                      <PaginationPrevious
                        onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                        aria-disabled={currentPage === 1}
                        className={currentPage === 1 ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
                      />
                    </PaginationItem>

                    {pageNumbers.map((item, i) =>
                      item === 'ellipsis' ? (
                        <PaginationItem key={`ellipsis-${i}`}>
                          <PaginationEllipsis />
                        </PaginationItem>
                      ) : (
                        <PaginationItem key={item}>
                          <PaginationLink
                            isActive={item === currentPage}
                            onClick={() => setCurrentPage(item)}
                            className="cursor-pointer"
                          >
                            {item}
                          </PaginationLink>
                        </PaginationItem>
                      )
                    )}

                    <PaginationItem>
                      <PaginationNext
                        onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                        aria-disabled={currentPage === totalPages}
                        className={currentPage === totalPages ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
                      />
                    </PaginationItem>
                  </PaginationContent>
                </Pagination>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
