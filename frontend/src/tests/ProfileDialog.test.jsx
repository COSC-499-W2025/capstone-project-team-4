import ProfileDialog from "@/components/custom/profiles/ProfileDialog";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/user_profile_API", () => ({
    createProfile: vi.fn(),
    getProfileByUserId: vi.fn(),
    updateProfile: vi.fn(),
    }));

    import {
    createProfile,
    getProfileByUserId,
    updateProfile,
} from "@/lib/user_profile_API";

    describe("ProfileDialog Component", () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    function setup(props = {}) {
        const onOpenChange = vi.fn();
        const onSaved = vi.fn();

        render(
        <ProfileDialog
            open
            onOpenChange={onOpenChange}
            onSaved={onSaved}
            {...props}
        />
        );

        const dialog = screen.getByRole("dialog");
        return { dialog, onOpenChange, onSaved };
    }

    const userIdInput = () => screen.getByPlaceholderText("1");

    const getTextInputNearLabel = (dialog, labelText) => {
        const label = within(dialog).getByText(new RegExp(`^${labelText}$`, "i"));
        const field = label.parentElement;
        return field?.querySelector("input, textarea");
    };

    const fillRequired = (dialog, { first = "John", last = "Doe", phone = "250-555-0123" } = {}) => {
        fireEvent.change(getTextInputNearLabel(dialog, "First name"), { target: { value: first } });
        fireEvent.change(getTextInputNearLabel(dialog, "Last name"), { target: { value: last } });
        fireEvent.change(getTextInputNearLabel(dialog, "Phone"), { target: { value: phone } });
    };

    it("renders create mode by default and disables Load profile until user id is valid", () => {
        const { dialog } = setup();

        expect(within(dialog).getByRole("heading", { name: /create profile/i })).toBeInTheDocument();

        const loadBtn = within(dialog).getByRole("button", { name: /load profile/i });
        expect(loadBtn).toBeDisabled();

        fireEvent.change(userIdInput(), { target: { value: "3" } });
        expect(loadBtn).toBeEnabled();
    });

    it("loads an existing profile and switches to update mode", async () => {
        getProfileByUserId.mockResolvedValueOnce({
        first_name: "Ada",
        last_name: "Lovelace",
        phone: "(250) 555-9999",
        city: "Kelowna",
        state: "BC",
        country: "Canada",
        linkedin_url: "https://www.linkedin.com/in/ada",
        github_url: "https://github.com/ada",
        portfolio_url: "https://ada.dev",
        summary: "Hello",
        });

        const { dialog } = setup();

        fireEvent.change(userIdInput(), { target: { value: "7" } });
        fireEvent.click(within(dialog).getByRole("button", { name: /load profile/i }));

        await waitFor(() => expect(getProfileByUserId).toHaveBeenCalledWith(7));
        expect(within(dialog).getByRole("heading", { name: /update profile/i })).toBeInTheDocument();

        await waitFor(() => {
        expect(getTextInputNearLabel(dialog, "First name")?.value).toBe("Ada");
        });

        expect(getTextInputNearLabel(dialog, "Last name").value).toBe("Lovelace");
        expect(getTextInputNearLabel(dialog, "Phone").value).toBe("2505559999");
    });

    it("creates a new profile when required fields are valid", async () => {
        createProfile.mockResolvedValueOnce({ ok: true });
        const { dialog, onOpenChange, onSaved } = setup();

        fireEvent.change(userIdInput(), { target: { value: "5" } });
        fillRequired(dialog);

        fireEvent.click(within(dialog).getByRole("button", { name: /create profile/i }));

        await waitFor(() => expect(createProfile).toHaveBeenCalledTimes(1));

        const [idArg, formArg] = createProfile.mock.calls[0];
        expect(idArg).toBe(5);
        expect(formArg.first_name).toBe("John");
        expect(formArg.last_name).toBe("Doe");
        expect(formArg.phone).toBe("2505550123");

        expect(onOpenChange).toHaveBeenCalledWith(false);
        expect(onSaved).toHaveBeenCalledTimes(1);
    });

    it("updates an existing profile when in update mode", async () => {
        getProfileByUserId.mockResolvedValueOnce({
        first_name: "A",
        last_name: "B",
        phone: "2505550123",
        city: "",
        state: "",
        country: "",
        linkedin_url: "",
        github_url: "",
        portfolio_url: "",
        summary: "",
        });

        updateProfile.mockResolvedValueOnce({ ok: true });

        const { dialog, onOpenChange, onSaved } = setup();

        fireEvent.change(userIdInput(), { target: { value: "10" } });
        fireEvent.click(within(dialog).getByRole("button", { name: /load profile/i }));

        await waitFor(() =>
        expect(within(dialog).getByRole("heading", { name: /update profile/i })).toBeInTheDocument()
        );

        fireEvent.change(getTextInputNearLabel(dialog, "First name"), { target: { value: "Grace" } });
        fireEvent.click(within(dialog).getByRole("button", { name: /save changes/i }));

        await waitFor(() => expect(updateProfile).toHaveBeenCalledTimes(1));

        const [idArg, formArg] = updateProfile.mock.calls[0];
        expect(idArg).toBe(10);
        expect(formArg.first_name).toBe("Grace");

        expect(onOpenChange).toHaveBeenCalledWith(false);
        expect(onSaved).toHaveBeenCalledTimes(1);
    });

    it("blocks submit when required fields are missing", () => {
    const { dialog } = setup();

    fireEvent.change(userIdInput(), { target: { value: "3" } });

    fireEvent.change(getTextInputNearLabel(dialog, "First name"), {
        target: { value: "John" },
    });

    const submitBtn = within(dialog).getByRole("button", { name: /create profile/i });

    expect(submitBtn).toBeDisabled();
    expect(createProfile).not.toHaveBeenCalled();
    });

    it("shows 'not found' message when loading profile returns 404", async () => {
        getProfileByUserId.mockRejectedValueOnce({ status: 404 });

        const { dialog } = setup();

        fireEvent.change(userIdInput(), { target: { value: "99" } });
        fireEvent.click(within(dialog).getByRole("button", { name: /load profile/i }));

        await waitFor(() => expect(getProfileByUserId).toHaveBeenCalledWith(99));

        expect(within(dialog).getByText(/no profile found for this user/i)).toBeInTheDocument();
        expect(within(dialog).getByRole("heading", { name: /create profile/i })).toBeInTheDocument();
    });
});
