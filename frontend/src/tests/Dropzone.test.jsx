import {
  render,
  screen,
  waitFor,
  fireEvent,
  within,
} from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import Dropzone from "../components/custom/Home/Dropzone.jsx/index.js";

// Mock 'react-dropzone' to bypass JSDOM limitations
// This ensures 'onDrop' is called immediately when we trigger the input
vi.mock("react-dropzone", () => ({
  useDropzone: ({ onDrop }) => ({
    getRootProps: () => ({ role: "presentation" }),
    getInputProps: () => ({
      // We force the input to be visible and predictable
      style: { display: "block" },
      type: "file",
      // When the test triggers a change, we manually feed the files to your onDrop handler
      onChange: (e) => {
        const files = Array.from(e.target.files);
        onDrop(files);
      },
    }),
    isDragActive: false,
  }),
}));

describe("Dropzone Component", () => {
  // Simple testing for the title prop
  it("renders the title", () => {
    render(<Dropzone title="Upload Artifacts" />);
    expect(screen.getByText(/Upload Artifacts/i)).toBeInTheDocument();
  });

  // Upload
  it("displays a file when it is uploaded", async () => {
    const { container } = render(<Dropzone />);

    const file = new File(["dummy content"], "my-resume.pdf", {
      type: "application/pdf",
    });

    // 1. Find the input
    const input = container.querySelector('input[type="file"]');

    // 2. Trigger the change
    fireEvent.change(input, { target: { files: [file] } });

    // 3. Verify
    await waitFor(() => {
      expect(screen.getByText("my-resume.pdf")).toBeInTheDocument();
    });
  });

  // Delete file
  it("removes the file when delete button is clicked", async () => {
    const { container } = render(<Dropzone />);
    const file = new File(["dummy content"], "mistake.png", {
      type: "image/png",
    });

    // 1. Upload
    const input = container.querySelector('input[type="file"]');
    fireEvent.change(input, { target: { files: [file] } });

    // 2. Wait for it to appear
    await waitFor(() => {
      expect(screen.getByText("mistake.png")).toBeInTheDocument();
    });

    // 3. Find and Click Delete
    const fileRow = screen.getByText("mistake.png").closest(".justify-between");
    const deleteBtn = within(fileRow).getByRole("button");

    fireEvent.click(deleteBtn);

    // 4. Verify Removal
    await waitFor(() => {
      expect(screen.queryByText("mistake.png")).not.toBeInTheDocument();
    });
  });
});
