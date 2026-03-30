import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, it, expect, vi, beforeEach } from "vitest";

vi.mock("axios", () => ({
  default: {
    get: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

vi.mock("@/lib/auth", () => ({
  getAccessToken: () => "fake-token",
  clearAccessToken: vi.fn(),
  isAuthenticated: () => true,
}));

vi.mock("@/hooks/useFileUpload", () => ({
  useFileUpload: () => ({
    clearAllData: vi.fn(),
  }),
}));

const localStorageMock = (() => {
  let store = {};
  return {
    getItem: (key) => store[key] ?? null,
    setItem: (key, val) => { store[key] = String(val); },
    removeItem: (key) => { delete store[key]; },
    reset: () => { store = {}; },
  };
})();

vi.stubGlobal("localStorage", localStorageMock);

import axios from "axios";
import AccountPage from "@/pages/Account";

const fakeUser = {
  id: 1,
  email: "test@example.com",
  is_active: true,
  created_at: "2025-01-01T00:00:00Z",
  updated_at: "2025-01-02T00:00:00Z",
};

const fakePrivacy = {
  allow_data_collection: true,
  allow_ai_resume_generation: false,
};

const emptyProjects = { items: [], total: 0, page: 1, page_size: 100, pages: 0 };

describe("AccountPage - Manage Data", () => {
  beforeEach(() => {
    localStorageMock.reset();
    vi.clearAllMocks();
    axios.get.mockResolvedValue({ data: fakeUser });
    axios.put.mockResolvedValue({ data: fakePrivacy });
    axios.delete.mockResolvedValue({});
  });

  it("renders the Manage Data button", async () => {
    render(
      <MemoryRouter>
        <AccountPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("Manage Data")).toBeInTheDocument();
    });
  });

  it("opens the modal when Manage Data is clicked", async () => {
    axios.get
      .mockResolvedValueOnce({ data: fakeUser })
      .mockResolvedValueOnce({ data: fakePrivacy });

    render(
      <MemoryRouter>
        <AccountPage />
      </MemoryRouter>
    );

    await waitFor(() => screen.getByText("Manage Data"));
    fireEvent.click(screen.getByText("Manage Data"));

    await waitFor(() => {
      expect(screen.getByText("Allow data collection")).toBeInTheDocument();  // ← changed
    });
  });

  it("displays both privacy toggles in the modal", async () => {
    axios.get
      .mockResolvedValueOnce({ data: fakeUser })
      .mockResolvedValueOnce({ data: fakePrivacy });

    render(
      <MemoryRouter>
        <AccountPage />
      </MemoryRouter>
    );

    await waitFor(() => screen.getByText("Manage Data"));
    fireEvent.click(screen.getByText("Manage Data"));

    await waitFor(() => {
      expect(screen.getByText("Allow data collection")).toBeInTheDocument();
      expect(screen.getByText("Allow AI generation")).toBeInTheDocument();
    });
  });

  it("sets consentGiven to false in localStorage when allow_data_collection is saved as false", async () => {
    axios.get
      .mockResolvedValueOnce({ data: fakeUser })
      .mockResolvedValueOnce({ data: { ...fakePrivacy, allow_data_collection: true } });

    localStorageMock.setItem("consentGiven", "true");

    render(
      <MemoryRouter>
        <AccountPage />
      </MemoryRouter>
    );

    await waitFor(() => screen.getByText("Manage Data"));
    fireEvent.click(screen.getByText("Manage Data"));

    await waitFor(() => screen.getByText("Allow data collection"));

    // Toggle data collection off
    const toggles = screen.getAllByRole("switch");
    await userEvent.click(toggles[0]);

    fireEvent.click(screen.getByText("Save Settings"));

    await waitFor(() => {
      expect(localStorageMock.getItem("consentGiven")).toBe("false");
    });
  });

  it("does not reset consentGiven when allow_data_collection is saved as true", async () => {
    axios.get
      .mockResolvedValueOnce({ data: fakeUser })
      .mockResolvedValueOnce({ data: { ...fakePrivacy, allow_data_collection: false } });

    localStorageMock.setItem("consentGiven", "true");

    render(
      <MemoryRouter>
        <AccountPage />
      </MemoryRouter>
    );

    await waitFor(() => screen.getByText("Manage Data"));
    fireEvent.click(screen.getByText("Manage Data"));

    await waitFor(() => screen.getByText("Allow data collection"));

    // Toggle data collection on
    const toggles = screen.getAllByRole("switch");
    await userEvent.click(toggles[0]);

    fireEvent.click(screen.getByText("Save Settings"));

    await waitFor(() => {
      expect(localStorageMock.getItem("consentGiven")).toBe("true");
    });
  });

  it("shows an error message if saving privacy settings fails", async () => {
    axios.get
      .mockResolvedValueOnce({ data: fakeUser })
      .mockResolvedValueOnce({ data: fakePrivacy });
    axios.put.mockRejectedValueOnce(new Error("Network error"));

    render(
      <MemoryRouter>
        <AccountPage />
      </MemoryRouter>
    );

    await waitFor(() => screen.getByText("Manage Data"));
    fireEvent.click(screen.getByText("Manage Data"));

    await waitFor(() => screen.getByText("Save Settings"));
    fireEvent.click(screen.getByText("Save Settings"));

    await waitFor(() => {
      expect(screen.getByText("Failed to save. Please try again.")).toBeInTheDocument();
    });
  });

  // Test 7: clicking Manage Projects switches to projects view
  it("switches to projects view when Manage Projects is clicked", async () => {
    axios.get
      .mockResolvedValueOnce({ data: fakeUser })
      .mockResolvedValueOnce({ data: fakePrivacy })
      .mockResolvedValueOnce({ data: emptyProjects });

    render(
      <MemoryRouter>
        <AccountPage />
      </MemoryRouter>
    );

    await waitFor(() => screen.getByText("Manage Data"));
    fireEvent.click(screen.getByText("Manage Data"));
    await waitFor(() => screen.getByText("Manage Projects"));
    fireEvent.click(screen.getByText("Manage Projects"));

    await waitFor(() => {
      expect(screen.getByText("View and delete your uploaded projects.")).toBeInTheDocument();
    });
  });

  // Test 8: projects list renders project names
  it("renders project names in the projects view", async () => {
    const fakeProjects = {
      items: [
        { id: 1, name: "My Project", file_count: 10, language_count: 2 },
        { id: 2, name: "Another Project", file_count: 5, language_count: 1 },
      ],
      total: 2, page: 1, page_size: 100, pages: 1,
    };

    axios.get
      .mockResolvedValueOnce({ data: fakeUser })
      .mockResolvedValueOnce({ data: fakePrivacy })
      .mockResolvedValueOnce({ data: fakeProjects });

    render(
      <MemoryRouter>
        <AccountPage />
      </MemoryRouter>
    );

    await waitFor(() => screen.getByText("Manage Data"));
    fireEvent.click(screen.getByText("Manage Data"));
    await waitFor(() => screen.getByText("Manage Projects"));
    fireEvent.click(screen.getByText("Manage Projects"));

    await waitFor(() => {
      expect(screen.getByText("My Project")).toBeInTheDocument();
      expect(screen.getByText("Another Project")).toBeInTheDocument();
    });
  });

  // Test 9: empty state shows when no projects
  it("shows empty state when there are no projects", async () => {
    axios.get
      .mockResolvedValueOnce({ data: fakeUser })
      .mockResolvedValueOnce({ data: fakePrivacy })
      .mockResolvedValueOnce({ data: emptyProjects });

    render(
      <MemoryRouter>
        <AccountPage />
      </MemoryRouter>
    );

    await waitFor(() => screen.getByText("Manage Data"));
    fireEvent.click(screen.getByText("Manage Data"));
    await waitFor(() => screen.getByText("Manage Projects"));
    fireEvent.click(screen.getByText("Manage Projects"));

    await waitFor(() => {
      expect(screen.getByText("No projects found.")).toBeInTheDocument();
    });
  });

  // Test 10: back arrow returns to privacy settings view
  it("returns to privacy settings view when back arrow is clicked", async () => {
    axios.get
      .mockResolvedValueOnce({ data: fakeUser })
      .mockResolvedValueOnce({ data: fakePrivacy })
      .mockResolvedValueOnce({ data: emptyProjects });

    render(
      <MemoryRouter>
        <AccountPage />
      </MemoryRouter>
    );

    await waitFor(() => screen.getByText("Manage Data"));
    fireEvent.click(screen.getByText("Manage Data"));
    await waitFor(() => screen.getByText("Manage Projects"));
    fireEvent.click(screen.getByText("Manage Projects"));
    await waitFor(() => screen.getByText("No projects found."));

    // Click the back arrow
    fireEvent.click(screen.getByRole("button", { name: "" }));

    await waitFor(() => {
      expect(screen.getByText("Allow data collection")).toBeInTheDocument();
    });
  });
});