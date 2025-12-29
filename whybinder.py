from __future__ import annotations
def setup_logging():
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        log_path = os.path.join(DATA_DIR, "app.log")
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            h = RotatingFileHandler(log_path, maxBytes=1_200_000, backupCount=3, encoding="utf-8")
            fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
            h.setFormatter(fmt)
            logger.addHandler(h)
        logging.info("=== Whybinder start ===")
    except Exception:
        pass


# whybinder.py — clean premium build (PySide6) — Windows 10+

import base64
import json
import os
import logging
from logging.handlers import RotatingFileHandler
import random
import sys
import time
import zlib
from dataclasses import dataclass, asdict
from datetime import datetime, date
from pathlib import Path
from typing import Any, Optional

# Optional deps
try:
    import keyboard  # type: ignore
except Exception:
    keyboard = None

try:
    import pyperclip  # type: ignore
except Exception:
    pyperclip = None

from PySide6 import QtCore, QtGui, QtWidgets, QtSvg

APP_TITLE_1 = "Whybinder - софт для чатера MATRIX TEAM"
APP_TITLE_2 = "powered by whynot_repow"
APP_NAME = "whybinder"
SHARE_PREFIX = "WB1:"

# ---------- Runtime paths ----------
def runtime_base_dir() -> Path:
    # next to script/exe
    try:
        return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    except Exception:
        return Path(__file__).resolve().parent

def runtime_data_dir() -> Path:
    d = runtime_base_dir() / "data"
    return d if d.exists() else runtime_base_dir()

DATA_DIR = Path.home() / f".{APP_NAME}"
DATA_DIR.mkdir(exist_ok=True)
TEMP_DIR = DATA_DIR / "tmp"
TEMP_DIR.mkdir(exist_ok=True)
SETTINGS_FILE = DATA_DIR / "settings.json"
PROFILES_DIR = DATA_DIR / "profiles"
PROFILES_DIR.mkdir(parents=True, exist_ok=True)
CONTENT_DB_FILE = DATA_DIR / "content_bases.json"
PRICE_FALLBACK_FILE = DATA_DIR / "price.txt"

DEFAULT_PROFILES = ["Judi", "Eva", "Molly"]
DEFAULT_BIND_CATEGORY = "Без категории"

# ---------- Themes ----------
THEMES: dict[str, dict[str, str]] = {
    "Ametrine": {
        "bg1": "#12062C", "bg2": "#220E70", "bg3": "#08255F",
        "surface": "rgba(8,6,18,0.34)", "accent": "rgba(160,120,255,0.32)",
        "text": "rgba(250,250,255,0.96)", "text2": "rgba(240,240,255,0.86)",
        "border": "rgba(255,255,255,0.18)", "grain": "16", "shadow": "48", "radius": "16",
    },
    "Carbon": {
        "bg1": "#06080F", "bg2": "#0E111A", "bg3": "#0B1528",
        "surface": "rgba(6,8,12,0.50)", "accent": "rgba(120,140,160,0.26)",
        "text": "rgba(240,244,255,0.96)", "text2": "rgba(210,214,230,0.82)",
        "border": "rgba(255,255,255,0.12)", "grain": "20", "shadow": "60", "radius": "12",
    },
    "Aurora": {
        "bg1": "#0A0E1F", "bg2": "#122437", "bg3": "#0A3A3B",
        "surface": "rgba(6,10,16,0.38)", "accent": "rgba(90,220,210,0.26)",
        "text": "rgba(240,255,250,0.96)", "text2": "rgba(210,238,234,0.82)",
        "border": "rgba(255,255,255,0.16)", "grain": "14", "shadow": "54", "radius": "18",
    },
    "Neon": {
        "bg1": "#120012", "bg2": "#28002E", "bg3": "#0E0033",
        "surface": "rgba(12,0,18,0.46)", "accent": "rgba(255,80,240,0.26)",
        "text": "rgba(255,245,255,0.96)", "text2": "rgba(235,215,245,0.82)",
        "border": "rgba(255,255,255,0.18)", "grain": "18", "shadow": "62", "radius": "18",
    },
    "Rose": {
        "bg1": "#2A0D14", "bg2": "#4B1527", "bg3": "#2B1638",
        "surface": "rgba(20,8,14,0.40)", "accent": "rgba(255,140,180,0.26)",
        "text": "rgba(255,245,250,0.96)", "text2": "rgba(235,220,230,0.82)",
        "border": "rgba(255,255,255,0.18)", "grain": "12", "shadow": "48", "radius": "20",
    },
}

def app_stylesheet(theme: str, density: str = "comfortable") -> str:
    t = THEMES.get(str(theme), THEMES["Ametrine"])
    accent = t["accent"]
    surface = t["surface"]
    text = t["text"]
    text2 = t["text2"]

    is_light = False
    menu_bg = "rgba(245,245,255,0.98)" if is_light else "rgba(12, 10, 28, 0.98)"
    menu_border = "rgba(0,0,0,0.14)" if is_light else "rgba(255,255,255,0.16)"
    btn_grad_top = "rgba(255,255,255,0.70)" if is_light else "rgba(255,255,255,0.20)"
    btn_grad_bot = "rgba(255,255,255,0.36)" if is_light else "rgba(255,255,255,0.08)"
    btn_border = t["border"]
    radius = int(float(t.get("radius", "16")))
    field_border = "rgba(0,0,0,0.12)" if is_light else "rgba(255,255,255,0.14)"
    header_bg = "rgba(0,0,0,0.06)" if is_light else "rgba(255,255,255,0.10)"

    dens = 0.86 if str(density) == "compact" else 1.0
    pad_btn_y = int(10 * dens)
    pad_btn_x = int(14 * dens)
    pad_field_y = int(8 * dens)
    pad_field_x = int(10 * dens)
    menu_pad_y = int(10 * dens)
    menu_pad_x = int(14 * dens)

    return f"""
    QWidget {{ background: transparent; }}
    * {{
        font-family: "Segoe UI Variable", "Segoe UI", "Inter", "Arial";
        font-size: {int(13 * dens)}px;
        color: {text};
        font-weight: 700;
        letter-spacing: 0.2px;
    }}
    QLabel#Title {{ font-size: 18px; font-weight: 900; letter-spacing: 0.4px; }}
    QLabel#Hint {{ color: {text2}; font-weight: 700; }}

    QPushButton, QToolButton {{
        font-weight: 900;
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(255,255,255,0.85), stop:0.45 {btn_grad_top}, stop:1 {btn_grad_bot});
        border: 1px solid {btn_border};
        padding: {pad_btn_y}px {pad_btn_x}px;
        border-radius: {radius}px;
        min-height: 18px;
    }}
    QPushButton:hover, QToolButton:hover {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(255,255,255,0.80), stop:1 rgba(255,255,255,0.46));
        border: 1px solid rgba(255,255,255,0.30);
    }}
    QPushButton:pressed, QToolButton:pressed {{
        background: {accent};
        border: 1px solid rgba(255,255,255,0.24);
    }}
    QPushButton#Danger {{
        background: rgba(255,80,110,0.24);
        border: 1px solid rgba(255,120,140,0.40);
    }}
    QPushButton#Danger:hover {{
        background: rgba(255,90,120,0.36);
    }}

    QLineEdit, QPlainTextEdit, QComboBox, QListWidget, QTableWidget {{
        background: {surface};
        border: 1px solid {field_border};
        border-radius: {max(10, radius - 4)}px;
        padding: {pad_field_y}px {pad_field_x}px;
        selection-background-color: {accent};
    }}
    QAbstractScrollArea::viewport {{ background: {surface}; }}
    QListWidget::item:hover {{ background: {accent}; border-radius: 8px; }}

    QHeaderView::section {{
        background: {header_bg};
        padding: 10px 10px;
        border: none;
        border-bottom: 1px solid {field_border};
        font-weight: 900;
    }}

    QMenu {{
        background: {menu_bg};
        border: 1px solid {menu_border};
        border-radius: {max(12, radius)}px;
        padding: 8px;
    }}
    QMenu::item {{ padding: {menu_pad_y}px {menu_pad_x}px; border-radius: 10px; font-weight: 900; }}
    QMenu::item:selected {{ background: {accent}; }}
    QMenu::separator {{ height: 1px; background: {menu_border}; margin: 6px 8px; }}
    QComboBox QAbstractItemView {{
        border-radius: {max(12, radius)}px;
        background: {menu_bg};
        border: 1px solid {menu_border};
        selection-background-color: {accent};
    }}

    QCheckBox::indicator {{
        width: 18px; height: 18px;
        border-radius: 6px;
        border: 1px solid {btn_border};
        background: rgba(0,0,0,0.10);
    }}
    QCheckBox::indicator:checked {{ background: {accent}; }}
    QTableWidget::item:hover {{ background: {accent}; }}
    QTableWidget::item:selected {{ background: {accent}; }}
    QWidget#Toast {{
        background: rgba(8, 6, 20, 0.78);
        border: 1px solid rgba(255,255,255,0.20);
        border-radius: 12px;
    }}
    QFrame#Card {{
        background: rgba(255,255,255,0.08);
        border: 1px solid {btn_border};
        border-radius: {max(12, radius)}px;
    }}
    QFrame#OnboardingCard {{
        background: rgba(18, 18, 32, 0.96);
        border: 1px solid rgba(255,255,255,0.20);
        border-radius: 18px;
    }}
    QFrame#ProfileOverlayCard {{
        background: rgba(20, 22, 36, 0.98);
        border: 1px solid rgba(255,255,255,0.26);
        border-radius: 16px;
    }}
    """



def ensure_data_layout():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(PROFILES_DIR, exist_ok=True)
    price_path = os.path.join(DATA_DIR, "price.txt")
    if not os.path.exists(price_path):
        with open(price_path, "w", encoding="utf-8") as f:
            f.write("")



def read_price_text() -> str:
    try:
        with open(os.path.join(DATA_DIR, "price.txt"), "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""



_GRAIN_CACHE: dict[int, QtGui.QPixmap] = {}

def _grain_pixmap(strength: int = 16, size: int = 128) -> QtGui.QPixmap:
    cached = _GRAIN_CACHE.get(strength)
    if cached:
        return cached
    img = QtGui.QImage(size, size, QtGui.QImage.Format_ARGB32_Premultiplied)
    img.fill(QtCore.Qt.transparent)
    rnd = QtCore.QRandomGenerator.global_()
    for y in range(size):
        for x in range(size):
            a = int(rnd.bounded(strength))
            if a == 0:
                continue
            v = 255 if rnd.bounded(2) == 0 else 0
            img.setPixelColor(x, y, QtGui.QColor(v, v, v, a))
    pm = QtGui.QPixmap.fromImage(img)
    _GRAIN_CACHE[strength] = pm
    return pm

def _draw_grain(p: QtGui.QPainter, rect: QtCore.QRect, strength: int = 16, step: int = 3):
    try:
        pm = _grain_pixmap(strength=strength)
        p.save()
        p.setOpacity(0.22)
        for y in range(rect.top(), rect.bottom(), pm.height()):
            for x in range(rect.left(), rect.right(), pm.width()):
                p.drawPixmap(x, y, pm)
        p.restore()
    except Exception:
        pass

def smooth_menu(menu: QtWidgets.QMenu):
    try:
        menu.setWindowFlag(QtCore.Qt.FramelessWindowHint, True)
        menu.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        menu.setContentsMargins(2, 2, 2, 2)
    except Exception:
        pass

def _parse_rgba(value: str) -> QtGui.QColor:
    v = (value or "").strip()
    if v.startswith("rgba"):
        raw = v[v.find("(") + 1:v.find(")")]
        parts = [p.strip() for p in raw.split(",")]
        if len(parts) == 4:
            r, g, b = (int(float(parts[i])) for i in range(3))
            a = float(parts[3])
            return QtGui.QColor(r, g, b, int(255 * a))
    c = QtGui.QColor()
    c.setNamedColor(v)
    return c if c.isValid() else QtGui.QColor(140, 160, 255, 120)

_SVG_ICONS = {
    "menu": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="white"><rect x="3" y="5" width="14" height="2" rx="1"/><rect x="3" y="9" width="14" height="2" rx="1"/><rect x="3" y="13" width="14" height="2" rx="1"/></svg>',
    "add": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="white"><rect x="9" y="4" width="2" height="12"/><rect x="4" y="9" width="12" height="2"/></svg>',
    "edit": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="white"><path d="M5 14l1.5-4.5L13 3l4 4-6.5 6.5L5 14z"/></svg>',
    "delete": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="white"><rect x="6" y="7" width="8" height="9" rx="1"/><rect x="5" y="5" width="10" height="2"/><rect x="8" y="3" width="4" height="2"/></svg>',
    "copy": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="white"><rect x="6" y="6" width="9" height="9" rx="1"/><rect x="4" y="4" width="9" height="9" rx="1" fill="none" stroke="white" stroke-width="1.5"/></svg>',
    "search": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="none" stroke="white" stroke-width="2"><circle cx="9" cy="9" r="5"/><line x1="13" y1="13" x2="17" y2="17"/></svg>',
    "dollar": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="none" stroke="white" stroke-width="2"><path d="M10 3v14"/><path d="M6 7c0-2 8-2 8 0s-8 2-8 4 8 2 8 4-8 2-8 0"/></svg>',
}

def icon_svg(name: str) -> QtGui.QIcon:
    svg = _SVG_ICONS.get(name, "")
    pix = QtGui.QPixmap(20, 20)
    pix.fill(QtCore.Qt.transparent)
    renderer = QtSvg.QSvgRenderer(QtCore.QByteArray(svg.encode("utf-8")))
    p = QtGui.QPainter(pix)
    renderer.render(p)
    p.end()
    return QtGui.QIcon(pix)

class HoverGlow(QtCore.QObject):
    def __init__(self, color_getter):
        super().__init__()
        self._color_getter = color_getter

    def eventFilter(self, obj, event):
        if isinstance(obj, (QtWidgets.QPushButton, QtWidgets.QToolButton)):
            if event.type() == QtCore.QEvent.Enter:
                try:
                    eff = QtWidgets.QGraphicsDropShadowEffect(obj)
                    eff.setBlurRadius(24)
                    eff.setOffset(0, 0)
                    eff.setColor(self._color_getter())
                    obj.setGraphicsEffect(eff)
                except Exception:
                    pass
            elif event.type() == QtCore.QEvent.Leave:
                try:
                    obj.setGraphicsEffect(None)
                except Exception:
                    pass
        return super().eventFilter(obj, event)


# ---------- Utils ----------
def safe_read_json(path: Path, default: Any) -> Any:
    try:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default

def safe_write_json(path: Path, obj: Any) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass

def today_key() -> str:
    return date.today().isoformat()

def utcnow() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"

def ensure_seed_files():
    # copy packaged ./data files to user DATA_DIR if missing
    rdata = runtime_data_dir()
    if (rdata/"content_bases.json").exists() and not CONTENT_DB_FILE.exists():
        CONTENT_DB_FILE.write_text((rdata/"content_bases.json").read_text(encoding="utf-8"), encoding="utf-8")
    if (rdata/"price.txt").exists() and not PRICE_FALLBACK_FILE.exists():
        PRICE_FALLBACK_FILE.write_text((rdata/"price.txt").read_text(encoding="utf-8"), encoding="utf-8")

def load_price_text() -> str:
    # Always prefer ./data/price.txt near script/exe
    try:
        p = runtime_data_dir()/"price.txt"
        if p.exists():
            return p.read_text(encoding="utf-8")
    except Exception:
        pass
    try:
        if PRICE_FALLBACK_FILE.exists():
            return PRICE_FALLBACK_FILE.read_text(encoding="utf-8")
    except Exception:
        pass
    return ""

# ---------- Share codes ----------
def encode_share(payload: dict) -> str:
    raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    comp = zlib.compress(raw, 9)
    b64 = base64.urlsafe_b64encode(comp).decode("ascii").rstrip("=")
    return SHARE_PREFIX + b64

def decode_share(code: str) -> dict:
    code = (code or "").strip()
    if code.startswith(SHARE_PREFIX):
        code = code[len(SHARE_PREFIX):]
    pad = "=" * ((4 - (len(code) % 4)) % 4)
    comp = base64.urlsafe_b64decode((code + pad).encode("ascii"))
    raw = zlib.decompress(comp)
    obj = json.loads(raw.decode("utf-8"))
    if not isinstance(obj, dict):
        raise ValueError("bad code")
    return obj

# ---------- Models ----------
@dataclass
class Bind:
    kind: str               # "hotkey" | "text"
    key: str                # e.g. "F10+1"
    text: str
    mode: str = "paste"     # "paste" or "type"
    enabled: bool = True
    category: str = DEFAULT_BIND_CATEGORY
    favorite: bool = False

def profile_dir(name: str) -> Path:
    d = PROFILES_DIR / name
    d.mkdir(parents=True, exist_ok=True)
    return d

def ensure_profiles():
    for n in DEFAULT_PROFILES:
        d = profile_dir(n)
        if not (d/"categories.json").exists():
            safe_write_json(d/"categories.json", [DEFAULT_BIND_CATEGORY, "Приветки", "О себе", "Ппв 1", "Ппв 2", "Ппв 3"])
        if not (d/"binds.json").exists():
            safe_write_json(d/"binds.json", [])

def load_profile(name: str) -> tuple[list[str], list[Bind]]:
    d = profile_dir(name)
    cats = safe_read_json(d/"categories.json", [DEFAULT_BIND_CATEGORY])
    if not isinstance(cats, list):
        cats = [DEFAULT_BIND_CATEGORY]
    cats = [str(x).strip() for x in cats if str(x).strip()]
    if DEFAULT_BIND_CATEGORY not in cats:
        cats.insert(0, DEFAULT_BIND_CATEGORY)

    raw = safe_read_json(d/"binds.json", [])
    binds: list[Bind] = []
    if isinstance(raw, list):
        for x in raw:
            if isinstance(x, dict):
                x.setdefault("category", DEFAULT_BIND_CATEGORY)
                x.setdefault("favorite", False)
                try:
                    binds.append(Bind(**x))
                except Exception:
                    pass
    # add missing categories from binds
    for b in binds:
        if b.category and b.category not in cats:
            cats.append(b.category)
    return cats, binds

def save_profile(name: str, cats: list[str], binds: list[Bind]):
    d = profile_dir(name)
    safe_write_json(d/"categories.json", cats)
    safe_write_json(d/"binds.json", [asdict(b) for b in binds])

# ---------- Content DB ----------
class ContentDB:
    def __init__(self, path: Path):
        self.path = path
        self.data = self._migrate(safe_read_json(path, None))

    def _default(self):
        return {
            "version": 2,
            "ppv": {k: {"items": []} for k in ["BOOBS","BOOBS+PUSSYPLAY","PUSSYPLAY","DILDO","FOOTJOB","BLOWJOB WITH DILDO"]},
            "mailing": {k: {"items": []} for k in ["SEXY","LIFESTYLE","GOVIP"]},
        }

    def _mk(self, text: str, hint: str="") -> dict:
        return {
            "id": f"t_{abs(hash((text, hint, time.time()))) % (10**12)}",
            "text": text.strip(),
            "hint": (hint or "").strip(),
            "created_at": utcnow(),
            "uses_total": 0,
            "uses_by_day": {},
            "last_used": None,
            "copies_total": 0,
        }

    def _migrate(self, obj: Any) -> dict:
        d = self._default()
        if not isinstance(obj, dict) or obj.get("version") != 2:
            return d
        # ensure keys
        for area in ("ppv","mailing"):
            if area not in obj or not isinstance(obj[area], dict):
                obj[area] = {}
            for cat in d[area].keys():
                obj[area].setdefault(cat, {"items": []})
                if not isinstance(obj[area][cat].get("items"), list):
                    obj[area][cat]["items"] = []
        return obj

    def save(self):
        safe_write_json(self.path, self.data)

    def categories(self, area: str) -> list[str]:
        return list(self.data.get(area, {}).keys())

    def items(self, area: str, cat: str) -> list[dict]:
        return list(self.data.get(area, {}).get(cat, {}).get("items", []))

    def add(self, area: str, cat: str, text: str, hint: str=""):
        self.data.setdefault(area, {}).setdefault(cat, {"items": []})
        it = self._mk(text, hint)
        self.data[area][cat]["items"].append(it)
        self.save()

    def update(self, area: str, cat: str, item_id: str, text: str, hint: str=""):
        arr = self.data.get(area, {}).get(cat, {}).get("items", [])
        for it in arr:
            if it.get("id") == item_id:
                it["text"] = text.strip()
                it["hint"] = (hint or "").strip()
                self.save()
                return
        raise KeyError(item_id)

    def delete(self, area: str, cat: str, item_id: str):
        arr = self.data.get(area, {}).get(cat, {}).get("items", [])
        n = len(arr)
        arr[:] = [it for it in arr if it.get("id") != item_id]
        if len(arr) == n:
            raise KeyError(item_id)
        self.save()

    def mark_used(self, area: str, cat: str, item_id: str, as_copy: bool):
        tk = today_key()
        arr = self.data.get(area, {}).get(cat, {}).get("items", [])
        for it in arr:
            if it.get("id") == item_id:
                if as_copy:
                    it["copies_total"] = int(it.get("copies_total") or 0) + 1
                it["uses_total"] = int(it.get("uses_total") or 0) + 1
                by = it.get("uses_by_day")
                if not isinstance(by, dict):
                    by = {}
                    it["uses_by_day"] = by
                by[tk] = int(by.get(tk) or 0) + 1
                it["last_used"] = datetime.now().isoformat(timespec="seconds")
                self.save()
                return

    def pick_random(self, area: str, cat: str, only_not_used_today: bool) -> Optional[dict]:
        items = self.items(area, cat)
        if not items:
            return None
        if not only_not_used_today:
            return random.choice(items)
        tk = today_key()
        fresh = [it for it in items if int((it.get("uses_by_day") or {}).get(tk) or 0) == 0]
        return random.choice(fresh) if fresh else random.choice(items)

    def import_json(self, area: str, cat: str, path: Path) -> int:
        obj = json.loads(path.read_text(encoding="utf-8"))
        added = 0
        self.data.setdefault(area, {}).setdefault(cat, {"items": []})
        arr = self.data[area][cat]["items"]
        if isinstance(obj, dict) and isinstance(obj.get("items"), list):
            for x in obj["items"]:
                if isinstance(x, dict) and (x.get("text") or "").strip():
                    arr.append(self._mk(str(x["text"]), str(x.get("hint") or ""))); added += 1
                elif isinstance(x, str) and x.strip():
                    arr.append(self._mk(x.strip(), "")); added += 1
        elif isinstance(obj, list):
            for x in obj:
                if isinstance(x, str) and x.strip():
                    arr.append(self._mk(x.strip(), "")); added += 1
        self.save()
        return added

    def export_json(self, area: str, cat: str, path: Path):
        payload = {
            "version": 1,
            "area": area,
            "category": cat,
            "exported_at": utcnow(),
            "items": [{"text": it.get("text",""), "hint": it.get("hint","")} for it in self.items(area, cat)],
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

# ---------- Anim ----------
class Toast(QtWidgets.QFrame):
    def __init__(self, parent, text: str, ms: int = 2200, kind: str = "info"):
        super().__init__(parent)
        self.setObjectName("Toast")
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)
        lay = QtWidgets.QHBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        self.lbl = QtWidgets.QLabel(text)
        self.lbl.setWordWrap(True)
        lay.addWidget(self.lbl, 1)
        self._ms = ms
        self.opacity = QtWidgets.QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity)
        self.opacity.setOpacity(0.0)
        self._timer = QtCore.QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._hide)

    def show_toast(self):
        self.adjustSize()
        p = self.parentWidget()
        if not p:
            return
        margin = 18
        self.move(max(margin, p.width() - self.width() - margin),
                  max(margin, p.height() - self.height() - margin))
        self.show()
        Anim.fade(self, 0.0, 1.0, 180)
        self._timer.start(self._ms)

    def _hide(self):
        Anim.fade(self, 1.0, 0.0, 180)
        QtCore.QTimer.singleShot(220, self.deleteLater)

class Anim:

    @staticmethod
    def pop(w: QtWidgets.QWidget, ms: int = 170):
        try:
            start = w.geometry()
            g = QtCore.QRect(start.x()+8, start.y()+8, max(1, start.width()-16), max(1, start.height()-16))
            a = QtCore.QPropertyAnimation(w, b"geometry")
            a.setDuration(ms)
            a.setStartValue(g)
            a.setEndValue(start)
            a.setEasingCurve(QtCore.QEasingCurve.OutBack)
            a.start(QtCore.QAbstractAnimation.DeleteWhenStopped)
        except Exception:
            pass

    @staticmethod
    def fade(widget: QtWidgets.QWidget, start=0.0, end=1.0, ms=180):
        eff = widget.graphicsEffect()
        if not isinstance(eff, QtWidgets.QGraphicsOpacityEffect):
            eff = QtWidgets.QGraphicsOpacityEffect(widget)
            widget.setGraphicsEffect(eff)
        eff.setOpacity(start)
        a = QtCore.QPropertyAnimation(eff, b"opacity", widget)
        a.setStartValue(start); a.setEndValue(end)
        a.setDuration(ms)
        a.setEasingCurve(QtCore.QEasingCurve.OutCubic)
        a.start(QtCore.QAbstractAnimation.DeleteWhenStopped)

    @staticmethod
    def slide_in(widget: QtWidgets.QWidget, dx=18, ms=220):
        end = widget.pos()
        start = end + QtCore.QPoint(dx, 0)
        widget.move(start)
        a = QtCore.QPropertyAnimation(widget, b"pos", widget)
        a.setStartValue(start); a.setEndValue(end)
        a.setDuration(ms)
        a.setEasingCurve(QtCore.QEasingCurve.OutCubic)
        a.start(QtCore.QAbstractAnimation.DeleteWhenStopped)

    @staticmethod
    def menu_pop(menu: QtWidgets.QMenu):
        def run():
            eff = menu.graphicsEffect()
            if not isinstance(eff, QtWidgets.QGraphicsOpacityEffect):
                eff = QtWidgets.QGraphicsOpacityEffect(menu)
                menu.setGraphicsEffect(eff)
            eff.setOpacity(0.0)
            geo = menu.geometry()
            start = QtCore.QRect(geo.x() + 10, geo.y() + 10, max(1, geo.width() - 20), max(1, geo.height() - 20))
            a1 = QtCore.QPropertyAnimation(eff, b"opacity", menu)
            a1.setStartValue(0.0); a1.setEndValue(1.0)
            a1.setDuration(140)
            a1.setEasingCurve(QtCore.QEasingCurve.OutCubic)
            a2 = QtCore.QPropertyAnimation(menu, b"geometry", menu)
            a2.setStartValue(start); a2.setEndValue(geo)
            a2.setDuration(160)
            a2.setEasingCurve(QtCore.QEasingCurve.OutCubic)
            group = QtCore.QParallelAnimationGroup(menu)
            group.addAnimation(a1); group.addAnimation(a2)
            group.start(QtCore.QAbstractAnimation.DeleteWhenStopped)
        QtCore.QTimer.singleShot(0, run)

    @staticmethod
    def slide_out(widget: QtWidgets.QWidget, dy=10, ms=180):
        start = widget.pos()
        end = start + QtCore.QPoint(0, dy)
        a = QtCore.QPropertyAnimation(widget, b"pos", widget)
        a.setStartValue(start); a.setEndValue(end)
        a.setDuration(ms)
        a.setEasingCurve(QtCore.QEasingCurve.InCubic)
        a.start(QtCore.QAbstractAnimation.DeleteWhenStopped)

    @staticmethod
    def motion_blur(widget: QtWidgets.QWidget, ms: int = 200):
        try:
            eff = QtWidgets.QGraphicsBlurEffect(widget)
            eff.setBlurRadius(8)
            widget.setGraphicsEffect(eff)
            anim = QtCore.QPropertyAnimation(eff, b"blurRadius", widget)
            anim.setDuration(ms)
            anim.setStartValue(8)
            anim.setEndValue(0)
            anim.setEasingCurve(QtCore.QEasingCurve.OutCubic)
            anim.finished.connect(lambda: widget.setGraphicsEffect(None))
            anim.start(QtCore.QAbstractAnimation.DeleteWhenStopped)
        except Exception:
            pass

    @staticmethod
    def shake(widget: QtWidgets.QWidget, dist: int = 6, ms: int = 240):
        try:
            pos = widget.pos()
            anim = QtCore.QPropertyAnimation(widget, b"pos", widget)
            anim.setDuration(ms)
            anim.setKeyValueAt(0.0, pos)
            anim.setKeyValueAt(0.2, pos + QtCore.QPoint(-dist, 0))
            anim.setKeyValueAt(0.4, pos + QtCore.QPoint(dist, 0))
            anim.setKeyValueAt(0.6, pos + QtCore.QPoint(-dist, 0))
            anim.setKeyValueAt(0.8, pos + QtCore.QPoint(dist, 0))
            anim.setKeyValueAt(1.0, pos)
            anim.setEasingCurve(QtCore.QEasingCurve.OutCubic)
            anim.start(QtCore.QAbstractAnimation.DeleteWhenStopped)
        except Exception:
            pass

    @staticmethod
    def bounce(widget: QtWidgets.QWidget, ms: int = 220):
        try:
            start = widget.geometry()
            grow = QtCore.QRect(start.x() - 2, start.y() - 2, start.width() + 4, start.height() + 4)
            anim = QtCore.QPropertyAnimation(widget, b"geometry", widget)
            anim.setDuration(ms)
            anim.setStartValue(start)
            anim.setKeyValueAt(0.5, grow)
            anim.setEndValue(start)
            anim.setEasingCurve(QtCore.QEasingCurve.OutBack)
            anim.start(QtCore.QAbstractAnimation.DeleteWhenStopped)
        except Exception:
            pass

# ---------- Glass root ----------
class GlassRoot(QtWidgets.QFrame):
    def __init__(self, get_theme, parent=None):
        super().__init__(parent)
        self.setObjectName("GlassRoot")
        self._get_theme = get_theme
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.setAttribute(QtCore.Qt.WA_NoSystemBackground, True)
        self.setAttribute(QtCore.Qt.WA_OpaquePaintEvent, False)

    def paintEvent(self, e: QtGui.QPaintEvent):
        p = QtGui.QPainter(self)
        if not p.isActive():
            return
        p.setRenderHint(QtGui.QPainter.Antialiasing, True)
        r = self.rect().adjusted(1, 1, -1, -1)

        t = THEMES.get(str(self._get_theme()), THEMES["Ametrine"])
        radius = float(t.get("radius", "16"))
        path = QtGui.QPainterPath()
        path.addRoundedRect(QtCore.QRectF(r), radius, radius)

        grad = QtGui.QLinearGradient(r.topLeft(), r.bottomRight())
        grad.setColorAt(0.0, QtGui.QColor(t["bg1"]))
        grad.setColorAt(0.45, QtGui.QColor(t["bg2"]))
        grad.setColorAt(1.0, QtGui.QColor(t["bg3"]))
        p.fillPath(path, grad)

        hl = QtGui.QLinearGradient(r.topLeft(), r.bottomLeft())
        hl.setColorAt(0.0, QtGui.QColor(255, 255, 255, 52))
        hl.setColorAt(1.0, QtGui.QColor(255, 255, 255, 10))
        p.fillPath(path, hl)

        pen = QtGui.QPen(QtGui.QColor(255, 255, 255, 36))
        pen.setWidthF(1.1)
        p.setPen(pen)
        p.drawPath(path)

        try:
            strength = int(t.get("grain", "12"))
            _draw_grain(p, r, strength=strength, step=3)
        except Exception:
            pass
        p.end()

# ---------- TitleBar ----------
class TitleBar(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._drag = None
        self.lbl = QtWidgets.QLabel("whybinder")
        self.lbl.setObjectName("Title")
        self.btn_theme = QtWidgets.QToolButton(); self.btn_theme.setIcon(icon_svg("menu")); self.btn_theme.setFixedWidth(48)
        self.btn_min = QtWidgets.QToolButton(); self.btn_min.setText("—"); self.btn_min.setFixedWidth(48)
        self.btn_close = QtWidgets.QToolButton(); self.btn_close.setText("✕"); self.btn_close.setFixedWidth(48)

        lay = QtWidgets.QHBoxLayout(self)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.addWidget(self.lbl)
        lay.addStretch(1)
        lay.addWidget(self.btn_theme)
        lay.addWidget(self.btn_min)
        lay.addWidget(self.btn_close)

    def mousePressEvent(self, e: QtGui.QMouseEvent):
        if e.button() == QtCore.Qt.LeftButton:
            self._drag = e.globalPosition().toPoint()
            e.accept()

    def mouseMoveEvent(self, e: QtGui.QMouseEvent):
        if self._drag and (e.buttons() & QtCore.Qt.LeftButton):
            w = self.window()
            delta = e.globalPosition().toPoint() - self._drag
            w.move(w.pos() + delta)
            self._drag = e.globalPosition().toPoint()
            e.accept()

    def mouseReleaseEvent(self, e: QtGui.QMouseEvent):
        self._drag = None

# ---------- Dialogs ----------
class GlassDialog(QtWidgets.QDialog):
    def __init__(self, get_theme, parent=None, w=720, h=480, title=""):
        super().__init__(parent)
        self._get_theme = get_theme
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.Dialog)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.resize(w, h)

        self.root = GlassRoot(self._get_theme, self)
        self.body = QtWidgets.QWidget(self.root)

        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(0,0,0,0)
        outer.addWidget(self.root)

        rlay = QtWidgets.QVBoxLayout(self.root)
        rlay.setContentsMargins(14, 14, 14, 14)

        top = QtWidgets.QHBoxLayout()
        lbl = QtWidgets.QLabel(title or "")
        lbl.setObjectName("Title")
        btn_x = QtWidgets.QToolButton(); btn_x.setText("✕"); btn_x.setFixedWidth(48)
        btn_x.clicked.connect(self.reject)
        top.addWidget(lbl)
        top.addStretch(1)
        top.addWidget(btn_x)
        rlay.addLayout(top)
        rlay.addWidget(self.body, 1)

class ProfileOverlay(QtWidgets.QFrame):
    def __init__(self, mw: 'MainWindow'):
        super().__init__(None)
        self.mw = mw
        self._drag = None
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.Tool | QtCore.Qt.WindowStaysOnTopHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.setObjectName("ProfileOverlay")

        self.root = QtWidgets.QFrame(self)
        self.root.setObjectName("ProfileOverlayCard")
        lay = QtWidgets.QHBoxLayout(self.root)
        lay.setContentsMargins(12, 10, 12, 10)
        lbl = QtWidgets.QLabel("Профиль:")
        self.cmb = QtWidgets.QComboBox()
        self.cmb.addItems(DEFAULT_PROFILES)
        self.cmb.setCurrentText(self.mw.cmb_profile.currentText())
        lay.addWidget(lbl)
        lay.addWidget(self.cmb)

        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self.root)

        self.cmb.currentTextChanged.connect(self._switch)

    def _switch(self, name: str):
        try:
            self.mw.cmb_profile.setCurrentText(name)
        except Exception:
            pass

    def showEvent(self, e):
        super().showEvent(e)
        try:
            screen = QtGui.QGuiApplication.primaryScreen().availableGeometry()
            self.adjustSize()
            self.move(screen.right() - self.width() - 24, screen.top() + 24)
        except Exception:
            pass

    def mousePressEvent(self, e: QtGui.QMouseEvent):
        if e.button() == QtCore.Qt.LeftButton:
            self._drag = e.globalPosition().toPoint()
            e.accept()

    def mouseMoveEvent(self, e: QtGui.QMouseEvent):
        if self._drag and (e.buttons() & QtCore.Qt.LeftButton):
            delta = e.globalPosition().toPoint() - self._drag
            self.move(self.pos() + delta)
            self._drag = e.globalPosition().toPoint()
            e.accept()

    def mouseReleaseEvent(self, e: QtGui.QMouseEvent):
        self._drag = None

    def showEvent(self, e):
        super().showEvent(e)
        Anim.fade(self, 0.0, 1.0, 220)
        Anim.pop(self, 180)
        try:
            Anim.slide_in(self.root, dx=12, ms=180)
        except Exception:
            pass

class ConfirmDialog(GlassDialog):
    def __init__(self, get_theme, parent=None, title="Подтверждение", message=""):
        super().__init__(get_theme, parent, 420, 220, title)
        lay = QtWidgets.QVBoxLayout(self.body)
        lbl = QtWidgets.QLabel(message)
        lbl.setWordWrap(True)
        lay.addWidget(lbl, 1)
        btns = QtWidgets.QHBoxLayout()
        btn_cancel = QtWidgets.QPushButton("Отмена")
        btn_ok = QtWidgets.QPushButton("Ок")
        btns.addStretch(1)
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_ok)
        lay.addLayout(btns)
        btn_cancel.clicked.connect(self.reject)
        btn_ok.clicked.connect(self.accept)

class InputDialog(GlassDialog):
    def __init__(self, get_theme, parent=None, title="Ввод", label="Название:", text=""):
        super().__init__(get_theme, parent, 480, 220, title)
        lay = QtWidgets.QVBoxLayout(self.body)
        lay.addWidget(QtWidgets.QLabel(label))
        self.edit = QtWidgets.QLineEdit()
        self.edit.setText(text or "")
        lay.addWidget(self.edit)
        btns = QtWidgets.QHBoxLayout()
        btn_cancel = QtWidgets.QPushButton("Отмена")
        btn_ok = QtWidgets.QPushButton("Ок")
        btns.addStretch(1)
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_ok)
        lay.addLayout(btns)
        btn_cancel.clicked.connect(self.reject)
        btn_ok.clicked.connect(self.accept)

    def get(self) -> str:
        return self.edit.text().strip()

class UpdateOverlay(QtWidgets.QFrame):
    def __init__(self, mw: 'MainWindow'):
        super().__init__(mw)
        self.hide()

class BindEditor(GlassDialog):
    def __init__(self, get_theme, parent=None, bind_obj: Optional[Bind]=None, categories: Optional[list[str]]=None):
        super().__init__(get_theme, parent, 760, 520, "Бинд")
        self.result_bind: Optional[Bind] = None
        cats = categories or [DEFAULT_BIND_CATEGORY]

        form = QtWidgets.QFormLayout(self.body)
        form.setLabelAlignment(QtCore.Qt.AlignRight)

        self.cmb_kind = QtWidgets.QComboBox(); self.cmb_kind.addItems(["hotkey", "text"])
        self.ed_key = QtWidgets.QLineEdit()
        self.cmb_mode = QtWidgets.QComboBox(); self.cmb_mode.addItems(["paste", "type"])
        self.cmb_cat = QtWidgets.QComboBox(); self.cmb_cat.addItems(cats)
        self.txt = QtWidgets.QPlainTextEdit()
        self.chk_en = QtWidgets.QCheckBox("Включён")
        self.chk_fav = QtWidgets.QCheckBox("Избранный ★")

        if bind_obj:
            self.cmb_kind.setCurrentText(bind_obj.kind)
            self.ed_key.setText(bind_obj.key)
            self.cmb_mode.setCurrentText(bind_obj.mode)
            if bind_obj.category in cats:
                self.cmb_cat.setCurrentText(bind_obj.category)
            self.txt.setPlainText(bind_obj.text)
            self.chk_en.setChecked(bind_obj.enabled)
            self.chk_fav.setChecked(bind_obj.favorite)
        else:
            self.chk_en.setChecked(True)

        form.addRow("Тип:", self.cmb_kind)
        form.addRow("Клавиши / триггер:", self.ed_key)
        form.addRow("Режим:", self.cmb_mode)
        form.addRow("Категория:", self.cmb_cat)
        form.addRow("Текст:", self.txt)
        form.addRow("", self.chk_en)
        form.addRow("", self.chk_fav)

        btns = QtWidgets.QHBoxLayout()
        btn_cancel = QtWidgets.QPushButton("Отмена")
        btn_ok = QtWidgets.QPushButton("Сохранить")
        btns.addStretch(1); btns.addWidget(btn_cancel); btns.addWidget(btn_ok)
        form.addRow("", btns)

        btn_cancel.clicked.connect(self.reject)
        btn_ok.clicked.connect(self._save)

    def _save(self):
        key = self.ed_key.text().strip()
        text = self.txt.toPlainText().rstrip()
        if not key:
            Toast(self, "Укажи триггер (клавиши).", kind="error").show_toast()
            Anim.shake(self.ed_key)
            return
        self.result_bind = Bind(
            kind=self.cmb_kind.currentText(),
            key=key,
            text=text,
            mode=self.cmb_mode.currentText(),
            enabled=self.chk_en.isChecked(),
            category=self.cmb_cat.currentText().strip() or DEFAULT_BIND_CATEGORY,
            favorite=self.chk_fav.isChecked(),
        )
        self.accept()

class TextEditor(GlassDialog):
    def __init__(self, get_theme, parent=None, title="Текст", text="", hint=""):
        super().__init__(get_theme, parent, 760, 540, title)
        lay = QtWidgets.QVBoxLayout(self.body)
        self.ed = QtWidgets.QPlainTextEdit(); self.ed.setPlainText(text)
        self.hint = QtWidgets.QLineEdit(); self.hint.setPlaceholderText("Подсказка по контенту (опционально)")
        self.hint.setText(hint or "")
        lay.addWidget(QtWidgets.QLabel("Текст:"))
        lay.addWidget(self.ed, 1)
        lay.addWidget(QtWidgets.QLabel("Подсказка:"))
        lay.addWidget(self.hint)

        btns = QtWidgets.QHBoxLayout()
        self.btn_cancel = QtWidgets.QPushButton("Отмена")
        self.btn_ok = QtWidgets.QPushButton("Сохранить")
        btns.addStretch(1); btns.addWidget(self.btn_cancel); btns.addWidget(self.btn_ok)
        lay.addLayout(btns)

        self.btn_cancel.clicked.connect(self.reject)
        self.btn_ok.clicked.connect(self.accept)

    def get(self) -> tuple[str, str]:
        return self.ed.toPlainText().rstrip(), self.hint.text().strip()

class SpotlightDialog(GlassDialog):
    def __init__(self, mw: 'MainWindow'):
        super().__init__(mw.get_theme, mw, 720, 420, "Поиск")
        self.mw = mw
        lay = QtWidgets.QVBoxLayout(self.body)
        self.query = QtWidgets.QLineEdit()
        self.query.setPlaceholderText("Поиск по биндам, категориям, PPV, рассылкам…")
        self.list = QtWidgets.QListWidget()
        lay.addWidget(self.query)
        lay.addWidget(self.list, 1)
        self.query.textChanged.connect(self._refresh)
        self.list.itemActivated.connect(self._open_item)
        self._items: list[dict[str, Any]] = []
        self._refresh("")

    def _collect(self) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for b in self.mw.binds:
            out.append({"type": "bind", "key": b.key, "category": b.category, "text": b.text})
        for area in ("ppv", "mailing"):
            for cat in self.mw.content_db.categories(area):
                for it in self.mw.content_db.items(area, cat):
                    out.append({"type": area, "category": cat, "text": it.get("text", ""), "id": it.get("id")})
        return out

    def _refresh(self, q: str):
        self.list.clear()
        q = (q or "").strip().lower()
        items = self._collect()
        self._items = []
        for it in items:
            blob = " ".join(str(v) for v in it.values()).lower()
            if q and q not in blob:
                continue
            label = ""
            if it["type"] == "bind":
                label = f"Бинд • {it['category']} • {it['key']} — {it['text'][:60]}"
            elif it["type"] == "ppv":
                label = f"PPV • {it['category']} — {it['text'][:60]}"
            else:
                label = f"Рассылка • {it['category']} — {it['text'][:60]}"
            self.list.addItem(label)
            self._items.append(it)

    def _open_item(self, item: QtWidgets.QListWidgetItem):
        row = self.list.row(item)
        if not (0 <= row < len(self._items)):
            return
        it = self._items[row]
        if it["type"] == "bind":
            self.mw.switch_page(self.mw.page_binds)
        elif it["type"] == "ppv":
            self.mw.switch_page(self.mw.page_ppv)
            self.mw.page_ppv.cmb.setCurrentText(it["category"])
        else:
            self.mw.switch_page(self.mw.page_mail)
            self.mw.page_mail.cmb.setCurrentText(it["category"])
        self.accept()

class OnboardingOverlay(QtWidgets.QFrame):
    def __init__(self, mw: 'MainWindow'):
        super().__init__(mw)
        self.mw = mw
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, False)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.setObjectName("Onboarding")
        self.setGeometry(mw.rect())

        self.card = QtWidgets.QFrame(self)
        self.card.setObjectName("OnboardingCard")
        self.card.setFixedSize(520, 220)
        self.title = QtWidgets.QLabel("Добро пожаловать", self.card)
        self.title.setObjectName("Title")
        self.text = QtWidgets.QLabel("", self.card)
        self.text.setWordWrap(True)
        self.btn_skip = QtWidgets.QPushButton("Пропустить", self.card)
        self.btn_back = QtWidgets.QPushButton("Назад", self.card)
        self.btn_next = QtWidgets.QPushButton("Далее", self.card)

        v = QtWidgets.QVBoxLayout(self.card)
        v.addWidget(self.title)
        v.addWidget(self.text, 1)
        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.btn_skip)
        row.addStretch(1)
        row.addWidget(self.btn_back)
        row.addWidget(self.btn_next)
        v.addLayout(row)

        self.lens = QtWidgets.QFrame(self)
        self.lens.setStyleSheet(
            "QFrame{border: 2px solid rgba(255,255,255,0.85); border-radius: 18px; background: rgba(255,255,255,0.08);}"
        )
        self.lens.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)

        self.steps = [
            {"title": "Бинды", "text": "Создавай бинды, включай/выключай и копируй в один клик.", "target": lambda: mw.page_binds.table, "page": lambda: mw.switch_page(mw.page_binds)},
            {"title": "PPV", "text": "PPV — быстрый доступ и копирование.", "target": lambda: mw.page_ppv.lst, "page": lambda: mw.switch_page(mw.page_ppv)},
            {"title": "Рассылка", "text": "Рассылки — шаблоны для быстрого ответа.", "target": lambda: mw.page_mail.lst, "page": lambda: mw.switch_page(mw.page_mail)},
            {"title": "Поиск", "text": "Spotlight (Ctrl+K) для быстрого поиска.", "target": lambda: mw.btn_menu, "page": lambda: None},
            {"title": "Темы", "text": "Смену темы и плотности ищи в меню.", "target": lambda: mw.titlebar.btn_theme, "page": lambda: None},
        ]
        self.index = 0
        self.btn_skip.clicked.connect(self.finish)
        self.btn_back.clicked.connect(self.prev_step)
        self.btn_next.clicked.connect(self.next_step)
        self.update_step()
        self.show()
        self.raise_()
        self.card.raise_()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.setGeometry(self.mw.rect())
        self._position_card()
        self._position_lens()

    def paintEvent(self, e):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing, True)
        p.fillRect(self.rect(), QtGui.QColor(6, 6, 16, 140))

    def _position_card(self):
        self.card.move(self.width() - self.card.width() - 24, 24)
        self.card.raise_()

    def _position_lens(self):
        target = self._target_rect()
        pad = 8
        rect = QtCore.QRect(target.x() - pad, target.y() - pad, target.width() + pad * 2, target.height() + pad * 2)
        self.lens.setGeometry(rect)

    def _target_rect(self) -> QtCore.QRect:
        try:
            w = self.steps[self.index]["target"]()
            if not w:
                return QtCore.QRect(40, 40, 200, 80)
            g = w.rect()
            top_left = w.mapToGlobal(g.topLeft())
            local = self.mapFromGlobal(top_left)
            return QtCore.QRect(local, g.size())
        except Exception:
            return QtCore.QRect(40, 40, 200, 80)

    def update_step(self):
        step = self.steps[self.index]
        try:
            if step.get("page"):
                step["page"]()
        except Exception:
            pass
        self.title.setText(step["title"])
        self.text.setText(step["text"])
        self.btn_back.setEnabled(self.index > 0)
        self.btn_next.setText("Готово" if self.index == len(self.steps) - 1 else "Далее")
        self._position_card()
        self._animate_lens()

    def _animate_lens(self):
        target = self._target_rect()
        pad = 8
        rect = QtCore.QRect(target.x() - pad, target.y() - pad, target.width() + pad * 2, target.height() + pad * 2)
        if self.card.geometry().intersects(rect):
            self.card.move(self.width() - self.card.width() - 24, rect.bottom() + 16)
            if self.card.geometry().intersects(rect):
                self.card.move(self.width() - self.card.width() - 24, max(24, rect.y() - self.card.height() - 16))
        self.card.raise_()
        self.card.raise_()
        anim = QtCore.QPropertyAnimation(self.lens, b"geometry", self)
        anim.setDuration(240)
        anim.setStartValue(self.lens.geometry())
        anim.setEndValue(rect)
        anim.setEasingCurve(QtCore.QEasingCurve.OutCubic)
        anim.start(QtCore.QAbstractAnimation.DeleteWhenStopped)

    def next_step(self):
        if self.index >= len(self.steps) - 1:
            self.finish()
            return
        self.index += 1
        self.update_step()

    def prev_step(self):
        self.index = max(0, self.index - 1)
        self.update_step()

    def finish(self):
        self.hide()
        self.deleteLater()
        try:
            self.mw.g["onboarding_seen"] = True
            save_settings(self.mw.g)
        except Exception:
            pass

# ---------- Binder engine ----------
class BinderEngine(QtCore.QObject):
    status = QtCore.Signal(str)
    def __init__(self):
        super().__init__()
        self.enabled = True
        self._hotkeys = []
        self.binds: list[Bind] = []
        self._text_hook = None
        self._text_buffer = ""
        self._injecting = False

    def set_enabled(self, on: bool):
        self.enabled = bool(on)
        self.status.emit("Двигатель запущен ✅" if self.enabled else "Двигатель остановлен ⛔")

    def clear_hotkeys(self):
        if keyboard is None:
            return
        for hk in self._hotkeys:
            try:
                keyboard.remove_hotkey(hk)
            except Exception:
                pass
        self._hotkeys = []
        if self._text_hook is not None:
            try:
                keyboard.unhook(self._text_hook)
            except Exception:
                pass
            self._text_hook = None
            self._text_buffer = ""

    def apply_binds(self, binds: list[Bind]):
        self.binds = binds[:]
        self.clear_hotkeys()
        if keyboard is None:
            self.status.emit("keyboard не установлен — бинды не активны")
            return

        # Fix: prioritize longer combos so F10+1 doesn't trigger F10
        enabled = [b for b in self.binds if b.enabled and b.kind == "hotkey" and b.key.strip()]
        enabled.sort(key=lambda b: len(b.key), reverse=True)

        for b in enabled:
            try:
                hk = keyboard.add_hotkey(b.key, lambda bb=b: self._fire(bb), suppress=True, trigger_on_release=False)
                self._hotkeys.append(hk)
            except Exception:
                pass
        self._setup_text_triggers()
        self.status.emit("Горячие клавиши обновлены")

    def _setup_text_triggers(self):
        if keyboard is None:
            return
        triggers = [b for b in self.binds if b.enabled and b.kind == "text" and b.key.strip()]
        if not triggers:
            return

        def on_key(e):
            if self._injecting or not self.enabled:
                return
            name = (e.name or "").lower()
            if name in ("space", "enter", "tab"):
                self._text_buffer += " "
            elif len(name) == 1:
                self._text_buffer += name
            elif name == "backspace":
                self._text_buffer = self._text_buffer[:-1]
            else:
                return
            self._text_buffer = self._text_buffer[-120:]
            for b in triggers:
                trig = b.key.strip().lower()
                if trig and self._text_buffer.endswith(trig):
                    try:
                        self._injecting = True
                        for _ in range(len(trig)):
                            keyboard.send("backspace")
                        keyboard.write(b.text, delay=0.0)
                        self._text_buffer = ""
                    finally:
                        self._injecting = False

        try:
            self._text_hook = keyboard.on_release(on_key)
        except Exception:
            self._text_hook = None

    def _fire(self, b: Bind):
        if not self.enabled:
            return
        try:
            if b.mode == "type" or pyperclip is None:
                if keyboard is not None:
                    keyboard.write(b.text, delay=0.0)
            else:
                # paste mode
                pyperclip.copy(b.text)
                if keyboard is not None:
                    keyboard.send("ctrl+v")
        except Exception:
            pass

# ---------- Pages ----------
class BindsPage(QtWidgets.QWidget):
    def __init__(self, mw: 'MainWindow'):
        super().__init__()
        self.mw = mw

        top = QtWidgets.QHBoxLayout()
        self.cmb_cat = QtWidgets.QComboBox()
        self.cmb_cat.currentTextChanged.connect(self.refresh)
        btn_cat = QtWidgets.QPushButton("Категории")
        try:
            btn_cat.clicked.connect(self.mw.open_categories)
        except Exception:
            pass

        top.addWidget(QtWidgets.QLabel("Категория:"))
        top.addWidget(self.cmb_cat, 1)
        top.addWidget(btn_cat)
        top.addStretch(1)

        self.table = QtWidgets.QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["★","Категория","Тип","Триггер","Режим","Вкл","Текст (превью)"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.cellClicked.connect(self._cell_clicked)
        self.table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._open_context_menu)

        btns1 = QtWidgets.QHBoxLayout()
        self.btn_add = QtWidgets.QPushButton("Добавить"); self.btn_add.setIcon(icon_svg("add"))
        self.btn_edit = QtWidgets.QPushButton("Редактировать"); self.btn_edit.setIcon(icon_svg("edit"))
        self.btn_del = QtWidgets.QPushButton("Удалить"); self.btn_del.setIcon(icon_svg("delete"))
        self.btn_dup = QtWidgets.QPushButton("Дублировать"); self.btn_dup.setIcon(icon_svg("copy"))
        self.btn_copy = QtWidgets.QPushButton("Copy"); self.btn_copy.setIcon(icon_svg("copy"))
        self.btn_toggle_table = QtWidgets.QPushButton("Свернуть список")
        self.btn_del.setObjectName("Danger")
        btns1.addWidget(self.btn_add)
        btns1.addWidget(self.btn_edit)
        btns1.addWidget(self.btn_del)
        btns1.addWidget(self.btn_dup)
        btns1.addWidget(self.btn_copy)
        btns1.addWidget(self.btn_toggle_table)
        btns1.addStretch(1)

        self.btn_engine = QtWidgets.QPushButton("Бинды включены")
        self.btn_engine.setCheckable(True)
        self.btn_engine.setChecked(True)

        btns2 = QtWidgets.QHBoxLayout()
        self.btn_mass_on = QtWidgets.QPushButton("Вкл выбранные")
        self.btn_mass_off = QtWidgets.QPushButton("Выкл выбранные")
        self.btn_mass_move = QtWidgets.QPushButton("Переместить в…")
        btns2.addWidget(self.btn_engine)
        btns2.addSpacing(12)
        btns2.addWidget(self.btn_mass_on)
        btns2.addWidget(self.btn_mass_off)
        btns2.addWidget(self.btn_mass_move)
        btns2.addStretch(1)

        self.table_card = QtWidgets.QFrame()
        self.table_card.setObjectName("Card")
        table_lay = QtWidgets.QVBoxLayout(self.table_card)
        table_lay.setContentsMargins(10, 10, 10, 10)
        table_lay.addWidget(self.table)
        self._table_expanded = True

        lay = QtWidgets.QVBoxLayout(self)
        lay.addLayout(top)
        lay.addWidget(self.table_card, 1)
        lay.addLayout(btns1)
        lay.addLayout(btns2)

        self.btn_add.clicked.connect(self.add_bind)
        self.btn_edit.clicked.connect(self.edit_bind)
        self.btn_del.clicked.connect(self.delete_binds)
        self.btn_dup.clicked.connect(self.duplicate_bind)
        self.btn_copy.clicked.connect(self.copy_bind)
        self.btn_toggle_table.clicked.connect(self.toggle_table)
        self.btn_engine.toggled.connect(self._toggle_engine)
        self.btn_mass_on.clicked.connect(lambda: self.mass_enable(True))
        self.btn_mass_off.clicked.connect(lambda: self.mass_enable(False))
        self.btn_mass_move.clicked.connect(self.mass_move)

    def setup_categories(self, cats: list[str]):
        self.cmb_cat.blockSignals(True)
        self.cmb_cat.clear()
        self.cmb_cat.addItem("Все")
        for c in cats:
            if c != "Все":
                self.cmb_cat.addItem(c)
        self.cmb_cat.blockSignals(False)

    def refresh(self):
        old_geom = self.table.geometry()
        self.table.setRowCount(0)
        cat = self.cmb_cat.currentText()
        binds = self.mw.binds
        if cat and cat != "Все":
            binds = [b for b in binds if b.category == cat]
        binds = sorted(binds, key=lambda b: (not b.favorite, b.category, b.key))
        for b in binds:
            r = self.table.rowCount()
            self.table.insertRow(r)
            star = QtWidgets.QTableWidgetItem("★" if b.favorite else "☆")
            star.setTextAlignment(QtCore.Qt.AlignCenter)
            self.table.setItem(r, 0, star)
            self.table.setItem(r, 1, QtWidgets.QTableWidgetItem(b.category))
            self.table.setItem(r, 2, QtWidgets.QTableWidgetItem(b.kind))
            self.table.setItem(r, 3, QtWidgets.QTableWidgetItem(b.key))
            self.table.setItem(r, 4, QtWidgets.QTableWidgetItem(b.mode))
            status = QtWidgets.QTableWidgetItem("●" if b.enabled else "●")
            status.setTextAlignment(QtCore.Qt.AlignCenter)
            status.setForeground(QtGui.QBrush(QtGui.QColor(90, 230, 140) if b.enabled else QtGui.QColor(255, 120, 120)))
            self.table.setItem(r, 5, status)
            prev = (b.text or "").replace("\n","  ")
            if len(prev) > 80:
                short = prev[:80] + "…"
            else:
                short = prev
            item = QtWidgets.QTableWidgetItem(short)
            item.setToolTip(prev)
            self.table.setItem(r, 6, item)
        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setSectionResizeMode(6, QtWidgets.QHeaderView.Stretch)
        self._animate_table_reorder(old_geom)

    def _animate_table_reorder(self, old_geom: QtCore.QRect):
        try:
            new_geom = self.table.geometry()
            if old_geom == new_geom:
                return
            ghost = QtWidgets.QLabel(self.table.parentWidget())
            pm = self.table.grab()
            ghost.setPixmap(pm)
            ghost.setGeometry(old_geom)
            ghost.show()
            anim = QtCore.QPropertyAnimation(ghost, b"geometry", ghost)
            anim.setDuration(200)
            anim.setStartValue(old_geom)
            anim.setEndValue(new_geom)
            anim.setEasingCurve(QtCore.QEasingCurve.OutCubic)
            anim.start(QtCore.QAbstractAnimation.DeleteWhenStopped)
            QtCore.QTimer.singleShot(220, ghost.deleteLater)
        except Exception:
            pass

    def selected_indices(self) -> list[int]:
        rows = sorted({i.row() for i in self.table.selectionModel().selectedRows()})
        if not rows:
            return []
        # map visible rows to real binds by key+text matching (stable)
        cat = self.cmb_cat.currentText()
        visible = self.mw.binds if (cat=="Все" or not cat) else [b for b in self.mw.binds if b.category==cat]
        visible = sorted(visible, key=lambda b: (not b.favorite, b.category, b.key))
        visible = sorted(visible, key=lambda b: (not b.favorite, b.category, b.key))
        out = []
        for r in rows:
            if 0 <= r < len(visible):
                b = visible[r]
                # find in global list
                for i, gb in enumerate(self.mw.binds):
                    if gb is b:
                        out.append(i); break
        return out

    def _cell_clicked(self, row: int, col: int):
        if col != 0:
            return
        cat = self.cmb_cat.currentText()
        visible = self.mw.binds if (cat=="Все" or not cat) else [b for b in self.mw.binds if b.category==cat]
        if 0 <= row < len(visible):
            b = visible[row]
            b.favorite = not b.favorite
            self.mw.save_all()
            self.refresh()
            self._flash_row(row)
            self._sparkle(row, col)
            Anim.bounce(self.table, 140)

    def _sparkle(self, row: int, col: int):
        try:
            rect = self.table.visualItemRect(self.table.item(row, col))
            lbl = QtWidgets.QLabel("★", self.table.viewport())
            lbl.setStyleSheet("QLabel{color: rgba(255,255,255,0.9); font-size: 18px;}")
            lbl.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)
            start = rect.center() - QtCore.QPoint(6, 6)
            lbl.move(start)
            lbl.show()
            eff = QtWidgets.QGraphicsOpacityEffect(lbl)
            lbl.setGraphicsEffect(eff)
            eff.setOpacity(0.0)
            a1 = QtCore.QPropertyAnimation(eff, b"opacity", lbl)
            a1.setStartValue(0.0); a1.setKeyValueAt(0.4, 1.0); a1.setEndValue(0.0)
            a1.setDuration(420)
            a2 = QtCore.QPropertyAnimation(lbl, b"pos", lbl)
            a2.setStartValue(start); a2.setEndValue(start - QtCore.QPoint(0, 18))
            a2.setDuration(420)
            group = QtCore.QParallelAnimationGroup(lbl)
            group.addAnimation(a1); group.addAnimation(a2)
            group.start(QtCore.QAbstractAnimation.DeleteWhenStopped)
            QtCore.QTimer.singleShot(450, lbl.deleteLater)
        except Exception:
            pass

    def _open_context_menu(self, pos: QtCore.QPoint):
        menu = QtWidgets.QMenu(self)
        smooth_menu(menu)
        act_edit = menu.addAction("Редактировать")
        act_del = menu.addAction("Удалить")
        act_dup = menu.addAction("Дублировать")
        act_copy = menu.addAction("Copy")
        menu.aboutToShow.connect(lambda: Anim.menu_pop(menu))
        action = menu.exec(self.table.viewport().mapToGlobal(pos))
        if action == act_edit:
            self.edit_bind()
        elif action == act_del:
            self.delete_binds()
        elif action == act_dup:
            self.duplicate_bind()
        elif action == act_copy:
            self.copy_bind()

    def _flash_row(self, row: int):
        try:
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item:
                    item.setBackground(QtGui.QColor(255, 255, 255, 30))
            QtCore.QTimer.singleShot(180, lambda: self.refresh())
        except Exception:
            pass

    def add_bind(self):
        dlg = BindEditor(self.mw.get_theme, self.mw, None, self.mw.categories)
        if dlg.exec() == QtWidgets.QDialog.Accepted and dlg.result_bind:
            Anim.fade(self.table_card, 1.0, 0.0, 120)
            self.mw.binds.append(dlg.result_bind)
            if dlg.result_bind.category not in self.mw.categories:
                self.mw.categories.append(dlg.result_bind.category)
            self.mw.save_all()
            self.mw.engine.apply_binds(self.mw.binds)
            self.setup_categories(self.mw.categories)
            QtCore.QTimer.singleShot(120, self._finish_add)

    def _finish_add(self):
        self.refresh()
        Anim.pop(self.table, 160)
        Anim.fade(self.table_card, 0.0, 1.0, 160)

    def edit_bind(self):
        idxs = self.selected_indices()
        if len(idxs) != 1:
            return
        i = idxs[0]
        dlg = BindEditor(self.mw.get_theme, self.mw, self.mw.binds[i], self.mw.categories)
        if dlg.exec() == QtWidgets.QDialog.Accepted and dlg.result_bind:
            self.mw.binds[i] = dlg.result_bind
            if dlg.result_bind.category not in self.mw.categories:
                self.mw.categories.append(dlg.result_bind.category)
            self.mw.save_all()
            self.mw.engine.apply_binds(self.mw.binds)
            self.setup_categories(self.mw.categories)
            self.refresh()

    def delete_binds(self):
        idxs = self.selected_indices()
        if not idxs:
            return
        idxs = sorted(idxs, reverse=True)
        dlg = ConfirmDialog(self.mw.get_theme, self, "Удалить", f"Удалить выбранные бинды: {len(idxs)}?")
        if dlg.exec() != QtWidgets.QDialog.Accepted:
            return
        Anim.fade(self.table_card, 1.0, 0.0, 140)
        QtCore.QTimer.singleShot(140, lambda: self._finish_delete(idxs))

    def _finish_delete(self, idxs: list[int]):
        for i in idxs:
            self.mw.binds.pop(i)
        self.mw.save_all()
        self.mw.engine.apply_binds(self.mw.binds)
        self.refresh()
        Anim.fade(self.table_card, 0.0, 1.0, 160)
        Anim.slide_in(self.table_card, dx=8, ms=160)

    def duplicate_bind(self):
        idxs = self.selected_indices()
        if len(idxs) != 1:
            return
        b = self.mw.binds[idxs[0]]
        nb = Bind(**asdict(b))
        nb.key = b.key + "_copy"
        self.mw.binds.append(nb)
        self.mw.save_all()
        self.mw.engine.apply_binds(self.mw.binds)
        self.refresh()

    def copy_bind(self):
        idxs = self.selected_indices()
        if len(idxs) != 1:
            Toast(self, "Выбери 1 бинд.", kind="info").show_toast()
            return
        b = self.mw.binds[idxs[0]]
        if pyperclip is not None:
            pyperclip.copy(b.text)
        else:
            QtWidgets.QApplication.clipboard().setText(b.text)
        Toast(self, "Бинд скопирован ✅", kind="info").show_toast()
        Anim.bounce(self.btn_copy, 180)

    def toggle_table(self):
        try:
            start = self.table_card.maximumHeight() if self.table_card.maximumHeight() > 0 else self.table_card.height()
            if self._table_expanded:
                end = 48
                self.btn_toggle_table.setText("Развернуть список")
            else:
                end = 1000
                self.btn_toggle_table.setText("Свернуть список")
            self._table_expanded = not self._table_expanded
            anim = QtCore.QPropertyAnimation(self.table_card, b"maximumHeight", self.table_card)
            anim.setDuration(200)
            anim.setStartValue(start)
            anim.setEndValue(end)
            anim.setEasingCurve(QtCore.QEasingCurve.OutCubic)
            anim.start(QtCore.QAbstractAnimation.DeleteWhenStopped)
        except Exception:
            pass

    def mass_enable(self, on: bool):
        idxs = self.selected_indices()
        if not idxs:
            return
        for i in idxs:
            self.mw.binds[i].enabled = on
        self.mw.save_all()
        self.mw.engine.apply_binds(self.mw.binds)
        self.refresh()

    def mass_move(self):
        idxs = self.selected_indices()
        if not idxs:
            return
        cat, ok = QtWidgets.QInputDialog.getItem(self, "Категория", "Переместить в категорию:", self.mw.categories, 0, False)
        if not ok or not cat:
            return
        for i in idxs:
            self.mw.binds[i].category = cat
        self.mw.save_all()
        self.refresh()

    def _toggle_engine(self, on: bool):
        self.btn_engine.setText("Бинды включены" if on else "Бинды выключены")
        self.mw.engine.set_enabled(on)
        Anim.bounce(self.btn_engine, 180)

class ContentPage(QtWidgets.QWidget):
    def __init__(self, mw: 'MainWindow', area: str, title: str, add_label: str):
        super().__init__()
        self.mw = mw
        self.area = area
        self.setObjectName(area)
        self.db = mw.content_db
        self.current_cat = self.db.categories(area)[0]
        self.only_today = False
        head = QtWidgets.QHBoxLayout()
        lbl = QtWidgets.QLabel(title); lbl.setObjectName("Title")
        head.addWidget(lbl)
        head.addStretch(1)
        self.stats = QtWidgets.QLabel("")
        self.stats.setObjectName("Hint")
        head.addWidget(self.stats)
        head.addSpacing(16)

        head.addSpacing(16)

        self.chk_today = QtWidgets.QCheckBox("Не использовался сегодня")
        self.chk_today.toggled.connect(self._set_today)
        head.addWidget(self.chk_today)

        head.addSpacing(12)
        head.addWidget(QtWidgets.QLabel("Категория:"))
        self.cmb = QtWidgets.QComboBox()
        self.cmb.addItems(self.db.categories(area))
        self.cmb.currentTextChanged.connect(self._cat_changed)
        head.addWidget(self.cmb)

        self.btn_menu = QtWidgets.QToolButton()
        self.btn_menu.setText("Меню")
        self.btn_menu.setIcon(icon_svg("menu"))
        self.btn_menu.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self.menu = QtWidgets.QMenu(self)
        smooth_menu(self.menu)
        self.btn_menu.setMenu(self.menu)
        self.menu.aboutToShow.connect(lambda: Anim.menu_pop(self.menu))
        self.act_add = self.menu.addAction(add_label)
        self.act_import = self.menu.addAction("Импорт JSON…")
        self.act_export = self.menu.addAction("Экспорт JSON…")
        self.menu.addSeparator()
        self.act_edit = self.menu.addAction("Редактировать выбранный")
        self.act_del = self.menu.addAction("Удалить выбранный")

        head.addWidget(self.btn_menu)

        self.lst = QtWidgets.QListWidget()
        self.preview = QtWidgets.QPlainTextEdit()
        self.preview.setReadOnly(True)
        self.hint = QtWidgets.QLabel("Подсказка по контенту: —")
        self.hint.setObjectName("Hint")
        self.stats = QtWidgets.QLabel("")
        self.stats.setObjectName("Hint")

        self.btn_random = QtWidgets.QPushButton("Случайный текст")
        self.btn_copy = QtWidgets.QPushButton("COPY"); self.btn_copy.setIcon(icon_svg("copy"))
        self.btn_toggle_preview = QtWidgets.QPushButton("Свернуть просмотр")

        bottom = QtWidgets.QHBoxLayout()
        bottom.addWidget(self.btn_random)
        bottom.addStretch(1)
        bottom.addWidget(self.btn_copy)
        bottom.addWidget(self.btn_toggle_preview)

        grid = QtWidgets.QGridLayout()
        grid.addLayout(head, 0, 0, 1, 2)
        grid.addWidget(QtWidgets.QLabel("Список:"), 1, 0)
        grid.addWidget(QtWidgets.QLabel("Просмотр:"), 1, 1)
        list_card = QtWidgets.QFrame()
        list_card.setObjectName("Card")
        list_lay = QtWidgets.QVBoxLayout(list_card)
        list_lay.setContentsMargins(10, 10, 10, 10)
        list_lay.addWidget(self.lst)

        self.prev_card = QtWidgets.QFrame()
        self.prev_card.setObjectName("Card")
        prev_lay = QtWidgets.QVBoxLayout(self.prev_card)
        prev_lay.setContentsMargins(10, 10, 10, 10)
        prev_lay.addWidget(self.preview)
        self._preview_expanded = True

        grid.addWidget(list_card, 2, 0)
        grid.addWidget(self.prev_card, 2, 1)
        grid.addWidget(self.hint, 3, 1)
        grid.addLayout(bottom, 4, 0, 1, 2)
        grid.setRowStretch(2, 1)
        grid.setColumnStretch(1, 2)

        self.setLayout(grid)

        self.lst.currentRowChanged.connect(self._sel_changed)
        self.btn_random.clicked.connect(self.pick_random)
        self.btn_copy.clicked.connect(self.copy_current)
        self.btn_toggle_preview.clicked.connect(self.toggle_preview)

        self.act_add.triggered.connect(self.add_item)
        self.act_import.triggered.connect(self.import_items)
        self.act_export.triggered.connect(self.export_items)
        self.act_edit.triggered.connect(self.edit_item)
        self.act_del.triggered.connect(self.delete_item)

        self.refresh()

    def _set_today(self, on: bool):
        self.only_today = bool(on)
        self.refresh()

    def toggle_preview(self):
        try:
            start = self.prev_card.maximumHeight() if self.prev_card.maximumHeight() > 0 else self.prev_card.height()
            if self._preview_expanded:
                end = 40
                self.btn_toggle_preview.setText("Развернуть просмотр")
            else:
                end = 1000
                self.btn_toggle_preview.setText("Свернуть просмотр")
            self._preview_expanded = not self._preview_expanded
            anim = QtCore.QPropertyAnimation(self.prev_card, b"maximumHeight", self.prev_card)
            anim.setDuration(200)
            anim.setStartValue(start)
            anim.setEndValue(end)
            anim.setEasingCurve(QtCore.QEasingCurve.OutCubic)
            anim.start(QtCore.QAbstractAnimation.DeleteWhenStopped)
        except Exception:
            pass

    def _cat_changed(self, cat: str):
        self.current_cat = cat
        self.refresh()

    def _items_filtered(self) -> list[dict]:
        items = self.db.items(self.area, self.current_cat)
        if not self.only_today:
            return items
        tk = today_key()
        return [it for it in items if int((it.get("uses_by_day") or {}).get(tk) or 0) == 0]

    def refresh(self):
        self.lst.clear()
        items = self._items_filtered()
        for it in items:
            txt = (it.get("text") or "").replace("\n"," ")
            short = txt[:60] + "…" if len(txt) > 60 else txt
            item = QtWidgets.QListWidgetItem(short)
            self.lst.addItem(item)
        self.preview.setPlainText("")
        self.hint.setText("Подсказка по контенту: —")
        self._update_stats()

    def _update_stats(self):
        items = self.db.items(self.area, self.current_cat)
        tk = today_key()
        used_today = sum(1 for it in items if int((it.get("uses_by_day") or {}).get(tk) or 0) > 0)
        total = len(items)
        copies = sum(int(it.get("copies_total") or 0) for it in items)
        self.stats.setText(f"Статистика: {total} шт • использовано сегодня: {used_today} • всего копий: {copies}")

    def _current_item(self) -> Optional[dict]:
        row = self.lst.currentRow()
        items = self._items_filtered()
        if 0 <= row < len(items):
            return items[row]
        return None

    def _sel_changed(self, row: int):
        it = self._current_item()
        if not it:
            self.preview.setPlainText("")
            self.hint.setText("Подсказка по контенту: —")
            return
        self.preview.setPlainText(it.get("text") or "")
        hint = it.get("hint") or "—"
        self.hint.setText(f"Подсказка по контенту: {hint}")

    def add_item(self):
        dlg = TextEditor(self.mw.get_theme, self.mw, "Добавить", "", "")
        if dlg.exec() == QtWidgets.QDialog.Accepted:
            text, hint = dlg.get()
            if text.strip():
                self.db.add(self.area, self.current_cat, text, hint)
                self.refresh()
                Anim.pop(self.lst, 160)

    def edit_item(self):
        it = self._current_item()
        if not it:
            return
        dlg = TextEditor(self.mw.get_theme, self.mw, "Редактировать", it.get("text",""), it.get("hint",""))
        if dlg.exec() == QtWidgets.QDialog.Accepted:
            text, hint = dlg.get()
            self.db.update(self.area, self.current_cat, it["id"], text, hint)
            self.refresh()

    def delete_item(self):
        it = self._current_item()
        if not it:
            return
        dlg = ConfirmDialog(self.mw.get_theme, self, "Удалить", "Удалить выбранный текст?")
        if dlg.exec() != QtWidgets.QDialog.Accepted:
            return
        self.db.delete(self.area, self.current_cat, it["id"])
        self.refresh()
        Anim.fade(self.lst, 0.0, 1.0, 160)

    def pick_random(self):
        it = self.db.pick_random(self.area, self.current_cat, self.only_today)
        if not it:
            return
        # select it in filtered list
        items = self._items_filtered()
        for i, x in enumerate(items):
            if x.get("id") == it.get("id"):
                self.lst.setCurrentRow(i)
                break

    def copy_current(self):
        it = self._current_item()
        if not it:
            return
        text = it.get("text","")
        if pyperclip is not None:
            pyperclip.copy(text)
        else:
            QtWidgets.QApplication.clipboard().setText(text)
        self.db.mark_used(self.area, self.current_cat, it["id"], as_copy=True)
        self._update_stats()
        Toast(self, "Скопировано ✅", kind="info").show_toast()
        Anim.bounce(self.btn_copy, 180)

    def import_items(self):
        fn, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Импорт JSON", "", "JSON (*.json)")
        if not fn:
            return
        n = self.db.import_json(self.area, self.current_cat, Path(fn))
        Toast(self, f"Добавлено: {n}", kind="info").show_toast()
        self.refresh()

    def export_items(self):
        fn, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Экспорт JSON", f"{self.area}_{self.current_cat}.json", "JSON (*.json)")
        if not fn:
            return
        self.db.export_json(self.area, self.current_cat, Path(fn))
        Toast(self, "Экспорт завершён", kind="info").show_toast()

class PricePage(QtWidgets.QWidget):
    def __init__(self, mw: 'MainWindow'):
        super().__init__()
        self.mw = mw
        lay = QtWidgets.QVBoxLayout(self)
        lbl = QtWidgets.QLabel("Прайс"); lbl.setObjectName("Title")
        self.text = QtWidgets.QPlainTextEdit()
        self.text.setReadOnly(True)
        card = QtWidgets.QFrame()
        card.setObjectName("Card")
        card_lay = QtWidgets.QVBoxLayout(card)
        card_lay.setContentsMargins(10, 10, 10, 10)
        card_lay.addWidget(self.text)
        lay.addWidget(lbl)
        lay.addWidget(card, 1)
        self.reload()

    def reload(self):
        self.text.setPlainText(load_price_text())

# ---------- Sidebar ----------
class Sidebar(QtWidgets.QFrame):
    def __init__(self):
        super().__init__()
        self.setFixedWidth(190)
        self.setStyleSheet("QFrame{background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.10); border-radius: 16px;}")
        self.l = QtWidgets.QVBoxLayout(self)
        self.l.setContentsMargins(10, 10, 10, 10)
        self.l.setSpacing(10)
        self._buttons: list[QtWidgets.QToolButton] = []
        self._indicator = QtWidgets.QFrame(self)
        self._indicator.setStyleSheet(
            "QFrame{background: rgba(255,255,255,0.12); border: 1px solid rgba(255,255,255,0.28); border-radius: 14px;}"
        )
        self._indicator.hide()

    def add_btn(self, text: str, icon_char: str, cb):
        b = QtWidgets.QToolButton()
        b.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        b.setText(text)
        icon_map = {"Бинды": "copy", "PPV": "search", "Рассылка": "edit", "Прайс": "dollar"}
        if text in icon_map:
            b.setIcon(icon_svg(icon_map[text]))
        b.clicked.connect(lambda: (self.set_active(b), cb()))
        b.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.l.addWidget(b)
        self._buttons.append(b)
        self._indicator.lower()
        return b

    def set_active(self, btn: QtWidgets.QToolButton):
        if btn not in self._buttons:
            return
        g = btn.geometry()
        target = QtCore.QRect(g.x() - 4, g.y() - 3, g.width() + 8, g.height() + 6)
        if not self._indicator.isVisible():
            self._indicator.setGeometry(target)
            self._indicator.show()
            return
        anim = QtCore.QPropertyAnimation(self._indicator, b"geometry", self)
        anim.setDuration(180)
        anim.setStartValue(self._indicator.geometry())
        anim.setEndValue(target)
        anim.setEasingCurve(QtCore.QEasingCurve.OutCubic)
        anim.start(QtCore.QAbstractAnimation.DeleteWhenStopped)

# ---------- Splash ----------
class Splash(GlassDialog):
    def __init__(self, get_theme, parent=None):
        super().__init__(get_theme, parent, 520, 220, "Запуск whybinder")
        lay = QtWidgets.QVBoxLayout(self.body)
        self.lbl = QtWidgets.QLabel("Подготовка…")
        self.lbl.setObjectName("Title")
        self.lbl.setWordWrap(True)
        lay.addWidget(self.lbl)
        self.hint = QtWidgets.QLabel("Проверяю файлы и компоненты…")
        self.hint.setObjectName("Hint")
        self.hint.setWordWrap(True)
        lay.addWidget(self.hint)

        self.bar = QtWidgets.QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setValue(0)
        self.bar.setTextVisible(True)
        self.bar.setFormat("%p%")
        self.bar.setFixedHeight(18)
        lay.addSpacing(8)
        lay.addWidget(self.bar)

        lay.addStretch(1)

    def set_message(self, msg: str):
        self.hint.setText(str(msg))

    def set_progress(self, val: int):
        try:
            self.bar.setValue(int(val))
        except Exception:
            pass


def set_status(self, txt: str, pct: int):
    try:
        if hasattr(self, "sub"):
            self.sub.setText(txt)
        elif hasattr(self, "lbl"):
            self.lbl.setText(txt)
    except Exception:
        pass
    try:
        if hasattr(self, "bar"):
            self.bar.setValue(int(max(0, min(100, pct))))
    except Exception:
        pass
    try:
        QtWidgets.QApplication.processEvents()
    except Exception:
        pass

class MainWindow(QtWidgets.QWidget):
    def __init__(self, g: dict):
        super().__init__()
        self._closing = False
        self.g = g
        self._theme = self.g.get("theme", "Ametrine")

        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(1100, 720)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.Window)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)

        self.root = GlassRoot(self.get_theme, self)

        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self.root)

        rlay = QtWidgets.QVBoxLayout(self.root)
        rlay.setContentsMargins(14, 14, 14, 14)
        rlay.setSpacing(12)

        # Titlebar
        self.titlebar = TitleBar(self.root)
        self.titlebar.btn_close.clicked.connect(self.close)
        self.titlebar.btn_min.clicked.connect(self.showMinimized)
        self.titlebar.btn_theme.clicked.connect(self.open_theme_menu)
        rlay.addWidget(self.titlebar)

        # Top controls row
        head = QtWidgets.QHBoxLayout()
        self.btn_menu = QtWidgets.QToolButton()
        self.btn_menu.setText("Меню")
        self.btn_menu.setIcon(icon_svg("menu"))
        self.btn_menu.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        head.addWidget(self.btn_menu)
        head.addStretch(1)
        head.addWidget(QtWidgets.QLabel("Профиль:"))
        self.cmb_profile = QtWidgets.QComboBox()
        self.cmb_profile.addItems(DEFAULT_PROFILES)
        self.cmb_profile.setCurrentText(self.g.get("profile", DEFAULT_PROFILES[0]))
        head.addWidget(self.cmb_profile)
        rlay.addLayout(head)

        # Layout: sidebar + stack
        mid = QtWidgets.QHBoxLayout()
        self.sidebar = Sidebar()
        mid.addWidget(self.sidebar)
        mid.addSpacing(12)
        self.stack = QtWidgets.QStackedWidget()
        mid.addWidget(self.stack, 1)
        rlay.addLayout(mid, 1)

        # Status
        self.status = QtWidgets.QLabel("")
        self.status.setObjectName("Hint")
        rlay.addWidget(self.status)

        # Data
        self.content_db = ContentDB(CONTENT_DB_FILE)
        self.categories, self.binds = load_profile(self.cmb_profile.currentText())

        # Engine
        self.engine = BinderEngine()
        self.engine.status.connect(self.set_status)
        self.engine.apply_binds(self.binds)
        self.engine.set_enabled(True)

        # Pages
        self.page_binds = BindsPage(self)
        self.page_ppv = ContentPage(self, "ppv", "PPV", "Добавить PPV")
        self.page_mail = ContentPage(self, "mailing", "Рассылка", "Добавить рассылку")
        self.page_price = PricePage(self)

        self.stack.addWidget(self.page_binds)
        self.stack.addWidget(self.page_ppv)
        self.stack.addWidget(self.page_mail)
        self.stack.addWidget(self.page_price)

        # Sidebar navigation (no emojis)
        self.btn_binds = self.sidebar.add_btn("Бинды", "", lambda: self.switch_page(self.page_binds))
        btn_ppv = self.sidebar.add_btn("PPV", "", lambda: self.switch_page(self.page_ppv))
        btn_mail = self.sidebar.add_btn("Рассылка", "", lambda: self.switch_page(self.page_mail))
        btn_price = self.sidebar.add_btn("Прайс", "", lambda: (self.page_price.reload(), self.switch_page(self.page_price)))
        self.sidebar.l.addStretch(1)
        QtCore.QTimer.singleShot(0, lambda: self.sidebar.set_active(self.btn_binds))

        # Menu
        self.menu = QtWidgets.QMenu(self)
        smooth_menu(self.menu)
        self.act_share = self.menu.addAction("Поделиться выбранным биндом (код)")
        self.act_import = self.menu.addAction("Импорт бинда (код)…")
        self.menu.addSeparator()
        self.act_spotlight = self.menu.addAction("Поиск (Spotlight)")
        self.act_onboarding = self.menu.addAction("Мастер новичка")
        self.act_profile_overlay = self.menu.addAction("Оверлей профиля")
        self.act_categories = self.menu.addAction("Категории…")
        self.menu.addSeparator()
        theme_menu = self.menu.addMenu("Тема")
        smooth_menu(theme_menu)
        self.act_theme_preview = self.menu.addAction("Color preview темы")
        self.act_theme_preview.triggered.connect(self.open_theme_preview)
        for name in THEMES.keys():
            a = theme_menu.addAction(name)
            a.triggered.connect(lambda checked=False, n=name: self.set_theme(n))
        dens_menu = self.menu.addMenu("Плотность")
        smooth_menu(dens_menu)
        self.act_dense_compact = dens_menu.addAction("Compact")
        self.act_dense_comfy = dens_menu.addAction("Comfortable")
        self.menu.addSeparator()
        self.act_open_log = self.menu.addAction("Открыть лог")
        self.act_about = self.menu.addAction("О приложении")

        self.btn_menu.setMenu(self.menu)
        self.menu.aboutToShow.connect(lambda: Anim.menu_pop(self.menu))
        theme_menu.aboutToShow.connect(lambda: Anim.menu_pop(theme_menu))
        dens_menu.aboutToShow.connect(lambda: Anim.menu_pop(dens_menu))

        # Connect menu actions
        try:

            self.act_open_log.triggered.connect(self.open_log)

        except Exception:

            pass
        try:

            self.act_about.triggered.connect(self.show_about)

        except Exception:

            pass
        self.act_categories.triggered.connect(self.open_categories)
        self.act_spotlight.triggered.connect(self.open_spotlight)
        self.act_onboarding.triggered.connect(self.open_onboarding)
        self.act_profile_overlay.triggered.connect(self.toggle_profile_overlay)
        self.act_spotlight.setShortcut("Ctrl+K")
        self.act_dense_compact.triggered.connect(lambda: self.set_density("compact"))
        self.act_dense_comfy.triggered.connect(lambda: self.set_density("comfortable"))
        try:

            self.act_share.triggered.connect(self.share_selected_bind)

        except Exception:

            pass
        try:

            self.act_import.triggered.connect(self.import_bind_code)

        except Exception:

            pass

        # Connect profile switch
        self.cmb_profile.currentTextChanged.connect(self.switch_profile)

        # Init binds page
        self.page_binds.setup_categories(self.categories)
        self.page_binds.refresh()

        # Show animation
        Anim.fade(self, 0.0, 1.0, 220)
        self._glow = None

    # --- Helpers ---
    def get_theme(self) -> str:
        return self._theme

    def set_status(self, s: str):
        self.status.setText(str(s))

    def showEvent(self, e):
        super().showEvent(e)
        try:
            geo = self.frameGeometry()
            center = QtGui.QGuiApplication.primaryScreen().availableGeometry().center()
            geo.moveCenter(center)
            self.move(geo.topLeft())
        except Exception:
            pass
        try:
            QtCore.QTimer.singleShot(0, lambda: self.sidebar.set_active(self.btn_binds))
        except Exception:
            pass
        try:
            if not self.g.get("onboarding_seen", False):
                self._onboarding = OnboardingOverlay(self)
                self._onboarding.btn_skip.clicked.connect(self._finish_onboarding)
        except Exception:
            pass

    def _finish_onboarding(self):
        try:
            self.g["onboarding_seen"] = True
            save_settings(self.g)
        except Exception:
            pass

    def closeEvent(self, e: QtGui.QCloseEvent):
        if self._closing:
            e.accept()
            return
        self._closing = True
        try:
            Anim.fade(self, 1.0, 0.0, 180)
            Anim.slide_out(self, dy=12, ms=180)
        except Exception:
            pass
        e.ignore()
        QtCore.QTimer.singleShot(200, self.close)

    def switch_page(self, w: QtWidgets.QWidget):
        cur = self.stack.currentWidget()
        if cur is w:
            return
        try:
            Anim.fade(cur, 1.0, 0.0, 120)
        except Exception:
            pass
        self.stack.setCurrentWidget(w)
        try:
            Anim.fade(w, 0.0, 1.0, 180)
            Anim.slide_in(w, dx=16, ms=180)
            Anim.motion_blur(w, 180)
        except Exception:
            pass

    def open_theme_menu(self):
        m = QtWidgets.QMenu(self)
        smooth_menu(m)
        for name in THEMES.keys():
            act = m.addAction(name)
            act.triggered.connect(lambda checked=False, n=name: self.set_theme(n))
        m.aboutToShow.connect(lambda: Anim.menu_pop(m))
        m.exec(QtGui.QCursor.pos())

    def set_theme(self, name: str):
        self._theme = str(name)
        self.g["theme"] = self._theme
        save_settings(self.g)
        QtWidgets.QApplication.instance().setStyleSheet(
            app_stylesheet(self._theme, self.g.get("density", "comfortable"))
        )
        self._theme_colors = THEMES.get(self._theme, THEMES["Ametrine"])
        try:
            Anim.fade(self.root, 0.0, 1.0, 220)
            Anim.slide_in(self.root, dx=10, ms=220)
        except Exception:
            pass
        self.root.update()


    def set_density(self, density: str):
        self.g["density"] = density
        save_settings(self.g)
        QtWidgets.QApplication.instance().setStyleSheet(
            app_stylesheet(self._theme, self.g.get("density", "comfortable"))
        )

    def open_spotlight(self):
        dlg = SpotlightDialog(self)
        dlg.exec()

    def open_onboarding(self):
        try:
            self._onboarding = OnboardingOverlay(self)
        except Exception:
            pass

    def open_theme_preview(self):
        try:
            t = THEMES.get(self._theme, THEMES["Ametrine"])
            dlg = GlassDialog(self.get_theme, self, 420, 260, "Color preview")
            lay = QtWidgets.QVBoxLayout(dlg.body)
            grid = QtWidgets.QGridLayout()
            labels = {
                "accent": "Акцент",
                "surface": "Поверхность",
                "bg1": "Фон 1",
                "bg2": "Фон 2",
                "bg3": "Фон 3",
            }
            for i, key in enumerate(["accent", "surface", "bg1", "bg2", "bg3"]):
                sw = QtWidgets.QFrame()
                sw.setFixedSize(48, 24)
                sw.setStyleSheet(f"QFrame{{background:{t.get(key)}; border-radius:6px;}}")
                lbl = QtWidgets.QLabel(labels.get(key, key))
                row = i // 2
                col = (i % 2) * 2
                grid.addWidget(sw, row, col)
                grid.addWidget(lbl, row, col + 1)
            lay.addLayout(grid)
            btn = QtWidgets.QPushButton("Закрыть")
            btn.clicked.connect(dlg.accept)
            lay.addWidget(btn, 0, QtCore.Qt.AlignRight)
            dlg.exec()
        except Exception:
            pass


    def toggle_profile_overlay(self):
        try:
            if getattr(self, "_profile_overlay", None) and self._profile_overlay.isVisible():
                self._profile_overlay.close()
                return
            self._profile_overlay = ProfileOverlay(self)
            self._profile_overlay.show()
        except Exception:
            pass

    def save_all(self):
        save_profile(self.cmb_profile.currentText(), self.categories, self.binds)
        save_settings(self.g)

    def switch_profile(self, name: str):
        self.categories, self.binds = load_profile(name)
        self.page_binds.setup_categories(self.categories)
        self.page_binds.refresh()
        self.engine.apply_binds(self.binds)
        self.g["profile"] = name
        self.save_all()

    def open_categories(self):
        dlg = GlassDialog(self.get_theme, self, 620, 420, "Категории")
        lay = QtWidgets.QVBoxLayout(dlg.body)
        lst = QtWidgets.QListWidget()
        lst.addItems(self.categories)
        lay.addWidget(QtWidgets.QLabel("Список категорий:"))
        lay.addWidget(lst, 1)
        row = QtWidgets.QHBoxLayout()
        btn_add = QtWidgets.QPushButton("Новая")
        btn_ren = QtWidgets.QPushButton("Переименовать")
        btn_del = QtWidgets.QPushButton("Удалить")
        btn_ok = QtWidgets.QPushButton("Готово")
        row.addWidget(btn_add); row.addWidget(btn_ren); row.addWidget(btn_del); row.addStretch(1); row.addWidget(btn_ok)
        lay.addLayout(row)

        def add_cat():
            inp = InputDialog(self.get_theme, dlg, "Новая", "Название:")
            if inp.exec() == QtWidgets.QDialog.Accepted:
                name = inp.get()
                if name and name not in self.categories:
                    self.categories.append(name)
                    lst.addItem(name)

        def ren_cat():
            it = lst.currentItem()
            if not it:
                return
            old = it.text()
            inp = InputDialog(self.get_theme, dlg, "Переименовать", "Название:", text=old)
            if inp.exec() == QtWidgets.QDialog.Accepted:
                name = inp.get()
                if name and name not in self.categories:
                    self.categories = [name if c == old else c for c in self.categories]
                    for b in self.binds:
                        if b.category == old:
                            b.category = name
                    it.setText(name)

        def del_cat():
            it = lst.currentItem()
            if not it:
                return
            name = it.text()
            if name == DEFAULT_BIND_CATEGORY:
                return
            confirm = ConfirmDialog(self.get_theme, dlg, "Удалить",
                                    f"Удалить категорию «{name}»? Бинды перейдут в «{DEFAULT_BIND_CATEGORY}».")
            if confirm.exec() != QtWidgets.QDialog.Accepted:
                return
            self.categories = [c for c in self.categories if c != name]
            for b in self.binds:
                if b.category == name:
                    b.category = DEFAULT_BIND_CATEGORY
            lst.takeItem(lst.currentRow())

        btn_add.clicked.connect(add_cat)
        btn_ren.clicked.connect(ren_cat)
        btn_del.clicked.connect(del_cat)
        btn_ok.clicked.connect(dlg.accept)

        if dlg.exec() == QtWidgets.QDialog.Accepted:
            if DEFAULT_BIND_CATEGORY not in self.categories:
                self.categories.insert(0, DEFAULT_BIND_CATEGORY)
            self.save_all()
            self.page_binds.setup_categories(self.categories)
            self.page_binds.refresh()


    def open_log(self):
        try:
            path = os.path.join(DATA_DIR, "app.log")
            if not os.path.exists(path):
                with open(path, "w", encoding="utf-8") as f:
                    f.write("")
            QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(path))
        except Exception:
            Toast(self, "Не удалось открыть лог-файл.", kind="error").show_toast()

    def show_about(self):
        dlg = GlassDialog(self.get_theme, self, 680, 280, "О приложении")
        lay = QtWidgets.QVBoxLayout(dlg.body)
        t1 = QtWidgets.QLabel(APP_TITLE_1); t1.setObjectName("Title"); t1.setWordWrap(True)
        t2 = QtWidgets.QLabel(APP_TITLE_2); t2.setObjectName("Hint"); t2.setWordWrap(True)
        lay.addWidget(t1)
        lay.addWidget(t2)
        lay.addStretch(1)
        row = QtWidgets.QHBoxLayout()
        row.addStretch(1)
        ok = QtWidgets.QPushButton("OK")
        row.addWidget(ok)
        lay.addLayout(row)
        ok.clicked.connect(dlg.accept)
        dlg.exec()

    def share_selected_bind(self):
        self.switch_page(self.page_binds)
        idxs = self.page_binds.selected_indices()
        if len(idxs) != 1:
            Toast(self, "Выбери 1 бинд.", kind="info").show_toast()
            return
        b = self.binds[idxs[0]]
        code = encode_share({"type": "bind", "bind": asdict(b)})
        try:
            import pyperclip  # type: ignore
            pyperclip.copy(code)
        except Exception:
            QtWidgets.QApplication.clipboard().setText(code)
        Toast(self, "Код бинда скопирован ✅").show_toast()

    def import_bind_code(self):
        text, ok = QtWidgets.QInputDialog.getMultiLineText(self, "Импорт бинда", "Вставь код:", "")
        if not ok:
            return
        try:
            obj = decode_share(text.strip())
            if obj.get("type") != "bind":
                raise ValueError("wrong type")
            bd = obj.get("bind")
            if not isinstance(bd, dict):
                raise ValueError("bad payload")
            bd.setdefault("category", DEFAULT_BIND_CATEGORY)
            bd.setdefault("favorite", False)
            b = Bind(**bd)
            self.binds.append(b)
            if b.category not in self.categories:
                self.categories.append(b.category)
            self.save_all()
            self.page_binds.setup_categories(self.categories)
            self.page_binds.refresh()
            self.engine.apply_binds(self.binds)
        except Exception:
            Toast(self, "Код не распознан ❌").show_toast()

# ---------- Settings ----------
def load_settings() -> dict:
    s = safe_read_json(SETTINGS_FILE, {})
    if not isinstance(s, dict):
        s = {}
    s.setdefault("theme", "Ametrine")
    s.setdefault("profile", DEFAULT_PROFILES[0])
    s.setdefault("density", "comfortable")
    s.setdefault("onboarding_seen", False)
    s.pop("last_updated_tag", None)
    s.pop("pending_update_tag", None)
    return s

def save_settings(s: dict):
    safe_write_json(SETTINGS_FILE, s)

# ---------- main ----------

def main():
    QtCore.QCoreApplication.setApplicationName(APP_NAME)
    try:
        os.environ["TMP"] = str(TEMP_DIR)
        os.environ["TEMP"] = str(TEMP_DIR)
    except Exception:
        pass
    app = QtWidgets.QApplication(sys.argv)
    try:
        app.setStyle("Fusion")
    except Exception:
        pass

    setup_logging()

    g = load_settings()
    app.setStyleSheet(app_stylesheet(g.get("theme", "Ametrine"), g.get("density", "comfortable")))

    splash = Splash(lambda: g.get("theme", "Ametrine"))
    try:
        splash.setWindowModality(QtCore.Qt.NonModal)
    except Exception:
        pass
    splash.show()
    QtWidgets.QApplication.processEvents()

    def step(txt, pct):
        try:
            logging.info(txt)
        except Exception:
            pass
        try:
            if hasattr(splash, "set_status"):
                splash.set_status(txt, pct)
            else:
                if hasattr(splash, "set_message"):
                    splash.set_message(txt)
                if hasattr(splash, "bar"):
                    splash.bar.setValue(int(max(0, min(100, pct))))
                QtWidgets.QApplication.processEvents()
        except Exception:
            pass

    try:
        step("Проверяю папки/файлы…", 10)
        ensure_data_layout()
        step("Проверяю базу контента…", 30)
        pass  # ContentDB.ensure not available
        step("Проверяю прайс…", 45)
        _ = read_price_text()
        step("Проверяю зависимости…", 60)
        if keyboard is None:
            step("keyboard не найден (горячие клавиши могут не работать)", 65)
        if pyperclip is None:
            step("pyperclip не найден (использую системный буфер)", 70)

        step("Готовлю интерфейс…", 85)
        w = MainWindow(g)
        step("Запуск…", 100)

        def finish():
            try:
                splash.close()
            except Exception:
                pass
            w.show()

        QtCore.QTimer.singleShot(0, finish)
        return sys.exit(app.exec())
    except Exception as e:
        try:
            logging.exception("Fatal error")
        except Exception:
            pass
        try:
            print("FATAL:", e, file=sys.stderr)
        except Exception:
            pass
        try:
            app = QtWidgets.QApplication.instance()
            if app is not None:
                host = QtWidgets.QWidget()
                host.setWindowFlags(QtCore.Qt.Tool | QtCore.Qt.FramelessWindowHint)
                host.resize(360, 120)
                host.show()
                Toast(host, f"Ошибка запуска: {e}", kind="error").show_toast()
                QtCore.QTimer.singleShot(2200, host.close)
                app.processEvents()
        except Exception:
            pass
        raise


if __name__ == "__main__":

    main()



# --- Safety patch: ensure Splash.set_status always exists ---
def _splash_set_status(self, txt: str, pct: int):
    try:
        if hasattr(self, "sub"):
            self.sub.setText(txt)
    except Exception:
        pass
    try:
        if hasattr(self, "bar"):
            self.bar.setValue(int(max(0, min(100, pct))))
    except Exception:
        pass
    try:
        QtWidgets.QApplication.processEvents()
    except Exception:
        pass

try:
    if 'Splash' in globals() and not hasattr(Splash, "set_status"):
        Splash.set_status = _splash_set_status
except Exception:
    pass