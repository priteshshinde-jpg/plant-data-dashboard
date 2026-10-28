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
