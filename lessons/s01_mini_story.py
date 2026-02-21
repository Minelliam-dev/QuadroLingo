import tkinter as tk

LESSON_META = {
    "id": "s01_mini_story",
    "title": "A tiny story",
    "subtitle": "Read and choose",
    "emoji": "📖",
    "kind": "stories",
    "order": 1
}

def build(parent, app, meta):
    t = app.theme()
    frame = tk.Frame(parent, bg=t["bg"])
    frame.grid_columnconfigure(0, weight=1)

    header = tk.Frame(frame, bg=t["bg"])
    header.grid(row=0, column=0, sticky="ew", padx=18, pady=(16, 10))
    header.grid_columnconfigure(1, weight=1)

    tk.Button(
        header, text="← Back", command=app.go_back,
        font=("Segoe UI", 10, "bold"),
        bg=t["panel"], fg=t["text"],
        activebackground=t["nav_hover"], activeforeground=t["text"],
        relief="flat", cursor="hand2",
        highlightbackground=t["border"], highlightthickness=1,
        padx=12, pady=8
    ).grid(row=0, column=0, sticky="w")

    tk.Label(header, text=meta["title"], bg=t["bg"], fg=t["text"],
             font=("Segoe UI", 18, "bold")).grid(row=0, column=1, sticky="w", padx=10)

    card = tk.Frame(frame, bg=t["panel"], highlightbackground=t["border"], highlightthickness=1)
    card.grid(row=1, column=0, sticky="ew", padx=18)
    card.grid_columnconfigure(0, weight=1)

    story = (
        "Alex walks into a café.\n"
        "They smile and say: “Hello!”\n"
        "Alex wants to drink something cold."
    )

    tk.Label(card, text="Story", bg=t["panel"], fg=t["muted"], font=("Segoe UI", 10)).grid(
        row=0, column=0, sticky="w", padx=16, pady=(14, 6)
    )
    tk.Label(card, text=story, bg=t["panel"], fg=t["text"], font=("Segoe UI", 12), justify="left").grid(
        row=1, column=0, sticky="w", padx=16, pady=(0, 12)
    )

    tk.Label(card, text="Question: What does Alex want?", bg=t["panel"], fg=t["text"],
             font=("Segoe UI", 12, "bold")).grid(row=2, column=0, sticky="w", padx=16)

    answers = tk.Frame(card, bg=t["panel"])
    answers.grid(row=3, column=0, sticky="ew", padx=16, pady=(10, 14))
    answers.grid_columnconfigure(0, weight=1)

    feedback = tk.Label(frame, text="", bg=t["bg"], fg=t["muted"], font=("Segoe UI", 11, "bold"))
    feedback.grid(row=2, column=0, sticky="w", padx=18, pady=(12, 0))

    def choose(ans):
        if ans == "A cold drink":
            feedback.config(text="✅ Correct!", fg=t["green"])
            app.toast.show("Nice reading!", kind="success", duration=1.2)
            app.complete_lesson(meta, gems=18, xp=18, message="Story completed!")
        else:
            feedback.config(text="❌ Try again.", fg=t["red"])
            app.toast.show("Try again.", kind="warn", duration=1.1)

    for i, opt in enumerate(["A cold drink", "A pizza", "A map"]):
        tk.Button(
            answers, text=opt, command=lambda o=opt: choose(o),
            font=("Segoe UI", 11, "bold"),
            bg=t["panel"], fg=t["text"],
            activebackground=t["nav_hover"], activeforeground=t["text"],
            relief="flat", cursor="hand2",
            highlightbackground=t["border"], highlightthickness=1,
            padx=12, pady=12
        ).grid(row=i, column=0, sticky="ew", pady=6)

    return frame