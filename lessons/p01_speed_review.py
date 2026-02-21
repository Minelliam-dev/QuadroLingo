import tkinter as tk

LESSON_META = {
    "id": "p01_speed_review",
    "title": "Speed review",
    "subtitle": "Quick-fire practice",
    "emoji": "⚡",
    "kind": "practice",
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

    prompt = tk.Label(card, text="", bg=t["panel"], fg=t["muted"], font=("Segoe UI", 10))
    prompt.grid(row=0, column=0, sticky="w", padx=16, pady=(14, 0))

    question = tk.Label(card, text="", bg=t["panel"], fg=t["text"], font=("Segoe UI", 16, "bold"))
    question.grid(row=1, column=0, sticky="w", padx=16, pady=(4, 12))

    answers = tk.Frame(card, bg=t["panel"])
    answers.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 14))
    answers.grid_columnconfigure(0, weight=1)
    answers.grid_columnconfigure(1, weight=1)

    feedback = tk.Label(frame, text="", bg=t["bg"], fg=t["muted"], font=("Segoe UI", 11, "bold"))
    feedback.grid(row=2, column=0, sticky="w", padx=18, pady=(12, 0))

    items = [
        {"prompt": "Tap the greeting:", "q": "___", "a": "Hello!", "b": "Goodbye!"},
        {"prompt": "Tap the polite order:", "q": "___", "a": "I would like…", "b": "No way."},
        {"prompt": "Tap the plan phrase:", "q": "___", "a": "I am going to…", "b": "I was yesterday…"},
        {"prompt": "Tap the payment phrase:", "q": "___", "a": "The bill, please.", "b": "The table, please."},
    ]

    state = {"i": 0, "score": 0}

    def clear_answers():
        for w in answers.winfo_children():
            w.destroy()

    def render():
        feedback.config(text="", fg=t["muted"])
        item = items[state["i"]]
        prompt.config(text=item["prompt"])
        question.config(text=item["q"])
        clear_answers()

        def make_btn(text, correct):
            return tk.Button(
                answers, text=text, command=lambda: choose(correct),
                font=("Segoe UI", 11, "bold"),
                bg=t["panel"], fg=t["text"],
                activebackground=t["nav_hover"], activeforeground=t["text"],
                relief="flat", cursor="hand2",
                highlightbackground=t["border"], highlightthickness=1,
                padx=12, pady=12
            )

        b1 = make_btn(item["a"], True)
        b2 = make_btn(item["b"], False)
        b1.grid(row=0, column=0, sticky="ew", padx=(0, 6), pady=6)
        b2.grid(row=0, column=1, sticky="ew", padx=(6, 0), pady=6)

    def choose(correct):
        if correct:
            state["score"] += 1
            feedback.config(text="✅ Nice!", fg=t["green"])
            app.toast.show("Nice!", kind="success", duration=0.9)
        else:
            feedback.config(text="❌ Oops!", fg=t["red"])
            app.toast.show("Oops!", kind="warn", duration=0.9)

        state["i"] += 1
        if state["i"] >= len(items):
            gems = 10 + 2 * state["score"]
            xp = 10 + 3 * state["score"]
            app.complete_lesson(meta, gems=gems, xp=xp, message=f"Practice done! {state['score']}/{len(items)}")
        else:
            render()

    render()
    return frame