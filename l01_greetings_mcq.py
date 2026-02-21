import tkinter as tk

LESSON_META = {
    "id": "l01_greetings_mcq",
    "title": "Greetings",
    "subtitle": "Choose the best translation",
    "emoji": "👋",
    "kind": "learn",
    "order": 1
}

def build(parent, app, meta):
    t = app.theme()
    frame = tk.Frame(parent, bg=t["bg"])
    frame.grid_columnconfigure(0, weight=1)

    # Header
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

    tk.Label(
        header, text=meta["title"],
        bg=t["bg"], fg=t["text"],
        font=("Segoe UI", 18, "bold")
    ).grid(row=0, column=1, sticky="w", padx=10)

    # Content card
    card = tk.Frame(frame, bg=t["panel"], highlightbackground=t["border"], highlightthickness=1)
    card.grid(row=1, column=0, sticky="ew", padx=18)
    card.grid_columnconfigure(0, weight=1)

    prompt = tk.Label(card, text="", bg=t["panel"], fg=t["muted"], font=("Segoe UI", 10))
    prompt.grid(row=0, column=0, sticky="w", padx=16, pady=(14, 0))

    question = tk.Label(card, text="", bg=t["panel"], fg=t["text"], font=("Segoe UI", 16, "bold"))
    question.grid(row=1, column=0, sticky="w", padx=16, pady=(4, 12))

    choices_frame = tk.Frame(card, bg=t["panel"])
    choices_frame.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 14))
    choices_frame.grid_columnconfigure(0, weight=1)

    feedback = tk.Label(frame, text="", bg=t["bg"], fg=t["muted"], font=("Segoe UI", 11, "bold"))
    feedback.grid(row=2, column=0, sticky="w", padx=18, pady=(12, 0))

    controls = tk.Frame(frame, bg=t["bg"])
    controls.grid(row=3, column=0, sticky="ew", padx=18, pady=16)
    controls.grid_columnconfigure(0, weight=1)
    controls.grid_columnconfigure(1, weight=1)

    next_btn = tk.Button(
        controls, text="Next", state="disabled",
        font=("Segoe UI", 11, "bold"),
        bg=t["green"], fg="white",
        activebackground=t["green_dark"], activeforeground="white",
        relief="flat", cursor="hand2", padx=14, pady=10
    )
    next_btn.grid(row=0, column=1, sticky="ew")

    items = [
        {"q": "Hello!", "prompt": "Pick the best English greeting:", "choices": ["Goodbye!", "Hello!", "Please."], "a": "Hello!"},
        {"q": "Good morning!", "prompt": "Pick the best greeting:", "choices": ["Good morning!", "Good night!", "Thanks!"], "a": "Good morning!"},
        {"q": "How are you?", "prompt": "Pick the best phrase:", "choices": ["How are you?", "Where are you?", "Who are you?"], "a": "How are you?"},
    ]

    state = {"i": 0, "selected": None, "locked": False, "score": 0}

    def clear_choices():
        for wdg in choices_frame.winfo_children():
            wdg.destroy()

    def render():
        state["selected"] = None
        state["locked"] = False
        feedback.config(text="", fg=t["muted"])
        next_btn.config(state="disabled", text="Next")

        item = items[state["i"]]
        prompt.config(text=item["prompt"])
        question.config(text=item["q"])

        clear_choices()
        for idx, text in enumerate(item["choices"]):
            btn = tk.Button(
                choices_frame,
                text=text,
                font=("Segoe UI", 11, "bold"),
                bg=t["panel"], fg=t["text"],
                activebackground=t["nav_hover"], activeforeground=t["text"],
                relief="flat", cursor="hand2",
                highlightbackground=t["border"], highlightthickness=1,
                padx=12, pady=10
            )
            btn.grid(row=idx, column=0, sticky="ew", pady=6)
            btn.configure(command=lambda tx=text, b=btn: choose(tx, b))

    def choose(choice_text, btn_widget):
        if state["locked"]:
            return
        state["selected"] = choice_text
        next_btn.config(state="normal", text="Check")

        # visually mark selection by updating all buttons
        for b in choices_frame.winfo_children():
            b.configure(bg=t["panel"])
        btn_widget.configure(bg=t["nav_hover"])

    def check_or_next():
        if state["locked"]:
            # next question
            state["i"] += 1
            if state["i"] >= len(items):
                # complete
                gems = 20 + state["score"] * 5
                xp = 15 + state["score"] * 5
                app.complete_lesson(meta, gems=gems, xp=xp, message=f"Completed! Score {state['score']}/{len(items)}")
                return
            render()
            return

        if state["selected"] is None:
            return

        item = items[state["i"]]
        state["locked"] = True
        if state["selected"] == item["a"]:
            state["score"] += 1
            feedback.config(text="✅ Correct!", fg=t["green"])
            app.toast.show("Correct!", kind="success", duration=1.3)
        else:
            feedback.config(text=f"❌ Correct answer: {item['a']}", fg=t["red"])
            app.toast.show("Try the next one!", kind="warn", duration=1.3)

        next_btn.config(text="Continue", state="normal")

    next_btn.configure(command=check_or_next)

    render()
    return frame
