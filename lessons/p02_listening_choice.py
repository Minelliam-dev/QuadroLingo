import tkinter as tk

LESSON_META = {
    "id": "p02_listening_choice",
    "title": "Listening drill",
    "subtitle": "Tap what you hear (simulated)",
    "emoji": "🎧",
    "kind": "practice",
    "order": 2
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

    info = tk.Label(card, text="Press ▶ then choose what you “heard”.",
                    bg=t["panel"], fg=t["muted"], font=("Segoe UI", 10))
    info.grid(row=0, column=0, sticky="w", padx=16, pady=(14, 10))

    play_btn = tk.Button(
        card, text="▶ Play", command=lambda: do_play(),
        font=("Segoe UI", 11, "bold"),
        bg=t["blue"], fg="white",
        activebackground=t["blue_dark"], activeforeground="white",
        relief="flat", cursor="hand2", padx=12, pady=10
    )
    play_btn.grid(row=1, column=0, sticky="w", padx=16, pady=(0, 12))

    heard_lbl = tk.Label(card, text="", bg=t["panel"], fg=t["text"], font=("Segoe UI", 15, "bold"))
    heard_lbl.grid(row=2, column=0, sticky="w", padx=16, pady=(0, 12))

    choices = tk.Frame(card, bg=t["panel"])
    choices.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 14))
    choices.grid_columnconfigure(0, weight=1)
    choices.grid_columnconfigure(1, weight=1)

    feedback = tk.Label(frame, text="", bg=t["bg"], fg=t["muted"], font=("Segoe UI", 11, "bold"))
    feedback.grid(row=2, column=0, sticky="w", padx=18, pady=(12, 0))

    items = [
        {"audio": "Hello!", "options": ["Hello!", "Goodbye!"], "a": "Hello!"},
        {"audio": "The bill, please.", "options": ["The bill, please.", "The table, please."], "a": "The bill, please."},
        {"audio": "Can I have water?", "options": ["Can I have water?", "Can I have sugar?"], "a": "Can I have water?"},
    ]

    state = {"i": 0, "score": 0, "played": False}

    def do_play():
        item = items[state["i"]]
        state["played"] = True
        heard_lbl.config(text=f"“{item['audio']}”")
        app.toast.show("Now choose the matching text.", kind="info", duration=1.2)

    def render():
        state["played"] = False
        heard_lbl.config(text="")
        feedback.config(text="", fg=t["muted"])
        for w in choices.winfo_children():
            w.destroy()

        item = items[state["i"]]

        def choose(opt):
            if not state["played"]:
                app.toast.show("Press ▶ first.", kind="warn", duration=1.2)
                return
            if opt == item["a"]:
                state["score"] += 1
                feedback.config(text="✅ Correct!", fg=t["green"])
                app.toast.show("Correct!", kind="success", duration=1.0)
            else:
                feedback.config(text=f"❌ It was: {item['a']}", fg=t["red"])
                app.toast.show("Try the next one.", kind="warn", duration=1.1)

            state["i"] += 1
            if state["i"] >= len(items):
                gems = 14 + 3 * state["score"]
                xp = 12 + 4 * state["score"]
                app.complete_lesson(meta, gems=gems, xp=xp, message=f"Listening done! {state['score']}/{len(items)}")
            else:
                render()

        b1 = tk.Button(
            choices, text=item["options"][0], command=lambda: choose(item["options"][0]),
            font=("Segoe UI", 11, "bold"),
            bg=t["panel"], fg=t["text"],
            activebackground=t["nav_hover"], activeforeground=t["text"],
            relief="flat", cursor="hand2",
            highlightbackground=t["border"], highlightthickness=1,
            padx=12, pady=12
        )
        b2 = tk.Button(
            choices, text=item["options"][1], command=lambda: choose(item["options"][1]),
            font=("Segoe UI", 11, "bold"),
            bg=t["panel"], fg=t["text"],
            activebackground=t["nav_hover"], activeforeground=t["text"],
            relief="flat", cursor="hand2",
            highlightbackground=t["border"], highlightthickness=1,
            padx=12, pady=12
        )
        b1.grid(row=0, column=0, sticky="ew", padx=(0, 6), pady=6)
        b2.grid(row=0, column=1, sticky="ew", padx=(6, 0), pady=6)

    render()
    return frame