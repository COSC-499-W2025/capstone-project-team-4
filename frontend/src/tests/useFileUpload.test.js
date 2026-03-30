import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('axios', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

vi.mock('@/lib/auth', () => ({
  getAccessToken: () => 'fake-token',
}));

// Stub localStorage since jsdom's version isn't available in this environment
const localStorageMock = (() => {
  let store = {};
  return {
    getItem: (key) => store[key] ?? null,
    setItem: (key, val) => { store[key] = String(val); },
    removeItem: (key) => { delete store[key]; },
    reset: () => { store = {}; },
  };
})();

vi.stubGlobal('localStorage', localStorageMock);

import axios from 'axios';
import { useFileUpload } from '@/hooks/useFileUpload';

const fakeProject = {
  project_name: 'NewProject',
  file_count: 5,
  total_lines_of_code: 200,
  languages: ['JavaScript'],
  frameworks: ['React'],
  libraries: [],
  tools_and_technologies: [],
  contextual_skills: ['Frontend'],
  complexity_summary: {},
  contributor_count: 1,
  project_id: 99,
  zip_uploaded_at: '2026-03-01T00:00:00Z',
  project_started_at: '2025-06-01T00:00:00Z',
  first_commit_date: null,
  first_file_created: '2025-06-01T00:00:00Z',
  library_count: 0,
  tool_count: 0,
};

const fakeDetail = {
  id: 5,
  name: 'Past Project',
  file_count: 10,
  created_at: '2025-12-01T00:00:00Z',
  zip_uploaded_at: '2025-12-01T00:00:00Z',
  project_started_at: null,
  first_commit_date: null,
  first_file_created: null,
  languages: ['TypeScript'],
  frameworks: ['Vue'],
  libraries: [],
  tools: [],
  total_lines_of_code: 500,
  avg_complexity: 1.5,
  max_complexity: 5,
  contributor_count: 2,
  library_count: 0,
  tool_count: 0,
};

describe('useFileUpload', () => {
  beforeEach(() => {
    localStorageMock.reset();
    vi.clearAllMocks();
    axios.post.mockResolvedValue({ data: [fakeProject] });
    // Default: empty project list so the load-on-mount effect does nothing
    axios.get.mockResolvedValue({ data: { items: [] } });
    axios.delete.mockResolvedValue({});
  });

  // ── Upload behaviour ──────────────────────────────────────────────────────

  it('prepends new results to existing projectData (newest appears first)', async () => {
    const existing = [{ name: 'ExistingProject', projectId: 1 }];
    localStorageMock.setItem('projectData', JSON.stringify(existing));
    localStorageMock.setItem('consentGiven', 'true');

    const { result } = renderHook(() => useFileUpload());

    act(() => {
      result.current.handleFileDrop([
        new File(['content'], 'test.zip', { type: 'application/zip' }),
      ]);
    });

    await act(async () => {
      await result.current.processFiles();
    });

    expect(result.current.projectData).toHaveLength(2);
    // New upload should be first
    expect(result.current.projectData[0].name).toBe('NewProject');
    expect(result.current.projectData[1].name).toBe('ExistingProject');
  });

  it('clears uploadedFiles after a successful analysis', async () => {
    localStorageMock.setItem('consentGiven', 'true');

    const { result } = renderHook(() => useFileUpload());

    act(() => {
      result.current.handleFileDrop([
        new File(['content'], 'test.zip', { type: 'application/zip' }),
      ]);
    });

    expect(result.current.uploadedFiles).toHaveLength(1);

    await act(async () => {
      await result.current.processFiles();
    });

    expect(result.current.uploadedFiles).toHaveLength(0);
  });

  it('does not clear uploadedFiles if the analysis fails', async () => {
    localStorageMock.setItem('consentGiven', 'true');
    axios.post.mockRejectedValue(new Error('Network error'));
    vi.stubGlobal('alert', vi.fn());

    const { result } = renderHook(() => useFileUpload());

    act(() => {
      result.current.handleFileDrop([
        new File(['content'], 'test.zip', { type: 'application/zip' }),
      ]);
    });

    await act(async () => {
      await result.current.processFiles();
    });

    expect(result.current.uploadedFiles).toHaveLength(1);
  });

  // ── recentProjectData ─────────────────────────────────────────────────────

  it('recentProjectData is null when projectData is null', () => {
    const { result } = renderHook(() => useFileUpload());
    expect(result.current.recentProjectData).toBeNull();
  });

  it('recentProjectData returns at most 4 projects', () => {
    const many = Array.from({ length: 10 }, (_, i) => ({ name: `P${i}`, projectId: i }));
    localStorageMock.setItem('projectData', JSON.stringify(many));

    const { result } = renderHook(() => useFileUpload());
    expect(result.current.recentProjectData).toHaveLength(4);
  });

  it('recentProjectData returns all projects when there are 4 or fewer', () => {
    const few = [{ name: 'A', projectId: 1 }, { name: 'B', projectId: 2 }];
    localStorageMock.setItem('projectData', JSON.stringify(few));

    const { result } = renderHook(() => useFileUpload());
    expect(result.current.recentProjectData).toHaveLength(2);
  });

  it('recentProjectData reflects the first 4 entries (most recent uploads first)', async () => {
    const existing = Array.from({ length: 4 }, (_, i) => ({ name: `Old${i}`, projectId: i }));
    localStorageMock.setItem('projectData', JSON.stringify(existing));
    localStorageMock.setItem('consentGiven', 'true');

    const { result } = renderHook(() => useFileUpload());

    act(() => {
      result.current.handleFileDrop([
        new File(['content'], 'new.zip', { type: 'application/zip' }),
      ]);
    });

    await act(async () => {
      await result.current.processFiles();
    });

    // Total is now 5; recentProjectData should show the 4 most recent
    expect(result.current.recentProjectData).toHaveLength(4);
    // The newly uploaded project should be first
    expect(result.current.recentProjectData[0].name).toBe('NewProject');
  });

  // ── handleDeleteProject ───────────────────────────────────────────────────

  it('handleDeleteProject calls DELETE endpoint with correct project id', async () => {
    const projects = [{ name: 'ToDelete', projectId: 7 }, { name: 'Keep', projectId: 8 }];
    localStorageMock.setItem('projectData', JSON.stringify(projects));

    const { result } = renderHook(() => useFileUpload());

    await act(async () => {
      await result.current.handleDeleteProject(7);
    });

    expect(axios.delete).toHaveBeenCalledWith(
      '/api/projects/7',
      expect.objectContaining({ headers: { Authorization: 'Bearer fake-token' } })
    );
  });

  it('handleDeleteProject removes the deleted project from projectData', async () => {
    const projects = [{ name: 'ToDelete', projectId: 7 }, { name: 'Keep', projectId: 8 }];
    localStorageMock.setItem('projectData', JSON.stringify(projects));

    const { result } = renderHook(() => useFileUpload());

    await act(async () => {
      await result.current.handleDeleteProject(7);
    });

    expect(result.current.projectData).toHaveLength(1);
    expect(result.current.projectData[0].name).toBe('Keep');
  });

  it('handleDeleteProject shows an alert when the DELETE request fails', async () => {
    vi.stubGlobal('alert', vi.fn());
    axios.delete.mockRejectedValue({ message: 'Server error' });
    localStorageMock.setItem('projectData', JSON.stringify([{ name: 'P', projectId: 1 }]));

    const { result } = renderHook(() => useFileUpload());

    await act(async () => {
      await result.current.handleDeleteProject(1);
    });

    expect(window.alert).toHaveBeenCalled();
    // Project should NOT be removed since the API call failed
    expect(result.current.projectData).toHaveLength(1);
  });

  // ── Load previous projects on mount ──────────────────────────────────────

  it('loads previous projects from the API on mount', async () => {
    axios.get
      .mockResolvedValueOnce({ data: { items: [{ id: 5 }] } })
      .mockResolvedValueOnce({ data: fakeDetail });

    const { result } = renderHook(() => useFileUpload());

    await waitFor(() => {
      expect(result.current.projectData).not.toBeNull();
    });

    expect(result.current.projectData).toHaveLength(1);
    expect(result.current.projectData[0].name).toBe('Past Project');
    expect(result.current.projectData[0].projectId).toBe(5);
    expect(result.current.projectData[0].languages).toEqual(['TypeScript']);
  });

  it('does not duplicate projects already present in localStorage', async () => {
    const existing = [{ name: 'Already Here', projectId: 5 }];
    localStorageMock.setItem('projectData', JSON.stringify(existing));

    axios.get
      .mockResolvedValueOnce({ data: { items: [{ id: 5 }] } })
      .mockResolvedValueOnce({ data: { ...fakeDetail, id: 5 } });

    const { result } = renderHook(() => useFileUpload());

    // Allow effects to settle; projectData should stay at 1, not grow to 2
    await act(async () => {
      await new Promise((r) => setTimeout(r, 0));
    });

    expect(result.current.projectData).toHaveLength(1);
  });

  it('silently ignores failures when loading previous projects', async () => {
    axios.get.mockRejectedValue(new Error('Network error'));

    const { result } = renderHook(() => useFileUpload());

    await act(async () => {
      await new Promise((r) => setTimeout(r, 0));
    });

    // Should not throw and should leave projectData as null
    expect(result.current.projectData).toBeNull();
  });

  // ── Misc ──────────────────────────────────────────────────────────────────

  it('starts with no projectData when localStorage is empty', () => {
    const { result } = renderHook(() => useFileUpload());
    expect(result.current.projectData).toBeNull();
  });

  it('recovers gracefully when localStorage contains corrupted JSON', () => {
    localStorageMock.setItem('projectData', 'not-valid-json{{{');
    localStorageMock.setItem('uploadedFiles', '[broken');
    const { result } = renderHook(() => useFileUpload());
    expect(result.current.projectData).toBeNull();
    expect(result.current.uploadedFiles).toEqual([]);
  });

  it('handleConsentAccept calls PUT privacy-settings with allow_data_collection true', async () => {
    const { result } = renderHook(() => useFileUpload());

    // Let the loadPreviousProjects mount effect settle first so it consumes
    // the default mock, not the one we're about to set up for /api/auth/me
    await act(async () => {
      await new Promise((r) => setTimeout(r, 0));
    });

    axios.get.mockResolvedValueOnce({ data: { id: 42 } });
    axios.put = vi.fn().mockResolvedValue({});

    await act(async () => {
      await result.current.handleConsentAccept();
    });

    expect(axios.put).toHaveBeenCalledWith(
      '/api/privacy-settings/42',
      { allow_data_collection: true },
      expect.objectContaining({ headers: expect.objectContaining({ Authorization: 'Bearer fake-token' }) })
    );
  });

  it('handleConsentAccept still processes files if backend call fails', async () => {
    axios.get.mockRejectedValueOnce(new Error('Network error'));
    axios.post.mockResolvedValue({ data: [fakeProject] });

    localStorageMock.setItem('consentGiven', 'false');

    const { result } = renderHook(() => useFileUpload());

    act(() => {
      result.current.handleFileDrop([
        new File(['content'], 'test.zip', { type: 'application/zip' }),
      ]);
    });

    await act(async () => {
      await result.current.handleConsentAccept();
    });

    expect(localStorageMock.getItem('consentGiven')).toBe('true');
    expect(result.current.projectData).toHaveLength(1);
  });
});
