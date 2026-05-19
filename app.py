"""
Elite Performance Lab — Streamlit Dashboard
Athlete Nutrition Intelligence · 2025 Season
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Elite Performance Lab",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

SPORT_COLORS = {
    "Tennis":     "#0099BB",
    "Basketball": "#E85D04",
    "Formula 1":  "#CC0033",
    "Soccer":     "#00875A",
    "Breaking":   "#7B1FA2",
}
SPORT_ICONS = {
    "Tennis": "🎾", "Basketball": "🏀",
    "Formula 1": "🏎️", "Soccer": "⚽", "Breaking": "💫",
}
INTENSITY_COLORS = {"High": "#CC2200", "Moderate": "#E87722", "Low": "#C8A000"}

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(244,246,255,0.55)",
    font_color="#1A1A2E",
    font_family="Space Grotesk, sans-serif",
    title_font_size=14,
    title_font_color="#E64A19",
    legend_bgcolor="rgba(255,255,255,0.85)",
    xaxis=dict(gridcolor="rgba(26,35,126,0.08)", zerolinecolor="rgba(26,35,126,0.13)"),
    yaxis=dict(gridcolor="rgba(26,35,126,0.08)", zerolinecolor="rgba(26,35,126,0.13)"),
    margin=dict(t=48, b=24, l=16, r=16),
)

def lay(**kw):
    """Merge PLOTLY_LAYOUT with per-chart overrides (kw wins on duplicate keys)."""
    return {**PLOTLY_LAYOUT, **kw}

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Space+Mono&display=swap');

html, body, [class*="css"] { font-family: 'Space Grotesk', sans-serif !important; }

/* Header */
.main-title {
    font-size: 2.6rem; font-weight: 700; letter-spacing: -2px;
    background: linear-gradient(110deg, #1A237E 0%, #E64A19 38%, #CC0033 65%, #00838F 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.main-sub {
    font-family: 'Space Mono', monospace; font-size: 0.68rem;
    letter-spacing: 2.5px; text-transform: uppercase; color: rgba(100,80,60,0.65);
}
.hdr-line {
    height: 2px; margin: 16px 0 24px; border-radius: 1px;
    background: linear-gradient(90deg, #1A237E, #E64A19, #00838F, transparent);
    opacity: 0.45;
}

/* Metric cards */
[data-testid="metric-container"] {
    background: linear-gradient(135deg, rgba(230,74,25,0.05) 0%, rgba(26,35,126,0.05) 100%);
    border: 1px solid rgba(230,74,25,0.22);
    border-radius: 10px; padding: 14px 16px;
    box-shadow: 0 2px 8px rgba(26,35,126,0.07);
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-family: 'Space Mono', monospace !important;
    color: #E64A19 !important; font-size: 1.5rem !important;
}
[data-testid="metric-container"] [data-testid="stMetricLabel"] {
    font-size: 0.68rem !important; letter-spacing: 1.5px;
    text-transform: uppercase; color: rgba(26,35,126,0.5) !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px; background: rgba(26,35,126,0.04);
    border-radius: 8px; padding: 4px;
    border: 1px solid rgba(26,35,126,0.12);
}
.stTabs [data-baseweb="tab"] {
    border-radius: 5px; font-weight: 500; font-size: 0.88rem;
    color: rgba(26,35,126,0.45) !important;
}
.stTabs [aria-selected="true"] {
    background: rgba(230,74,25,0.1) !important;
    color: #E64A19 !important;
}

/* Insight boxes */
.insight {
    background: rgba(0,131,143,0.06);
    border-left: 3px solid #00838F;
    border-radius: 0 10px 10px 0;
    padding: 12px 16px; margin: 4px 0 18px;
    font-size: 0.84rem; color: rgba(26,35,126,0.85);
    line-height: 1.55;
}
.insight-tag {
    font-family: 'Space Mono', monospace;
    font-size: 0.62rem; letter-spacing: 2px;
    text-transform: uppercase; color: #00838F;
    display: block; margin-bottom: 5px;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #F4F6FF !important;
    border-right: 1px solid rgba(26,35,126,0.1);
}

/* Section headers */
.section-hdr {
    font-size: 0.65rem; font-family: 'Space Mono', monospace;
    letter-spacing: 2px; text-transform: uppercase;
    color: rgba(26,35,126,0.45); margin-bottom: 12px;
    padding-bottom: 6px;
    border-bottom: 1px solid rgba(26,35,126,0.1);
}
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data():
    D = "data"

    athletes = pd.read_csv(f"{D}/Athletes.csv")
    body     = pd.read_csv(f"{D}/AthleteBodyMetrics.csv")
    meals    = pd.read_csv(f"{D}/Meals.csv")
    items    = pd.read_csv(f"{D}/MealItems.csv")
    fn       = pd.read_csv(f"{D}/FoodNutrients.csv")
    nuts     = pd.read_csv(f"{D}/Nutrients.csv")
    sessions = pd.read_csv(f"{D}/PerformanceSessions.csv")
    at       = pd.read_csv(f"{D}/AthleteTeams.csv")[["athlete_id", "team_id"]]
    teams    = pd.read_csv(f"{D}/Teams.csv")[["team_id", "team_name", "sport_id"]]
    sports   = pd.read_csv(f"{D}/Sports.csv")[["sport_id", "sport_name"]]
    hydration= pd.read_csv(f"{D}/HydrationLogs.csv")
    diet_res = pd.read_csv(f"{D}/AthleteDietaryRestrictions.csv")

    # Compute macros via join chain
    mi = (items
          .merge(meals[["meal_id", "athlete_id", "meal_type"]], on="meal_id")
          .merge(fn, on="food_id")
          .merge(nuts, on="nutrient_id"))
    mi["total"] = mi["amount_per_serving"] * mi["servings"]
    macros = (mi.pivot_table(index="athlete_id", columns="nutrient_name",
                              values="total", aggfunc="sum")
                .reset_index())

    # Count meals per athlete
    meal_counts = meals.groupby("athlete_id").size().reset_index(name="meal_count")
    # Meal type breakdown
    meal_types = (meals.groupby(["athlete_id", "meal_type"])
                  .size().unstack(fill_value=0).reset_index())

    # Hydration aggregates
    hyd = (hydration.groupby("athlete_id")
           .agg(hydration_ml=("volume_ml", "sum"),
                electrolytes_mg=("estimated_electrolyte_mg", "sum"))
           .reset_index())

    # Dietary restrictions count
    diet_count = (diet_res.groupby("athlete_id").size()
                  .reset_index(name="diet_restrictions"))

    # Build master
    df = (athletes[["athlete_id", "first_name", "last_name", "biological_sex", "notes"]]
          .merge(body[["athlete_id", "body_weight_kg", "body_fat_percent", "height_cm"]], on="athlete_id")
          .merge(at, on="athlete_id")
          .merge(teams, on="team_id")
          .merge(sports, on="sport_id")
          .merge(sessions[["athlete_id", "intensity_level", "duration_minutes",
                            "session_type", "environment"]], on="athlete_id")
          .merge(macros, on="athlete_id", how="left")
          .merge(meal_counts, on="athlete_id", how="left")
          .merge(hyd, on="athlete_id", how="left")
          .merge(diet_count, on="athlete_id", how="left")
          )

    df["name"]      = df["first_name"] + " " + df["last_name"]
    df["last_name"] = df["last_name"]
    df["icon"]      = df["sport_name"].map(SPORT_ICONS)

    df = df.rename(columns={
        "body_weight_kg":   "weight_kg",
        "body_fat_percent": "body_fat_pct",
        "sport_name":       "sport",
        "team_name":        "team",
        "duration_minutes": "session_min",
        "intensity_level":  "intensity",
        "Energy":           "kcal",
        "Protein":          "protein_g",
        "Carbohydrate":     "carbs_g",
        "Fat":              "fat_g",
        "Sodium":           "sodium_mg",
        "Potassium":        "potassium_mg",
    })

    # Derived metrics
    df["lean_mass_kg"]   = (df.weight_kg * (1 - df.body_fat_pct / 100)).round(1)
    df["fat_mass_kg"]    = (df.weight_kg * df.body_fat_pct / 100).round(1)
    df["bmi"]            = (df.weight_kg / (df.height_cm / 100) ** 2).round(1)
    df["protein_per_kg"] = (df.protein_g / df.weight_kg).round(3)
    df["carbs_per_kg"]   = (df.carbs_g   / df.weight_kg).round(3)
    df["fat_per_kg"]     = (df.fat_g     / df.weight_kg).round(3)
    df["kcal_per_kg"]    = (df.kcal      / df.weight_kg).round(2)
    df["kcal_per_min"]   = (df.kcal      / df.session_min).round(2)
    df["pct_protein"]    = (df.protein_g * 4 / df.kcal * 100).round(1)
    df["pct_carbs"]      = (df.carbs_g   * 4 / df.kcal * 100).round(1)
    df["pct_fat"]        = (df.fat_g     * 9 / df.kcal * 100).round(1)
    df["hydration_per_kg"] = (df.hydration_ml / df.weight_kg).round(1)
    df["diet_restrictions"] = df["diet_restrictions"].fillna(0).astype(int)

    return df


df = load_data()

st.markdown("""
<div style="text-align:center; padding: 20px 0 0">
  <div class="main-title">Elite Performance Lab</div>
  <div class="main-sub">Athlete Nutrition Intelligence &nbsp;·&nbsp; 2025 Season</div>
</div>
<div class="hdr-line"></div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### ⚡ Filters")
    all_sports = sorted(df.sport.unique())
    sel_sports = st.multiselect(
        "Sports",
        options=all_sports,
        default=all_sports,
        format_func=lambda s: f"{SPORT_ICONS.get(s,'')} {s}",
    )
    sel_intensity = st.multiselect(
        "Session Intensity",
        options=["High", "Moderate", "Low"],
        default=["High", "Moderate", "Low"],
    )
    st.markdown("---")
    st.markdown('<div class="section-hdr">Dataset</div>', unsafe_allow_html=True)
    st.markdown("20 relational CSV tables  \n15 elite athletes  \n5 professional sports  \n30 meals logged")

fdf = df[df.sport.isin(sel_sports) & df.intensity.isin(sel_intensity)] if sel_sports else df



t1, t2, t3, t4 = st.tabs([
    "📊  Overview",
    "💪  Body Composition",
    "🥗  Nutrition Intelligence",
    "⚡  Training & Fueling",
])



with t1:
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Athletes",    len(fdf))
    c2.metric("Avg Calories", f"{fdf.kcal.mean():.0f} kcal")
    c3.metric("Avg Protein",  f"{fdf.protein_g.mean():.0f} g")
    c4.metric("Avg Carbs",    f"{fdf.carbs_g.mean():.0f} g")
    c5.metric("Avg Session",  f"{fdf.session_min.mean():.0f} min")
    c6.metric("Avg Body Fat", f"{fdf.body_fat_pct.mean():.1f}%")

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown('<div class="section-hdr">Squad Breakdown</div>', unsafe_allow_html=True)
        sport_counts = fdf.groupby("sport").size().reset_index(name="n")
        fig = px.pie(
            sport_counts, names="sport", values="n",
            color="sport", color_discrete_map=SPORT_COLORS,
            hole=0.58,
        )
        fig.update_traces(
            textposition="outside", textfont_size=11,
            pull=[0.04]*len(sport_counts),
        )
        fig.update_layout(**PLOTLY_LAYOUT, height=300, showlegend=True,
                          title="Squad Breakdown by Sport",
                          legend=dict(x=1, y=0.5))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown('<div class="section-hdr">Sport Averages — select metric</div>', unsafe_allow_html=True)
        metric_map = {
            "Calories (kcal)": "kcal",
            "Protein (g)": "protein_g",
            "Carbs (g)": "carbs_g",
            "Fat (g)": "fat_g",
            "Session Duration (min)": "session_min",
            "Body Weight (kg)": "weight_kg",
            "Body Fat (%)": "body_fat_pct",
            "Protein per kg": "protein_per_kg",
        }
        sel_metric = st.selectbox("Metric", list(metric_map.keys()), label_visibility="collapsed")
        col = metric_map[sel_metric]

        sport_avg = (fdf.groupby("sport")[col].mean()
                     .reset_index().rename(columns={col: "value"})
                     .sort_values("value"))
        sport_avg["label"] = sport_avg.sport.apply(
            lambda s: SPORT_ICONS.get(s, "") + " " + s
        )

        fig = px.bar(
            sport_avg, x="value", y="label", orientation="h",
            color="sport", color_discrete_map=SPORT_COLORS,
            text=sport_avg["value"].map("{:.1f}".format),
        )
        fig.update_traces(textposition="outside", textfont_size=11)
        fig.update_layout(**PLOTLY_LAYOUT, height=300, showlegend=False,
                          title=f"Avg {sel_metric} by Sport",
                          xaxis_title=sel_metric, yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="section-hdr">All Athletes</div>', unsafe_allow_html=True)
    overview_cols = ["name", "sport", "team", "weight_kg", "body_fat_pct",
                     "height_cm", "kcal", "protein_g", "carbs_g", "fat_g",
                     "session_min", "intensity"]
    st.dataframe(
        fdf[overview_cols].rename(columns={
            "name": "Athlete", "sport": "Sport", "team": "Team",
            "weight_kg": "Weight (kg)", "body_fat_pct": "Body Fat %",
            "height_cm": "Height (cm)", "kcal": "Calories",
            "protein_g": "Protein (g)", "carbs_g": "Carbs (g)", "fat_g": "Fat (g)",
            "session_min": "Session (min)", "intensity": "Intensity",
        }).reset_index(drop=True),
        use_container_width=True,
        hide_index=True,
    )



with t2:
    st.markdown("""
    <div class="insight">
      <span class="insight-tag">💡 Key Insight</span>
      F1 drivers cluster at the <strong>lowest weight + lowest body fat</strong> —
      FIA regulations penalise mass, forcing extreme leanness despite the high neuromuscular
      demands of 5G cornering. Basketball players are statistical outliers in weight AND height.
      Despite appearing "overweight" on BMI, LeBron James carries <strong>101.7 kg of lean mass</strong>
      — more than any other athlete in this dataset.
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="section-hdr">Weight vs Body Fat % — bubble size = height</div>', unsafe_allow_html=True)
        fig = px.scatter(
            fdf, x="weight_kg", y="body_fat_pct",
            size="height_cm", color="sport",
            color_discrete_map=SPORT_COLORS,
            hover_name="name",
            hover_data={
                "sport": True, "team": True,
                "weight_kg": ":.0f", "body_fat_pct": ":.1f",
                "height_cm": ":.0f", "lean_mass_kg": ":.1f",
                "bmi": ":.1f",
            },
            size_max=30,
            labels={"weight_kg": "Body Weight (kg)", "body_fat_pct": "Body Fat (%)"},
        )
        fig.update_layout(**PLOTLY_LAYOUT, height=380, showlegend=True,
                          title="Weight vs Body Fat %")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown('<div class="section-hdr">Body Composition — Lean Mass vs Fat Mass</div>', unsafe_allow_html=True)
        bc = fdf[["name", "sport", "lean_mass_kg", "fat_mass_kg"]].sort_values("lean_mass_kg", ascending=False)
        fig = go.Figure()
        fig.add_trace(go.Bar(
            name="Lean Mass (kg)",
            x=bc.name, y=bc.lean_mass_kg,
            marker_color=[SPORT_COLORS[s] for s in bc.sport],
            marker_opacity=0.88,
        ))
        fig.add_trace(go.Bar(
            name="Fat Mass (kg)",
            x=bc.name, y=bc.fat_mass_kg,
            marker_color=[SPORT_COLORS[s] for s in bc.sport],
            marker_opacity=0.32,
            marker_pattern_shape="/",
        ))
        fig.update_layout(
            **PLOTLY_LAYOUT,
            title="Lean Mass vs Fat Mass",
            barmode="stack", height=380,
            xaxis_tickangle=-38, xaxis_title="",
            yaxis_title="Body Mass (kg)",
            legend=dict(orientation="h", y=1.08, bgcolor="rgba(0,0,0,0)"),
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="section-hdr">BMI by Athlete — with clinical reference lines</div>', unsafe_allow_html=True)
    bmi_df = fdf[["name", "sport", "bmi", "lean_mass_kg", "fat_mass_kg", "body_fat_pct"]].sort_values("bmi")
    fig = px.bar(
        bmi_df, x="bmi", y="name", orientation="h",
        color="sport", color_discrete_map=SPORT_COLORS,
        hover_data={"lean_mass_kg": ":.1f", "body_fat_pct": ":.1f", "bmi": ":.1f"},
        labels={"bmi": "BMI (kg/m²)", "name": ""},
    )
    fig.add_vline(x=18.5, line_dash="dot",  line_color="#888888", opacity=0.6,
                  annotation_text="Underweight (<18.5)", annotation_position="top right",
                  annotation_font_size=10)
    fig.add_vline(x=25.0, line_dash="dash", line_color="#FF8C00", opacity=0.6,
                  annotation_text="Overweight (>25)", annotation_position="top right",
                  annotation_font_size=10)
    fig.update_layout(**lay(title="BMI by Athlete", height=430, margin=dict(t=48, b=24, l=150, r=60), showlegend=True))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("""
    <div class="insight">
      <span class="insight-tag">📌 BMI Limitation</span>
      BMI flags LeBron James (26.6) and Doncic (25.7) as overweight — yet their body fat
      is only 10–11%. This illustrates why BMI alone is meaningless for elite athletes.
      The lean mass chart above provides the accurate picture: more muscle, not more fat.
    </div>
    """, unsafe_allow_html=True)


with t3:
    st.markdown("""
    <div class="insight">
      <span class="insight-tag">💡 Key Insight</span>
      <strong>No athlete meets the 1.6 g/kg protein threshold</strong> recommended for strength athletes —
      the highest is Doncic at 0.66 g/kg. F1's Lewis Hamilton (plant-based) has the lowest protein
      intake (0.14 g/kg) and lowest total calories (340 kcal), yet maintains competitive body composition.
      Macro calorie splits show Tennis and F1 are the most carbohydrate-dominant sports.
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="section-hdr">Macro Calorie Split (% of total intake)</div>', unsafe_allow_html=True)
        mac = fdf[["name", "sport", "pct_protein", "pct_carbs", "pct_fat"]].copy()
        mac = mac.sort_values(["sport", "pct_carbs"], ascending=[True, False])
        fig = go.Figure()
        fig.add_trace(go.Bar(name="Protein %", x=mac.name, y=mac.pct_protein,
                             marker_color="#00C8FF", marker_opacity=0.9))
        fig.add_trace(go.Bar(name="Carbs %",   x=mac.name, y=mac.pct_carbs,
                             marker_color="#FF8800", marker_opacity=0.9))
        fig.add_trace(go.Bar(name="Fat %",     x=mac.name, y=mac.pct_fat,
                             marker_color="#FF2244", marker_opacity=0.9))
        fig.update_layout(
            **PLOTLY_LAYOUT,
            title="Macro Calorie Split",
            barmode="stack", height=380,
            xaxis_tickangle=-38, xaxis_title="",
            yaxis_title="% of Calories",
            legend=dict(orientation="h", y=1.1, bgcolor="rgba(0,0,0,0)"),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown('<div class="section-hdr">Protein per kg Bodyweight — sports nutrition standard</div>', unsafe_allow_html=True)
        prot = fdf[["name", "sport", "protein_per_kg", "protein_g", "weight_kg"]].sort_values("protein_per_kg", ascending=False)
        fig = px.bar(
            prot, x="name", y="protein_per_kg",
            color="sport", color_discrete_map=SPORT_COLORS,
            hover_data={"protein_g": ":.0f", "weight_kg": ":.0f", "protein_per_kg": ":.3f"},
            labels={"protein_per_kg": "g protein / kg bodyweight", "name": ""},
        )
        fig.add_hline(y=1.6, line_dash="dash", line_color="#00E676", opacity=0.7,
                      annotation_text="Strength rec. 1.6 g/kg", annotation_font_size=10,
                      annotation_position="top left")
        fig.add_hline(y=0.8, line_dash="dot",  line_color="#888888", opacity=0.5,
                      annotation_text="Sedentary RDA 0.8 g/kg", annotation_font_size=10,
                      annotation_position="top left")
        fig.update_layout(**PLOTLY_LAYOUT, title="Protein per kg Bodyweight",
                          height=380, xaxis_tickangle=-38, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        st.markdown('<div class="section-hdr">Calorie Intake vs Session Duration — does training load drive fueling?</div>', unsafe_allow_html=True)
        fig = px.scatter(
            fdf, x="session_min", y="kcal",
            color="sport", color_discrete_map=SPORT_COLORS,
            size="weight_kg", size_max=22,
            hover_name="name",
            hover_data={"session_min": True, "kcal": True, "intensity": True, "weight_kg": ":.0f"},
            labels={"session_min": "Session Duration (min)", "kcal": "Daily Calories (kcal)"},
            trendline="ols", trendline_scope="overall",
            trendline_color_override="rgba(26,35,126,0.25)",
        )
        fig.update_layout(**PLOTLY_LAYOUT, title="Calorie Intake vs Session Duration", height=340)
        st.plotly_chart(fig, use_container_width=True)

    with col4:
        st.markdown('<div class="section-hdr">Nutrient Density Heatmap — per kg bodyweight (row-normalised)</div>', unsafe_allow_html=True)
        heat = fdf[["last_name", "sport", "protein_per_kg", "carbs_per_kg", "fat_per_kg", "kcal_per_kg"]].copy()
        heat = heat.sort_values(["sport", "protein_per_kg"])
        nutrients = ["protein_per_kg", "carbs_per_kg", "fat_per_kg", "kcal_per_kg"]
        # Normalise each nutrient column to 0-1
        z_norm = heat[nutrients].copy()
        for col in nutrients:
            mn, mx = z_norm[col].min(), z_norm[col].max()
            z_norm[col] = (z_norm[col] - mn) / (mx - mn + 1e-9)
        fig = go.Figure(go.Heatmap(
            z=z_norm[nutrients].values.T,
            x=heat.last_name,
            y=["Protein/kg", "Carbs/kg", "Fat/kg", "kcal/kg"],
            customdata=heat[nutrients].values.T,
            hovertemplate="<b>%{x}</b><br>%{y}: %{customdata:.3f}<extra></extra>",
            colorscale=[[0, "#EEF2FF"], [0.35, "#AABFFF"], [0.65, "#E64A19"], [1, "#7B1FA2"]],
            showscale=True,
            colorbar=dict(tickfont=dict(color="#1A1A2E"), thickness=12),
        ))
        fig.update_layout(**lay(title="Nutrient Density Heatmap", height=340, xaxis_tickangle=-38, margin=dict(t=48, b=60, l=80, r=40)))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="section-hdr">Sport Nutritional Fingerprint — radar of normalised averages</div>', unsafe_allow_html=True)
    radar_metrics = ["kcal", "protein_g", "carbs_g", "fat_g", "hydration_ml"]
    radar_labels  = ["Calories", "Protein", "Carbs", "Fat", "Hydration"]
    sport_avg = fdf.groupby("sport")[radar_metrics].mean()
    norm_avg  = (sport_avg - sport_avg.min()) / (sport_avg.max() - sport_avg.min() + 1e-9)

    fig = go.Figure()
    for sport in norm_avg.index:
        vals = norm_avg.loc[sport].tolist()
        vals += [vals[0]]  # close the polygon
        fig.add_trace(go.Scatterpolar(
            r=vals, theta=radar_labels + [radar_labels[0]],
            name=f"{SPORT_ICONS.get(sport,'')} {sport}",
            line_color=SPORT_COLORS.get(sport, "#fff"),
            fill="toself",
            fillcolor=SPORT_COLORS.get(sport, "#fff").replace("#", "rgba(").replace("FF", "FF,").replace(")", ",0.08)") + ")"
                if False else f"rgba(0,0,0,0)",
            line_width=2.5,
        ))
    fig.update_layout(**lay(
        title="Sport Nutritional Fingerprint",
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True, range=[0, 1], gridcolor="rgba(26,35,126,0.1)",
                            tickfont=dict(color="rgba(26,35,126,0.35)"), showticklabels=False),
            angularaxis=dict(gridcolor="rgba(26,35,126,0.12)", tickfont=dict(color="#1A1A2E", size=12)),
        ),
        height=420,
        showlegend=True,
        legend=dict(orientation="h", y=-0.08, x=0.5, xanchor="center"),
        margin=dict(t=48, b=60, l=40, r=40),
    ))
    st.plotly_chart(fig, use_container_width=True)



with t4:
    st.markdown("""
    <div class="insight">
      <span class="insight-tag">💡 Key Insight</span>
      <strong>Calorie intake per minute of training</strong> exposes Hamilton as a severe under-fueler
      at 3.8 kcal/min for a 90-min moderate session. Breaking dancers train the longest (120 min High intensity)
      yet consume only 4.2 kcal/min — suggesting high aerobic efficiency. Basketball's Doncic tops caloric
      density at 14.0 kcal/min for a Low-intensity 60-min session, pointing to a high resting energy demand.
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="section-hdr">Calorie Intake per Minute of Training</div>', unsafe_allow_html=True)
        eff = fdf[["name", "sport", "kcal_per_min", "intensity", "kcal", "session_min"]].sort_values("kcal_per_min")
        fig = px.bar(
            eff, x="kcal_per_min", y="name", orientation="h",
            color="intensity", color_discrete_map=INTENSITY_COLORS,
            hover_data={"kcal": True, "session_min": True, "sport": True, "kcal_per_min": ":.2f"},
            labels={"kcal_per_min": "kcal / min of training", "name": ""},
        )
        fig.update_layout(**lay(title="Calorie Intake per Minute of Training",
                                height=430, margin=dict(t=48, b=24, l=160, r=40), legend_title="Intensity"))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown('<div class="section-hdr">Session Duration vs Calories per kg — relative training load</div>', unsafe_allow_html=True)
        fig = px.scatter(
            fdf, x="session_min", y="kcal_per_kg",
            color="sport", color_discrete_map=SPORT_COLORS,
            size="body_fat_pct", size_max=22,
            text="last_name",
            hover_name="name",
            hover_data={"kcal_per_kg": ":.2f", "session_min": True,
                        "intensity": True, "body_fat_pct": ":.1f"},
            labels={
                "session_min":  "Session Duration (min)",
                "kcal_per_kg":  "Calories per kg bodyweight",
            },
        )
        fig.update_traces(textposition="top center", textfont_size=9,
                          textfont_color="rgba(26,35,126,0.7)")
        fig.update_layout(**PLOTLY_LAYOUT, title="Session Duration vs Calories per kg", height=430)
        st.plotly_chart(fig, use_container_width=True)

    # Sport-level bubble: avg session duration vs avg kcal/min, size = avg protein/kg
    st.markdown('<div class="section-hdr">Sport Training Profile — session length vs fueling rate (size = protein efficiency)</div>', unsafe_allow_html=True)
    sp_profile = fdf.groupby("sport").agg(
        avg_session=("session_min",    "mean"),
        avg_kcal_min=("kcal_per_min",  "mean"),
        avg_prot_kg=("protein_per_kg", "mean"),
        avg_hydration=("hydration_ml", "mean"),
        n=("name", "count"),
    ).reset_index()
    sp_profile["label"] = sp_profile.sport.apply(lambda s: SPORT_ICONS.get(s, "") + " " + s)

    fig = px.scatter(
        sp_profile,
        x="avg_session", y="avg_kcal_min",
        size="avg_prot_kg", size_max=55,
        color="sport", color_discrete_map=SPORT_COLORS,
        text="label",
        hover_data={
            "avg_session":   ":.0f",
            "avg_kcal_min":  ":.2f",
            "avg_prot_kg":   ":.3f",
            "avg_hydration": ":.0f",
        },
        labels={
            "avg_session":  "Avg Session Duration (min)",
            "avg_kcal_min": "Avg kcal per Minute",
        },
    )
    fig.update_traces(textposition="top center", textfont_size=11,
                      textfont_color="#1A1A2E")
    fig.update_layout(**lay(title="Sport Training Profile",
                            height=420, showlegend=False, margin=dict(t=48, b=24, l=60, r=40)))
    st.plotly_chart(fig, use_container_width=True)

    # Hydration analysis
    col3, col4 = st.columns(2)
    with col3:
        st.markdown('<div class="section-hdr">Total Hydration per Session (ml)</div>', unsafe_allow_html=True)
        hyd_df = fdf[["name", "sport", "hydration_ml", "electrolytes_mg"]].sort_values("hydration_ml", ascending=False)
        fig = px.bar(
            hyd_df, x="name", y="hydration_ml",
            color="sport", color_discrete_map=SPORT_COLORS,
            hover_data={"electrolytes_mg": ":.0f", "hydration_ml": ":.0f"},
            labels={"hydration_ml": "Total Volume (ml)", "name": ""},
        )
        fig.update_layout(**PLOTLY_LAYOUT, title="Total Hydration per Session",
                          height=320, xaxis_tickangle=-35, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col4:
        st.markdown('<div class="section-hdr">Hydration per kg Bodyweight — relative fluid intake</div>', unsafe_allow_html=True)
        hyd_kg = fdf[["name", "sport", "hydration_per_kg", "weight_kg"]].sort_values("hydration_per_kg", ascending=False)
        fig = px.bar(
            hyd_kg, x="name", y="hydration_per_kg",
            color="sport", color_discrete_map=SPORT_COLORS,
            hover_data={"weight_kg": ":.0f", "hydration_per_kg": ":.2f"},
            labels={"hydration_per_kg": "ml / kg bodyweight", "name": ""},
        )
        fig.update_layout(**PLOTLY_LAYOUT, title="Hydration per kg Bodyweight",
                          height=320, xaxis_tickangle=-35, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
