import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('axios', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
    put: vi.fn(),
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

describe('useFileUpload', () => {
  beforeEach(() => {
    localStorageMock.reset();
    vi.clearAllMocks();
    axios.post.mockResolvedValue({ data: [fakeProject] });
    axios.get.mockResolvedValue({ data: { items: [] } });
  });

  it('appends new results to existing projectData instead of replacing', async () => {
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
    expect(result.current.projectData[0].name).toBe('ExistingProject');
    expect(result.current.projectData[1].name).toBe('NewProject');
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
    axios.get.mockResolvedValueOnce({ data: { id: 42, items: [] } });
    axios.put = vi.fn().mockResolvedValue({});

    const { result } = renderHook(() => useFileUpload());

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

