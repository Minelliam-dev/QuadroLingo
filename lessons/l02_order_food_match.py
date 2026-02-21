import tkinter as tk
import random

LESSON_META = {
    "id": "l02_order_food_match",
    "title": "Order food",
    "subtitle": "Match phrases",
    "emoji": "🍕",
    "kind": "learn",
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
    card.grid(row=1, column=0, sticky="nsew", padx=18)
    card.grid_columnconfigure(0, weight=1)
    card.grid_columnconfigure(1, weight=1)

    tk.Label(card, text="Tap one on the left, then its match on the right.",
             bg=t["panel"], fg=t["muted"], font=("Segoe UI", 10)
             ).grid(row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(14, 10))

    pairs = [
        ("I would like…", "A polite way to order"),
        ("The bill, please.", "Ask to pay"),
        ("Can I have water?", "Request a drink"),
        ("No onions, please.", "Ask to remove something"),
    ]

    left_items = [p[0] for p in pairs]
    right_items = [p[1] for p in pairs]
    random.shuffle(left_items)
    random.shuffle(right_items)

    left_frame = tk.Frame(card, bg=t["panel"])
    right_frame = tk.Frame(card, bg=t["panel"])
    left_frame.grid(row=1, column=0, sticky="nsew", padx=(16, 8), pady=(0, 14))
    right_frame.grid(row=1, column=1, sticky="nsew", padx=(8, 16), pady=(0, 14))
    left_frame.grid_columnconfigure(0, weight=1)
    right_frame.grid_columnconfigure(0, weight=1)

    feedback = tk.Label(frame, text="", bg=t["bg"], fg=t["muted"], font=("Segoe UI", 11, "bold"))
    feedback.grid(row=2, column=0, sticky="w", padx=18, pady=(12, 0))

    selected = {"side": None, "text": None}
    matched = set()
    score = {"ok": 0}

    def make_btn(parent, text):
        b = tk.Button(
            parent, text=text,
            font=("Segoe UI", 11, "bold"),
            bg=t["panel"], fg=t["text"],
            activebackground=t["nav_hover"], activeforeground=t["text"],
            relief="flat", cursor="hand2",
            highlightbackground=t["border"], highlightthickness=1,
            padx=12, pady=12
        )
        return b

    def reset_styles():
        for b in left_frame.winfo_children():
            b.configure(bg=t["panel"])
        for b in right_frame.winfo_children():
            b.configure(bg=t["panel"])

    def click(side, text, btn):
        if text in matched:
            return

        # pick first
        if selected["text"] is None:
            selected["side"] = side
            selected["text"] = text
            reset_styles()
            btn.configure(bg=t["nav_hover"])
            feedback.config(text="Pick the match.", fg=t["muted"])
            return

        # if clicked same side, switch selection
        if selected["side"] == side:
            selected["text"] = text
            reset_styles()
            btn.configure(bg=t["nav_hover"])
            return

        # check match
        a = selected["text"]
        btext = text
        selected["side"] = None
        selected["text"] = None
        reset_styles()

        # Determine correct pair
        correct = False
        for left, right in pairs:
            if (a == left and btext == right) or (a == right and btext == left):
                correct = True
                # mark both as matched
                matched.add(left)
                matched.add(right)
                score["ok"] += 1
                break

        if correct:
            feedback.config(text="✅ Match!", fg=t["green"])
            app.toast.show("Match!", kind="success", duration=1.1)
            # disable matched buttons
            for btn2 in left_frame.winfo_children():
                if btn2.cget("text") in matched:
                    btn2.configure(state="disabled", bg=t["disabled"], fg=t["muted"])
            for btn2 in right_frame.winfo_children():
                if btn2.cget("text") in matched:
                    btn2.configure(state="disabled", bg=t["disabled"], fg=t["muted"])

            if score["ok"] == len(pairs):
                app.complete_lesson(meta, gems=30, xp=25, message="All matched!")
        else:
            feedback.config(text="❌ Not a match.", fg=t["red"])
            app.toast.show("Not a match.", kind="warn", duration=1.1)

    # build buttons
    for i, text in enumerate(left_items):
        b = make_btn(left_frame, text)
        b.grid(row=i, column=0, sticky="ew", pady=6)
        b.configure(command=lambda tx=text, btn=b: click("L", tx, btn))

    for i, text in enumerate(right_items):
        b = make_btn(right_frame, text)
        b.grid(row=i, column=0, sticky="ew", pady=6)
        b.configure(command=lambda tx=text, btn=b: click("R", tx, btn))

    return frame