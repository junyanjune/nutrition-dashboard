"""
Elite Performance Lab — Athlete Nutrition Analysis
Reads CSV data, computes key nutrition/performance metrics,
and generates writeup.pdf.
"""

import os
import sys
import textwrap
import pandas as pd
import numpy as np
from fpdf import FPDF
from fpdf.enums import XPos, YPos

DATA_DIR = "data"


# ── Load ──────────────────────────────────────────────────────────────────────

def load_data():
    tables = [
        "Athletes", "AthleteBodyMetrics", "AthleteTeams",
        "Meals", "MealItems", "Foods", "FoodNutrients", "Nutrients",
        "PerformanceSessions", "PerformanceMetrics",
        "Sports", "Teams", "FoodCategories", "HydrationLogs",
    ]
    data = {}
    for t in tables:
        path = os.path.join(DATA_DIR, f"{t}.csv")
        if os.path.exists(path):
            data[t] = pd.read_csv(path)
        else:
            print(f"  [warn] missing: {path}")
    return data


# ── Compute macros per athlete ─────────────────────────────────────────────────

def compute_macros(data):
    mi   = data["MealItems"]
    m    = data["Meals"][["meal_id", "athlete_id"]]
    fn   = data["FoodNutrients"]
    nut  = data["Nutrients"]

    mi = mi.merge(m, on="meal_id")
    mi = mi.merge(fn, on="food_id")
    mi = mi.merge(nut, on="nutrient_id")
    mi["total"] = mi["amount_per_serving"] * mi["servings"]

    macros = (
        mi.pivot_table(index="athlete_id", columns="nutrient_name",
                       values="total", aggfunc="sum")
          .reset_index()
    )
    return macros


# ── Build athlete master table ─────────────────────────────────────────────────

def build_master(data, macros):
    ath  = data["Athletes"]
    bm   = data["AthleteBodyMetrics"]
    at   = data["AthleteTeams"][["athlete_id", "team_id"]]
    tm   = data["Teams"][["team_id", "team_name", "sport_id"]]
    sp   = data["Sports"][["sport_id", "sport_name"]]
    sess = data["PerformanceSessions"][["session_id", "athlete_id",
                                        "session_type", "intensity_level",
                                        "duration_minutes"]]

    master = (
        ath[["athlete_id", "first_name", "last_name"]]
        .merge(bm[["athlete_id", "body_weight_kg", "body_fat_percent",
                   "height_cm"]], on="athlete_id")
        .merge(at, on="athlete_id")
        .merge(tm, on="team_id")
        .merge(sp, on="sport_id")
        .merge(sess, on="athlete_id")
        .merge(macros, on="athlete_id", how="left")
    )
    master["name"] = master["first_name"] + " " + master["last_name"]
    master["lean_mass_kg"] = (
        master["body_weight_kg"] * (1 - master["body_fat_percent"] / 100)
    ).round(1)
    return master


# ── Summary stats ──────────────────────────────────────────────────────────────

def sport_summary(master):
    cols = {"Energy": "kcal", "Protein": "protein_g",
            "Carbohydrate": "carbs_g", "Fat": "fat_g"}
    rename = {k: v for k, v in cols.items() if k in master.columns}
    m = master.rename(columns=rename)

    agg = {
        "body_weight_kg":   "mean",
        "body_fat_percent": "mean",
        "height_cm":        "mean",
        "duration_minutes": "mean",
    }
    for v in rename.values():
        if v in m.columns:
            agg[v] = "mean"

    summary = m.groupby("sport_name").agg(agg).round(1).reset_index()
    summary.columns.name = None
    return summary


def top_protein_athletes(master):
    if "Protein" not in master.columns:
        return pd.DataFrame()
    return (
        master[["name", "sport_name", "Protein"]]
        .sort_values("Protein", ascending=False)
        .head(5)
        .rename(columns={"Protein": "protein_g", "sport_name": "sport"})
    )


def hydration_summary(data):
    if "HydrationLogs" not in data:
        return pd.DataFrame()
    hl   = data["HydrationLogs"]
    ath  = data["Athletes"][["athlete_id", "first_name", "last_name"]]
    h = hl.merge(ath, on="athlete_id")
    h["name"] = h["first_name"] + " " + h["last_name"]
    return (
        h.groupby("name")["volume_ml"].sum()
          .reset_index()
          .rename(columns={"volume_ml": "total_ml"})
          .sort_values("total_ml", ascending=False)
    )


# ── PDF ────────────────────────────────────────────────────────────────────────

def _s(text):
    """Sanitise text to latin-1 safe characters for fpdf Helvetica font."""
    return (str(text)
        .replace('—', '--').replace('–', '-')
        .replace('•', '*').replace('→', '->')
        .replace('─', '-').replace('·', '.')
        .replace('‘', "'").replace('’', "'")
        .replace('“', '"').replace('”', '"')
    )


ORANGE  = (255, 102,   0)
RED     = (220,  30,   0)
BLUE    = (  0, 180, 255)
WHITE   = (255, 255, 255)
DARK    = ( 12,   8,   0)
LGRAY   = (230, 230, 230)
MID     = (100, 100, 100)


class Report(FPDF):
    def header(self):
        self.set_fill_color(*DARK)
        self.rect(0, 0, 210, 22, "F")
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(*ORANGE)
        self.set_xy(0, 4)
        self.cell(0, 7, "ELITE PERFORMANCE LAB", align="C",
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(180, 130, 80)
        self.cell(0, 5, "Athlete Nutrition Intelligence Report -- 2025 Season",
                  align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(6)

    def footer(self):
        self.set_y(-13)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(*MID)
        self.cell(0, 6, f"Page {self.page_no()}  |  Elite Performance Lab  |  2025",
                  align="C")

    def section(self, title):
        self.ln(4)
        self.set_fill_color(*DARK)
        self.rect(self.l_margin, self.get_y(), 190, 7, "F")
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*ORANGE)
        self.cell(0, 7, _s(f"  {title}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_draw_color(*RED)
        self.set_line_width(0.4)
        y = self.get_y()
        self.line(self.l_margin, y, self.l_margin + 190, y)
        self.ln(3)

    def body(self, text, indent=0):
        self.set_font("Helvetica", "", 9.5)
        self.set_text_color(40, 40, 40)
        self.set_x(self.l_margin + indent)
        self.multi_cell(190 - indent, 5.5, _s(text),
                        new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(1)

    def bullet(self, text):
        self.set_font("Helvetica", "", 9.5)
        self.set_text_color(40, 40, 40)
        self.set_x(self.l_margin + 4)
        self.cell(5, 5.5, "*")
        self.multi_cell(181, 5.5, _s(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def kv(self, label, value, color=None):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(60, 60, 60)
        self.cell(55, 6, _s(label) + ":", new_x=XPos.RIGHT, new_y=YPos.LAST)
        self.set_font("Helvetica", "", 9)
        if color:
            self.set_text_color(*color)
        else:
            self.set_text_color(*ORANGE)
        self.cell(0, 6, _s(value), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(40, 40, 40)

    def table(self, headers, rows, col_widths=None):
        n = len(headers)
        if col_widths is None:
            col_widths = [190 // n] * n

        # header row
        self.set_fill_color(*DARK)
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*ORANGE)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 6, _s(h), border=0, fill=True,
                      new_x=XPos.RIGHT, new_y=YPos.LAST)
        self.ln()

        # data rows
        for ri, row in enumerate(rows):
            fill_color = (248, 244, 240) if ri % 2 == 0 else WHITE
            self.set_fill_color(*fill_color)
            self.set_font("Helvetica", "", 8)
            self.set_text_color(30, 30, 30)
            for i, val in enumerate(row):
                self.cell(col_widths[i], 5.5, _s(val), border=0, fill=True,
                          new_x=XPos.RIGHT, new_y=YPos.LAST)
            self.ln()
        self.ln(3)


# ── Generate ───────────────────────────────────────────────────────────────────

def generate_pdf(master, sport_sum, top_prot, hydration, output="writeup.pdf"):
    pdf = Report(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    # ── Cover block ──────────────────────────────────────────────────────────
    pdf.set_fill_color(248, 244, 240)
    pdf.rect(pdf.l_margin, pdf.get_y(), 190, 34, "F")
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(*DARK)
    pdf.set_xy(pdf.l_margin, pdf.get_y() + 5)
    pdf.cell(0, 10, "Athlete Nutrition Intelligence", align="C",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(*MID)
    pdf.cell(0, 7, "Interactive Dashboard -- Design & Analysis Report", align="C",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(0, 6, "May 2026  |  15 Athletes  |  5 Sports  |  Python + Chart.js",
             align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(8)

    # ── 1. Project Overview ───────────────────────────────────────────────────
    pdf.section("1. Project Overview")
    pdf.body(
        "This project builds a fully interactive, browser-based nutrition intelligence "
        "dashboard for 15 elite athletes across five professional sports — Tennis, "
        "Basketball, Formula 1, Soccer, and Breaking. The dashboard visualises body "
        "composition, macronutrient profiles, and training session load from a "
        "relational CSV dataset of 20 tables."
    )
    pdf.body(
        "The interactive frontend (dashboard.html) is a single self-contained file "
        "built with Chart.js and vanilla JavaScript, requiring no server. The Python "
        "analysis layer (analysis.py) handles data loading, merging, and statistical "
        "summarisation using pandas, and produces this PDF report."
    )

    # ── 2. Dataset Description ────────────────────────────────────────────────
    pdf.section("2. Dataset Description")
    pdf.body("The dataset is structured as a relational schema with 20 CSV tables:")
    schema = [
        ("Athletes", "15 elite athletes with name, DOB, sex, position"),
        ("AthleteBodyMetrics", "Weight, height, body-fat % per athlete"),
        ("Sports / Teams / AthleteTeams", "Sport taxonomy and team membership"),
        ("Meals / MealItems", "30 meal records linked to food items"),
        ("Foods / FoodNutrients / Nutrients", "Nutrient composition per food serving"),
        ("PerformanceSessions / PerformanceMetrics", "Training sessions and output metrics"),
        ("HydrationLogs / BeverageTypes", "Fluid intake per session"),
        ("FoodCategories / Seasons / DataSources", "Reference / lookup tables"),
    ]
    for name, desc in schema:
        pdf.bullet(f"{name}: {desc}")
    pdf.ln(2)

    # ── 3. Key Findings ───────────────────────────────────────────────────────
    pdf.section("3. Key Findings")

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(0, 6, "3.1  Body Composition by Sport", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    if not sport_sum.empty:
        headers = ["Sport", "Avg Weight (kg)", "Avg Body Fat %",
                   "Avg Height (cm)", "Avg Session (min)"]
        widths  = [42, 36, 34, 38, 40]
        rows = []
        for _, r in sport_sum.iterrows():
            rows.append([
                r.get("sport_name", "-"),
                f"{r.get('body_weight_kg', 0):.1f}",
                f"{r.get('body_fat_percent', 0):.1f}%",
                f"{r.get('height_cm', 0):.0f}",
                f"{r.get('duration_minutes', 0):.0f}",
            ])
        pdf.table(headers, rows, widths)

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(0, 6, "3.2  Top Athletes by Protein Intake", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    if not top_prot.empty:
        headers = ["Athlete", "Sport", "Protein (g/day)"]
        widths  = [70, 60, 60]
        rows = [
            [r["name"], r["sport"], f"{r['protein_g']:.0f}"]
            for _, r in top_prot.iterrows()
        ]
        pdf.table(headers, rows, widths)

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(0, 6, "3.3  Hydration Totals per Athlete (ml / session)", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    if not hydration.empty:
        headers = ["Athlete", "Total Volume (ml)"]
        widths  = [100, 90]
        rows = [[r["name"], f"{r['total_ml']:.0f}"] for _, r in hydration.head(8).iterrows()]
        pdf.table(headers, rows, widths)

    # ── 4. Visualisation Design ───────────────────────────────────────────────
    pdf.section("4. Dashboard Visualisation Design")

    viz = [
        (
            "Chart 1 — Body Composition Intelligence (Bubble Chart)",
            "Each athlete is plotted as a bubble: X-axis = body weight (kg), "
            "Y-axis = body fat percentage, bubble radius = height (cm). Colour "
            "encodes sport. Hovering any bubble triggers a custom HTML overlay card "
            "that reveals the athlete's name, sport badge, team, all three body "
            "metrics, daily calorie intake with a proportional fill bar, and macro "
            "gram breakdown — giving deep insight into individual observations "
            "without cluttering the base chart.",
        ),
        (
            "Chart 2 — Macronutrient Profiles (Radar Chart + Toggle)",
            "A radar chart with four axes — Calories, Protein, Carbs, Fat — "
            "normalised to the maximum per axis so all sports fit on the same scale. "
            "Five sport-coloured toggle pills (Tennis, Basketball, Formula 1, Soccer, "
            "Breaking) animate their dataset in or out with Chart.js transitions. "
            "Active toggles glow in their sport colour; inactive ones dim to 40% "
            "opacity. Hovering any datapoint shows the actual gram/kcal value "
            "for that sport.",
        ),
        (
            "Chart 3 — Session Analysis (Animated Bar Chart)",
            "A vertical bar chart groups all 15 athletes by sport, separated by "
            "dashed dividers with emoji sport labels drawn via a custom Chart.js "
            "plugin. Bar opacity encodes intensity level (High = 0.82, Moderate = "
            "0.55, Low = 0.32). A Duration / Calories tab pair animates a data "
            "swap, and the Replay button sequences bars in from zero one-by-one "
            "with a 75 ms stagger — foregrounding the comparative load narrative.",
        ),
    ]
    for title, desc in viz:
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*ORANGE)
        pdf.cell(0, 6, _s(title), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.body(desc, indent=4)

    # ── 5. Design Choices ─────────────────────────────────────────────────────
    pdf.section("5. Visual Design Choices")
    choices = [
        "Pure-black base (#000000) with diagonal carbon-fibre grid (two overlapping 28 px diamond grids) and CRT scanlines for a street-racing aesthetic.",
        "90 animated speed-streak lines drawn on a background <canvas> element, using orange/red/white/blue gradients flying left-to-right at varied speeds and opacities.",
        "Dual ambient neon blobs: orange fireball (bottom-left) and cold blue glow (top-right) that slowly breathe via CSS keyframes.",
        "Angled clip-path: polygon(...) on cards and buttons gives a mechanical, armoured panel feel consistent across components.",
        "Sport colours (Tennis #00D4FF, Basketball #FF6B2B, F1 #FF0044, Soccer #00E676, Breaking #D500F9) are used consistently across legend, radar, bubbles, and bar fills.",
        "Space Grotesk (headings / UI) and Space Mono (numbers / monospace labels) from Google Fonts for a technical data-lab feel.",
        "Hover on the bubble chart updates a background orb tint and slides in a rich tooltip card — coupling micro-interaction with sport identity.",
    ]
    for c in choices:
        pdf.bullet(c)

    # ── 6. Technical Stack ────────────────────────────────────────────────────
    pdf.section("6. Technical Stack")
    stack = [
        ("Frontend",   "HTML5, CSS3 (clip-path, backdrop-filter, keyframes), JavaScript ES2022"),
        ("Charts",     "Chart.js 4.x — bubble, radar, bar chart types; two custom plugins"),
        ("Fonts",      "Google Fonts: Space Grotesk, Space Mono"),
        ("Data layer", "Python 3, pandas, numpy"),
        ("Report",     "fpdf2 — programmatic PDF generation"),
        ("Hosting",    "Single self-contained HTML file — no server required"),
    ]
    for label, val in stack:
        pdf.kv(label, val, color=(40, 40, 40))
    pdf.ln(2)

    # ── 7. How to Run ─────────────────────────────────────────────────────────
    pdf.section("7. How to Run")
    pdf.body("Prerequisites: Python 3.9+, pip packages in requirements.txt")
    steps = [
        "git clone https://github.com/junyanjune/nutrition-dashboard",
        "cd nutrition-dashboard",
        "pip install -r requirements.txt",
        "python analysis.py          # generates writeup.pdf and prints summary",
        "open dashboard.html         # or double-click — works in any modern browser",
    ]
    for s in steps:
        pdf.set_font("Courier", "", 8.5)
        pdf.set_text_color(30, 90, 150)
        pdf.set_x(pdf.l_margin + 6)
        pdf.cell(0, 5.5, _s(f"$ {s}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)
    pdf.body("No internet connection is needed to view the dashboard offline -- "
             "Chart.js and Google Fonts are loaded from CDN; save those locally "
             "for fully offline use.")

    pdf.output(output)
    print(f"  PDF written -> {output}")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print("Loading data...")
    data = load_data()

    print("Computing macros...")
    macros = compute_macros(data)

    print("Building master table...")
    master = build_master(data, macros)

    print("Summarising by sport...")
    sport_sum  = sport_summary(master)
    top_prot   = top_protein_athletes(master)
    hydration  = hydration_summary(data)

    # Console summary
    print("\n-- Sport Summary --")
    print(sport_sum.to_string(index=False))
    print("\n-- Top 5 Athletes by Protein --")
    print(top_prot.to_string(index=False))
    print("\n-- Hydration Totals --")
    print(hydration.head(8).to_string(index=False))

    print("\nGenerating PDF...")
    generate_pdf(master, sport_sum, top_prot, hydration)

    print("\nDone.")


if __name__ == "__main__":
    main()
