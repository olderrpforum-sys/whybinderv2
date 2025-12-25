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

from PySide6 import QtCore, QtGui, QtWidgets

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
SETTINGS_FILE = DATA_DIR / "settings.json"
PROFILES_DIR = DATA_DIR / "profiles"
PROFILES_DIR.mkdir(parents=True, exist_ok=True)
CONTENT_DB_FILE = DATA_DIR / "content_bases.json"
PRICE_FALLBACK_FILE = DATA_DIR / "price.txt"

DEFAULT_PROFILES = ["Judi", "Eva"]
DEFAULT_BIND_CATEGORY = "Без категории"

# ---------- Themes ----------
THEMES: dict[str, dict[str, str]] = {
    "Ametrine": {"bg1": "#12062C", "bg2": "#220E70", "bg3": "#08255F", "surface": "rgba(8,6,18,0.34)", "accent": "rgba(160,120,255,0.32)"},
    "Midnight": {"bg1": "#070716", "bg2": "#101036", "bg3": "#071B3A", "surface": "rgba(0,0,0,0.42)", "accent": "rgba(120,160,255,0.28)"},
    "Pearl": {"bg1": "#EDEDF4", "bg2": "#E2E6FF", "bg3": "#D8F1FF", "surface": "rgba(255,255,255,0.58)", "accent": "rgba(80,140,255,0.22)"},
    "Emerald": {"bg1": "#061A14", "bg2": "#0B2F23", "bg3": "#08392F", "surface": "rgba(0,0,0,0.34)", "accent": "rgba(70,220,170,0.22)"},
}

def app_stylesheet(theme: str) -> str:
    t = THEMES.get(str(theme), THEMES["Ametrine"])
    accent = t["accent"]
    surface = t["surface"]

    is_light = str(theme) == "Pearl"
    text = "rgba(30,32,40,0.94)" if is_light else "rgba(250,250,255,0.96)"
    text2 = "rgba(45,48,60,0.78)" if is_light else "rgba(240,240,255,0.86)"
    menu_bg = "rgba(245,245,255,0.98)" if is_light else "rgba(12, 10, 28, 0.98)"
    menu_border = "rgba(0,0,0,0.14)" if is_light else "rgba(255,255,255,0.16)"
    btn_grad_top = "rgba(255,255,255,0.70)" if is_light else "rgba(255,255,255,0.22)"
    btn_grad_bot = "rgba(255,255,255,0.40)" if is_light else "rgba(255,255,255,0.09)"
    btn_border = "rgba(0,0,0,0.12)" if is_light else "rgba(255,255,255,0.18)"
    field_border = "rgba(0,0,0,0.12)" if is_light else "rgba(255,255,255,0.14)"
    header_bg = "rgba(0,0,0,0.06)" if is_light else "rgba(255,255,255,0.10)"

    return f"""
    QWidget {{ background: transparent; }}
    * {{
        font-family: "Segoe UI Variable", "Segoe UI", "Inter", "Arial";
        font-size: 13px;
        color: {text};
        font-weight: 800;
    }}
    QLabel#Title {{ font-size: 18px; font-weight: 900; letter-spacing: 0.2px; }}
    QLabel#Hint {{ color: {text2}; font-weight: 800; }}

    QPushButton, QToolButton {{
        font-weight: 900;
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {btn_grad_top}, stop:1 {btn_grad_bot});
        border: 1px solid {btn_border};
        padding: 10px 14px;
        border-radius: 16px;
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

    QLineEdit, QPlainTextEdit, QComboBox, QListWidget, QTableWidget {{
        background: {surface};
        border: 1px solid {field_border};
        border-radius: 12px;
        padding: 8px 10px;
        selection-background-color: {accent};
    }}
    QAbstractScrollArea::viewport {{ background: {surface}; }}

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
        border-radius: 14px;
        padding: 8px;
    }}
    QMenu::item {{ padding: 10px 14px; border-radius: 10px; font-weight: 900; }}
    QMenu::item:selected {{ background: {accent}; }}
    QMenu::separator {{ height: 1px; background: {menu_border}; margin: 6px 8px; }}

    QCheckBox::indicator {{
        width: 18px; height: 18px;
        border-radius: 6px;
        border: 1px solid {btn_border};
        background: rgba(0,0,0,0.10);
    }}
    QCheckBox::indicator:checked {{ background: {accent}; }}
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



def _draw_grain(p: QtGui.QPainter, rect: QtCore.QRect, strength: int = 16, step: int = 3):
    try:
        rnd = QtCore.QRandomGenerator.global_()
        p.save()
        p.setPen(QtCore.Qt.NoPen)
        for y in range(rect.top(), rect.bottom(), step):
            for x in range(rect.left(), rect.right(), step):
                a = int(rnd.bounded(strength))
                if a == 0:
                    continue
                c = QtGui.QColor(255, 255, 255, a) if rnd.bounded(2) == 0 else QtGui.QColor(0, 0, 0, a)
                p.setBrush(QtGui.QBrush(c))
                p.drawRect(x, y, 1, 1)
        p.restore()
    except Exception:
        pass


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
    kind: str               # "hotkey"
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

# ---------- Glass root ----------
class GlassRoot(QtWidgets.QFrame):
    def __init__(self, get_theme, parent=None):
        super().__init__(parent)
        self.setObjectName("GlassRoot")
        self._get_theme = get_theme
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)

    def paintEvent(self, e: QtGui.QPaintEvent):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing, True)
        r = self.rect().adjusted(1, 1, -1, -1)
        path = QtGui.QPainterPath()
        path.addRoundedRect(QtCore.QRectF(r), 18.0, 18.0)

        t = THEMES.get(str(self._get_theme()), THEMES["Ametrine"])
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

# ---------- TitleBar ----------
class TitleBar(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._drag = None
        self.lbl = QtWidgets.QLabel("whybinder")
        self.lbl.setObjectName("Title")
        self.btn_theme = QtWidgets.QToolButton(); self.btn_theme.setText("🎨"); self.btn_theme.setFixedWidth(48)
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

    def showEvent(self, e):
        super().showEvent(e)
        Anim.fade(self, 0.0, 1.0, 220)

class BindEditor(GlassDialog):
    def __init__(self, get_theme, parent=None, bind_obj: Optional[Bind]=None, categories: Optional[list[str]]=None):
        super().__init__(get_theme, parent, 760, 520, "Бинд")
        self.result_bind: Optional[Bind] = None
        cats = categories or [DEFAULT_BIND_CATEGORY]

        form = QtWidgets.QFormLayout(self.body)
        form.setLabelAlignment(QtCore.Qt.AlignRight)

        self.cmb_kind = QtWidgets.QComboBox(); self.cmb_kind.addItems(["hotkey"])
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
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Укажи триггер (клавиши).")
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

# ---------- Binder engine ----------
class BinderEngine(QtCore.QObject):
    status = QtCore.Signal(str)
    def __init__(self):
        super().__init__()
        self.enabled = True
        self._hotkeys = []
        self.binds: list[Bind] = []

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
        self.status.emit("Горячие клавиши обновлены")

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

        btns1 = QtWidgets.QHBoxLayout()
        self.btn_add = QtWidgets.QPushButton("Добавить")
        self.btn_edit = QtWidgets.QPushButton("Редактировать")
        self.btn_del = QtWidgets.QPushButton("Удалить")
        self.btn_dup = QtWidgets.QPushButton("Дублировать")
        btns1.addWidget(self.btn_add)
        btns1.addWidget(self.btn_edit)
        btns1.addWidget(self.btn_del)
        btns1.addWidget(self.btn_dup)
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

        lay = QtWidgets.QVBoxLayout(self)
        lay.addLayout(top)
        lay.addWidget(self.table, 1)
        lay.addLayout(btns1)
        lay.addLayout(btns2)

        self.btn_add.clicked.connect(self.add_bind)
        self.btn_edit.clicked.connect(self.edit_bind)
        self.btn_del.clicked.connect(self.delete_binds)
        self.btn_dup.clicked.connect(self.duplicate_bind)
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
        self.table.setRowCount(0)
        cat = self.cmb_cat.currentText()
        binds = self.mw.binds
        if cat and cat != "Все":
            binds = [b for b in binds if b.category == cat]
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
            self.table.setItem(r, 5, QtWidgets.QTableWidgetItem("Да" if b.enabled else "Нет"))
            prev = (b.text or "").replace("\n","  ")
            if len(prev) > 80:
                prev = prev[:80] + "…"
            self.table.setItem(r, 6, QtWidgets.QTableWidgetItem(prev))
        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setSectionResizeMode(6, QtWidgets.QHeaderView.Stretch)

    def selected_indices(self) -> list[int]:
        rows = sorted({i.row() for i in self.table.selectionModel().selectedRows()})
        if not rows:
            return []
        # map visible rows to real binds by key+text matching (stable)
        cat = self.cmb_cat.currentText()
        visible = self.mw.binds if (cat=="Все" or not cat) else [b for b in self.mw.binds if b.category==cat]
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

    def add_bind(self):
        dlg = BindEditor(self.mw.get_theme, self.mw, None, self.mw.categories)
        if dlg.exec() == QtWidgets.QDialog.Accepted and dlg.result_bind:
            self.mw.binds.append(dlg.result_bind)
            if dlg.result_bind.category not in self.mw.categories:
                self.mw.categories.append(dlg.result_bind.category)
            self.mw.save_all()
            self.mw.engine.apply_binds(self.mw.binds)
            self.setup_categories(self.mw.categories)
            self.refresh()

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
        if QtWidgets.QMessageBox.question(self, "Удалить", f"Удалить выбранные бинды: {len(idxs)}?") != QtWidgets.QMessageBox.Yes:
            return
        for i in idxs:
            self.mw.binds.pop(i)
        self.mw.save_all()
        self.mw.engine.apply_binds(self.mw.binds)
        self.refresh()

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
        self.btn_menu.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self.menu = QtWidgets.QMenu(self)
        self.btn_menu.setMenu(self.menu)
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
        self.btn_copy = QtWidgets.QPushButton("COPY")

        bottom = QtWidgets.QHBoxLayout()
        bottom.addWidget(self.btn_random)
        bottom.addStretch(1)
        bottom.addWidget(self.btn_copy)

        grid = QtWidgets.QGridLayout()
        grid.addLayout(head, 0, 0, 1, 2)
        grid.addWidget(QtWidgets.QLabel("Список:"), 1, 0)
        grid.addWidget(QtWidgets.QLabel("Просмотр:"), 1, 1)
        grid.addWidget(self.lst, 2, 0)
        grid.addWidget(self.preview, 2, 1)
        grid.addWidget(self.hint, 3, 1)
        grid.addLayout(bottom, 4, 0, 1, 2)
        grid.setRowStretch(2, 1)
        grid.setColumnStretch(1, 2)

        self.setLayout(grid)

        self.lst.currentRowChanged.connect(self._sel_changed)
        self.btn_random.clicked.connect(self.pick_random)
        self.btn_copy.clicked.connect(self.copy_current)

        self.act_add.triggered.connect(self.add_item)
        self.act_import.triggered.connect(self.import_items)
        self.act_export.triggered.connect(self.export_items)
        self.act_edit.triggered.connect(self.edit_item)
        self.act_del.triggered.connect(self.delete_item)

        self.refresh()

    def _set_today(self, on: bool):
        self.only_today = bool(on)
        self.refresh()

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
            if len(txt) > 60:
                txt = txt[:60] + "…"
            self.lst.addItem(txt)
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
        if QtWidgets.QMessageBox.question(self, "Удалить", "Удалить выбранный текст?") != QtWidgets.QMessageBox.Yes:
            return
        self.db.delete(self.area, self.current_cat, it["id"])
        self.refresh()

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

    def import_items(self):
        fn, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Импорт JSON", "", "JSON (*.json)")
        if not fn:
            return
        n = self.db.import_json(self.area, self.current_cat, Path(fn))
        QtWidgets.QMessageBox.information(self, "Импорт", f"Добавлено: {n}")
        self.refresh()

    def export_items(self):
        fn, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Экспорт JSON", f"{self.area}_{self.current_cat}.json", "JSON (*.json)")
        if not fn:
            return
        self.db.export_json(self.area, self.current_cat, Path(fn))
        QtWidgets.QMessageBox.information(self, "Экспорт", "Готово")

class PricePage(QtWidgets.QWidget):
    def __init__(self, mw: 'MainWindow'):
        super().__init__()
        self.mw = mw
        lay = QtWidgets.QVBoxLayout(self)
        lbl = QtWidgets.QLabel("Прайс"); lbl.setObjectName("Title")
        self.text = QtWidgets.QPlainTextEdit()
        self.text.setReadOnly(True)
        lay.addWidget(lbl)
        lay.addWidget(self.text, 1)
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

    def add_btn(self, text: str, icon_char: str, cb):
        b = QtWidgets.QToolButton()
        b.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        b.setText(text)
        # Use emoji icon (always available) — avoids pixelated low-quality images
        b.setIcon(QtGui.QIcon())  # keep empty; emoji in text is ok
        b.setText(text)
        b.clicked.connect(cb)
        b.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.l.addWidget(b)
        return b

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
        self.sidebar.add_btn("Бинды", "", lambda: self.switch_page(self.page_binds))
        self.sidebar.add_btn("PPV", "", lambda: self.switch_page(self.page_ppv))
        self.sidebar.add_btn("Рассылка", "", lambda: self.switch_page(self.page_mail))
        self.sidebar.add_btn("Прайс", "", lambda: (self.page_price.reload(), self.switch_page(self.page_price)))
        self.sidebar.l.addStretch(1)

        # Menu
        self.menu = QtWidgets.QMenu(self)
        self.act_share = self.menu.addAction("Поделиться выбранным биндом (код)")
        self.act_import = self.menu.addAction("Импорт бинда (код)…")
        self.menu.addSeparator()
        self.act_categories = self.menu.addAction("Категории…")
        self.menu.addSeparator()
        theme_menu = self.menu.addMenu("Тема")
        for name in THEMES.keys():
            a = theme_menu.addAction(name)
            a.triggered.connect(lambda checked=False, n=name: self.set_theme(n))
        self.menu.addSeparator()
        self.act_open_log = self.menu.addAction("Открыть лог")
        self.act_about = self.menu.addAction("О приложении")

        self.btn_menu.setMenu(self.menu)

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
        except Exception:
            pass

    def open_theme_menu(self):
        m = QtWidgets.QMenu(self)
        for name in THEMES.keys():
            act = m.addAction(name)
            act.triggered.connect(lambda checked=False, n=name: self.set_theme(n))
        m.exec(QtGui.QCursor.pos())

    def set_theme(self, name: str):
        self._theme = str(name)
        self.g["theme"] = self._theme
        save_settings(self.g)
        QtWidgets.QApplication.instance().setStyleSheet(app_stylesheet(self._theme))
        try:
            Anim.fade(self.root, 0.0, 1.0, 220)
            Anim.slide_in(self.root, dx=10, ms=220)
        except Exception:
            pass
        self.root.update()

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
            name, ok = QtWidgets.QInputDialog.getText(dlg, "Новая", "Название:")
            if ok:
                name = name.strip()
                if name and name not in self.categories:
                    self.categories.append(name)
                    lst.addItem(name)

        def ren_cat():
            it = lst.currentItem()
            if not it:
                return
            old = it.text()
            name, ok = QtWidgets.QInputDialog.getText(dlg, "Переименовать", "Название:", text=old)
            if ok:
                name = name.strip()
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
            if QtWidgets.QMessageBox.question(dlg, "Удалить", f"Удалить категорию «{name}»? Бинды перейдут в «{DEFAULT_BIND_CATEGORY}».") != QtWidgets.QMessageBox.Yes:
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
        QtWidgets.QMessageBox.information(self, "Лог", "Не удалось открыть лог-файл.")

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
            QtWidgets.QMessageBox.information(self, "Поделиться", "Выбери 1 бинд.")
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
    return s

def save_settings(s: dict):
    safe_write_json(SETTINGS_FILE, s)

# ---------- main ----------

def main():
    QtCore.QCoreApplication.setApplicationName(APP_NAME)
    app = QtWidgets.QApplication(sys.argv)
    try:
        app.setStyle("Fusion")
    except Exception:
        pass

    setup_logging()

    g = load_settings()
    app.setStyleSheet(app_stylesheet(g.get("theme", "Ametrine")))

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
            QtWidgets.QMessageBox.critical(None, "Ошибка запуска", str(e))
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
