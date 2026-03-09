import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, it, expect, vi, beforeEach } from "vitest";

vi.mock("axios", () => ({
  default: {
    get: vi.fn(),
    put: vi.fn(),
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

describe("AccountPage - Manage Data", () => {
  beforeEach(() => {
    localStorageMock.reset();
    vi.clearAllMocks();
    axios.get.mockResolvedValue({ data: fakeUser });
    axios.put.mockResolvedValue({ data: fakePrivacy });
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
    fireEvent.click(toggles[0]);

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
    fireEvent.click(toggles[0]);

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
});
