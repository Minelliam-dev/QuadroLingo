import tkinter as tk

LESSON_META = {
    "id": "l03_plans_fillblank",
    "title": "Weekend plans",
    "subtitle": "Fill in the missing word",
    "emoji": "🗓️",
    "kind": "learn",
    "order": 3
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

    tk.Label(card, text="Fill in the blank:", bg=t["panel"], fg=t["muted"], font=("Segoe UI", 10)).grid(
        row=0, column=0, sticky="w", padx=16, pady=(14, 0)
    )

    sentence = tk.Label(card, text="", bg=t["panel"], fg=t["text"], font=("Segoe UI", 16, "bold"))
    sentence.grid(row=1, column=0, sticky="w", padx=16, pady=(6, 6))

    entry = tk.Entry(card, font=("Segoe UI", 13))
    entry.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 14), ipady=8)

    feedback = tk.Label(frame, text="", bg=t["bg"], fg=t["muted"], font=("Segoe UI", 11, "bold"))
    feedback.grid(row=2, column=0, sticky="w", padx=18, pady=(12, 0))

    btn = tk.Button(
        frame, text="Check",
        font=("Segoe UI", 11, "bold"),
        bg=t["green"], fg="white",
        activebackground=t["green_dark"], activeforeground="white",
        relief="flat", cursor="hand2", padx=14, pady=10
    )
    btn.grid(row=3, column=0, sticky="ew", padx=18, pady=16)

    items = [
        ("I ___ going to the park.", "am"),
        ("We ___ pizza tonight.", "are"),
        ("She ___ to watch a movie.", "wants"),
    ]
    state = {"i": 0, "score": 0}

    def render():
        feedback.config(text="", fg=t["muted"])
        entry.delete(0, tk.END)
        a, _ = items[state["i"]]
        sentence.config(text=a)

    def check():
        correct = items[state["i"]][1].strip().lower()
        ans = entry.get().strip().lower()
        if ans == correct:
            state["score"] += 1
            feedback.config(text="✅ Correct!", fg=t["green"])
            app.toast.show("Correct!", kind="success", duration=1.0)
        else:
            feedback.config(text=f"❌ Correct answer: {correct}", fg=t["red"])
            app.toast.show("Close — keep going!", kind="warn", duration=1.2)

        state["i"] += 1
        if state["i"] >= len(items):
            gems = 18 + 4 * state["score"]
            xp = 15 + 5 * state["score"]
            app.complete_lesson(meta, gems=gems, xp=xp, message=f"Finished! {state['score']}/{len(items)} correct")
        else:
            render()

    btn.configure(command=check)
    render()
    return frame