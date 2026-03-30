import ProfileDialog from "@/components/custom/ProfileDialog";
import { getMyProfile, upsertMyProfile } from "@/lib/userProfileApi";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/userProfileApi", () => ({
    getMyProfile: vi.fn(),
    upsertMyProfile: vi.fn(),
}));

const existingProfile = {
    first_name: "Kussh",
    last_name: "Satija",
    phone: "2505550123",
    city: "Kelowna",
    state: "British Columbia",
    country: "Canada",
    linkedin_url: "https://linkedin.com/in/kussh",
    github_url: "https://github.com/kussh",
    portfolio_url: "https://kussh.dev",
    summary: "Computer science student building data-driven products.",
};

describe("ProfileDialog", () => {
    const onOpenChange = vi.fn();

    beforeEach(() => {
        vi.clearAllMocks();
    });

    it("loads existing profile data into the form", async () => {
        getMyProfile.mockResolvedValue(existingProfile);
        render(<ProfileDialog open={true} onOpenChange={onOpenChange} />);
        expect(getMyProfile).toHaveBeenCalledTimes(1);
        expect(await screen.findByDisplayValue("Kussh")).toBeInTheDocument();
        expect(screen.getByDisplayValue("Satija")).toBeInTheDocument();
        expect(screen.getByDisplayValue("Kelowna")).toBeInTheDocument();
        expect(
            screen.getByDisplayValue("https://github.com/kussh")
        ).toBeInTheDocument();
    });
    it("shows validation error when first name and last name are empty", async () => {
        getMyProfile.mockRejectedValue({ status: 404 });
        render(<ProfileDialog open={true} onOpenChange={onOpenChange} />);
        const saveButton = await screen.findByRole("button", { name: /save profile/i });
        fireEvent.click(saveButton);
        expect(
            await screen.findByText("First name and last name are required.")
        ).toBeInTheDocument();
        expect(upsertMyProfile).not.toHaveBeenCalled();
    });
    it("saves profile data and closes the dialog", async () => {
        getMyProfile.mockRejectedValue({ status: 404 });
        upsertMyProfile.mockResolvedValue({
            ...existingProfile,
            first_name: "Kussh",
            last_name: "Satija",
        });
        render(<ProfileDialog open={true} onOpenChange={onOpenChange} />);
        const firstNameInput = await screen.findByPlaceholderText("First Name");
        const lastNameInput = screen.getByPlaceholderText("Last Name");
        fireEvent.change(firstNameInput, { target: { value: "Kussh" } });
        fireEvent.change(lastNameInput, { target: { value: "Satija" } });
        fireEvent.click(screen.getByRole("button", { name: /save profile/i }));
        await waitFor(() => {
            expect(upsertMyProfile).toHaveBeenCalledTimes(1);
        });
        expect(upsertMyProfile).toHaveBeenCalledWith({
            first_name: "Kussh",
            last_name: "Satija",
            phone: "",
            city: "",
            state: "",
            country: "",
            linkedin_url: "",
            github_url: "",
            portfolio_url: "",
            summary: "",
        });
        expect(onOpenChange).toHaveBeenCalledWith(false);
    });
    it("shows an error message when profile load fails with a non-404 error", async () => {
        getMyProfile.mockRejectedValue({ status: 500, message: "Server error" });
        render(<ProfileDialog open={true} onOpenChange={onOpenChange} />);
        expect(
            await screen.findByText("Failed to load profile.")
        ).toBeInTheDocument();
    });
});