import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi } from 'vitest';

vi.mock('@/components/custom/Generator/ProjectSummary', () => ({
  default: ({ projects }) => (
    <div data-testid="project-summary">Projects: {projects.length}</div>
  ),
}));

import SummarySection from '@/components/custom/Generator/SummarySection';

const fakeProjects = [
  { name: 'Alpha', projectId: 1 },
  { name: 'Beta', projectId: 2 },
];

const renderSection = (props = {}) =>
  render(
    <MemoryRouter>
      <SummarySection {...props} />
    </MemoryRouter>
  );

describe('SummarySection', () => {
  it('renders nothing when projectData is null', () => {
    const { container } = renderSection({ projectData: null });
    expect(container.firstChild).toBeNull();
  });

  it('renders ProjectSummary when projectData is provided', () => {
    renderSection({ projectData: fakeProjects });
    expect(screen.getByTestId('project-summary')).toBeInTheDocument();
    expect(screen.getByText('Projects: 2')).toBeInTheDocument();
  });

  it('does not show the history link when hasMore is false', () => {
    renderSection({ projectData: fakeProjects, hasMore: false, totalCount: 2 });
    expect(screen.queryByText(/View full history/i)).not.toBeInTheDocument();
  });

  it('shows "View full history" link when hasMore is true', () => {
    renderSection({ projectData: fakeProjects, hasMore: true, totalCount: 10 });
    expect(screen.getByText(/View full history/i)).toBeInTheDocument();
  });

  it('displays the correct counts in the footer', () => {
    renderSection({ projectData: fakeProjects, hasMore: true, totalCount: 10 });
    expect(screen.getByText(/Showing 4 of 10 projects/i)).toBeInTheDocument();
  });

  it('the history link points to /history', () => {
    renderSection({ projectData: fakeProjects, hasMore: true, totalCount: 10 });
    const link = screen.getByRole('link', { name: /View full history/i });
    expect(link.getAttribute('href')).toBe('/history');
  });
});
