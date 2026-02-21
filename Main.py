import os
import json
import time
import tkinter as tk
from tkinter import ttk
import importlib.util


# ---------------- Persistence ----------------
DATA_FILE = "user_data.json"

PROJECT_NAME = "QuadroLingo"

DEFAULT_DATA = {
    "gems": 0,
    "xp": 0,
    "owned_items": [],
    "completed_lessons": {},
    "settings": {
        "theme": "light",  # "light" or "dark"
    }
}

def load_data():
    if not os.path.exists(DATA_FILE):
        return json.loads(json.dumps(DEFAULT_DATA))
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            d = json.load(f) or {}
        merged = json.loads(json.dumps(DEFAULT_DATA))
        # shallow merge
        for k, v in d.items():
            merged[k] = v
        merged.setdefault("settings", {})
        merged["settings"].setdefault("theme", "light")
        merged.setdefault("owned_items", [])
        merged.setdefault("completed_lessons", {})
        return merged
    except Exception:
        return json.loads(json.dumps(DEFAULT_DATA))

def save_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("[save error]", e)


# ---------------- Plugin Loading ----------------
def load_lessons(lessons_dir="lessons"):
    lessons = []
    base = os.path.abspath(lessons_dir)
    if not os.path.isdir(base):
        return lessons

    for filename in sorted(os.listdir(base)):
        if not filename.endswith(".py") or filename.startswith("_"):
            continue

        path = os.path.join(base, filename)
        mod_name = f"lessonmod_{os.path.splitext(filename)[0]}"

        spec = importlib.util.spec_from_file_location(mod_name, path)
        if spec is None or spec.loader is None:
            continue
        module = importlib.util.module_from_spec(spec)

        try:
            spec.loader.exec_module(module)
        except Exception as e:
            print(f"[Lesson load error] {filename}: {e}")
            continue

        meta = getattr(module, "LESSON_META", None)
        build = getattr(module, "build", None)
        if not isinstance(meta, dict) or not callable(build):
            print(f"[Lesson skipped] {filename}: needs LESSON_META dict + build()")
            continue

        meta = dict(meta)
        meta.setdefault("id", os.path.splitext(filename)[0])
        meta.setdefault("title", "Untitled Lesson")
        meta.setdefault("subtitle", "")
        meta.setdefault("emoji", "📘")
        meta.setdefault("kind", "learn")
        meta.setdefault("order", 999)

        lessons.append({"meta": meta, "build": build, "path": path})

    lessons.sort(key=lambda x: (x["meta"]["kind"], x["meta"].get("order", 999), x["meta"]["title"]))
    return lessons


# ---------------- UI Helpers ----------------
def round_rect(canvas, x1, y1, x2, y2, r=16, **kwargs):
    points = [
        x1+r, y1, x2-r, y1, x2, y1, x2, y1+r,
        x2, y2-r, x2, y2, x2-r, y2, x1+r, y2,
        x1, y2, x1, y2-r, x1, y1+r, x1, y1
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)

def ease_out_quad(t: float) -> float:
    return 1 - (1 - t) * (1 - t)

def clamp01(x):
    return 0 if x < 0 else 1 if x > 1 else x


# ---------------- Animated integer ----------------
class AnimatedInt:
    def __init__(self, initial=0):
        self.value = int(initial)
        self._start = int(initial)
        self._target = int(initial)
        self._t0 = 0.0
        self._dur = 0.0
        self.running = False

    def animate_to(self, target, duration=0.45):
        self._start = self.value
        self._target = int(target)
        self._t0 = time.time()
        self._dur = max(0.01, float(duration))
        self.running = True

    def tick(self):
        if not self.running:
            return self.value
        t = (time.time() - self._t0) / self._dur
        if t >= 1:
            self.value = self._target
            self.running = False
            return self.value
        e = ease_out_quad(clamp01(t))
        self.value = int(round(self._start + (self._target - self._start) * e))
        return self.value


# ---------------- Toast bar (single-window notifications) ----------------
class ToastBar(tk.Frame):
    def __init__(self, parent, get_theme):
        super().__init__(parent)
        self.get_theme = get_theme
        self._visible = False
        self._target_y = 0
        self._y = -60

        self.canvas = tk.Canvas(self, height=52, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.msg = ""
        self.kind = "info"  # info/success/warn/error
        self.after_id = None

        self.bind("<Configure>", lambda e: self.redraw())

    def show(self, msg, kind="info", duration=2.2):
        self.msg = msg
        self.kind = kind
        self._visible = True
        self.redraw()
        self._animate_to(0)

        if self.after_id:
            self.after_cancel(self.after_id)
        self.after_id = self.after(int(duration * 1000), self.hide)

    def hide(self):
        if not self._visible:
            return
        self._visible = False
        self._animate_to(-60)

    def redraw(self):
        t = self.get_theme()
        self.configure(bg=t["bg"])
        self.canvas.configure(bg=t["bg"])
        self.canvas.delete("all")

        w = max(300, self.winfo_width())
        h = 52

        accent = t["blue"]
        if self.kind == "success":
            accent = t["green"]
        elif self.kind == "warn":
            accent = t["orange"]
        elif self.kind == "error":
            accent = t["red"]

        # shadow + pill
        round_rect(self.canvas, 10, 8, w-10, h-6, r=16, fill=t["shadow"], outline="")
        round_rect(self.canvas, 10, 4, w-10, h-10, r=16, fill=t["panel"], outline=t["border"], width=1)
        self.canvas.create_oval(20, 16, 36, 32, fill=accent, outline="")
        self.canvas.create_text(44, 24, text=self.msg, anchor="w",
                                font=("Segoe UI", 11, "bold"), fill=t["text"])

    def _animate_to(self, target_y):
        # Smooth slide using ease-out
        start_y = self._y
        end_y = target_y
        t0 = time.time()
        dur = 0.22

        def step():
            nonlocal start_y, end_y, t0, dur
            t = (time.time() - t0) / dur
            if t >= 1:
                self._y = end_y
                self.place_configure(y=int(self._y))
                return
            e = ease_out_quad(clamp01(t))
            self._y = start_y + (end_y - start_y) * e
            self.place_configure(y=int(self._y))
            self.after(16, step)

        step()


# ---------------- Sidebar button (no flicker) ----------------
class SidebarButton(tk.Canvas):
    def __init__(self, parent, get_theme, text, icon, command):
        super().__init__(parent, height=46, highlightthickness=0)
        self.get_theme = get_theme
        self.text = text
        self.icon = icon
        self.command = command
        self.selected = False
        self.hover = False

        self.bind("<Configure>", lambda e: self.redraw())
        self.bind("<Enter>", lambda e: self._set_hover(True))
        self.bind("<Leave>", lambda e: self._set_hover(False))
        self.bind("<Button-1>", lambda e: self.command())

    def _set_hover(self, v):
        self.hover = v
        self.redraw()

    def set_selected(self, v):
        self.selected = v
        self.redraw()

    def redraw(self):
        t = self.get_theme()
        self.configure(bg=t["panel"])
        self.delete("all")

        w = max(200, self.winfo_width())
        h = 46

        if self.selected:
            bg = t["nav_selected"]
            outline = t["border"]
            fw = "bold"
        else:
            bg = t["panel"] if not self.hover else t["nav_hover"]
            outline = t["panel"]
            fw = "normal"

        round_rect(self, 6, 4, w-6, h-4, r=14, fill=bg, outline=outline, width=1)
        self.create_text(24, h//2, text=self.icon, font=("Segoe UI Emoji", 13), anchor="w", fill=t["text"])
        self.create_text(56, h//2, text=self.text, font=("Segoe UI", 11, fw),
                         anchor="w", fill=t["text"])


# ---------------- Animated “lift” card base ----------------
class LiftCard(tk.Canvas):
    def __init__(self, parent, get_theme, height=98):
        super().__init__(parent, height=height, highlightthickness=0)
        self.get_theme = get_theme
        self.lift = 0.0  # 0..1
        self.hover = False
        self._animating = False

        self.bind("<Enter>", lambda e: self.set_hover(True))
        self.bind("<Leave>", lambda e: self.set_hover(False))
        self.bind("<Configure>", lambda e: self.redraw())

    def set_hover(self, v):
        if self.hover == v:
            return
        self.hover = v
        self._animate_lift(1.0 if v else 0.0)

    def _animate_lift(self, target):
        if self._animating:
            # let current animation continue; new target will be followed on next tick
            pass
        self._animating = True
        start = self.lift
        end = target
        t0 = time.time()
        dur = 0.12

        def step():
            nonlocal start, end, t0, dur
            t = (time.time() - t0) / dur
            if t >= 1:
                self.lift = end
                self._animating = False
                self.redraw()
                return
            e = ease_out_quad(clamp01(t))
            self.lift = start + (end - start) * e
            self.redraw()
            self.after(16, step)

        step()

    def redraw(self):
        # subclass should draw
        pass


class LessonCard(LiftCard):
    def __init__(self, parent, app, entry, get_theme):
        super().__init__(parent, get_theme, height=98)
        self.app = app
        self.entry = entry
        self.bind("<Button-1>", lambda e: self.app.open_lesson(self.entry))

    def redraw(self):
        t = self.get_theme()
        self.configure(bg=t["bg"])
        self.delete("all")

        w = max(320, self.winfo_width())
        h = 98

        # lift effect
        y = int(2 - 2 * self.lift)
        shadow_y = int(6 + 2 * self.lift)

        # shadow + card
        round_rect(self, 8, 8+shadow_y+y, w-8, h-8+shadow_y+y, r=18, fill=t["shadow"], outline="")
        round_rect(self, 8, 8+y, w-8, h-8+y, r=18, fill=t["panel"], outline=t["border"], width=1)

        meta = self.entry["meta"]
        self.create_oval(22, 28+y, 64, 70+y, fill=t["bubble"], outline="")
        self.create_text(43, 49+y, text=meta.get("emoji", "📘"), font=("Segoe UI Emoji", 16), fill=t["text"])

        kind = meta.get("kind", "learn").capitalize()
        self.create_text(80, 32+y, text=kind, anchor="w", font=("Segoe UI", 9), fill=t["muted"])
        self.create_text(80, 56+y, text=meta.get("title", "Untitled"), anchor="w",
                         font=("Segoe UI", 12, "bold"), fill=t["text"])
        sub = meta.get("subtitle", "")
        if sub:
            self.create_text(80, 76+y, text=sub, anchor="w", font=("Segoe UI", 9), fill=t["muted"])

        # start button (drawn, not a real Button => no flicker)
        bx2 = w - 18
        bx1 = bx2 - 88
        by1 = 34 + y
        by2 = 66 + y
        btn_fill = t["green"] if self.hover else t["green_dark"]
        round_rect(self, bx1, by1, bx2, by2, r=14, fill=btn_fill, outline="")
        self.create_text((bx1+bx2)//2, (by1+by2)//2, text="Start",
                         font=("Segoe UI", 10, "bold"), fill="white")


class ShopItemCard(LiftCard):
    def __init__(self, parent, app, item, get_theme):
        super().__init__(parent, get_theme, height=114)
        self.app = app
        self.item = item
        self.bind("<Button-1>", lambda e: self.app.try_buy_item(self.item["id"]))

    def redraw(self):
        t = self.get_theme()
        self.configure(bg=t["bg"])
        self.delete("all")

        w = max(320, self.winfo_width())
        h = 114

        y = int(2 - 2 * self.lift)
        shadow_y = int(6 + 2 * self.lift)

        round_rect(self, 8, 8+shadow_y+y, w-8, h-8+shadow_y+y, r=18, fill=t["shadow"], outline="")
        round_rect(self, 8, 8+y, w-8, h-8+y, r=18, fill=t["panel"], outline=t["border"], width=1)

        owned = self.app.has_item(self.item["id"])

        self.create_oval(22, 32+y, 64, 74+y, fill=t["bubble"], outline="")
        self.create_text(43, 53+y, text=self.item["emoji"], font=("Segoe UI Emoji", 16), fill=t["text"])

        self.create_text(80, 36+y, text=self.item["name"], anchor="w",
                         font=("Segoe UI", 12, "bold"), fill=t["text"])
        self.create_text(80, 60+y, text=self.item["desc"], anchor="w",
                         font=("Segoe UI", 9), fill=t["muted"])

        price_text = "Owned" if owned else f"{self.item['price']} 💎"
        price_color = t["green"] if owned else t["text"]
        self.create_text(w-180, 55+y, text=price_text, anchor="w",
                         font=("Segoe UI", 11, "bold"), fill=price_color)

        bx2 = w - 18
        bx1 = bx2 - 88
        by1 = 38 + y
        by2 = 72 + y

        if owned:
            round_rect(self, bx1, by1, bx2, by2, r=14, fill=t["disabled"], outline="")
            self.create_text((bx1+bx2)//2, (by1+by2)//2, text="Owned",
                             font=("Segoe UI", 10, "bold"), fill=t["muted"])
        else:
            btn_fill = t["blue"] if self.hover else t["blue_dark"]
            round_rect(self, bx1, by1, bx2, by2, r=14, fill=btn_fill, outline="")
            self.create_text((bx1+bx2)//2, (by1+by2)//2, text="Buy",
                             font=("Segoe UI", 10, "bold"), fill="white")


# ---------------- Main App ----------------
class DuoPluginApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(PROJECT_NAME)
        self.geometry("1100x720")
        self.minsize(980, 620)

        # Data & state
        self.data = load_data()
        self.lessons = load_lessons("lessons")
        self.active_page = "learn"
        self.current_view = None  # placed frame

        # Economy
        self.shop_items = [
            {"id": "streak_freeze", "name": "Streak Freeze", "desc": "Miss a day without losing streak.", "price": 80, "emoji": "🧊"},
            {"id": "heart_refill", "name": "Heart Refill", "desc": "More tries in tough lessons.", "price": 50, "emoji": "❤️"},
            {"id": "double_xp", "name": "Double XP (1h)", "desc": "Earn 2× XP for one hour.", "price": 120, "emoji": "⚡"},
            {"id": "sticker_pack", "name": "Sticker Pack", "desc": "Cosmetic reward. Pure vibes.", "price": 60, "emoji": "🎨"},
            {"id": "owl_hat", "name": "Owl Hat", "desc": "A silly cosmetic. Big flex.", "price": 200, "emoji": "🎩"},
        ]

        # Animated header counters
        self.gem_anim = AnimatedInt(self.data["gems"])
        self.xp_anim = AnimatedInt(self.data["xp"])

        # Themes
        self.THEMES = {
            "light": {
                "bg": "#F6F7FB",
                "panel": "#FFFFFF",
                "text": "#1F2A37",
                "muted": "#6B7280",
                "border": "#E5E7EB",
                "shadow": "#000000",
                "bubble": "#EEF2F7",
                "nav_hover": "#F3F4F6",
                "nav_selected": "#EAF8D8",
                "green": "#58CC02",
                "green_dark": "#46A302",
                "blue": "#1CB0F6",
                "blue_dark": "#0F96D5",
                "orange": "#FF9600",
                "red": "#FF4B4B",
                "disabled": "#E5E7EB",
            },
            "dark": {
                "bg": "#0B1220",
                "panel": "#111A2E",
                "text": "#E5E7EB",
                "muted": "#9CA3AF",
                "border": "#23304A",
                "shadow": "#000000",
                "bubble": "#0F1A33",
                "nav_hover": "#182444",
                "nav_selected": "#14331B",  # dark green tint
                "green": "#58CC02",
                "green_dark": "#46A302",
                "blue": "#1CB0F6",
                "blue_dark": "#0F96D5",
                "orange": "#FF9600",
                "red": "#FF4B4B",
                "disabled": "#23304A",
            }
        }

        self.configure(bg=self.theme()["bg"])

        self._build_layout()
        self._build_pages()
        self.show_page("learn", animate=False)

        # Toast (top)
        self.toast = ToastBar(self, self.theme)
        self.toast.place(x=0, y=-60, relwidth=1)

        # Periodic ticks
        self._ui_tick()

    def theme(self):
        name = self.data.get("settings", {}).get("theme", "light")
        return self.THEMES.get(name, self.THEMES["light"])

    # ---------- Layout ----------
    def _build_layout(self):
        t = self.theme()
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = tk.Frame(self, bg=t["panel"], highlightbackground=t["border"], highlightthickness=1)
        self.sidebar.grid(row=0, column=0, sticky="nsw")
        self.sidebar.grid_columnconfigure(0, weight=1)
        self.sidebar.grid_rowconfigure(98, weight=1)

        # Content
        self.content = tk.Frame(self, bg=t["bg"])
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        # Container for slide transitions
        self.view_container = tk.Frame(self.content, bg=t["bg"])
        self.view_container.grid(row=0, column=0, sticky="nsew")
        self.view_container.grid_columnconfigure(0, weight=1)
        self.view_container.grid_rowconfigure(0, weight=1)

        self._build_sidebar()

    def _build_sidebar(self):
        t = self.theme()
        top = tk.Frame(self.sidebar, bg=t["panel"])
        top.grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 10))
        top.grid_columnconfigure(1, weight=1)

        logo = tk.Canvas(top, width=34, height=34, bg=t["panel"], highlightthickness=0)
        logo.grid(row=0, column=0, padx=(0, 10))
        round_rect(logo, 2, 2, 32, 32, r=10, fill=t["green"], outline="")
        logo.create_text(17, 17, text="🦉", font=("Segoe UI Emoji", 14), fill="white")

        tk.Label(top, text=PROJECT_NAME, bg=t["panel"], fg=t["text"],
                 font=("Segoe UI", 14, "bold")).grid(row=0, column=1, sticky="w")

        nav = tk.Frame(self.sidebar, bg=t["panel"])
        nav.grid(row=1, column=0, sticky="new", padx=12)
        nav.grid_columnconfigure(0, weight=1)

        self.nav = {}
        self.nav["learn"] = SidebarButton(nav, self.theme, "Learn", "📚", lambda: self.show_page("learn"))
        self.nav["practice"] = SidebarButton(nav, self.theme, "Practice", "🎯", lambda: self.show_page("practice"))
        self.nav["stories"] = SidebarButton(nav, self.theme, "Stories", "📖", lambda: self.show_page("stories"))
        self.nav["leaderboard"] = SidebarButton(nav, self.theme, "Leaderboard", "🏆", lambda: self.show_page("leaderboard"))
        self.nav["shop"] = SidebarButton(nav, self.theme, "Shop", "🛍️", lambda: self.show_page("shop"))
        self.nav["settings"] = SidebarButton(nav, self.theme, "Settings", "⚙️", lambda: self.show_page("settings"))

        order = ["learn", "practice", "stories", "leaderboard", "shop", "settings"]
        for i, key in enumerate(order):
            self.nav[key].grid(row=i, column=0, sticky="ew", pady=6)

        # bottom profile
        bottom = tk.Frame(self.sidebar, bg=t["panel"])
        bottom.grid(row=99, column=0, sticky="sew", padx=12, pady=12)
        bottom.grid_columnconfigure(1, weight=1)

        avatar = tk.Canvas(bottom, width=40, height=40, bg=t["panel"], highlightthickness=0)
        avatar.grid(row=0, column=0, padx=(0, 10))
        round_rect(avatar, 2, 2, 38, 38, r=12, fill="#111827", outline="")
        avatar.create_text(20, 20, text="🙂", font=("Segoe UI Emoji", 14), fill="white")

        tk.Label(bottom, text="Guest", bg=t["panel"], fg=t["text"],
                 font=("Segoe UI", 11, "bold")).grid(row=0, column=1, sticky="w")
        self.profile_sub = tk.Label(bottom, text="Local profile", bg=t["panel"], fg=t["muted"],
                                    font=("Segoe UI", 9))
        self.profile_sub.grid(row=1, column=1, sticky="w")

        self._set_nav_selected("learn")

    def _set_nav_selected(self, page):
        for key, btn in self.nav.items():
            btn.set_selected(key == page)

    # ---------- Pages ----------
    def _build_pages(self):
        # Keep a dict of pages; rebuild when theme changes or plugins reload
        self.pages = {}
        self.pages["learn"] = self._build_list_page(kind="learn", title="Learn", subtitle="Install more lessons in ./lessons")
        self.pages["practice"] = self._build_list_page(kind="practice", title="Practice", subtitle="Drills & review (plugins too)")
        self.pages["stories"] = self._build_list_page(kind="stories", title="Stories", subtitle="Reading & mini-stories (plugins too)")
        self.pages["leaderboard"] = self._build_leaderboard_page()
        self.pages["shop"] = self._build_shop_page()
        self.pages["settings"] = self._build_settings_page()

    def _header(self, parent, title, subtitle):
        t = self.theme()

        header = tk.Frame(parent, bg=t["bg"])
        header.grid(row=0, column=0, sticky="ew", padx=18, pady=(16, 10))
        header.grid_columnconfigure(0, weight=1)

        left = tk.Frame(header, bg=t["bg"])
        left.grid(row=0, column=0, sticky="w")
        tk.Label(left, text=subtitle, bg=t["bg"], fg=t["muted"], font=("Segoe UI", 10)).grid(row=0, column=0, sticky="w")
        tk.Label(left, text=title, bg=t["bg"], fg=t["text"], font=("Segoe UI", 18, "bold")).grid(row=1, column=0, sticky="w")

        # Right: gem + xp
        right = tk.Frame(header, bg=t["bg"])
        right.grid(row=0, column=1, sticky="e")

        self.header_gems = self._stat_pill(right, "💎", str(self.data["gems"]), "gems", t["blue"])
        self.header_xp = self._stat_pill(right, "⭐", str(self.data["xp"]), "XP", t["orange"])
        self.header_gems.grid(row=0, column=0, padx=6)
        self.header_xp.grid(row=0, column=1, padx=6)

    def _stat_pill(self, parent, icon, big, small, accent):
        t = self.theme()
        c = tk.Canvas(parent, width=170, height=48, bg=t["bg"], highlightthickness=0)
        round_rect(c, 0, 4, 170, 44, r=20, fill=t["panel"], outline=t["border"], width=1)
        c.create_text(22, 24, text=icon, font=("Segoe UI Emoji", 14), fill=t["text"])
        big_id = c.create_text(62, 20, text=big, font=("Segoe UI", 13, "bold"),
                               fill=t["text"], anchor="w")
        c.create_text(62, 33, text=small, font=("Segoe UI", 9), fill=t["muted"], anchor="w")
        c.create_oval(150, 18, 160, 28, fill=accent, outline="")
        c._big_id = big_id
        return c

    def _build_list_page(self, kind, title, subtitle):
        t = self.theme()
        page = tk.Frame(self.view_container, bg=t["bg"])
        page.grid_rowconfigure(1, weight=1)
        page.grid_columnconfigure(0, weight=1)

        self._header(page, title, subtitle)

        body = tk.Frame(page, bg=t["bg"])
        body.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 16))
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(1, weight=1)

        top = tk.Frame(body, bg=t["bg"])
        top.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        top.grid_columnconfigure(0, weight=1)

        tk.Label(top, text=f"{kind.capitalize()} content", bg=t["bg"], fg=t["text"],
                 font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="w")

        reload_btn = tk.Button(
            top, text="Reload plugins",
            command=self.reload_lessons,
            font=("Segoe UI", 10, "bold"),
            bg=t["panel"], fg=t["text"],
            activebackground=t["nav_hover"], activeforeground=t["text"],
            relief="flat", cursor="hand2",
            highlightbackground=t["border"], highlightthickness=1,
            padx=12, pady=8
        )
        reload_btn.grid(row=0, column=1, sticky="e")

        # Scroll
        canvas = tk.Canvas(body, bg=t["bg"], highlightthickness=0)
        canvas.grid(row=1, column=0, sticky="nsew")

        sb = ttk.Scrollbar(body, orient="vertical", command=canvas.yview)
        sb.grid(row=1, column=1, sticky="ns")
        canvas.configure(yscrollcommand=sb.set)

        inner = tk.Frame(canvas, bg=t["bg"])
        win = canvas.create_window((0, 0), window=inner, anchor="nw")

        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win, width=e.width))

        entries = [l for l in self.lessons if l["meta"].get("kind", "learn") == kind]
        if not entries:
            tk.Label(inner,
                     text=f"No '{kind}' plugins found.\nAdd .py files to ./lessons with kind='{kind}'.",
                     bg=t["bg"], fg=t["muted"], font=("Segoe UI", 11)
                     ).pack(anchor="w", pady=10)
        else:
            for i, entry in enumerate(entries):
                card = LessonCard(inner, self, entry, self.theme)
                card.grid(row=i, column=0, sticky="ew", pady=8)
                inner.grid_columnconfigure(0, weight=1)

        return page

    def _build_leaderboard_page(self):
        t = self.theme()
        page = tk.Frame(self.view_container, bg=t["bg"])
        page.grid_rowconfigure(1, weight=1)
        page.grid_columnconfigure(0, weight=1)

        self._header(page, "Leaderboard", "Weekly XP (local mock)")

        body = tk.Frame(page, bg=t["bg"])
        body.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 16))
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(0, weight=1)

        card = tk.Canvas(body, bg=t["bg"], highlightthickness=0)
        card.grid(row=0, column=0, sticky="nsew")
        round_rect(card, 0, 0, 9999, 9999, r=18, fill=t["panel"], outline=t["border"], width=1)

        your_xp = int(self.data["xp"])
        rows = [
            ("1", "Nova", max(1200, your_xp + 420)),
            ("2", "Rin", max(980, your_xp + 210)),
            ("3", "You", your_xp),
            ("4", "Kai", max(420, your_xp - 180)),
            ("5", "Mila", max(250, your_xp - 320)),
        ]

        card.create_text(24, 28, text="This week", anchor="w", font=("Segoe UI", 16, "bold"), fill=t["text"])
        y = 78
        for rank, name, xp in rows:
            color = t["text"] if name != "You" else t["green"]
            card.create_text(34, y, text=rank, anchor="w", font=("Segoe UI", 12, "bold"), fill=t["muted"])
            card.create_text(70, y, text=name, anchor="w", font=("Segoe UI", 12, "bold"), fill=color)
            card.create_text(300, y, text=f"{xp} XP", anchor="w", font=("Segoe UI", 11), fill=t["muted"])
            y += 46

        return page

    def _build_shop_page(self):
        t = self.theme()
        page = tk.Frame(self.view_container, bg=t["bg"])
        page.grid_rowconfigure(1, weight=1)
        page.grid_columnconfigure(0, weight=1)

        self._header(page, "Shop", "Earn gems by completing lessons")

        body = tk.Frame(page, bg=t["bg"])
        body.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 16))
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(2, weight=1)

        # Balance strip
        strip = tk.Frame(body, bg=t["panel"], highlightbackground=t["border"], highlightthickness=1)
        strip.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        strip.grid_columnconfigure(1, weight=1)

        tk.Label(strip, text="💎 Balance", bg=t["panel"], fg=t["muted"], font=("Segoe UI", 10)).grid(
            row=0, column=0, padx=12, pady=10, sticky="w"
        )
        self.shop_balance_lbl = tk.Label(strip, text=str(self.data["gems"]), bg=t["panel"], fg=t["text"],
                                         font=("Segoe UI", 14, "bold"))
        self.shop_balance_lbl.grid(row=0, column=1, padx=12, pady=10, sticky="w")

        # Inventory
        inv = tk.Frame(body, bg=t["bg"])
        inv.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        inv.grid_columnconfigure(0, weight=1)

        tk.Label(inv, text="Inventory", bg=t["bg"], fg=t["text"],
                 font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="w")
        self.inventory_lbl = tk.Label(inv, text=self._inventory_text(), bg=t["bg"], fg=t["muted"],
                                      font=("Segoe UI", 10))
        self.inventory_lbl.grid(row=1, column=0, sticky="w", pady=(4, 0))

        # Items scroll
        canvas = tk.Canvas(body, bg=t["bg"], highlightthickness=0)
        canvas.grid(row=2, column=0, sticky="nsew")

        sb = ttk.Scrollbar(body, orient="vertical", command=canvas.yview)
        sb.grid(row=2, column=1, sticky="ns")
        canvas.configure(yscrollcommand=sb.set)

        inner = tk.Frame(canvas, bg=t["bg"])
        win = canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win, width=e.width))

        for i, item in enumerate(self.shop_items):
            card = ShopItemCard(inner, self, item, self.theme)
            card.grid(row=i, column=0, sticky="ew", pady=8)
            inner.grid_columnconfigure(0, weight=1)

        return page

    def _build_settings_page(self):
        t = self.theme()
        page = tk.Frame(self.view_container, bg=t["bg"])
        page.grid_rowconfigure(1, weight=1)
        page.grid_columnconfigure(0, weight=1)

        self._header(page, "Settings", "Customize the look & feel")

        body = tk.Frame(page, bg=t["bg"])
        body.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 16))
        body.grid_columnconfigure(0, weight=1)

        card = tk.Canvas(body, bg=t["bg"], highlightthickness=0, height=220)
        card.grid(row=0, column=0, sticky="ew")
        round_rect(card, 0, 0, 9999, 220, r=18, fill=t["panel"], outline=t["border"], width=1)

        card.create_text(24, 30, text="Appearance", anchor="w",
                         font=("Segoe UI", 14, "bold"), fill=t["text"])
        card.create_text(24, 64, text="Theme", anchor="w",
                         font=("Segoe UI", 11), fill=t["muted"])

        # A simple toggle button (no ttk theme complexity)
        toggle = tk.Button(
            body,
            text="Switch to Dark" if self.data["settings"]["theme"] == "light" else "Switch to Light",
            command=self.toggle_theme,
            font=("Segoe UI", 11, "bold"),
            bg=t["panel"], fg=t["text"],
            activebackground=t["nav_hover"], activeforeground=t["text"],
            relief="flat", cursor="hand2",
            highlightbackground=t["border"], highlightthickness=1,
            padx=14, pady=10
        )
        toggle.grid(row=1, column=0, sticky="w", pady=(12, 0))
        self.settings_toggle_btn = toggle

        hint = tk.Label(body, text="Theme is saved to user_data.json",
                        bg=t["bg"], fg=t["muted"], font=("Segoe UI", 10))
        hint.grid(row=2, column=0, sticky="w", pady=(10, 0))

        return page

    # ---------- Navigation / Smooth transitions ----------
    def show_page(self, page, animate=True):
        if page not in self.pages:
            return
        self.active_page = page
        self._set_nav_selected(page)
        self._transition_to(self.pages[page], animate=animate)

    def open_lesson(self, entry):
        # Build lesson frame
        try:
            frame = entry["build"](self.view_container, self, entry["meta"])
        except Exception as e:
            self.toast.show(f"Lesson error: {e}", kind="error", duration=3.2)
            return
        self._transition_to(frame, animate=True)

    def go_back(self):
        self.show_page(self.active_page, animate=True)

    def _transition_to(self, new_view, animate=True):
        # Place-based slide transition, eased
        self.view_container.update_idletasks()
        w = max(1, self.view_container.winfo_width())

        old = self.current_view
        if old is not None:
            try:
                old.place(in_=self.view_container, x=0, y=0, relwidth=1, relheight=1)
            except Exception:
                pass

        new_view.place(in_=self.view_container, x=w, y=0, relwidth=1, relheight=1)
        self.current_view = new_view

        if not animate:
            if old is not None:
                old.place_forget()
            new_view.place_configure(x=0)
            return

        t0 = time.time()
        dur = 0.24

        def step():
            nonlocal t0, dur, w, old, new_view
            t = (time.time() - t0) / dur
            if t >= 1:
                if old is not None:
                    old.place_forget()
                new_view.place_configure(x=0)
                return
            e = ease_out_quad(clamp01(t))
            x_new = int(w * (1 - e))
            x_old = int(-w * e)
            new_view.place_configure(x=x_new)
            if old is not None:
                try:
                    old.place_configure(x=x_old)
                except Exception:
                    pass
            self.after(16, step)

        step()

    # ---------- Economy (no popups) ----------
    def complete_lesson(self, lesson_meta, gems=15, xp=10, message="Lesson completed!"):
        lid = lesson_meta.get("id", "unknown")
        now = int(time.time())

        comp = self.data["completed_lessons"].get(lid, {"times": 0, "last_completed": 0})
        comp["times"] = int(comp.get("times", 0)) + 1
        comp["last_completed"] = now
        self.data["completed_lessons"][lid] = comp

        self.data["gems"] = int(self.data["gems"]) + int(gems)
        self.data["xp"] = int(self.data["xp"]) + int(xp)
        save_data(self.data)

        self.gem_anim.animate_to(self.data["gems"], duration=0.55)
        self.xp_anim.animate_to(self.data["xp"], duration=0.55)

        self.toast.show(f"{message}  +{gems}💎  +{xp}⭐", kind="success", duration=2.6)

        # Return to page
        self.go_back()

    def has_item(self, item_id):
        return item_id in set(self.data.get("owned_items", []))

    def try_buy_item(self, item_id):
        item = next((x for x in self.shop_items if x["id"] == item_id), None)
        if item is None:
            self.toast.show("Item not found.", kind="error", duration=2.2)
            return

        if self.has_item(item_id):
            self.toast.show("Already owned.", kind="info", duration=1.8)
            return

        price = int(item["price"])
        if int(self.data["gems"]) < price:
            self.toast.show(f"Not enough gems. Need {price}💎.", kind="warn", duration=2.4)
            return

        # Buy
        self.data["gems"] -= price
        self.data["owned_items"].append(item_id)
        save_data(self.data)

        self.gem_anim.animate_to(self.data["gems"], duration=0.35)
        self.toast.show(f"Purchased {item['name']} {item['emoji']}", kind="success", duration=2.2)
        self._refresh_shop_ui()

    def _inventory_text(self):
        if not self.data.get("owned_items"):
            return "Empty — buy something fun!"
        names = []
        for oid in self.data["owned_items"]:
            it = next((x for x in self.shop_items if x["id"] == oid), None)
            names.append(it["name"] if it else oid)
        return "• " + "\n• ".join(names)

    def _refresh_shop_ui(self):
        if hasattr(self, "inventory_lbl"):
            self.inventory_lbl.configure(text=self._inventory_text())
        if hasattr(self, "shop_balance_lbl"):
            self.shop_balance_lbl.configure(text=str(self.data["gems"]))

    # ---------- Settings ----------
    def toggle_theme(self):
        cur = self.data["settings"]["theme"]
        self.data["settings"]["theme"] = "dark" if cur == "light" else "light"
        save_data(self.data)

        # rebuild UI with new theme
        self.apply_theme_rebuild()

        self.toast.show(f"Theme set to {self.data['settings']['theme']}.", kind="info", duration=1.8)

    def apply_theme_rebuild(self):
        # Update root bg
        t = self.theme()
        self.configure(bg=t["bg"])
        self.content.configure(bg=t["bg"])
        self.view_container.configure(bg=t["bg"])
        self.sidebar.configure(bg=t["panel"], highlightbackground=t["border"])

        # Destroy and rebuild pages (simplest reliable approach)
        if hasattr(self, "pages"):
            for p in self.pages.values():
                try:
                    p.destroy()
                except Exception:
                    pass
        self._build_pages()

        # Update sidebar buttons visuals
        for btn in self.nav.values():
            btn.redraw()
        self._set_nav_selected(self.active_page)

        # Update settings toggle text if visible
        if hasattr(self, "settings_toggle_btn"):
            self.settings_toggle_btn.configure(
                text="Switch to Dark" if self.data["settings"]["theme"] == "light" else "Switch to Light"
            )

        # Jump to active page without animation to avoid weirdness during rebuild
        self.show_page(self.active_page, animate=False)

        # Ensure toast uses new theme
        self.toast.redraw()

    # ---------- Plugins reload ----------
    def reload_lessons(self):
        self.lessons = load_lessons("lessons")
        self.apply_theme_rebuild()
        self.toast.show("Plugins reloaded.", kind="info", duration=1.6)

    # ---------- UI Tick ----------
    def _ui_tick(self):
        gems_val = self.gem_anim.tick()
        xp_val = self.xp_anim.tick()

        # update header pills if present
        for pill_canvas, val in ((getattr(self, "header_gems", None), gems_val),
                                 (getattr(self, "header_xp", None), xp_val)):
            if pill_canvas is not None and hasattr(pill_canvas, "_big_id"):
                try:
                    pill_canvas.itemconfig(pill_canvas._big_id, text=str(val))
                except Exception:
                    pass

        # shop balance label
        if hasattr(self, "shop_balance_lbl"):
            try:
                self.shop_balance_lbl.configure(text=str(gems_val))
            except Exception:
                pass

        self.after(16, self._ui_tick)  # ~60fps


if __name__ == "__main__":
    # ttk just for scrollbar; keep it minimal
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    app = DuoPluginApp()
    app.mainloop()
