import { useMemo, useState } from "react";

export function usePasswordToggle() {
    const [show, setShow] = useState(false);
    return useMemo(
        () => ({
        show,
        toggle: () => setShow((s) => !s),
        inputType: show ? "text" : "password",
        }),
        [show]
    );
}
