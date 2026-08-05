"""
"What's new" popup shown once after a self-update.

The changelog is fetched by updater.get_changelog() BEFORE the exe is swapped
(while we know we have a working connection) and stashed in settings.json; this
module is only the window that displays it on the next launch. Kept separate
from gui.py so it can be previewed on its own -- see __main__ at the bottom.
"""

import ttkbootstrap as ttk
from ttkbootstrap.scrolled import ScrolledText

from paths import resource_path


def show_changelog_window(parent, from_version, to_tag, entries):
    """
    Open the "what's new" window. `entries` is a list of commit subject lines
    (newest first); an empty list shows a placeholder instead.

    Non-modal on purpose -- it sits above the main window but never blocks it,
    so a user who just wants to work can ignore it.
    """
    win = ttk.Toplevel(parent)
    win.title(f"What's new in {to_tag}")
    win.geometry("520x400")
    win.minsize(380, 260)
    win.transient(parent)

    try:
        win.iconbitmap(resource_path("AutoPaste.ico"))
    except Exception:
        pass

    header = (
        f"Updated v{from_version} → {to_tag}"
        if from_version
        else f"Updated to {to_tag}"
    )
    ttk.Label(
        win, text=header, font=("Helvetica", 13, "bold")
    ).pack(anchor="w", padx=14, pady=(14, 0))

    ttk.Label(
        win,
        text=(
            f"{len(entries)} change{'' if len(entries) == 1 else 's'} in this release:"
            if entries
            else "Release details:"
        ),
        font=("Helvetica", 9),
        foreground="#adb5bd",
    ).pack(anchor="w", padx=14, pady=(2, 8))

    body = ScrolledText(win, wrap="word", autohide=True)
    body.pack(fill="both", expand=True, padx=14)
    body.insert(
        "1.0",
        "\n".join(f"•  {line}" for line in entries)
        if entries
        else "No change details are available for this release.",
    )
    body.text.configure(state="disabled")

    ttk.Button(
        win, text="Close", command=win.destroy, bootstyle="secondary"
    ).pack(anchor="e", padx=14, pady=12)

    # Put it in front of the main window without stealing keyboard focus for
    # longer than the moment it appears.
    win.lift()
    win.focus_set()
    return win


if __name__ == "__main__":
    # Preview the window standalone:  python changelog.py
    root = ttk.Window(themename="superhero")
    root.withdraw()
    demo = show_changelog_window(
        root,
        "2.0.3",
        "v2.0.4",
        [
            "show a changelog popup after updating",
            "fixed P Cabinetry parsing of Chrome-copied tables",
            "fixed update missing DLL bug",
        ],
    )
    demo.protocol("WM_DELETE_WINDOW", root.destroy)
    root.mainloop()
