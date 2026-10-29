import calendar
import io
import math
import sqlite3
from datetime import date
from html import escape

import altair as alt
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

DB = "plant_data.db"
st.set_page_config(page_title="Plant Data", layout="wide", initial_sidebar_state="collapsed")

# ------------------------------------------------------------------ THEME
INK = "#1B2B34"        # slate - text, banner
MUTED = "#5F6F76"
LINE = "#CBD3D6"
GRID = "#DDE3E5"
C_AMOUNT = "#12667A"   # steel teal  -> Amount
C_QTY = "#D9920B"      # safety amber -> Qty

TOP_HI, TOP_LO = "Top 4 Highest", "Top 3 Lowest"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600&family=Barlow+Condensed:wght@500;600;700&display=swap');

html, body, .stApp { font-family: 'Barlow', 'Segoe UI', sans-serif; }
/* Avoid applying global typography to Streamlit's internal dataframe/menu widgets;
   broad [class*="st-"] selectors can distort the column action popup. */
.stApp p, .stApp label, .stApp input, .stApp textarea, .stApp select, .stApp button, .stApp [data-testid="stMarkdownContainer"] { font-family: 'Barlow', 'Segoe UI', sans-serif; }
.stApp { background: #E9ECEC; }
.block-container { padding-top: 1.4rem; padding-bottom: 3rem; max-width: 1400px; }
footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; }

h1, h2, h3, h4 {
    font-family: 'Barlow Condensed', 'Arial Narrow', sans-serif !important;
    color: #1B2B34; letter-spacing: 0.01em; font-weight: 600 !important;
}
h3 { font-size: 1.45rem !important; padding-bottom: 0.2rem !important; }

/* ---------- top banner ---------- */
.banner {
    background: linear-gradient(120deg, #1B2B34 0%, #26414D 60%, #12667A 130%); color: #fff;
    border-radius: 12px; box-shadow: 0 6px 18px rgba(27,43,52,.18);
    padding: 20px 28px; margin-bottom: 16px;
    display: flex; justify-content: space-between; align-items: baseline; flex-wrap: wrap; gap: 6px;
}
.banner .t { font-family: 'Barlow Condensed', sans-serif; font-size: 2.1rem; font-weight: 700; letter-spacing: .02em; }
.banner .s { color: #A9B8BF; font-size: .98rem; }

/* ---------- tabs ---------- */
button[data-baseweb="tab"] p {
    font-family: 'Barlow Condensed', sans-serif; font-size: 1.2rem; font-weight: 600; letter-spacing: .02em;
}

/* ---------- panels ---------- */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #FFFFFF; border: 1px solid #DDE3E5 !important; border-radius: 12px;
    box-shadow: 0 2px 10px rgba(27,43,52,.06);
}

/* ---------- KPI strip ---------- */
.kpis {
    display: grid; grid-template-columns: repeat(4, 1fr); gap: 1px;
    background: #DDE3E5; border: 1px solid #DDE3E5; border-radius: 12px; overflow: hidden;
    box-shadow: 0 2px 10px rgba(27,43,52,.06);
    margin: 6px 0 14px 0;
}
.kpi { background: #fff; padding: 16px 22px 14px 22px; border-top: 4px solid #1B2B34; }
.kpi.amt { border-top-color: #12667A; }
.kpi.qty { border-top-color: #D9920B; }
.kpi.trp { border-top-color: #5E548E; }
.kpi .l { color: #5F6F76; font-size: .95rem; font-weight: 500; }
.kpi .v {
    font-family: 'Barlow Condensed', sans-serif; font-size: 2.6rem; font-weight: 700;
    color: #1B2B34; line-height: 1.1; font-variant-numeric: tabular-nums;
}
.kpi .d { color: #5F6F76; font-size: .92rem; margin-top: 2px; }
@media (max-width: 1000px) { .kpis { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 640px) { .kpis { grid-template-columns: 1fr; } }

.kpi .d .up { color: #1E8A3C; font-weight: 600; }
.kpi .d .down { color: #C62828; font-weight: 600; }

.yr { text-align: center; font-family: 'Barlow Condensed', sans-serif; font-size: 1.7rem;
       font-weight: 700; color: #1B2B34; line-height: 2.3rem; }
.selm { color: #5F6F76; font-size: .95rem; margin-top: 8px; }
.selm b { color: #1B2B34; }

/* ---------- calendar ---------- */
.calwrap { overflow-x: auto; }
.cal {
    display: grid; grid-template-columns: repeat(7, 1fr) 1.2fr; gap: 1px; min-width: 720px;
    background: #CBD3D6; border: 1px solid #CBD3D6; border-radius: 4px; overflow: hidden;
}
.cal .h {
    background: #1B2B34; color: #fff; padding: 8px 6px; text-align: center;
    font-family: 'Barlow Condensed', sans-serif; font-size: 1.05rem; font-weight: 600; letter-spacing: .03em;
}
.cal .cd { background: #fff; min-height: 88px; padding: 6px 9px; }
.cal .cd.empty { background: #F4F6F6; }
.cal .cd.today { outline: 2px solid #1B2B34; outline-offset: -2px; }
.cal .cd.wk { background: #F4F6F6; }
.cal .n { font-size: .85rem; font-weight: 600; color: #5F6F76; }
.cal .a {
    font-family: 'Barlow Condensed', sans-serif; font-size: 1.3rem; font-weight: 700;
    color: #1B2B34; line-height: 1.15; font-variant-numeric: tabular-nums;
}
.cal .q { font-size: .88rem; color: #1B2B34; font-variant-numeric: tabular-nums; }
.cal .none { color: #A9B4B9; font-size: .85rem; }

/* ---------- clickable calendar ---------- */
.st-key-calgrid { background: transparent; border: none; overflow-x: auto; padding: 6px 4px 12px; gap: 8px !important; }
.st-key-calgrid div[data-testid="stVerticalBlock"] { gap: 0; }
.st-key-calgrid > div[data-testid="stVerticalBlock"] { gap: 8px; }
.st-key-calgrid div[data-testid="stHorizontalBlock"] { gap: 8px; min-width: 720px; flex-wrap: nowrap; }
.st-key-calgrid div[data-testid="stColumn"] { min-width: 0; }

.calx .h {
    background: linear-gradient(135deg, #1B2B34, #2B4452); color: #fff; padding: 9px 6px; text-align: center;
    border-radius: 8px; font-family: 'Barlow Condensed', sans-serif; font-size: 1.05rem;
    font-weight: 600; letter-spacing: .08em; text-transform: uppercase;
}
.calx .cd {
    display: flex; flex-direction: column; min-height: 100px; padding: 9px 11px 10px; box-sizing: border-box;
    background: #fff; border: 1px solid #E1E7E9; border-radius: 10px;
    box-shadow: 0 1px 3px rgba(27,43,52,.06); transition: transform .15s ease, box-shadow .15s ease;
}
.calx .cd.empty { background: transparent; border: 1px dashed #D5DCDE; box-shadow: none; }
.calx .cd.we { background: #F6F8F8; }
.calx .top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
.calx .dn {
    display: inline-flex; align-items: center; justify-content: center; min-width: 26px; height: 26px;
    border-radius: 13px; background: rgba(27,43,52,.08); color: #1B2B34;
    font-size: .85rem; font-weight: 700;
}
.calx .cd.today .dn { background: #1B2B34; color: #fff; }
.calx .cd.dim { opacity: .25; }
.calx .cd.hl { outline: 3px solid #5E548E; outline-offset: -3px; }
.calx .tg { font-size: .66rem; font-weight: 700; letter-spacing: .08em; color: #12667A; }
.calx .a {
    font-family: 'Barlow Condensed', sans-serif; font-size: 1.4rem; font-weight: 700;
    color: #1B2B34; line-height: 1.15; font-variant-numeric: tabular-nums;
}
.calx .q { font-size: .88rem; color: #3D4F57; font-variant-numeric: tabular-nums; }
.calx .none { color: #A9B4B9; font-size: .83rem; }
.calx .bar { margin-top: auto; padding-top: 8px; }
.calx .bar i { display: block; height: 4px; border-radius: 2px; min-width: 6px; }
.calx .cd.wk {
    background: linear-gradient(145deg, #1B2B34, #2B4452); border: none;
    box-shadow: 0 3px 10px rgba(27,43,52,.22);
}
.calx .cd.wk .dn, .calx .cd.wk .n { color: #A9B8BF; background: none; padding: 0; font-size: .8rem;
    letter-spacing: .08em; text-transform: uppercase; }
.calx .cd.wk .a { color: #fff; }
.calx .cd.wk .q { color: #D5DEE2; }
.calx .cd.wk .none { color: #6F8590; }

/* invisible button laid over each day cell = click area */
.st-key-calgrid div[data-testid="stVerticalBlock"]:has(> div[class*="st-key-cal_"]) { position: relative; }
.st-key-calgrid div[class*="st-key-cal_"] {
    position: absolute !important; top: 0; left: 0; right: 0; bottom: 0;
    width: 100% !important; height: 100% !important; z-index: 5;
}
.st-key-calgrid div[class*="st-key-cal_"] > div { height: 100%; width: 100%; }
.st-key-calgrid div[class*="st-key-cal_"] button { width: 100%; height: 100%; opacity: 0; cursor: pointer; }
.st-key-calgrid div[data-testid="stVerticalBlock"]:has(> div[class*="st-key-cal_"]:hover) .cd {
    transform: translateY(-3px); box-shadow: 0 10px 20px rgba(27,43,52,.16);
}

/* ---------- day detail ---------- */
.dd-head {
    display: flex; align-items: center; gap: 18px; padding: 16px 22px; margin: 4px 0 14px 0;
    background: linear-gradient(120deg, #1B2B34 0%, #26414D 65%, #12667A 140%); border-radius: 12px; color: #fff;
}
.dd-head .big { font-family: 'Barlow Condensed', sans-serif; font-size: 3.4rem; font-weight: 700; line-height: 1; }
.dd-head .wd { font-family: 'Barlow Condensed', sans-serif; font-size: 1.5rem; font-weight: 600; line-height: 1.1; }
.dd-head .my { color: #A9B8BF; font-size: .98rem; }
.dd-chips { margin-left: auto; display: flex; gap: 10px; flex-wrap: wrap; }
.dd-chip { background: rgba(255,255,255,.10); border-radius: 10px; padding: 8px 16px; min-width: 120px; }
.dd-chip .l { color: #A9B8BF; font-size: .8rem; letter-spacing: .05em; text-transform: uppercase; }
.dd-chip .v { font-family: 'Barlow Condensed', sans-serif; font-size: 1.7rem; font-weight: 700; line-height: 1.15; }
.mrow {
    background: #fff; border: 1px solid #E1E7E9; border-radius: 10px; padding: 12px 16px; margin-bottom: 8px;
    box-shadow: 0 1px 3px rgba(27,43,52,.05);
}
.mrow .mt { display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; }
.mrow .nm { font-weight: 600; color: #1B2B34; font-size: 1.02rem; }
.mrow .qt {
    background: rgba(217,146,11,.14); color: #8A5A00; border-radius: 999px; padding: 3px 12px;
    font-weight: 700; font-size: .92rem; font-variant-numeric: tabular-nums;
}
.mrow .am {
    font-family: 'Barlow Condensed', sans-serif; font-size: 1.35rem; font-weight: 700;
    color: #12667A; font-variant-numeric: tabular-nums; margin-left: auto;
}
.mrow .tr { background: #E9EEEF; border-radius: 3px; height: 6px; margin-top: 9px; overflow: hidden; }
.mrow .tr i { display: block; height: 100%; background: linear-gradient(90deg, #12667A, #3FA0B5); border-radius: 3px; }
.mrow .sb { color: #5F6F76; font-size: .84rem; margin-top: 5px; }
.mrow .sites { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }
.mrow .sites span {
    background: #E9EEEF; color: #1B2B34; border-radius: 6px; padding: 3px 10px;
    font-size: .84rem; font-variant-numeric: tabular-nums;
}
.mrow .sites b { color: #12667A; }

/* ---------- buttons ---------- */
div.stButton > button, div.stDownloadButton > button { border-radius: 4px; font-weight: 600; }

/* ---------- main menu (square button on the right inside the Plant Data banner) ---------- */
@keyframes spinOpen { from { transform: rotate(-90deg) scale(.5); opacity: 0; } to { transform: none; opacity: 1; } }
@keyframes spinClose { from { transform: rotate(90deg) scale(.5); opacity: 0; } to { transform: none; opacity: 1; } }
@keyframes menuDrop { from { opacity: 0; transform: translateY(-8px); } to { opacity: 1; transform: none; } }
@keyframes pageInA { from { opacity: 0; transform: translateY(18px); } to { opacity: 1; transform: none; } }
@keyframes pageInB { from { opacity: 0; transform: translateY(18px); } to { opacity: 1; transform: none; } }

section[data-testid="stSidebar"], [data-testid="stExpandSidebarButton"], [data-testid="collapsedControl"] { display: none !important; }

/* the banner background belongs to the container so the button fits inside it */
.st-key-headrow {
    position: relative; margin-bottom: 16px; padding: 14px 20px 14px 28px; border-radius: 12px; color: #fff;
    background: linear-gradient(120deg, #1B2B34 0%, #26414D 60%, #12667A 130%);
    box-shadow: 0 6px 18px rgba(27,43,52,.18);
}
.st-key-headrow div[data-testid="stHorizontalBlock"] { gap: 12px; flex-wrap: nowrap; align-items: center; }
.st-key-headrow div[data-testid="stColumn"]:last-child { flex: 0 0 52px !important; width: 52px !important; min-width: 0 !important; }
.st-key-headrow div[data-testid="stColumn"]:first-child { flex: 1 1 0 !important; min-width: 0 !important; }
.st-key-headrow .banner { background: none; box-shadow: none; padding: 0; margin: 0; border-radius: 0; }

.st-key-menu_btn, .st-key-menu_btn div[data-testid="stButton"] { width: 52px; height: 52px; }
.st-key-menu_btn button {
    width: 52px; height: 52px; min-height: 0; padding: 0; border-radius: 10px; color: #fff;
    background: rgba(255,255,255,.12); border: 1px solid rgba(255,255,255,.28);
    transition: background .15s ease, transform .15s ease;
}
.st-key-menu_btn button:hover { background: rgba(255,255,255,.22); border-color: rgba(255,255,255,.5); color: #fff; transform: translateY(-1px); }
.st-key-menu_btn button p { display: none; }
.st-key-menu_btn button span[data-testid="stIconMaterial"] { font-size: 1.7rem; color: #fff; }

.st-key-menulist {
    position: absolute; top: 100%; right: 0; margin-top: 8px; width: 260px; z-index: 1000;
    background: #fff; border: 1px solid #DDE3E5; border-radius: 12px; padding: 8px;
    box-shadow: 0 12px 28px rgba(27,43,52,.18); animation: menuDrop .22s ease;
}
.st-key-menulist div[data-testid="stVerticalBlock"] { gap: 2px; }
.st-key-menulist button {
    width: 100%; justify-content: flex-start; padding: .65rem 1rem; border: none; border-radius: 8px;
    background: transparent; color: #1B2B34; box-shadow: none;
}
.st-key-menulist button p { font-size: 1.05rem; font-weight: 500; text-align: left; color: inherit; }
.st-key-menulist button:hover { background: rgba(27,43,52,.06); color: #1B2B34; }
.st-key-menulist button[data-testid="stBaseButton-primary"] { background: rgba(18,102,122,.13); color: #12667A; box-shadow: inset 3px 0 0 #12667A; }
.st-key-menulist button[data-testid="stBaseButton-primary"] p { font-weight: 700; }

@media (max-width: 640px) {
  .st-key-headrow { padding: 10px 12px 10px 16px; }
  .st-key-headrow div[data-testid="stColumn"]:last-child { flex: 0 0 44px !important; width: 44px !important; }
  .st-key-menu_btn, .st-key-menu_btn div[data-testid="stButton"], .st-key-menu_btn button { width: 44px; height: 44px; }
  .st-key-menu_btn button span[data-testid="stIconMaterial"] { font-size: 1.5rem; }
  .st-key-menulist { width: min(260px, 80vw); }
}

/* ================= MOBILE ================= */
@media (max-width: 640px) {
  .block-container { padding: 0.8rem 0.6rem 2rem !important; }
  h3 { font-size: 1.2rem !important; }
  button[data-baseweb="tab"] p { font-size: 1rem; }

  .banner { padding: 14px 16px; margin-bottom: 12px; }
  .banner .t { font-size: 1.6rem; }
  .banner .s { font-size: .85rem; }

  .kpi { padding: 12px 16px 10px; }
  .kpi .v { font-size: 2rem; }

  /* calendar: all 7 days on one screen, hide the Week total column */
  .st-key-calgrid { padding: 4px 0 8px; gap: 3px !important; }
  .st-key-calgrid > div[data-testid="stVerticalBlock"] { gap: 3px; }
  .st-key-calgrid div[data-testid="stHorizontalBlock"] { min-width: 0; gap: 3px; }
  .st-key-calgrid div[data-testid="stColumn"] { flex: 1 1 0 !important; width: auto !important; min-width: 0 !important; }
  .st-key-calgrid div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:nth-child(8) { display: none; }
  .calx .h { font-size: .7rem; padding: 6px 0; letter-spacing: 0; border-radius: 5px; }
  .calx .cd { min-height: 56px; padding: 4px 4px 5px; border-radius: 6px; }
  .calx .dn { min-width: 18px; height: 18px; font-size: .68rem; border-radius: 9px; }
  .calx .tg, .calx .none { display: none; }
  .calx .a { font-size: .74rem; }
  .calx .q { font-size: .64rem; }
  .calx .bar { padding-top: 3px; }
  .calx .bar i { height: 3px; }

  /* day detail */
  .dd-head { flex-wrap: wrap; padding: 12px 14px; gap: 10px; }
  .dd-head .big { font-size: 2.6rem; }
  .dd-chips { margin-left: 0; width: 100%; }
  .dd-chip { flex: 1 1 28%; min-width: 0; padding: 6px 10px; }
  .dd-chip .v { font-size: 1.2rem; }
  .mrow .am { margin-left: 0; }
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ------------------------------------------------------------------ DB
def conn():
    c = sqlite3.connect(DB, timeout=30)
    c.execute("PRAGMA foreign_keys = ON")
    return c


_DUP_KEY = """CASE
                        WHEN TRIM(COALESCE(e.serial_no, '')) <> ''
                        THEN 'S|' || UPPER(TRIM(e.serial_no)) || '|' || e.plant_id
                        ELSE 'F|' || e.entry_date || '|' || e.plant_id || '|' || e.material_id || '|'
                             || COALESCE(TRIM(e.site), '') || '|' || COALESCE(TRIM(e.location), '') || '|'
                             || e.qty || '|' || e.rate END"""

ENTRIES_VIEW_SQL = f"""CREATE VIEW entries_v AS
        SELECT e.id, e.entry_date AS date, substr(e.entry_date, 1, 7) AS month,
               p.name AS plant, m.name AS material, m.unit,
               COALESCE(NULLIF(TRIM(e.site), ''), 'Not set')     AS site,
               COALESCE(NULLIF(TRIM(e.location), ''), 'Not set') AS location,
               COALESCE(NULLIF(TRIM(l.vendor), ''), 'Not set')   AS tm_name,
               COALESCE(TRIM(e.serial_no), '')                   AS serial_no,
               e.qty, e.rate, e.amount,
               SUM(e.qty) OVER (PARTITION BY e.plant_id, e.material_id, substr(e.entry_date, 1, 7)
                                ORDER BY e.entry_date, e.id) AS cum_qty,
               SUM(e.amount) OVER (PARTITION BY e.plant_id, e.material_id, substr(e.entry_date, 1, 7)
                                   ORDER BY e.entry_date, e.id) AS cum_amount,
               ROW_NUMBER() OVER (PARTITION BY {_DUP_KEY} ORDER BY e.id) AS dup_rank,
               COUNT(*) OVER (PARTITION BY {_DUP_KEY}) AS dup_count
        FROM entries e
        JOIN plants p    ON p.id = e.plant_id
        JOIN materials m ON m.id = e.material_id
        LEFT JOIN locations l ON l.name = e.location"""


def init_db():
    with conn() as c:
        c.executescript(
            """
        CREATE TABLE IF NOT EXISTS plants(
            id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL);
        CREATE TABLE IF NOT EXISTS materials(
            id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL, unit TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS entries(
            id INTEGER PRIMARY KEY,
            entry_date TEXT NOT NULL,
            plant_id INTEGER NOT NULL REFERENCES plants(id),
            material_id INTEGER NOT NULL REFERENCES materials(id),
            site TEXT,
            location TEXT,
            qty REAL NOT NULL CHECK(qty >= 0),
            rate REAL NOT NULL CHECK(rate >= 0),
            amount REAL NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE INDEX IF NOT EXISTS ix_entries
            ON entries(entry_date, plant_id, material_id);
        """
        )
        # add site / location / serial_no columns to older databases (existing data stays safe)
        have = [r[1] for r in c.execute("PRAGMA table_info(entries)")]
        for col in ("site", "location", "serial_no"):
            if col not in have:
                c.execute(f"ALTER TABLE entries ADD COLUMN {col} TEXT")
        for tbl, col in (("sites", "site"), ("locations", "location")):
            fresh = c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                              (tbl,)).fetchone() is None
            c.execute(f"CREATE TABLE IF NOT EXISTS {tbl}(id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL)")
            if fresh:  # first run: seed the list with names already present in entries
                c.execute(f"INSERT OR IGNORE INTO {tbl}(name) SELECT DISTINCT TRIM({col}) FROM entries"
                          f" WHERE TRIM(COALESCE({col}, '')) <> ''")
        # TM Name (vendor) is stored in the TM number master
        if "vendor" not in [r[1] for r in c.execute("PRAGMA table_info(locations)")]:
            c.execute("ALTER TABLE locations ADD COLUMN vendor TEXT")
        # Re-create the view only when its definition changed. Streamlit re-runs this file on
        # every click, so dropping/creating it each time needs a write lock and can fail with
        # "database is locked" when another session or a DB viewer has the file open.
        have_view = c.execute("SELECT sql FROM sqlite_master WHERE type='view' AND name='entries_v'").fetchone()
        if have_view is None or (have_view[0] or "").strip() != ENTRIES_VIEW_SQL.strip():
            c.execute("DROP VIEW IF EXISTS entries_v")
            c.execute(ENTRIES_VIEW_SQL)


def q(sql, params=()):
    with conn() as c:
        return pd.read_sql(sql, c, params=params)


def run(sql, params=()):
    with conn() as c:
        c.execute(sql, params)


def save_tm(number, vendor=""):
    """Save/update a TM number. If the vendor is empty, the existing vendor is kept."""
    run("INSERT INTO locations(name, vendor) VALUES(?, ?) ON CONFLICT(name) DO UPDATE "
        "SET vendor = COALESCE(NULLIF(excluded.vendor, ''), locations.vendor)",
        (number, vendor or None))


def rs(x):
    return f"Rs. {x:,.0f}"


def df_to_excel_bytes(frame):
    """DataFrame -> .xlsx bytes (openpyxl must be listed in requirements.txt)."""
    buffer = io.BytesIO()
    frame.to_excel(buffer, index=False, engine="openpyxl")
    return buffer.getvalue()


# ------------------------------------------------------------------ DUPLICATE / SEARCH helpers
def clean_txt(v):
    """Turn an Excel / CSV cell into clean text (1234.0 -> '1234', NaN -> '')."""
    if v is None:
        return ""
    try:
        if pd.isna(v):
            return ""
    except (TypeError, ValueError):
        pass
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v).strip()


def dup_key(d, plant, material, site, location, qty, rate, serial):
    """Duplicate rule: with a Serial No, same (Serial No + Plant) = duplicate.
    Without a Serial No, same Date, Plant, Material, Site, TM Number, Qty and Rate = duplicate."""
    serial = clean_txt(serial).upper()
    if serial:
        return ("S", serial, plant)
    return ("F", str(d), plant, material, clean_txt(site) or "Not set",
            clean_txt(location) or "Not set", round(float(qty), 6), round(float(rate), 6))


def existing_key_map():
    ex = q("SELECT id, date, plant, material, site, location, serial_no, qty, rate FROM entries_v")
    out = {}
    for r in ex.itertuples(index=False):
        k = dup_key(r.date, r.plant, r.material, r.site, r.location, r.qty, r.rate, r.serial_no)
        out.setdefault(k, []).append(int(r.id))
    return out


def find_duplicates(d, plant, material, site, location, qty, rate, serial, exclude_id=None):
    ids = existing_key_map().get(dup_key(d, plant, material, site, location, qty, rate, serial), [])
    return [i for i in ids if i != exclude_id]


def sql_search(text):
    """Every space-separated word must match some column of entries_v (AND)."""
    sql, params = "", []
    for t in text.lower().split():
        sql += (" AND LOWER(CAST(id AS TEXT) || ' ' || date || ' ' || plant || ' ' || material || ' ' || site"
                " || ' ' || location || ' ' || tm_name || ' ' || serial_no) LIKE ?")
        params.append(f"%{t}%")
    return sql, params


def text_filter(frame, text):
    terms = text.lower().split()
    if not terms or frame.empty:
        return frame
    hay = (frame[["id", "date", "plant", "material", "site", "location", "tm_name", "serial_no"]]
           .astype(str).agg(" ".join, axis=1).str.lower())
    mask = pd.Series(True, index=frame.index)
    for t in terms:
        mask &= hay.str.contains(t, regex=False)
    return frame[mask]


def entries_table(frame):
    show = frame.rename(columns={
        "date": "Date", "plant": "Plant Name", "material": "Material Description",
        "site": "Site", "location": "TM Number", "tm_name": "TM Name", "serial_no": "Serial No",
        "unit": "Unit", "qty": "Qty", "rate": "Rate", "amount": "Amount",
        "cum_qty": "Cumulative Qty", "cum_amount": "Cumulative Amount"})
    show["Duplicate"] = show["dup_rank"].map(lambda n: "Duplicate" if n > 1 else "")
    cols = ["id", "Date", "Plant Name", "Material Description", "Site", "TM Number", "TM Name",
            "Serial No", "Unit", "Qty", "Rate", "Amount", "Cumulative Qty", "Cumulative Amount", "Duplicate"]
    return show[cols]


# ------------------------------------------------------------------ UI helpers
def trend_chart(series, label, kind, color):
    """kind = 'bar' (month-wise) or 'line' (day-wise). Y-axis always starts at 0."""
    d = series.reset_index()
    d.columns = ["period", "value"]
    base = alt.Chart(d)
    if kind == "bar":
        mark = base.mark_bar(color=color, size=38)
        x = alt.X("period:N", title="Month", axis=alt.Axis(labelAngle=0, grid=False))
    else:
        mark = base.mark_line(
            color=color, strokeWidth=2.5,
            point=alt.OverlayMarkDef(color=color, size=50, filled=True),
        )
        x = alt.X("period:N", title="Day of month",
                  axis=alt.Axis(labelAngle=0, grid=False, labelExpr="slice(datum.label, 8)"))
    chart = mark.encode(
        x=x,
        y=alt.Y("value:Q", title=label, scale=alt.Scale(domainMin=0),
                axis=alt.Axis(format=",.0f", gridColor=GRID)),
        tooltip=[alt.Tooltip("period:N", title="Period"),
                 alt.Tooltip("value:Q", format=",.2f", title=label)],
    ).properties(height=300)
    return (
        chart.configure(background="transparent")
        .configure_view(stroke=None)
        .configure_axis(labelFont="Barlow", titleFont="Barlow", labelColor=MUTED,
                        titleColor=MUTED, tickColor=LINE, domainColor=LINE,
                        labelFontSize=12, titleFontSize=12, titleFontWeight=500)
    )


def plant_compare_chart(frame, value_col, label):
    """Day-wise: one line per plant in a single chart for comparison. Click the legend to highlight."""
    d = (frame.groupby(["date", "plant"], as_index=False)[value_col].sum()
         .rename(columns={"plant": "Plant", value_col: "value"}))
    pick = alt.selection_point(fields=["Plant"], bind="legend")
    chart = (
        alt.Chart(d)
        .mark_line(strokeWidth=2.5, point=alt.OverlayMarkDef(size=55, filled=True))
        .encode(
            x=alt.X("date:N", title="Day of month",
                    axis=alt.Axis(labelAngle=0, grid=False, labelExpr="slice(datum.label, 8)")),
            y=alt.Y("value:Q", title=label, scale=alt.Scale(domainMin=0),
                    axis=alt.Axis(format=",.0f", gridColor=GRID)),
            color=alt.Color("Plant:N", scale=alt.Scale(scheme="tableau10"),
                            legend=alt.Legend(orient="bottom", title="Plant")),
            opacity=alt.condition(pick, alt.value(1), alt.value(0.2)),
            tooltip=[alt.Tooltip("date:N", title="Date"), alt.Tooltip("Plant:N"),
                     alt.Tooltip("value:Q", format=",.2f", title=label)],
        )
        .add_params(pick).properties(height=340)
    )
    return (chart.configure(background="transparent").configure_view(stroke=None)
            .configure_axis(labelFont="Barlow", titleFont="Barlow", labelColor=MUTED,
                            titleColor=MUTED, tickColor=LINE, domainColor=LINE,
                            labelFontSize=12, titleFontSize=12, titleFontWeight=500))


def plant_compare_table(frame, metric):
    col = {"Qty": "qty", "Trips": "trips"}.get(metric, "amount")
    g = frame.groupby("plant")[["amount", "qty", "trips"]].sum()
    daily = frame.groupby(["plant", "date"])[col].sum()
    g["Active days"] = daily.groupby("plant").size()
    g["Peak day"] = daily.groupby("plant").idxmax().map(lambda t: t[1])
    g["Share %"] = g[col] / g[col].sum() * 100 if g[col].sum() else 0
    g = g.sort_values(col, ascending=False).reset_index().rename(columns={
        "plant": "Plant", "amount": "Amount (Rs.)", "qty": "Qty", "trips": "Trips"})
    st.dataframe(g.style.format({"Amount (Rs.)": "{:,.0f}", "Qty": "{:,.2f}", "Share %": "{:.1f}%"}),
                 hide_index=True, use_container_width=True)
    with st.expander("Plant x Date table"):
        pv = frame.pivot_table(index="date", columns="plant", values=col, aggfunc="sum").fillna(0)
        pv["Total"] = pv.sum(axis=1)
        st.dataframe(pv.style.format("{:,.2f}"), use_container_width=True)


def kpi_strip(amount, amount_d, qty, qty_d, entries, sub, trips=0, trips_d=""):
    def cell(cls, label, value, note):
        return (f'<div class="kpi {cls}"><div class="l">{label}</div>'
                f'<div class="v">{value}</div><div class="d">{note}</div></div>')

    html = (
        '<div class="kpis">'
        + cell("amt", "Amount this month", rs(amount), amount_d)
        + cell("qty", "Qty this month", f"{qty:,.1f}", qty_d)
        + cell("trp", "Trips (TM) this month", f"{trips:,}", trips_d)
        + cell("", "Entries", f"{entries:,}", sub)
        + "</div>"
    )
    st.markdown(html, unsafe_allow_html=True)


def short_rs(x):
    if x >= 1e7:
        return f"Rs. {x / 1e7:.2f} Cr"
    if x >= 1e5:
        return f"Rs. {x / 1e5:.2f} L"
    if x >= 1e3:
        return f"Rs. {x / 1e3:.1f} K"
    return f"Rs. {x:,.0f}"


def cell_lines(metric, a, qy, tr=0):
    out = ""
    if metric in ("Amount", "Both"):
        out += f'<div class="a">{short_rs(a)}</div>'
    if metric in ("Qty", "Both"):
        cls = "a" if metric == "Qty" else "q"
        out += f'<div class="{cls}">{"" if metric == "Qty" else "Qty "}{qy:,.1f}</div>'
    if metric == "Trips":
        out += f'<div class="a">{int(tr)} trips</div>'
    elif tr:
        out += f'<div class="q">{int(tr)} trips</div>'
    return out


def pick_day(key):
    st.session_state["cal_sel"] = key
    st.session_state["scroll_to_detail"] = True


def scroll_to_detail():
    """Smooth-scroll to the day detail on every click. The script differs each time (nonce),
    otherwise Streamlit does not re-run identical HTML and scrolling stops after the 2nd click."""
    if not st.session_state.pop("scroll_to_detail", False):
        return
    n = st.session_state.get("scroll_n", 0) + 1
    st.session_state["scroll_n"] = n
    components.html(
        f"""<script>
        // click #{n}
        const doc = window.parent.document;
        let tries = 0;
        const go = () => {{
            const el = doc.getElementById('day-detail-anchor');
            if (el) {{ el.scrollIntoView({{behavior: 'smooth', block: 'start'}}); }}
            else if (tries++ < 15) {{ setTimeout(go, 120); }}
        }};
        setTimeout(go, 250);
        </script>""",
        height=0,
    )


def extreme_ranks(data, col, extreme):
    """{period: rank} for Top 4 Highest or Top 3 Lowest."""
    if extreme == "All" or data.empty:
        return {}
    s = data[col]
    pick = s.nlargest(4) if extreme == TOP_HI else s.nsmallest(3)
    return {k: i + 1 for i, k in enumerate(pick.index)}


def show_extremes(data, metric):
    """Show the Top 4 Highest and Top 3 Lowest periods."""
    col = {"Qty": "qty", "Trips": "trips"}.get(metric, "amount")
    if data.empty:
        return
    fmt = rs if col == "amount" else (lambda v: f"{v:,.0f}" if col == "trips" else f"{v:,.1f}")
    hi, lo = data[col].nlargest(4), data[col].nsmallest(3)
    st.caption("🔺 Top 4 Highest: " + "  |  ".join(f"{k} ({fmt(v)})" for k, v in hi.items()))
    st.caption("🔻 Top 3 Lowest: " + "  |  ".join(f"{k} ({fmt(v)})" for k, v in lo.items()))


def calendar_ui(daily, month, metric, extreme="All"):
    """Styled calendar with clickable days. Clicking a day opens its detail below."""
    y, m = map(int, month.split("-"))
    weeks = calendar.Calendar(firstweekday=0).monthdayscalendar(y, m)
    rgb = {"Qty": "217,146,11", "Trips": "94,84,142"}.get(metric, "18,102,122")
    col = {"Qty": "qty", "Trips": "trips"}.get(metric, "amount")
    mx = float(daily[col].max()) if len(daily) else 0
    mx = mx or 1.0
    ranks = extreme_ranks(daily, col, extreme)
    hl = set(ranks)
    today = date.today().isoformat()
    sel = st.session_state.get("cal_sel")
    widths = [1] * 7 + [1.2]
    css = []

    with st.container(key="calgrid"):
        for c_, name in zip(st.columns(widths),
                            ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun", "Week total"]):
            c_.markdown(f'<div class="calx"><div class="h">{name}</div></div>', unsafe_allow_html=True)

        for wk in weeks:
            cols = st.columns(widths)
            wa = wq = wt = 0.0
            for i, (c_, day) in enumerate(zip(cols[:7], wk)):
                if day == 0:
                    c_.markdown('<div class="calx"><div class="cd empty"></div></div>',
                                unsafe_allow_html=True)
                    continue
                key = f"{month}-{day:02d}"
                cls = ("cd" + (" today" if key == today else "") + (" we" if i >= 5 else "")
                       + ((" hl" if key in hl else " dim") if extreme != "All" else ""))
                tag = '<span class="tg">TODAY</span>' if key == today else ""
                if key in hl:
                    tag = f'<span class="tg">{"HIGH" if extreme == TOP_HI else "LOW"} #{ranks[key]}</span>'
                if key in daily.index:
                    a, qy = float(daily.loc[key, "amount"]), float(daily.loc[key, "qty"])
                    tr = int(daily.loc[key, "trips"])
                    wa += a
                    wq += qy
                    wt += tr
                    ratio = float(daily.loc[key, col]) / mx
                    alpha = 0.05 + 0.30 * ratio
                    html = (f'<div class="calx"><div class="{cls}" '
                            f'style="background:linear-gradient(150deg, rgba({rgb},{alpha:.2f}) 0%, #fff 78%)">'
                            f'<div class="top"><span class="dn">{day}</span>{tag}</div>'
                            f'{cell_lines(metric, a, qy, tr)}'
                            f'<div class="bar"><i style="width:{max(ratio, 0.04) * 100:.0f}%;'
                            f'background:rgb({rgb})"></i></div></div></div>')
                else:
                    html = (f'<div class="calx"><div class="{cls}">'
                            f'<div class="top"><span class="dn">{day}</span>{tag}</div>'
                            f'<div class="none">No entry</div></div></div>')
                with c_:
                    st.markdown(html, unsafe_allow_html=True)
                    st.button(str(day), key=f"cal_{key}", on_click=pick_day, args=(key,))
                if key == sel:
                    css.append(f'.st-key-calgrid div[data-testid="stVerticalBlock"]:has(> .st-key-cal_{key}) .cd'
                               f'{{box-shadow: 0 0 0 3px #12667A, 0 10px 22px rgba(18,102,122,.28);}}')
            tot = cell_lines(metric, wa, wq, wt) if (wa or wq or wt) else '<div class="none">-</div>'
            cols[7].markdown(f'<div class="calx"><div class="cd wk"><div class="top"><span class="n">Week</span></div>'
                             f'{tot}</div></div>', unsafe_allow_html=True)

    if css:
        st.markdown("<style>" + " ".join(css) + "</style>", unsafe_allow_html=True)


def day_detail(cdf, month):
    """Site-wise qty / amount for the clicked calendar day, with grade-wise rows inside each site."""
    sel = st.session_state.get("cal_sel")
    if not sel or not sel.startswith(month):
        st.caption("Click any day to see its site-wise and grade-wise breakdown below.")
        return
    st.markdown('<div id="day-detail-anchor" style="scroll-margin-top:70px"></div>',
                unsafe_allow_html=True)
    dd = cdf[cdf["date"] == sel]
    dt = pd.to_datetime(sel)
    if dd.empty:
        st.info(f"No entries on {dt.strftime('%d %B %Y')}.")
        scroll_to_detail()
        return
    tot_amt = float(dd["amount"].sum())
    head = (
        f'<div class="dd-head"><div class="big">{dt.day}</div>'
        f'<div><div class="wd">{dt.strftime("%A")}</div><div class="my">{dt.strftime("%B %Y")}</div></div>'
        f'<div class="dd-chips">'
        f'<div class="dd-chip"><div class="l">Amount</div><div class="v">{rs(tot_amt)}</div></div>'
        f'<div class="dd-chip"><div class="l">Total Qty</div><div class="v">{dd["qty"].sum():,.2f}</div></div>'
        f'<div class="dd-chip"><div class="l">Sites</div><div class="v">{dd.loc[dd["site"] != "Not set", "site"].nunique():,}</div></div>'
        f'<div class="dd-chip"><div class="l">Trips</div><div class="v">{int(dd["trips"].sum()):,}</div></div>'
        f'<div class="dd-chip"><div class="l">Entries</div><div class="v">{len(dd):,}</div></div>'
        f'</div></div>'
    )
    det = (dd.groupby("site", as_index=False)[["qty", "amount", "trips"]].sum()
           .sort_values("amount", ascending=False))
    rows = ""
    for r in det.itertuples():
        share = (r.amount / tot_amt * 100) if tot_amt else 0
        sname = "Site not set" if r.site == "Not set" else str(r.site)
        sdf = dd[dd["site"] == r.site]
        units = sdf["unit"].unique()
        unit_txt = escape(str(units[0])) if len(units) == 1 else ""
        dg = (sdf.groupby(["material", "unit"])[["qty", "trips"]].sum()
              .sort_values("qty", ascending=False))
        grade_html = "".join(
            f'<span><b>{escape(str(m))}</b>'
            f' | {x.qty:,.2f} {escape(str(u))} | {int(x.trips)} trips</span>'
            for (m, u), x in dg.iterrows())
        rows += (
            f'<div class="mrow"><div class="mt"><span class="nm">{escape(sname)}</span>'
            f'<span class="qt">Qty {r.qty:,.2f} {unit_txt} | {int(r.trips)} trips</span>'
            f'<span class="am">{rs(r.amount)}</span></div>'
            f'<div class="tr"><i style="width:{max(share, 2):.0f}%"></i></div>'
            f'<div class="sites">{grade_html}</div>'
            f'<div class="sb">{share:.0f}% of the day\'s amount</div></div>'
        )
    st.markdown(head + rows, unsafe_allow_html=True)
    scroll_to_detail()


def flash(msg):
    st.session_state["flash"] = msg
    st.rerun()


def pick_one(col, label, options, key):
    """Pick a Site / TM Number from the master list ('(none)' = empty)."""
    choice = col.selectbox(label, ["(none)"] + options, key=key)
    if not options:
        col.caption(f"Open the 'Plants & Materials' page to add a {label.lower()}.")
    return "" if choice == "(none)" else choice


def in_clause(col, vals):
    if not vals:
        return "", []
    return f" AND {col} IN ({','.join('?' * len(vals))})", list(vals)


def delete_entries_by_ids(ids):
    with conn() as c:
        for i in range(0, len(ids), 500):
            chunk = ids[i:i + 500]
            c.execute(f"DELETE FROM entries WHERE id IN ({','.join('?' * len(chunk))})", chunk)


def duplicate_delete_ui(prefix):
    """List duplicate entries and delete them with one button (the oldest entry is kept)."""
    dups = q("SELECT id, date AS Date, plant AS Plant, material AS Material, site AS Site,"
             " location AS 'TM Number', serial_no AS 'Serial No', qty AS Qty, rate AS Rate,"
             " amount AS Amount, dup_count AS 'Total copies'"
             " FROM entries_v WHERE dup_rank > 1 ORDER BY date, id")
    st.caption("Duplicate rule: with a Serial No, the same Serial No + Plant. Without one, the same Date, Plant, "
               "Material, Site, TM Number, Qty and Rate. The oldest entry is kept and the rest are deleted.")
    if dups.empty:
        st.success("No duplicate entries found.")
        return
    st.warning(f"{len(dups):,} duplicate entries found (the original of each will be kept).")
    st.dataframe(dups, hide_index=True, use_container_width=True)
    typed = st.text_input("Type DELETE to confirm", key=f"{prefix}_dup_confirm")
    if st.button(f"Delete {len(dups):,} duplicates", type="primary",
                 disabled=typed.strip().upper() != "DELETE", key=f"{prefix}_dup_btn"):
        delete_entries_by_ids(dups["id"].tolist())
        flash(f"{len(dups):,} duplicate entries deleted.")


def delete_simple(table, label, mode):
    """Delete from the Site / TM Number master list (old entries keep the name as it is)."""
    rows = q(f"SELECT id, name FROM {table} ORDER BY name")
    if rows.empty:
        st.info(f"There are no {label.lower()}s yet.")
        return
    names = dict(zip(rows["id"].tolist(), rows["name"].tolist()))
    if mode == "Single delete":
        ids = [st.selectbox(f"Select {label.lower()}", list(names), format_func=lambda i: names[i],
                            key=f"ds1_{table}")]
    else:
        ids = st.multiselect(f"Select {label.lower()} (one or more)", list(names),
                             format_func=lambda i: names[i], key=f"dsb_{table}")
    if not ids:
        return
    st.caption("This only removes it from the dropdown list. Old entries keep this name.")
    ok = True
    if mode == "Bulk delete":
        ok = st.text_input("Type DELETE to confirm",
                           key=f"dst_{table}").strip().upper() == "DELETE"
    if st.button(f"Delete {len(ids)} {label.lower()}", type="primary", disabled=not ok,
                 key=f"dsbtn_{table}_{mode}"):
        with conn() as c:
            c.execute(f"DELETE FROM {table} WHERE id IN ({','.join('?' * len(ids))})", ids)
        flash(f"{len(ids)} {label.lower()}(s) deleted.")


def delete_master(table, fk, label, mode):
    """Delete Plants / Materials (single or bulk). If entries exist, offer to delete them too."""
    rows = q(f"SELECT t.id, t.name, (SELECT COUNT(*) FROM entries e WHERE e.{fk} = t.id) AS n"
             f" FROM {table} t ORDER BY t.name")
    if rows.empty:
        st.info(f"There are no {label.lower()}s yet.")
        return
    info = dict(zip(rows["id"].tolist(), zip(rows["name"].tolist(), rows["n"].tolist())))

    def fmt(i):
        return f"{info[i][0]}  ({info[i][1]} entries)"

    if mode == "Single delete":
        ids = [st.selectbox(f"Select {label.lower()}", list(info), format_func=fmt, key=f"dm1_{table}")]
    else:
        ids = st.multiselect(f"Select {label.lower()} (one or more)", list(info),
                             format_func=fmt, key=f"dmb_{table}")
    if not ids:
        return

    n = sum(info[i][1] for i in ids)
    ok, cascade = True, False
    if n:
        st.warning(f"{n} data entries are linked to these. They must be deleted too.")
        cascade = st.checkbox(f"Yes, permanently delete their {n} entries as well",
                              key=f"dmc_{table}_{mode}")
        ok = cascade
    if mode == "Bulk delete":
        typed = st.text_input("Type DELETE to confirm", key=f"dmt_{table}")
        ok = ok and typed.strip().upper() == "DELETE"

    if st.button(f"Delete {len(ids)} {label.lower()}", type="primary", disabled=not ok,
                 key=f"dmbtn_{table}_{mode}"):
        ph = ",".join("?" * len(ids))
        with conn() as c:
            if cascade:
                c.execute(f"DELETE FROM entries WHERE {fk} IN ({ph})", ids)
            c.execute(f"DELETE FROM {table} WHERE id IN ({ph})", ids)
        flash(f"{len(ids)} {label.lower()}(s) deleted" + (f" (and {n} entries)." if n else "."))


# ------------------------------------------------------------------ MAIN MENU
PAGES = [("Dashboard", "📊"), ("Data Entry", "📝"), ("Edit Entry", "✏️"),
         ("Bulk Upload", "📤"), ("Plants & Materials", "🏭")]
MENU_ICONS = {"Dashboard": ":material/dashboard:", "Data Entry": ":material/add_circle:",
              "Edit Entry": ":material/edit:", "Bulk Upload": ":material/upload_file:",
              "Plants & Materials": ":material/factory:"}


def toggle_menu():
    st.session_state["menu_open"] = not st.session_state.get("menu_open", False)


def go_page(name):
    st.session_state["page"] = name
    st.session_state["menu_open"] = False
    st.session_state["page_n"] = st.session_state.get("page_n", 0) + 1


def nav_menu():
    """Square menu button on the right of the header plus a simple list. Returns the selected page name."""
    page = st.session_state.setdefault("page", "Dashboard")
    is_open = st.session_state.get("menu_open", False)
    page_anim = "pageInA" if st.session_state.get("page_n", 0) % 2 else "pageInB"
    spin = "spinOpen" if is_open else "spinClose"
    st.markdown(
        "<style>"
        f".st-key-pagebody {{ animation: {page_anim} .45s ease; }}"
        f".st-key-menu_btn span[data-testid=\"stIconMaterial\"] {{ animation: {spin} .3s ease; }}"
        "</style>",
        unsafe_allow_html=True,
    )
    with st.container(key="headrow"):
        c1, c2 = st.columns([12, 1])
        c1.markdown(
            f'<div class="banner"><span class="t">Plant Data</span>'
            f'<span class="s">{escape(page)}</span></div>',
            unsafe_allow_html=True,
        )
        c2.button("Menu", key="menu_btn", icon=":material/close:" if is_open else ":material/menu:",
                  help="Menu", on_click=toggle_menu)
        if is_open:
            with st.container(key="menulist"):
                for i, (name, _emoji) in enumerate(PAGES):
                    st.button(name, key=f"nav_{i}", on_click=go_page, args=(name,),
                              type="primary" if name == page else "secondary")
    return page


# ------------------------------------------------------------------ APP
init_db()
page = nav_menu()


with st.container(key="pagebody"):
    # ---------------------------------------------------------------- BULK UPLOAD
    if page == "Bulk Upload":
        if "flash" in st.session_state:
            st.success(st.session_state.pop("flash"))
        st.subheader("Bulk Upload — Excel / CSV")
        st.write("Import multiple entries at once from Excel or CSV. A preview and validation are shown before importing.")
        plants_bulk = q("SELECT name FROM plants ORDER BY name")["name"].tolist()
        mats_bulk = q("SELECT name, unit FROM materials ORDER BY name")
        sites_bulk = q("SELECT name FROM sites ORDER BY name")["name"].tolist()

        template_cols = ["Date", "Plant Name", "Material Description", "Site", "TM Number", "TM Name",
                         "Serial No", "Qty", "Rate"]
        template_df = pd.DataFrame([
            {"Date": "2026-10-01", "Plant Name": plants_bulk[0] if plants_bulk else "Add plant first",
             "Material Description": mats_bulk.iloc[0]["name"] if not mats_bulk.empty else "Add material first",
             "Site": sites_bulk[0] if sites_bulk else "", "TM Number": "", "TM Name": "",
             "Serial No": "", "Qty": 10, "Rate": 100}
        ], columns=template_cols)
        st.download_button(
            "Download Excel Template",
            data=df_to_excel_bytes(template_df),
            file_name="plant_bulk_upload_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            help="Replace the sample row with your own data."
        )
        st.caption("Required columns: Date, Plant Name, Material Description, Qty, Rate. Site, TM Number, TM Name and Serial No are optional. Amount is calculated as Qty × Rate.")
        skip_dups = st.checkbox("Skip duplicate rows (already in the database or repeated in the file)",
                                value=True, key="bulk_skip_dups")
        uploaded = st.file_uploader("Select an Excel (.xlsx) or CSV file", type=["xlsx", "csv"], key="bulk_upload_file")

        if uploaded is not None:
            try:
                if uploaded.name.lower().endswith(".csv"):
                    raw_bulk = pd.read_csv(uploaded)
                else:
                    raw_bulk = pd.read_excel(uploaded)
                raw_bulk.columns = [str(c).strip() for c in raw_bulk.columns]
                # Common column name alternatives are accepted.
                aliases = {
                    "date": "Date", "entry date": "Date",
                    "plant": "Plant Name", "plant name": "Plant Name",
                    "material": "Material Description", "material description": "Material Description",
                    "site": "Site", "tm number": "TM Number", "tm no": "TM Number", "location": "TM Number",
                    "tm name": "TM Name", "vendor": "TM Name", "vendor name": "TM Name",
                    "serial no": "Serial No", "serial": "Serial No", "sr no": "Serial No", "sr. no": "Serial No",
                    "slip no": "Serial No", "challan no": "Serial No",
                    "qty": "Qty", "quantity": "Qty", "rate": "Rate", "amount": "Amount"
                }
                rename_map = {col: aliases.get(str(col).strip().lower(), str(col).strip()) for col in raw_bulk.columns}
                raw_bulk = raw_bulk.rename(columns=rename_map)
                required = ["Date", "Plant Name", "Material Description", "Qty", "Rate"]
                missing = [col for col in required if col not in raw_bulk.columns]
                if missing:
                    st.error("Required columns missing: " + ", ".join(missing))
                    st.info("Download the template and keep the columns in the same format.")
                else:
                    raw_bulk = raw_bulk.dropna(how="all").copy()
                    valid_rows = []
                    errors = []
                    plant_map = {str(n).strip().casefold(): str(n).strip() for n in plants_bulk}
                    material_map = {str(n).strip().casefold(): (str(n).strip(), str(u)) for n, u in mats_bulk[["name", "unit"]].itertuples(index=False, name=None)}
                    for idx, row in raw_bulk.iterrows():
                        excel_row = idx + 2
                        try:
                            if pd.isna(row["Date"]) or str(row["Date"]).strip() == "":
                                raise ValueError("Date missing")
                            parsed_date = pd.to_datetime(row["Date"], dayfirst=True, errors="raise")
                            plant_in = str(row["Plant Name"]).strip()
                            material_in = str(row["Material Description"]).strip()
                            plant_key, material_key = plant_in.casefold(), material_in.casefold()
                            if not plant_in or plant_key not in plant_map:
                                raise ValueError(f"Plant '{plant_in}' is not in the Plants & Materials list")
                            if not material_in or material_key not in material_map:
                                raise ValueError(f"Material '{material_in}' is not in the master list")
                            qty_val = pd.to_numeric(row["Qty"], errors="raise")
                            rate_val = pd.to_numeric(row["Rate"], errors="raise")
                            if pd.isna(qty_val) or float(qty_val) <= 0:
                                raise ValueError("Qty must be greater than zero")
                            if pd.isna(rate_val) or float(rate_val) < 0:
                                raise ValueError("Rate cannot be negative")
                            valid_rows.append({
                                "Excel Row": excel_row,
                                "Date": parsed_date.date().isoformat(),
                                "Plant Name": plant_map[plant_key],
                                "Material Description": material_map[material_key][0],
                                "Site": clean_txt(row.get("Site")) if "Site" in raw_bulk.columns else "",
                                "TM Number": clean_txt(row.get("TM Number")) if "TM Number" in raw_bulk.columns else "",
                                "TM Name": clean_txt(row.get("TM Name")) if "TM Name" in raw_bulk.columns else "",
                                "Serial No": clean_txt(row.get("Serial No")) if "Serial No" in raw_bulk.columns else "",
                                "Qty": float(qty_val), "Rate": float(rate_val),
                                "Amount": float(qty_val) * float(rate_val)
                            })
                        except Exception as exc:
                            errors.append({"Excel Row": excel_row, "Error": str(exc)})

                    # duplicates: already in the database or repeated within this file
                    existing = existing_key_map() if skip_dups else {}
                    seen, to_import, dup_rows = set(), [], []
                    for item in valid_rows:
                        k = dup_key(item["Date"], item["Plant Name"], item["Material Description"],
                                    item["Site"], item["TM Number"], item["Qty"], item["Rate"], item["Serial No"])
                        if skip_dups and (k in existing or k in seen):
                            dup_rows.append({"Excel Row": item["Excel Row"], "Date": item["Date"],
                                             "Plant Name": item["Plant Name"], "Serial No": item["Serial No"],
                                             "Qty": item["Qty"],
                                             "Reason": ("Already in database" if k in existing
                                                        else "Repeated in file")})
                            continue
                        seen.add(k)
                        to_import.append(item)

                    preview = pd.DataFrame(to_import)
                    st.markdown("#### Import preview")
                    mc1, mc2, mc3 = st.columns(3)
                    mc1.metric("Rows to import", f"{len(preview):,}")
                    mc2.metric("Duplicates skipped", f"{len(dup_rows):,}")
                    mc3.metric("Rows with errors", f"{len(errors):,}")
                    if not preview.empty:
                        st.dataframe(preview, hide_index=True, use_container_width=True)
                    if dup_rows:
                        with st.expander("Skipped duplicate rows"):
                            st.dataframe(pd.DataFrame(dup_rows), hide_index=True, use_container_width=True)
                    if errors:
                        with st.expander("Validation errors — correct these rows in Excel"):
                            st.dataframe(pd.DataFrame(errors), hide_index=True, use_container_width=True)
                    if not preview.empty and not errors:
                        if not skip_dups:
                            st.warning("Duplicate skipping is off: if you import the file again, the entries will be added again.")
                        confirm_bulk = st.checkbox("I have checked the preview; import these entries.", key="bulk_confirm_import")
                        if st.button("Import all rows", type="primary", disabled=not confirm_bulk, key="bulk_import_btn"):
                            inserted = 0
                            with conn() as c:
                                for item in to_import:
                                    plant_id = c.execute("SELECT id FROM plants WHERE name=?", (item["Plant Name"],)).fetchone()[0]
                                    material_id = c.execute("SELECT id FROM materials WHERE name=?", (item["Material Description"],)).fetchone()[0]
                                    site_val = item["Site"] or None
                                    tm_val = item["TM Number"] or None
                                    c.execute(
                                        "INSERT INTO entries(entry_date, plant_id, material_id, site, location, serial_no, qty, rate, amount) VALUES(?,?,?,?,?,?,?,?,?)",
                                        (item["Date"], plant_id, material_id, site_val, tm_val, item["Serial No"] or None,
                                         item["Qty"], item["Rate"], item["Amount"])
                                    )
                                    if site_val:
                                        c.execute("INSERT OR IGNORE INTO sites(name) VALUES(?)", (site_val,))
                                    if tm_val:
                                        c.execute("INSERT INTO locations(name, vendor) VALUES(?,?) ON CONFLICT(name) DO UPDATE "
                                                  "SET vendor = COALESCE(NULLIF(excluded.vendor,''), locations.vendor)",
                                                  (tm_val, item["TM Name"] or None))
                                    inserted += 1
                            st.session_state["flash"] = (f"Successfully imported {inserted:,} entries"
                                                         + (f" ({len(dup_rows):,} duplicates skipped)." if dup_rows else "."))
                            st.rerun()
            except Exception as exc:
                st.error(f"Could not read the file: {exc}")
                st.info("Save the Excel file as .xlsx, or use CSV in UTF-8 format.")


    # ---------------------------------------------------------------- MASTER
    if page == "Plants & Materials":
        c1, c2 = st.columns(2)
        with c1, st.container(border=True):
            st.subheader("Add plant")
            new_plant = st.text_input("Plant name", key="np")
            if st.button("Save plant"):
                if new_plant.strip():
                    try:
                        run("INSERT INTO plants(name) VALUES(?)", (new_plant.strip(),))
                        st.success("Plant saved")
                    except sqlite3.IntegrityError:
                        st.error("This plant already exists")
            st.dataframe(q("SELECT name AS Plant FROM plants ORDER BY name"),
                         hide_index=True, use_container_width=True)
        with c2, st.container(border=True):
            st.subheader("Add material")
            new_mat = st.text_input("Material description", key="nm")
            new_unit = st.text_input("Unit (MT, Cum, Ltr...)", key="nu")
            if st.button("Save material"):
                if new_mat.strip() and new_unit.strip():
                    try:
                        run(
                            "INSERT INTO materials(name, unit) VALUES(?, ?)",
                            (new_mat.strip(), new_unit.strip()),
                        )
                        st.success("Material saved")
                    except sqlite3.IntegrityError:
                        st.error("This material already exists")
            st.dataframe(
                q("SELECT name AS Material, unit AS Unit FROM materials ORDER BY name"),
                hide_index=True, use_container_width=True,
            )

        c3, c4 = st.columns(2)
        for col, table, label, title, key in ((c3, "sites", "site", "Site", "ns"),
                                              (c4, "locations", "TM number", "TM Number", "nl")):
            with col, st.container(border=True):
                st.subheader(f"Add {label}")
                nv = st.text_input(f"{title} (name / number)", key=key)
                vendor = ""
                if table == "locations":
                    vendor = st.text_input("TM Name (vendor name)", key="nlv").strip()
                if st.button(f"Save {label}", key=f"save_{key}"):
                    if nv.strip():
                        if table == "locations":
                            existed = not q("SELECT 1 FROM locations WHERE name=?", (nv.strip(),)).empty
                            save_tm(nv.strip(), vendor)
                            st.success("TM Number updated" if existed else "TM Number saved")
                        else:
                            try:
                                run(f"INSERT INTO {table}(name) VALUES(?)", (nv.strip(),))
                                st.success(f"{title} saved")
                            except sqlite3.IntegrityError:
                                st.error(f"This {label} already exists")
                if table == "locations":
                    st.dataframe(q("SELECT name AS \"TM Number\", COALESCE(vendor, '') AS \"TM Name\""
                                   " FROM locations ORDER BY name"),
                                 hide_index=True, use_container_width=True)
                else:
                    st.dataframe(q(f'SELECT name AS "{title}" FROM {table} ORDER BY name'),
                                 hide_index=True, use_container_width=True)

        # ---------------- DELETE ----------------
        with st.container(border=True):
            st.subheader("Delete")
            if "flash" in st.session_state:
                st.success(st.session_state.pop("flash"))
            x1, x2 = st.columns(2)
            what = x1.radio("What do you want to delete?", ["Data entries", "Duplicate entries", "Plants", "Materials", "Sites", "TM Numbers"],
                            horizontal=True, key="del_what")
            mode = x2.radio("Option", ["Single delete", "Bulk delete"],
                            horizontal=True, key="del_mode")

            if what == "Duplicate entries":
                duplicate_delete_ui("pm")
            elif what == "Plants":
                delete_master("plants", "plant_id", "Plant", mode)
            elif what == "Materials":
                delete_master("materials", "material_id", "Material", mode)
            elif what == "Sites":
                delete_simple("sites", "Site", mode)
            elif what == "TM Numbers":
                delete_simple("locations", "TM Number", mode)
            elif mode == "Single delete":
                srch = st.text_input("Search (ID, Serial No, TM Number, TM Name, plant, material, site, date...)",
                                     key="del_search", placeholder="e.g. 1234 ABC")
                sc, sp = sql_search(srch)
                recent = q("SELECT id, date, plant, material, unit, site, location, tm_name, serial_no, qty, amount"
                           " FROM entries_v WHERE 1=1" + sc + " ORDER BY date DESC, id DESC LIMIT 1000", tuple(sp))
                if recent.empty:
                    st.info("No entries found.")
                else:
                    st.caption(f"{len(recent):,} entries found (showing up to 1000).")
                    labels = {
                        int(r.id): (f"#{r.id} | {r.date} | {r.plant} | {r.material} | "
                                    f"{r.qty:,.2f} {r.unit} | {rs(r.amount)} | {r.site} / {r.location}"
                                    + (f" | SN {r.serial_no}" if r.serial_no else "")
                                    + (f" | {r.tm_name}" if r.tm_name != "Not set" else ""))
                        for r in recent.itertuples()
                    }
                    pick = st.selectbox("Select entry", list(labels), format_func=lambda i: labels[i], key="del_one")
                    if st.button("Delete this entry", type="primary", key="btn_del_one"):
                        delete_entries_by_ids([pick])
                        flash(f"Entry #{pick} deleted.")
            else:
                allv = q("SELECT date, plant, material, site, location FROM entries_v")
                if allv.empty:
                    st.info("There are no entries yet.")
                else:
                    d0 = pd.to_datetime(allv["date"]).min().date()
                    d1 = pd.to_datetime(allv["date"]).max().date()
                    r1, r2 = st.columns(2)
                    rng = r1.date_input("Date range", value=(d0, d1), min_value=d0, max_value=d1,
                                        format="DD/MM/YYYY", key="bulk_rng")
                    bp = r2.multiselect("Plant", sorted(allv["plant"].unique()),
                                        placeholder="All plants", key="bulk_p")
                    r3, r4, r5 = st.columns(3)
                    bm = r3.multiselect("Material", sorted(allv["material"].unique()),
                                        placeholder="All materials", key="bulk_m")
                    bs = r4.multiselect("Site", sorted(allv["site"].unique()),
                                        placeholder="All sites", key="bulk_s")
                    bl = r5.multiselect("TM Number", sorted(allv["location"].unique()),
                                        placeholder="All TM numbers", key="bulk_l")
                    btxt = st.text_input("Search text (optional): ID, Serial No, TM Name...", key="bulk_search")
                    if not (isinstance(rng, (tuple, list)) and len(rng) == 2):
                        st.info("Select both dates of the range (from and to).")
                    else:
                        sql = ("SELECT id, date, plant, material, site, location, tm_name, serial_no, qty, amount"
                               " FROM entries_v WHERE date BETWEEN ? AND ?")
                        params = [rng[0].isoformat(), rng[1].isoformat()]
                        for col, vals in (("plant", bp), ("material", bm), ("site", bs), ("location", bl)):
                            cl, pr = in_clause(col, vals)
                            sql += cl
                            params += pr
                        sc, sp = sql_search(btxt)
                        sql += sc
                        params += sp
                        hit = q(sql + " ORDER BY date, id", tuple(params))
                        m1, m2 = st.columns(2)
                        m1.metric("Entries to be deleted", f"{len(hit):,}")
                        m2.metric("Total amount", rs(hit["amount"].sum()))
                        if hit.empty:
                            st.info("No entries match these filters.")
                        else:
                            with st.expander("View the list of entries"):
                                st.dataframe(hit, hide_index=True, use_container_width=True)
                            typed = st.text_input("Type DELETE to confirm", key="bulk_confirm")
                            if st.button(f"Delete {len(hit):,} entries", type="primary",
                                         disabled=typed.strip().upper() != "DELETE", key="btn_bulk"):
                                delete_entries_by_ids(hit["id"].tolist())
                                flash(f"{len(hit):,} entries deleted.")

    # ---------------------------------------------------------------- ENTRY
    if page == "Data Entry":
        plants = q("SELECT * FROM plants ORDER BY name")
        mats = q("SELECT * FROM materials ORDER BY name")
        if plants.empty or mats.empty:
            st.info("First add at least one plant and one material on the 'Plants & Materials' page.")
        else:
            with st.container(border=True):
                st.subheader("New entry")
                a, b, c = st.columns(3)
                d = a.date_input("Date", date.today())
                plant = b.selectbox("Plant name", plants["name"])
                mat = c.selectbox("Material description", mats["name"])
                unit = mats.loc[mats["name"] == mat, "unit"].iloc[0]

                sites = q("SELECT name FROM sites ORDER BY name")["name"].tolist()
                s1, s2, s3 = st.columns(3)
                site = pick_one(s1, "Site", sites, "site_sel")
                location = s2.text_input("TM Number", key="tm_no", placeholder="e.g. 1234").strip()
                tm_vendor = s3.text_input("TM Name (vendor)", key="tm_vendor",
                                          placeholder="Vendor name").strip()
                if location:
                    old = q("SELECT vendor FROM locations WHERE name=?", (location,))
                    if not old.empty and old.iloc[0, 0]:
                        s3.caption(f"Saved vendor: {old.iloc[0, 0]}")

                x1, x2, _x3 = st.columns(3)
                serial = x1.text_input("Serial No (slip / challan no.)", key="serial_no",
                                       placeholder="Optional - used to detect duplicates").strip()
                no_dup = x2.checkbox("Do not allow duplicate entries", value=True, key="no_dup_entry",
                                     help="On: an entry that already exists will not be saved again.")

                e, f, g = st.columns(3)
                qty = e.number_input(f"Qty ({unit})", min_value=0.0, step=1.0, format="%.2f")
                rate = f.number_input("Rate", min_value=0.0, step=1.0, format="%.2f")
                amount = qty * rate
                g.metric("Amount", rs(amount))

                if st.button("Save entry", type="primary"):
                    if qty <= 0:
                        st.error("Qty must be greater than zero")
                    else:
                        dup_ids = (find_duplicates(d.isoformat(), plant, mat, site, location, qty, rate, serial)
                                   if no_dup else [])
                        if dup_ids:
                            st.error("Duplicate entry: this entry already exists (ID "
                                     + ", ".join(f"#{i}" for i in dup_ids[:5])
                                     + "). Not saved. To save it anyway, turn off 'Do not allow duplicate entries'.")
                        else:
                            pid = int(plants.loc[plants["name"] == plant, "id"].iloc[0])
                            mid = int(mats.loc[mats["name"] == mat, "id"].iloc[0])
                            run(
                                "INSERT INTO entries(entry_date, plant_id, material_id, site, location, serial_no, qty, rate, amount)"
                                " VALUES(?,?,?,?,?,?,?,?,?)",
                                (d.isoformat(), pid, mid, site or None, location or None, serial or None,
                                 qty, rate, amount),
                            )
                            if location:  # also save the TM number + vendor in the master so they show in filters
                                save_tm(location, tm_vendor)
                            last = q(
                                "SELECT cum_qty, cum_amount FROM entries_v"
                                " WHERE plant=? AND material=? AND month=? ORDER BY date DESC, id DESC LIMIT 1",
                                (plant, mat, d.isoformat()[:7]),
                            ).iloc[0]
                            st.success(
                                f"Saved. This month's cumulative: {last.cum_qty:,.2f} {unit} / {rs(last.cum_amount)}"
                            )

    # ---------------------------------------------------------------- EDIT
    if page == "Edit Entry":
        with st.container(border=True):
            st.subheader("Edit entry (by ID number)")
            eid = int(st.number_input("Entry ID", min_value=1, step=1, key="edit_id"))
            row = q("SELECT * FROM entries WHERE id = ?", (eid,))
            e_plants = q("SELECT * FROM plants ORDER BY name")
            e_mats = q("SELECT * FROM materials ORDER BY name")

            if row.empty:
                st.warning(f"No entry found with ID {eid}.")
            else:
                r = row.iloc[0]
                p_names = e_plants["name"].tolist()
                m_names = e_mats["name"].tolist()
                cur_p = e_plants.loc[e_plants["id"] == r["plant_id"], "name"].iloc[0]
                cur_m = e_mats.loc[e_mats["id"] == r["material_id"], "name"].iloc[0]
                site_opts = ["(none)"] + q("SELECT name FROM sites ORDER BY name")["name"].tolist()
                cur_site = (r["site"] or "").strip() or "(none)"
                if cur_site not in site_opts:
                    site_opts.append(cur_site)
                k = f"_{eid}"  # changing the ID refills the form with that entry's data

                a, b, c = st.columns(3)
                n_date = a.date_input("Date", date.fromisoformat(r["entry_date"]),
                                      format="DD/MM/YYYY", key="ed_date" + k)
                n_plant = b.selectbox("Plant name", p_names, index=p_names.index(cur_p), key="ed_plant" + k)
                n_mat = c.selectbox("Material description", m_names, index=m_names.index(cur_m), key="ed_mat" + k)
                n_unit = e_mats.loc[e_mats["name"] == n_mat, "unit"].iloc[0]

                s1, s2, s3 = st.columns(3)
                n_site = s1.selectbox("Site", site_opts, index=site_opts.index(cur_site), key="ed_site" + k)
                n_tm = s2.text_input("TM Number", value=(r["location"] or ""), key="ed_tm" + k).strip()
                cur_vendor = ""
                if r["location"]:
                    vv = q("SELECT vendor FROM locations WHERE name=?", (r["location"],))
                    if not vv.empty and vv.iloc[0, 0]:
                        cur_vendor = vv.iloc[0, 0]
                n_vendor = s3.text_input("TM Name (vendor)", value=cur_vendor, key="ed_vendor" + k).strip()

                x1, x2, _x3 = st.columns(3)
                n_serial = x1.text_input("Serial No", value=clean_txt(r["serial_no"]),
                                         key="ed_serial" + k).strip()
                n_nodup = x2.checkbox("Do not allow duplicates", value=True, key="ed_nodup" + k)

                e, f, g = st.columns(3)
                n_qty = e.number_input(f"Qty ({n_unit})", min_value=0.0, value=float(r["qty"]),
                                       step=1.0, format="%.2f", key="ed_qty" + k)
                n_rate = f.number_input("Rate", min_value=0.0, value=float(r["rate"]),
                                        step=1.0, format="%.2f", key="ed_rate" + k)
                g.metric("Amount", rs(n_qty * n_rate))

                if st.button("Save changes", type="primary", key="ed_save" + k):
                    if n_qty <= 0:
                        st.error("Qty must be greater than zero")
                    else:
                        site_txt = "" if n_site == "(none)" else n_site
                        dup_ids = (find_duplicates(n_date.isoformat(), n_plant, n_mat, site_txt, n_tm,
                                                   n_qty, n_rate, n_serial, exclude_id=eid)
                                   if n_nodup else [])
                        if dup_ids:
                            st.error("Duplicate entry: a matching entry already exists (ID "
                                     + ", ".join(f"#{i}" for i in dup_ids[:5]) + "). Changes were not saved.")
                        else:
                            pid = int(e_plants.loc[e_plants["name"] == n_plant, "id"].iloc[0])
                            mid = int(e_mats.loc[e_mats["name"] == n_mat, "id"].iloc[0])
                            run(
                                "UPDATE entries SET entry_date=?, plant_id=?, material_id=?, site=?,"
                                " location=?, serial_no=?, qty=?, rate=?, amount=? WHERE id=?",
                                (n_date.isoformat(), pid, mid, site_txt or None, n_tm or None,
                                 n_serial or None, n_qty, n_rate, n_qty * n_rate, eid),
                            )
                            if n_tm:
                                save_tm(n_tm, n_vendor)
                            st.success(f"Entry #{eid} updated. Cumulative values are recalculated automatically.")

        with st.expander("Don't remember the ID? View the latest entries"):
            latest = q("SELECT id, date AS Date, plant AS Plant, material AS Material, site AS Site,"
                       " location AS 'TM Number', tm_name AS 'TM Name', serial_no AS 'Serial No', qty AS Qty, rate AS Rate, amount AS Amount"
                       " FROM entries_v ORDER BY date DESC, id DESC LIMIT 100")
            st.dataframe(latest, hide_index=True, use_container_width=True)

    # ------------------------------------------------------------- DASHBOARD
    if page == "Dashboard":
        if "flash" in st.session_state:
            st.success(st.session_state.pop("flash"))
        df = q("SELECT * FROM entries_v")
        df["trips"] = (df["location"] != "Not set").astype(int)  # 1 entry with a TM number = 1 trip
        if df.empty:
            st.info("There are no entries yet. Add the first entry on the Data Entry page.")
        else:
            dmin = pd.Period(df["month"].min()).start_time.date()
            dmax = pd.Period(df["month"].max()).end_time.date()
            dlast = pd.to_datetime(df["date"]).max().date()

            with st.container(border=True):
                left, right = st.columns(2)
                picked = left.date_input("Month (pick any date in the month)",
                                         value=dlast, min_value=dmin, max_value=dmax,
                                         format="DD/MM/YYYY", key="dash_date")
                plant_f = right.multiselect("Plant (select one or more; empty = all plants)",
                                            sorted(df["plant"].unique()),
                                            placeholder="All plants")
                g1, g2, g3, g4 = st.columns(4)
                site_f = g1.multiselect("Site (empty = all sites)",
                                        sorted(df["site"].unique()), placeholder="All sites")
                loc_f = g2.multiselect("TM Number (empty = all)",
                                       sorted(df["location"].unique()), placeholder="All TM numbers")
                tmn_f = g3.multiselect("TM Name / Vendor (empty = all)",
                                       sorted(df["tm_name"].unique()), placeholder="All vendors")
                mat_f = g4.multiselect("Material Description (empty = all)",
                                       sorted(df["material"].unique()), placeholder="All materials")
                plant_txt = ", ".join(plant_f) if plant_f else "All plants"
                if site_f:
                    plant_txt += " | Site: " + ", ".join(site_f)
                if loc_f:
                    plant_txt += " | TM Number: " + ", ".join(loc_f)
                if tmn_f:
                    plant_txt += " | TM Name: " + ", ".join(tmn_f)
                if mat_f:
                    plant_txt += " | Material: " + ", ".join(mat_f)
                pf0 = st.session_state.get("pie_filter")
                if pf0 and pf0["vals"]:
                    plant_txt += f" | Pie {pf0['label']}: " + ", ".join(pf0["vals"])
                cur = picked.strftime("%Y-%m")
                st.markdown(f'<div class="selm">Showing <b>{pd.Period(cur).strftime("%B %Y")}</b>'
                            f' &nbsp;|&nbsp; {escape(plant_txt)}</div>', unsafe_allow_html=True)
            prev = str(pd.Period(cur) - 1)

            view = df
            if plant_f:
                view = view[view["plant"].isin(plant_f)]
            if site_f:
                view = view[view["site"].isin(site_f)]
            if loc_f:
                view = view[view["location"].isin(loc_f)]
            if tmn_f:
                view = view[view["tm_name"].isin(tmn_f)]
            if mat_f:
                view = view[view["material"].isin(mat_f)]
            # Slices selected in the pie (Grade / Site / Plant / TM Name) filter the whole dashboard.
            view_base = view  # the pie is built from this data so multiple slices can be selected
            pf = st.session_state.get("pie_filter")
            if pf and pf["vals"]:
                view = view[view[pf["col"]].astype(str).isin(pf["vals"])]
            cdf, pdf = view[view["month"] == cur], view[view["month"] == prev]
            cdf_base = view_base[view_base["month"] == cur]

            def delta(a, b):
                if b == 0:
                    return f"No data for {prev}"
                pct = (a - b) / b * 100
                if pct == 0:
                    return f"No change vs {prev}"
                cls, arrow = ("up", "▲") if pct > 0 else ("down", "▼")
                return f'<span class="{cls}">{arrow} {abs(pct):.1f}% vs {prev}</span>'

            kpi_strip(
                cdf["amount"].sum(), delta(cdf["amount"].sum(), pdf["amount"].sum()),
                cdf["qty"].sum(), delta(cdf["qty"].sum(), pdf["qty"].sum()),
                len(cdf),
                f"{cdf['plant'].nunique()} plant(s), {cdf['material'].nunique()} material(s)",
                int(cdf["trips"].sum()), delta(cdf["trips"].sum(), pdf["trips"].sum()),
            )

            # ---------------- Calendar / Day-wise / Month-wise ----------------
            with st.container(border=True):
                t1, t2, t3 = st.columns([5, 4, 4])
                view_by = t1.radio("View as",
                                   ["Calendar", "Day-wise chart", "Month-wise chart", "Grade-wise"],
                                   horizontal=True)
                metric_choice = t2.radio("Show", ["Amount", "Qty", "Trips", "Both"],
                                         horizontal=True)
                extreme_choice = t3.radio("Highest / Lowest", ["All", TOP_HI, TOP_LO],
                                          horizontal=True)

                if view_by == "Calendar":
                    data = cdf.groupby("date")[["amount", "qty", "trips"]].sum()
                    st.subheader(f"Calendar - {cur}")
                    show_extremes(data, metric_choice)
                    calendar_ui(data, cur, metric_choice, extreme_choice)
                    day_detail(cdf, cur)
                elif view_by == "Grade-wise":
                    st.subheader(f"Pie breakdown - {cur}")
                    dims = {"Grade": "material", "Site": "site", "Plant": "plant", "TM Name": "tm_name"}
                    pc1, pc2 = st.columns(2)
                    dim_label = pc1.radio("Pie by", list(dims), horizontal=True, key="pie_dim")
                    pie_metric = pc2.radio("Pie chart metric", ["Both", "Qty", "Amount"], horizontal=True,
                                           key="grade_pie_metric")
                    dim_col = dims[dim_label]
                    reset_n = st.session_state.get("pie_reset_n", 0)
                    # The pie is always built from the data before pie selection, so multiple slices can be picked
                    pie_src = cdf_base if not cdf_base.empty else view_base
                    summary = (pie_src.groupby(dim_col, as_index=False)[["qty", "amount"]]
                               .sum().rename(columns={dim_col: "Label"}))
                    if summary.empty:
                        st.info("No data available for the selected period.")
                    else:
                        if extreme_choice != "All":
                            rank_col = "qty" if pie_metric == "Qty" else "amount"
                            pos = summary[summary[rank_col] > 0]
                            if not pos.empty:
                                summary = (pos.nlargest(4, rank_col) if extreme_choice == TOP_HI
                                           else pos.nsmallest(3, rank_col))
                                st.info(f"{extreme_choice} {dim_label} (by {'Qty' if rank_col == 'qty' else 'Amount'}): "
                                        + ", ".join(summary["Label"].astype(str)))
                        st.caption("Click a slice to select it, click again to unselect. You can select several slices. "
                                   "KPIs, calendar and entries are filtered by the selected slices.")
                        pie_value_cols = (["qty", "amount"] if pie_metric == "Both"
                                          else (["qty"] if pie_metric == "Qty" else ["amount"]))
                        chart_cols = st.columns(len(pie_value_cols))
                        picked_vals = []
                        for chart_idx, pie_value in enumerate(pie_value_cols):
                            pie_data = summary[summary[pie_value] > 0].copy()
                            if pie_data.empty:
                                chart_cols[chart_idx].info("No data for this metric.")
                                continue
                            metric_label = "Qty" if pie_value == "qty" else "Amount (₹)"
                            total_value = float(pie_data[pie_value].sum())
                            pie_data["pct"] = pie_data[pie_value] / total_value * 100
                            pie_data["pct_label"] = pie_data["pct"].map(lambda p: f"{p:.1f}%" if p >= 3 else "")
                            sel_name = f"pie_pick_{pie_value}"
                            selected = alt.selection_point(name=sel_name, fields=["Label"], on="click",
                                                           toggle=True, clear="dblclick", empty=True)
                            theta = alt.Theta(field=pie_value, type="quantitative", stack=True)
                            order = alt.Order(field=pie_value, type="quantitative", sort="descending")
                            donut = alt.Chart(pie_data).mark_arc(
                                innerRadius=62, outerRadius=112, stroke="white", strokeWidth=2
                            ).encode(
                                theta=theta, order=order,
                                color=alt.Color(field="Label", type="nominal", title=dim_label,
                                                scale=alt.Scale(scheme="tableau10"),
                                                legend=alt.Legend(orient="bottom", titleFontSize=12, labelFontSize=11,
                                                                  columns=3, offset=14, symbolLimit=30)),
                                opacity=alt.condition(selected, alt.value(1), alt.value(0.4)),
                                tooltip=[alt.Tooltip("Label:N", title=dim_label),
                                         alt.Tooltip(f"{pie_value}:Q", title=metric_label, format=",.2f"),
                                         alt.Tooltip("pct:Q", title="Share %", format=".1f")],
                            ).add_params(selected)
                            pct_text = alt.Chart(pie_data).mark_text(
                                radius=87, size=12, fontWeight="bold", color="white"
                            ).encode(theta=theta, order=order, text="pct_label:N")
                            center = alt.Chart(pd.DataFrame({"label": ["Total"]})).mark_text(
                                fontSize=13, fontWeight=600, color=INK, dy=-9).encode(text="label:N")
                            center_value = alt.Chart(pd.DataFrame({"label": [
                                f"{total_value:,.2f}" if pie_value == "qty" else f"₹ {total_value:,.2f}"]})).mark_text(
                                fontSize=15, fontWeight=700, color=C_AMOUNT, dy=13).encode(text="label:N")
                            chart = (donut + pct_text + center + center_value).properties(
                                height=270, padding={"top": 12, "bottom": 12, "left": 8, "right": 8})
                            chart_cols[chart_idx].markdown(f"**{dim_label}-wise {metric_label}**")
                            event = chart_cols[chart_idx].altair_chart(
                                chart, use_container_width=True, theme=None,
                                key=f"pie_{dim_col}_{pie_value}_{reset_n}",
                                on_select="rerun", selection_mode=sel_name)
                            try:
                                for p in event.selection.get(sel_name, []):
                                    v = p.get("Label")
                                    if v is not None and str(v) not in picked_vals:
                                        picked_vals.append(str(v))
                            except (AttributeError, TypeError, IndexError):
                                pass

                        if picked_vals:
                            new_pf = {"col": dim_col, "label": dim_label, "vals": sorted(picked_vals)}
                            if st.session_state.get("pie_filter") != new_pf:
                                st.session_state["pie_filter"] = new_pf
                                st.rerun()

                        pf = st.session_state.get("pie_filter")
                        active = bool(pf and pf["vals"])
                        if active:
                            fc, cc = st.columns([4, 1])
                            fc.info(f"Selected {pf['label']}: **{', '.join(pf['vals'])}**")
                            if cc.button("Clear selection", key="pie_clear"):
                                st.session_state.pop("pie_filter", None)
                                st.session_state["pie_reset_n"] = reset_n + 1
                                st.rerun()

                        tbl = summary.copy()
                        tq, ta = float(tbl["qty"].sum()), float(tbl["amount"].sum())
                        tbl["Qty Share %"] = tbl["qty"] / tq * 100 if tq else 0
                        tbl["Amount Share %"] = tbl["amount"] / ta * 100 if ta else 0
                        tbl = tbl.sort_values("amount", ascending=False)
                        if active and pf["col"] == dim_col:
                            sel_rows = tbl[tbl["Label"].isin(pf["vals"])]
                            st.caption(f"Selected total: Qty {sel_rows['qty'].sum():,.2f} "
                                       f"({sel_rows['Qty Share %'].sum():.1f}%)  |  "
                                       f"Amount {rs(sel_rows['amount'].sum())} ({sel_rows['Amount Share %'].sum():.1f}%)")
                            tbl = sel_rows
                        st.dataframe(
                            tbl.rename(columns={"Label": dim_label, "qty": "Qty", "amount": "Amount (₹)"}).style.format(
                                {"Qty": "{:,.2f}", "Amount (₹)": "₹ {:,.2f}",
                                 "Qty Share %": "{:.1f}%", "Amount Share %": "{:.1f}%"}),
                            hide_index=True, use_container_width=True)
                elif view_by == "Day-wise chart":
                    st.subheader(f"Plant-wise day comparison - {cur}")
                    data = cdf.groupby("date")[["amount", "qty", "trips"]].sum()
                    show_extremes(data, metric_choice)
                    if cdf.empty:
                        st.info("No data in this month.")
                    else:
                        specs = {"Amount": [("amount", "Amount (Rs.)")],
                                 "Qty": [("qty", "Qty")],
                                 "Trips": [("trips", "Trips (TM)")],
                                 "Both": [("amount", "Amount (Rs.)"), ("qty", "Qty")]}[metric_choice]
                        cols_ = st.columns(len(specs))
                        for c_, (vc, lb) in zip(cols_, specs):
                            c_.markdown(f"**{lb}**")
                            c_.altair_chart(plant_compare_chart(cdf, vc, lb),
                                            use_container_width=True, theme=None)
                        st.caption("Click a plant in the legend to highlight it.")
                        plant_compare_table(cdf, metric_choice)
                else:
                    data = view.groupby("month")[["amount", "qty", "trips"]].sum()
                    kind, title = "bar", "Month-wise trend (current + back data)"
                    st.subheader(title)
                    show_extremes(data, metric_choice)
                    if metric_choice == "Amount":
                        st.altair_chart(trend_chart(data["amount"], "Amount (Rs.)", kind, C_AMOUNT),
                                        use_container_width=True, theme=None)
                    elif metric_choice == "Qty":
                        st.altair_chart(trend_chart(data["qty"], "Qty", kind, C_QTY),
                                        use_container_width=True, theme=None)
                    elif metric_choice == "Trips":
                        st.altair_chart(trend_chart(data["trips"], "Trips (TM)", kind, "#5E548E"),
                                        use_container_width=True, theme=None)
                    else:
                        col_a, col_b = st.columns(2)
                        col_a.markdown("**Amount**")
                        col_a.altair_chart(trend_chart(data["amount"], "Amount (Rs.)", kind, C_AMOUNT),
                                           use_container_width=True, theme=None)
                        col_b.markdown("**Qty**")
                        col_b.altair_chart(trend_chart(data["qty"], "Qty", kind, C_QTY),
                                           use_container_width=True, theme=None)

            # ---------------- Material-wise ----------------
            with st.container(border=True):
                st.subheader(f"Material-wise: {cur} vs {prev}")
                cm = cdf.groupby(["material", "unit"])[["qty", "amount"]].sum()
                pm = pdf.groupby(["material", "unit"])[["qty", "amount"]].sum()
                comp = cm.join(pm, how="outer", lsuffix=f" {cur}", rsuffix=f" {prev}").fillna(0).reset_index()
                st.dataframe(comp.style.format(precision=2, thousands=","), hide_index=True,
                             use_container_width=True)

            # ---------------- Entries ----------------
            with st.container(border=True):
                st.subheader("Entries (with cumulative)")
                show = entries_table(cdf)
                st.dataframe(show.sort_values(["Date", "id"], ascending=False),
                             hide_index=True, use_container_width=True)
                st.download_button("Download CSV", show.to_csv(index=False),
                                   f"entries_{cur}.csv", "text/csv")

            # ---------------- Search + Duplicates ----------------
            with st.container(border=True):
                st.subheader("Search")
                sc1, sc2 = st.columns([4, 3])
                term = sc1.text_input("Search (ID, Serial No, date, plant, material, site, TM Number, TM Name...)",
                                      key="dash_search", placeholder="e.g. 1234 ABC 2026-10")
                scope = sc2.radio("Search in", ["All data", "Selected month + filters"],
                                  horizontal=True, key="dash_search_scope")
                pool = df if scope == "All data" else cdf
                if term.strip():
                    res = text_filter(pool, term)
                    r1, r2, r3 = st.columns(3)
                    r1.metric("Matches", f"{len(res):,}")
                    r2.metric("Qty", f"{res['qty'].sum():,.2f}")
                    r3.metric("Amount", rs(res["amount"].sum()))
                    if res.empty:
                        st.info("No entries matched.")
                    else:
                        out = entries_table(res).sort_values(["Date", "id"], ascending=False)
                        st.dataframe(out, hide_index=True, use_container_width=True)
                        st.download_button("Download search results (CSV)", out.to_csv(index=False),
                                           "search_results.csv", "text/csv", key="dl_search")
                else:
                    st.caption("Type something above. With several words, only entries matching all of them are shown.")

                ndup = int((df["dup_rank"] > 1).sum())
                with st.expander(f"Duplicate entries ({ndup:,})", expanded=False):
                    duplicate_delete_ui("dash")