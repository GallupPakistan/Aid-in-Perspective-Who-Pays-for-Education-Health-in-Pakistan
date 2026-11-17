"""
Who Pays? Financing education and health in Pakistan
Households (HIES) vs government (PIE / Pakistan Economic Survey) vs international aid (OECD CRS).

Run:  streamlit run app.py
All data files must sit in the same folder as this script.
"""
import re
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

DATA = Path(__file__).parent

# --------------------------------------------------------------------------
# Assumptions (change here if needed; every one is listed on the Methodology page)
# --------------------------------------------------------------------------
HOUSEHOLDS = 38_340_566        # Census 2023 (PBS): total households in Pakistan
PKR_PER_USD = 278.55           # Interbank rate at end-2024
CPI_FY19_TO_FY25 = 2.254       # Cumulative CPI rise FY2019 -> FY2025 (PBS annual
                               # average inflation: 10.7%, 8.9%, 12.2%, 29.2%, 23.4%, 4.5%)
AID_YEAR = 2024                # Latest complete OECD CRS year
HIES_YEAR = "2024-25"
# UNESCO GEM Report convention for "level unspecified" education aid
UNESCO_SPLIT = {"Basic (primary)": 0.50, "Secondary": 0.25, "Post-secondary": 0.25}

# --------------------------------------------------------------------------
# Design tokens
# --------------------------------------------------------------------------
NAVY = "#14365D"
INK = "#1F2933"
MUTED = "#6B7785"
GRID = "#E6EAF0"
COL = {"Households": "#6A3D9A", "Government": "#8C99A6", "Aid": "#E07B39"}
SERIES = ["#2F6EBA", "#E07B39", "#2E9E6B", "#C2417A", "#8C6BB1",
          "#D4A72C", "#3FA7C6", "#9C6B4E", "#7F8C99", "#B7C0CA"]
LVL_ORDER = ["Basic (primary)", "Secondary", "Post-secondary", "System-wide (not level-specific)"]
LVL_COL = dict(zip(LVL_ORDER, ["#2F6EBA", "#2E9E6B", "#8C6BB1", "#B7C0CA"]))
FONT = "Inter, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"

pio.templates["clean"] = go.layout.Template(layout=dict(
    font=dict(family=FONT, size=13, color=INK),
    colorway=SERIES, plot_bgcolor="white", paper_bgcolor="white",
    hoverlabel=dict(bgcolor="white", bordercolor=GRID, font=dict(family=FONT, size=13, color=INK)),
    xaxis=dict(showgrid=False, linecolor="#C9D1DB", ticks="outside", tickcolor="#C9D1DB",
               tickfont=dict(color=MUTED, size=12), title=dict(font=dict(color=MUTED, size=12))),
    yaxis=dict(gridcolor=GRID, zeroline=False, tickfont=dict(color=MUTED, size=12),
               title=dict(font=dict(color=MUTED, size=12))),
    legend=dict(orientation="h", y=-0.18, x=0, font=dict(size=12, color=INK), title=None),
    margin=dict(l=8, r=16, t=16, b=8),
))
pio.templates.default = "clean"

st.set_page_config(page_title="Who Pays? Pakistan", page_icon="📊", layout="wide",
                   initial_sidebar_state="expanded")

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"], .stMarkdown, .stRadio, .stSelectbox, .stCheckbox {{ font-family: {FONT}; }}
.stApp {{ background: #F4F6F9; }}
.block-container {{ padding-top: 1.2rem; padding-bottom: 3rem; max-width: 1320px; }}
header[data-testid="stHeader"] {{ background: transparent; }}

/* sidebar */
section[data-testid="stSidebar"] {{ background: {NAVY}; }}
section[data-testid="stSidebar"] .stMarkdown, section[data-testid="stSidebar"] .stMarkdown *,
section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] *,
section[data-testid="stSidebar"] .stRadio label, section[data-testid="stSidebar"] .stRadio label * {{ color: #E8EEF6 !important; }}
section[data-testid="stSidebar"] [data-testid="stTooltipIcon"] svg {{ color: #E8EEF6 !important; stroke: #E8EEF6 !important; }}
section[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] * {{ color: #E8EEF6 !important; }}
section[data-testid="stSidebar"] [data-baseweb="select"] input {{ -webkit-text-fill-color: {INK} !important; }}
section[data-testid="stSidebar"] .stRadio label p {{ font-size: 0.98rem; }}
.sb-brand {{ font-weight: 700; font-size: 1.15rem; letter-spacing: .2px; margin: .2rem 0 .1rem; }}
.sb-sub {{ font-size: .8rem; opacity: .75; margin-bottom: 1.2rem; }}
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {{ padding-top: 0 !important; }}
section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] {{ height: 2.2rem; padding-bottom: 0; }}
section[data-testid="stSidebar"] [data-testid="stImage"] {{ margin-top: -0.6rem; margin-bottom: .4rem; }}
.sb-org {{ font-size: .78rem; letter-spacing: .06em; text-transform: uppercase; font-weight: 700;
          opacity: .85; margin: .2rem 0 .6rem; }}
.foot {{ margin-top: 2rem; padding-top: .8rem; border-top: 1px solid {GRID}; color: {MUTED}; font-size: .8rem;
        display: flex; justify-content: space-between; flex-wrap: wrap; gap: .5rem; }}
.notes {{ background: white; border: 1px solid {GRID}; border-left: 4px solid #D4A72C; border-radius: 10px;
         padding: .9rem 1.1rem; margin: .3rem 0 1rem; font-size: .92rem; color: {INK}; }}
.notes b {{ font-weight: 650; }}
.notes ol {{ margin: .4rem 0 0 1.1rem; padding: 0; }}
.notes li {{ margin-bottom: .3rem; }}
.sb-filt {{ font-size: .72rem; letter-spacing: .1em; text-transform: uppercase; font-weight: 700;
           opacity: .7; margin: 1.3rem 0 .3rem; border-top: 1px solid rgba(255,255,255,.15); padding-top: .9rem; }}
section[data-testid="stSidebar"] [data-baseweb="select"] > div {{ background: white; border-radius: 8px; }}
section[data-testid="stSidebar"] [data-baseweb="select"] *,
section[data-testid="stSidebar"] [data-baseweb="tag"] * {{ color: {INK} !important; }}
section[data-testid="stSidebar"] [data-baseweb="tag"] {{ background: #E3ECF7 !important; }}
section[data-testid="stSidebar"] [data-baseweb="select"] svg {{ fill: {INK} !important; }}
section[data-testid="stSidebar"] .stSelectbox label p, section[data-testid="stSidebar"] .stMultiSelect label p {{
    font-size: .85rem; font-weight: 600; }}
.sb-foot {{ font-size: .75rem; opacity: .7; line-height: 1.5; margin-top: 1.5rem;
           border-top: 1px solid rgba(255,255,255,.15); padding-top: .8rem; }}

/* page header */
.hero {{ background: linear-gradient(120deg, {NAVY} 0%, #1E5A8A 100%); color: white;
        border-radius: 14px; padding: 1.4rem 1.6rem; margin-bottom: 1.2rem; }}
.hero h1 {{ color: white; font-size: 1.65rem; font-weight: 700; margin: 0 0 .3rem; padding: 0; }}
.hero p {{ color: #D6E2F0; margin: 0; font-size: .95rem; }}
.hero .tag {{ display:inline-block; background: rgba(255,255,255,.14); border-radius: 999px;
             padding: .15rem .65rem; font-size: .75rem; margin-right: .4rem; margin-top: .7rem; }}

/* KPI cards */
.kpi {{ background: white; border: 1px solid {GRID}; border-radius: 12px; padding: 1rem 1.1rem;
       box-shadow: 0 1px 2px rgba(16,24,40,.05); height: 100%; position: relative; overflow: hidden; }}
.kpi:before {{ content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 4px;
              background: var(--accent, {NAVY}); }}
.kpi .lbl {{ font-size: .74rem; letter-spacing: .06em; text-transform: uppercase;
            color: {MUTED}; font-weight: 600; }}
.kpi .val {{ font-size: 1.9rem; font-weight: 700; color: {INK}; line-height: 1.25; margin-top: .25rem; }}
.kpi .sub {{ font-size: .85rem; color: {MUTED}; margin-top: .15rem; }}

/* section cards */
div[data-testid="stVerticalBlockBorderWrapper"] {{ background: white; border-radius: 12px !important;
    border: 1px solid {GRID} !important; box-shadow: 0 1px 2px rgba(16,24,40,.05); }}
.ct {{ font-weight: 650; font-size: 1.02rem; color: {INK}; margin: 0; }}
.cs {{ font-size: .85rem; color: {MUTED}; margin: .1rem 0 .4rem; }}
.src {{ font-size: .76rem; color: {MUTED}; border-top: 1px solid {GRID}; padding-top: .45rem; margin-top: .2rem; }}
.insight {{ background: #FFF6EE; border: 1px solid #F6D7BD; border-left: 4px solid {COL['Aid']};
           border-radius: 10px; padding: .85rem 1.1rem; color: {INK}; font-size: 1rem; margin-bottom: 1rem; }}
.sec {{ font-size: .8rem; letter-spacing: .08em; text-transform: uppercase; color: {MUTED};
       font-weight: 700; margin: 1.1rem 0 .5rem; }}
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------------------------------
# UI helpers
# --------------------------------------------------------------------------
def pct(x, d=1):
    return f"{x:.{d}f}%"


def bn(x):
    return f"Rs {x:,.0f} bn"


def usd_m(x):
    return f"US$ {x:,.0f}m" if abs(x) < 1000 else f"US$ {x/1000:,.2f}bn"


def hero(title, text, tags=()):
    t = "".join(f"<span class='tag'>{x}</span>" for x in tags)
    st.markdown(f"<div class='hero'><div style='font-size:.75rem;letter-spacing:.08em;text-transform:uppercase;"
                f"opacity:.8;margin-bottom:.35rem'>Gallup Pakistan · Digital Analytics · Draft for discussion</div>"
                f"<h1>{title}</h1><p>{text}</p>{t}</div>", unsafe_allow_html=True)


def kpi(col, label, value, sub="", accent=NAVY):
    col.markdown(f"<div class='kpi' style='--accent:{accent}'><div class='lbl'>{label}</div>"
                 f"<div class='val'>{value}</div><div class='sub'>{sub}</div></div>",
                 unsafe_allow_html=True)


def section(label):
    st.markdown(f"<div class='sec'>{label}</div>", unsafe_allow_html=True)


def insight(html):
    st.markdown(f"<div class='insight'>{html}</div>", unsafe_allow_html=True)


def chart(fig, title, subtitle="", source="", h=400, legend=True):
    with st.container(border=True):
        st.markdown(f"<p class='ct'>{title}</p>" + (f"<p class='cs'>{subtitle}</p>" if subtitle else ""),
                    unsafe_allow_html=True)
        fig.update_layout(height=h, showlegend=legend, legend_title_text="")
        st.plotly_chart(fig, width="stretch", config={"displaylogo": False,
                        "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d"]})
        if source:
            st.markdown(f"<div class='src'>{source}</div>", unsafe_allow_html=True)
        data = chart_data(fig)
        if not data.empty:
            st.download_button("⬇ Download data (CSV)", data.to_csv(index=False).encode("utf-8"),
                               file_name=re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")[:60] + ".csv",
                               mime="text/csv", key=f"dl_{title}_{subtitle}"[:200], type="tertiary")


def chart_data(fig):
    """The numbers behind a Plotly chart, as a tidy table."""
    rows = []
    for t in fig.data:
        if t.type == "pie":
            rows += [{"series": "", "category": l, "value": round(v, 2)} for l, v in zip(t.labels, t.values)]
            continue
        if getattr(t, "mode", None) == "text" or t.x is None or t.y is None:
            continue
        horiz = getattr(t, "orientation", None) == "h"
        cats, vals = (t.y, t.x) if horiz else (t.x, t.y)
        for c, v in zip(cats, vals):
            rows.append({"series": t.name or "", "category": c,
                         "value": round(v, 2) if isinstance(v, (int, float)) else v})
    return pd.DataFrame(rows)


def total_labels(fig, s, fmt):
    fig.add_trace(go.Scatter(x=list(s.index), y=list(s.values), mode="text",
                             text=[fmt(v) for v in s.values], textposition="top center",
                             textfont=dict(size=12, color=INK), showlegend=False, hoverinfo="skip"))


def hbar(df, x, y, color, h, label_col, hover):
    fig = px.bar(df.iloc[::-1], x=x, y=y, orientation="h", text=df.iloc[::-1][label_col],
                 color_discrete_sequence=[color])
    fig.update_traces(textposition="outside", cliponaxis=False, hovertemplate=hover,
                      marker_line_width=0, textfont=dict(color=INK, size=12))
    fig.update_layout(xaxis_title="US$ million", yaxis_title=None, bargap=0.3,
                      xaxis=dict(tickformat=",", range=[0, df[x].max() * 1.2], showgrid=True,
                                 gridcolor=GRID))
    return fig




# ---- simple chart builders (one idea per chart, easy to read) -------------
POP_2023 = {"Pakistan": 241_499_431, "Punjab": 127_688_922, "Sindh": 55_696_147,
            "Khyber Pakhtunkhwa": 40_856_097, "Balochistan": 14_894_402}   # Census 2023 (PBS)
GOOD, BAD = "#2E9E6B", "#C2417A"


def donut(labels, values, colors=None, center="", unit="US$ m"):
    fig = go.Figure(go.Pie(
        labels=list(labels), values=list(values), hole=0.58, sort=False, direction="clockwise",
        marker=dict(colors=colors, line=dict(color="white", width=2)),
        texttemplate="%{percent:.1%}", textfont=dict(size=13), insidetextorientation="horizontal",
        textposition="auto",
        hovertemplate="<b>%{label}</b><br>%{value:,.1f} " + unit + " · %{percent:.1%}<extra></extra>"))
    if center:
        fig.add_annotation(text=center, showarrow=False, font=dict(size=14, color=INK))
    fig.update_layout(legend=dict(orientation="h", y=-0.08, x=0.5, xanchor="center"))
    return fig


def vbar(x, y, color="#2F6EBA", text=None, ytitle="", ysuffix="", hover="%{x}: %{y:,.1f}"):
    colors = color if isinstance(color, list) else [color] * len(list(x))
    fig = go.Figure(go.Bar(x=list(x), y=list(y), marker=dict(color=colors, line_width=0),
                           text=text, textposition="outside", cliponaxis=False,
                           textfont=dict(size=12, color=INK), hovertemplate=hover + "<extra></extra>"))
    ymax, ymin = max(list(y) + [0]), min(list(y) + [0])
    pad = (ymax - ymin) * 0.18 or 1
    fig.update_layout(bargap=0.35, xaxis_title=None, yaxis_title=ytitle,
                      yaxis=dict(tickformat=",", ticksuffix=ysuffix,
                                 range=[ymin - (pad if ymin < 0 else 0), ymax + pad]))
    if all(isinstance(v, (int, float)) and 2000 < v < 2100 for v in list(x)):
        fig.update_xaxes(dtick=1)
    else:
        fig.update_xaxes(type="category")
    return fig


def hb(cats, vals, labels, color="#2F6EBA", xtitle="US$ million", hover="%{y}: %{x:,.1f}"):
    cats, vals, labels = list(cats)[::-1], list(vals)[::-1], list(labels)[::-1]
    colors = color[::-1] if isinstance(color, list) else [color] * len(cats)
    fig = go.Figure(go.Bar(y=cats, x=vals, orientation="h", marker=dict(color=colors, line_width=0),
                           text=labels, textposition="outside", cliponaxis=False,
                           textfont=dict(size=12, color=INK), hovertemplate=hover + "<extra></extra>"))
    lo, hi = min(vals + [0]), max(vals + [0])
    pad = (hi - lo) * 0.38 or 1
    fig.update_layout(bargap=0.3, xaxis_title=xtitle, yaxis_title=None,
                      xaxis=dict(tickformat=",", showgrid=True, gridcolor=GRID,
                                 range=[lo - (pad if lo < 0 else 0), hi + pad]))
    return fig


def pm_bars(cats, vals, suffix="%", xtitle=None, horizontal=True, dec=1):
    """Positive/negative change bars: green up, red down."""
    cols = [GOOD if v >= 0 else BAD for v in vals]
    lab = [f"{v:+.{dec}f}{suffix}" for v in vals]
    if horizontal:
        return hb(cats, vals, lab, cols, xtitle or "", "%{y}: %{x:+.1f}" + suffix)
    return vbar(cats, vals, cols, lab, "", suffix, "%{x}: %{y:+.1f}" + suffix)


def line(df, x, y, color=None, ytitle="", ysuffix="", colors=None, fmt=",.1f"):
    fig = px.line(df, x=x, y=y, color=color, markers=True, color_discrete_sequence=colors or SERIES)
    fig.update_traces(line_width=2.5, marker_size=7,
                      hovertemplate=("<b>%{fullData.name}</b><br>" if color else "") +
                      "%{x}: %{y:" + fmt + "}" + ysuffix + "<extra></extra>")
    fig.update_layout(xaxis_title=None, yaxis_title=ytitle, legend_title_text="",
                      yaxis=dict(tickformat=",", ticksuffix=ysuffix, rangemode="tozero"))
    if pd.api.types.is_numeric_dtype(df[x]):
        fig.update_xaxes(dtick=1)
    return fig


def stack(df, x, y, color, cmap=None, order=None, ytitle="US$ million", pct_mode=False):
    fig = px.bar(df, x=x, y=y, color=color, color_discrete_map=cmap,
                 category_orders={color: order} if order else None,
                 text=df[y].map(lambda v: f"{v:.0f}%" if v >= 8 else "") if pct_mode else None)
    fig.update_traces(marker_line_width=0, textposition="inside", textfont=dict(color="white", size=11),
                      hovertemplate="<b>%{fullData.name}</b><br>%{x}: %{y:,.1f}" + ("%" if pct_mode else "")
                      + "<extra></extra>")
    fig.update_layout(barmode="stack", bargap=0.3, xaxis_title=None, yaxis_title=ytitle,
                      yaxis=dict(tickformat=",", ticksuffix="%" if pct_mode else "",
                                 range=[0, 100] if pct_mode else None))
    if pd.api.types.is_numeric_dtype(df[x]):
        fig.update_xaxes(dtick=1)
    return fig


def grid(n=2):
    return st.columns(n)


def sector3(purpose_code):
    """3-digit DAC sector from a 5-digit purpose code."""
    return purpose_code // 100


CHANNEL_GROUP = {1: "Government (public sector)", 2: "NGOs & civil society", 3: "Public-private partnerships",
                 4: "Multilateral organisations", 5: "Universities & research", 6: "Private sector",
                 9: "Other"}


# --------------------------------------------------------------------------
# Data
# --------------------------------------------------------------------------
GROUPS = {
    **{c: "Education" for c in (111, 112, 113, 114)},
    **{c: "Health" for c in (121, 122, 123)},
    130: "Population & reproductive health", 140: "Water & sanitation",
    151: "Government & civil society", 152: "Government & civil society",
    160: "Other social services",
    210: "Transport & communications", 220: "Transport & communications",
    **{c: "Energy" for c in (231, 232, 233, 234, 235, 236)},
    240: "Banking & business", 250: "Banking & business",
    311: "Agriculture", 312: "Agriculture", 313: "Agriculture",
    321: "Industry & mining", 322: "Industry & mining", 323: "Industry & mining",
    331: "Trade & tourism", 332: "Trade & tourism",
    410: "Environment", 430: "Multisector",
    510: "General budget support",
    520: "Food & commodity aid", 530: "Food & commodity aid",
    600: "Debt relief",
    720: "Humanitarian", 730: "Humanitarian", 740: "Humanitarian",
    910: "Other / unallocated", 930: "Other / unallocated", 998: "Other / unallocated",
}
LEVEL = {111: "System-wide (not level-specific)", 112: "Basic (primary)",
         113: "Secondary", 114: "Post-secondary"}


@st.cache_data
def load():
    aid = pd.read_csv(DATA / "pakistan_oda_by_donor_sector_2015_2024.csv") \
            .rename(columns={"usd_disbursement_defl": "usd_m"})
    aid["group"] = aid.sector_code.map(GROUPS).fillna("Other / unallocated")
    mod = pd.read_csv(DATA / "pakistan_aid_by_modality_2015_2024.csv")
    proj = pd.read_csv(DATA / "pakistan_oda_projects_2015_2024.csv",
                       usecols=["year", "donor", "flow", "purpose_code", "purpose",
                                "commitment_usd_m_2024prices", "disbursement_usd_m_2024prices",
                                "gender_marker", "climate_mitigation_marker", "climate_adaptation_marker",
                                "channel_code", "bilateral_multilateral"])
    mm, ma = proj.climate_mitigation_marker, proj.climate_adaptation_marker
    proj["climate_marker"] = "Not screened"
    for lvl in ["Not targeted", "Significant objective", "Principal objective"]:  # higher level wins
        proj.loc[(mm == lvl) | (ma == lvl), "climate_marker"] = lvl
    hies = pd.read_csv(DATA / "hies_household_spending_2018-19_2024-25.csv")
    pie = pd.read_csv(DATA / "education_spending_PIE_2019-20_2025-26.csv")
    pes = pd.read_csv(DATA / "government_spending_education_health_2018-19_2024-25.csv")
    school = pd.read_csv(DATA / "hies_school_type_2024-25.csv")
    dac1 = pd.read_csv(DATA / "oecd_dac1_total_oda_by_donor_2023_2025.csv")
    trend = pd.read_csv(DATA / "who_pays_trend_inputs.csv").set_index("fiscal_year")
    return aid, mod, proj, hies, pie, pes, school, dac1, trend


aid, mod, proj, hies, pie, pes, school, dac1, trend = load()
YEARS = sorted(aid.year.unique())
e02 = (mod[(mod.sector_code == 110) & (mod.modality_code == "E02")]
       .set_index("year").usd_million_2024prices.reindex(YEARS).fillna(0))
alloc = aid[aid.sector_code.between(111, 430)].groupby("year").usd_m.sum()


def edu_aid_by_year(exclude_isc=True):
    s = aid[aid.group == "Education"].groupby("year").usd_m.sum().reindex(YEARS).fillna(0)
    return s - e02 if exclude_isc else s


def health_aid_by_year():
    return (aid[aid.group.isin(["Health", "Population & reproductive health"])]
            .groupby("year").usd_m.sum().reindex(YEARS).fillna(0))


def hh_monthly(item, area="PAKISTAN", year=HIES_YEAR):
    r = hies[(hies.item == item) & (hies.area == area) & (hies.year == year)]
    return float(r.total.iloc[0])


PIE_GOVS = ["Federal", "Punjab", "Sindh", "Khyber Pakhtunkhwa", "Balochistan"]


def gov_edu(fy):
    return pie[(pie.fiscal_year == fy) & (pie.government.isin(PIE_GOVS))].total_rs_m.sum() / 1000


def gov_health(fy):
    return pes[(pes.sector == "Health") & (pes.fiscal_year == fy)
               & (pes.government == "Pakistan")].total_rs_m.sum() / 1000


def who_pays(fy, gov_edu_fy="2024-25"):
    """Rs billion by payer for one fiscal year (2018-19 or 2024-25)."""
    t = trend.loc[fy]
    hh = lambda item: hh_monthly(item, year=fy) * 12 * t.households / 1e9
    g_edu = (pes[(pes.sector == "Education") & (pes.fiscal_year == "2018-19") & (pes.government == "Pakistan")]
             .total_rs_m.sum() / 1000) if fy == "2018-19" else gov_edu(gov_edu_fy)
    return {
        "Education": {"Households": hh("Education"), "Government": g_edu,
                      "Aid": t.edu_aid_usd_m_current * t.pkr_per_usd / 1000},
        "Health": {"Households": hh("Health"), "Government": gov_health(fy),
                   "Aid": t.health_aid_usd_m_current * t.pkr_per_usd / 1000},
    }


def shares(d):
    return {s: {p: v / sum(x.values()) * 100 for p, v in x.items()} for s, x in d.items()}


# 2025 aid-cut scenario: apply each donor's overall 2024->2025 change (OECD preliminary) to its 2024 aid to Pakistan
CHG = dac1.set_index("donor").change_2024_2025_pct


def cut_scenario(frame):
    d = frame[frame.year == AID_YEAR].groupby("donor").usd_m.sum().rename("aid_2024").reset_index()
    d["change_pct"] = d.donor.map(CHG)
    d["status"] = d.change_pct.apply(lambda v: "2025 data available" if pd.notna(v) else "No 2025 data yet")
    d["aid_2025_est"] = d.aid_2024 * (1 + d.change_pct.fillna(0) / 100)
    d["loss"] = d.aid_2024 - d.aid_2025_est
    return d.sort_values("aid_2024", ascending=False)


# --------------------------------------------------------------------------
# Sidebar navigation
# --------------------------------------------------------------------------
PAGES = ["Key findings", "Who pays", "Aid overview", "2025 aid cuts", "Education aid", "Health aid",
         "Pipeline & priorities", "Government spending", "Household spending", "Methodology"]
ORG = "Gallup Pakistan · Digital Analytics"
LOGO = next((DATA / f for f in ("logo.png", "logo.jpg", "logo.jpeg", "logo.svg") if (DATA / f).exists()), None)
with st.sidebar:
    if LOGO:
        import base64
        mime = "image/svg+xml" if LOGO.suffix == ".svg" else f"image/{LOGO.suffix[1:].replace('jpg', 'jpeg')}"
        b64 = base64.b64encode(LOGO.read_bytes()).decode()
        # full-resolution image scaled by the browser stays sharp on high-resolution screens
        st.markdown(f"<img src='data:{mime};base64,{b64}' alt='Gallup Pakistan Digital Analytics' "
                    f"style='width:170px;height:auto;display:block;margin:-0.4rem 0 .9rem;"
                    f"image-rendering:auto'>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='sb-org'>{ORG}</div>", unsafe_allow_html=True)
    st.markdown("<div class='sb-brand'>Who Pays?</div>"
                "<div class='sb-sub'>Financing education & health in Pakistan</div>",
                unsafe_allow_html=True)
    page = st.radio("Navigate", PAGES, label_visibility="collapsed")
    if page not in ("Methodology", "Key findings"):
        st.markdown("<div class='sb-filt'>Filters</div>", unsafe_allow_html=True)
SB_FOOT = (f"<div class='sb-foot'><b>Data</b><br>OECD CRS (Oct 2026 release)<br>"
                f"HIES 2018-19 & 2024-25 (PBS)<br>PIE Public Financing in Education 2025-26<br>"
                f"Pakistan Economic Survey 2024-25 & 2025-26<br><br>"
                f"Aid in constant 2024 US$ · Rs {PKR_PER_USD}/US$</div>")

# ==========================================================================
# 1. WHO PAYS
# ==========================================================================
if page == "Key findings":
    hero("Key findings",
         "The main messages from the data, at a glance. Open the page named on each card for the detail.",
         ["Pakistan", "Education & health", "2015–2025"])
    now, then = shares(who_pays("2024-25")), shares(who_pays("2018-19"))
    sc = cut_scenario(aid)
    known = sc[sc.status == "2025 data available"]
    ea_ = edu_aid_by_year()
    lvl_ = aid[aid.group == "Education"].copy()
    basic15 = lvl_[(lvl_.sector_code == 112) & (lvl_.year == YEARS[0])].usd_m.sum()
    basic24 = lvl_[(lvl_.sector_code == 112) & (lvl_.year == AID_YEAR)].usd_m.sum()
    tot24 = aid[aid.year == AID_YEAR].usd_m.sum()
    sau24 = aid[(aid.year == AID_YEAR) & (aid.donor == "Saudi Arabia")].usd_m.sum()
    hh_e = hies[(hies.area == "PAKISTAN") & (hies.item == "Education")].set_index("year").total
    real_e = (hh_e["2024-25"] / (hh_e["2018-19"] * CPI_FY19_TO_FY25) - 1) * 100
    q = hies[(hies.area == "PAKISTAN") & (hies.item == "Education") & (hies.year == "2024-25")].iloc[0]
    usa = CHG.get("United States")
    dac = dac1.set_index("donor_code").change_2024_2025_pct.get("DAC")

    F = [
        ("Who pays", COL["Aid"], f"{now['Education']['Aid']:.1f}%",
         "of education spending in Pakistan comes from international aid",
         f"In health it is {now['Health']['Aid']:.1f}%. Government pays {now['Education']['Government']:.0f}% of "
         f"education and households {now['Education']['Households']:.0f}% (2024-25)."),
        ("Who pays", COL["Households"], f"{now['Health']['Households']:.0f}%",
         "of health spending is paid by households themselves",
         f"Up from {then['Health']['Households']:.0f}% in 2018-19, while the government's share fell from "
         f"{then['Health']['Government']:.0f}% to {now['Health']['Government']:.0f}%."),
        ("Education aid", "#C2417A", f"{(ea_[AID_YEAR] / ea_[YEARS[0]] - 1) * 100:+.0f}%",
         f"change in education aid, {YEARS[0]}–{AID_YEAR}",
         f"From {usd_m(ea_[YEARS[0]])} to {usd_m(ea_[AID_YEAR])} (2024 prices). Aid to basic education fell from "
         f"{usd_m(basic15)} to {usd_m(basic24)}."),
        ("2025 aid cuts", "#C2417A", f"{dac:+.1f}%",
         "fall in total aid from DAC donors in 2025",
         f"The United States cut its aid by {abs(usa):.0f}%. If donors cut aid to Pakistan in line with their "
         f"overall cuts, Pakistan would lose about {usd_m(known.loss.sum())} a year."),
        ("Aid overview", "#D4A72C", f"{sau24 / tot24 * 100:.0f}%",
         f"of all aid to Pakistan in {AID_YEAR} came from Saudi Arabia",
         f"Almost all of it was general budget support, not tied to any sector. Total aid was {usd_m(tot24)}."),
        ("Household spending", "#2E9E6B", f"{q.q5_richest / q.q1_poorest:.1f}×",
         "more spent on education by the richest 20% than the poorest 20%",
         f"Rs {q.q5_richest:,.0f} vs Rs {q.q1_poorest:,.0f} a month. After inflation, the average household spends "
         f"{abs(real_e):.0f}% {'less' if real_e < 0 else 'more'} on education than in 2018-19."),
    ]
    hp_ = proj[proj.purpose_code.between(12000, 13999) & (proj.year == AID_YEAR)]
    vacc = hp_[hp_.purpose_code.isin([12250, 12262, 12263, 13040])].disbursement_usd_m_2024prices.sum()
    gavi = hp_[hp_.donor == "Gavi"].disbursement_usd_m_2024prices.sum()
    p24 = proj[proj.year == AID_YEAR]
    com24, dis24 = p24.commitment_usd_m_2024prices.sum(), p24.disbursement_usd_m_2024prices.sum()
    scr = p24[p24.climate_marker != "Not screened"]
    clim = scr[scr.climate_marker.isin(["Principal objective", "Significant objective"])].disbursement_usd_m_2024prices.sum() \
        / scr.disbursement_usd_m_2024prices.sum() * 100
    e23 = gov_edu("2023-24")
    pun = pie[(pie.fiscal_year == "2023-24") & (pie.government == "Punjab")].total_rs_m.sum() / 1000
    F += [
        ("Health aid", "#C2417A", f"{vacc / hp_.disbursement_usd_m_2024prices.sum() * 100:.0f}%",
         f"of health aid in {AID_YEAR} went to fighting infectious diseases and vaccines",
         f"Gavi, the vaccine alliance, was the largest health donor with {usd_m(gavi)}."),
        ("Pipeline & priorities", "#2F6EBA", usd_m(com24),
         f"of new aid was promised to Pakistan in {AID_YEAR}",
         f"{usd_m(dis24)} was actually paid out that year ({dis24 / com24 * 100:.0f}% of the promised amount)."),
        ("Pipeline & priorities", "#2E9E6B", f"{clim:.0f}%",
         f"of screened aid in {AID_YEAR} targeted climate change",
         "Up from roughly a quarter to a third of aid in 2015-2023."),
        ("Government spending", "#3FA7C6", bn(e23),
         "spent by federal and provincial governments on education in 2023-24",
         f"Punjab alone spent {bn(pun)} ({pun / e23 * 100:.0f}%). Actual spending, Pakistan Institute of Education."),
    ]
    st.markdown(
        "<div class='notes'><b>Notes on the data</b><ol>"
        "<li><b>2025 aid cuts for Pakistan are an estimate.</b> They apply each donor's overall 2025 cut "
        "(OECD preliminary data) to its 2024 aid to Pakistan. Actual 2025 aid to Pakistan is not published yet.</li>"
        "<li><b>Government education spending for 2024-25 is a budget allocation</b>, not actual spending. "
        "The latest actual figure is 2023-24, which can be selected on the <i>Who pays</i> page.</li>"
        "<li><b>Official sources differ for some years.</b> This dashboard uses the most reliable one for "
        "education: actual spending from the Pakistan Institute of Education. The Pakistan Economic Survey is used "
        "for health.</li>"
        "<li><b>Gender and climate shares</b> cover only aid that donors screened for those markers.</li>"
        "</ol></div>", unsafe_allow_html=True)
    for i in range(0, len(F), 2):
        cols = st.columns(2)
        for col, (pg_, acc, big, line, detail) in zip(cols, F[i:i + 2]):
            col.markdown(
                f"<div class='kpi' style='--accent:{acc};min-height:190px'>"
                f"<div class='lbl'>{pg_}</div><div class='val' style='font-size:2.3rem'>{big}</div>"
                f"<div style='font-weight:600;color:{INK};margin:.2rem 0 .5rem'>{line}</div>"
                f"<div class='sub'>{detail}</div></div>", unsafe_allow_html=True)
        st.write("")
    st.markdown(f"<div class='src'>Sources: OECD CRS and DAC1 (2025 preliminary), HIES 2018-19 and 2024-25, "
                f"Pakistan Institute of Education, Pakistan Economic Survey. Government education figure for "
                f"2024-25 is a budget allocation. See Methodology.</div>", unsafe_allow_html=True)

elif page == "Who pays":
    hero("Who pays for education and health in Pakistan?",
         "How much comes from households, the government and international aid, and how that has changed.",
         ["Households: HIES", "Government: PIE / Economic Survey", f"Aid: OECD CRS"])
    gov_basis = st.sidebar.selectbox(
        "Government education figure", ["2024-25 budget allocation", "2023-24 actual spending"],
        help="2024-25 matches the HIES and aid year but is a budget allocation; "
             "2023-24 is the latest actual spending.")
    fy_gov = "2024-25" if gov_basis.startswith("2024-25") else "2023-24"
    w, w0 = who_pays("2024-25", fy_gov), who_pays("2018-19")
    s, s0 = shares(w), shares(w0)
    P = ["Households", "Government", "Aid"]
    PC = [COL[p] for p in P]

    insight(f"Of every <b>Rs 100</b> spent on education in Pakistan, about <b>Rs {s['Education']['Aid']:.0f}</b> "
            f"comes from international aid (<b>Rs {s['Health']['Aid']:.0f}</b> in health). "
            f"Households and the government pay the rest.")
    src_now = (f"HIES 2024-25 × {HOUSEHOLDS:,} households; government education {fy_gov} (PIE); government "
               f"health 2024-25 (Economic Survey); aid 2024 (OECD CRS) at Rs {PKR_PER_USD}/US$.")
    src_then = "2018-19: HIES 2018-19 × 32,205,111 households (Census 2017); Economic Survey; aid 2018 at Rs 139.86/US$."

    c1, c2 = grid()
    with c1:
        chart(donut(P, [w["Education"][p] for p in P], PC, "Education", "Rs bn"),
              "1 · Who pays for education", "Share of total education spending, 2024-25", h=380, source=src_now)
    with c2:
        chart(donut(P, [w["Health"][p] for p in P], PC, "Health", "Rs bn"),
              "2 · Who pays for health", "Share of total health spending, 2024-25", h=380, source=src_now)
    c1, c2 = grid()
    with c1:
        chart(pm_bars(P, [s["Education"][p] - s0["Education"][p] for p in P], " pts", "percentage points"),
              "3 · Education: how each share changed", "Change in share, 2018-19 → 2024-25 (percentage points)",
              h=330, legend=False, source=src_then)
    with c2:
        chart(pm_bars(P, [s["Health"][p] - s0["Health"][p] for p in P], " pts", "percentage points"),
              "4 · Health: how each share changed", "Change in share, 2018-19 → 2024-25 (percentage points)",
              h=330, legend=False, source=src_then)
    c1, c2 = grid()
    with c1:
        chart(pm_bars(P, [(w["Education"][p] / (w0["Education"][p] * CPI_FY19_TO_FY25) - 1) * 100 for p in P]),
              "5 · Education: real growth in spending", "2018-19 → 2024-25, after inflation",
              h=330, legend=False, source="Inflation-adjusted with cumulative CPI ×2.254 (PBS).")
    with c2:
        chart(pm_bars(P, [(w["Health"][p] / (w0["Health"][p] * CPI_FY19_TO_FY25) - 1) * 100 for p in P]),
              "6 · Health: real growth in spending", "2018-19 → 2024-25, after inflation",
              h=330, legend=False, source="Inflation-adjusted with cumulative CPI ×2.254 (PBS).")
    c1, c2 = grid()
    with c1:
        tot = [sum(w[k].values()) for k in ["Education", "Health"]]
        chart(vbar(["Education", "Health"], tot, ["#2F6EBA", "#C2417A"], [bn(v) for v in tot], "Rs billion",
                   hover="%{x}: Rs %{y:,.0f} bn"),
              "7 · Total spending: education vs health", "All sources combined, Rs billion a year, 2024-25",
              h=330, legend=False)
    with c2:
        hm = [hh_monthly("Education"), hh_monthly("Health")]
        chart(vbar(["Education", "Health"], hm, [COL["Households"]] * 2, [f"Rs {v:,.0f}" for v in hm],
                   "Rs per month", hover="%{x}: Rs %{y:,.0f} a month"),
              "8 · What one household pays each month", "Average household, 2024-25",
              h=330, legend=False, source="Source: HIES 2024-25, Table 16.")
    c1, c2 = grid()
    with c1:
        ap = [w[k]["Aid"] / w[k]["Government"] * 100 for k in ["Education", "Health"]]
        chart(vbar(["Education", "Health"], ap, [COL["Aid"]] * 2, [f"{v:.1f}%" for v in ap], "%", "%",
                   "%{x}: %{y:.1f}%"),
              "9 · Aid compared with government spending", "Aid as % of the government's own spending, 2024-25",
              h=330, legend=False)
    with c2:
        au = [edu_aid_by_year()[AID_YEAR], health_aid_by_year()[AID_YEAR]]
        chart(vbar(["Education", "Health"], au, [COL["Aid"]] * 2, [usd_m(v) for v in au], "US$ million",
                   hover="%{x}: US$ %{y:,.0f}m"),
              f"10 · International aid: education vs health", f"US$ million, {AID_YEAR}",
              h=330, legend=False, source="Education excludes imputed student costs; health includes population "
                                          "& reproductive health.")

# ==========================================================================
# AID OVERVIEW
# ==========================================================================
elif page == "Aid overview":
    hero("International aid to Pakistan",
         "Official development assistance from all donors, by year, donor, sector and type.",
         ["OECD CRS", "Disbursements", "Constant 2024 US$"])
    y0 = st.sidebar.selectbox("From year", YEARS[:-1], index=0)
    y1 = st.sidebar.selectbox("To year", [y for y in YEARS if y > y0], index=len([y for y in YEARS if y > y0]) - 1)
    yr = (y0, y1)
    excl_gbs = st.sidebar.selectbox("General budget support", ["Include", "Exclude"],
                                    help="Saudi Arabia's 2023-24 support (US$2-3bn a year) is general budget "
                                         "support and is not tied to any sector.") == "Exclude"
    a = aid[aid.year.between(*yr)]
    pj = proj[proj.year.between(*yr)].copy()
    pj["group"] = sector3(pj.purpose_code).map(GROUPS).fillna("Other / unallocated")
    if excl_gbs:
        a, pj = a[a.group != "General budget support"], pj[pj.group != "General budget support"]
    secs = st.sidebar.multiselect("Sectors", sorted(a.group.unique()), placeholder="All sectors")
    if secs:
        a, pj = a[a.group.isin(secs)], pj[pj.group.isin(secs)]
    dons = st.sidebar.multiselect("Donors", sorted(a.donor.unique()), placeholder="All donors")
    if dons:
        a, pj = a[a.donor.isin(dons)], pj[pj.donor.isin(dons)]
    if a.empty:
        st.warning("No aid matches these filters.")
        st.stop()
    Y = list(range(y0, y1 + 1))
    tot = a.groupby("year").usd_m.sum().reindex(Y).fillna(0)
    top = a[a.year == y1].groupby("donor").usd_m.sum().sort_values(ascending=False)
    scope = ("all donors" if not dons else f"{len(dons)} donor(s)") + " · " + \
            ("all sectors" if not secs else f"{len(secs)} sector(s)")

    c = st.columns(4)
    kpi(c[0], f"Total aid {y1}", usd_m(tot.iloc[-1]), scope)
    kpi(c[1], f"Change since {y0}", f"{(tot.iloc[-1] / tot.iloc[0] - 1) * 100:+.1f}%" if tot.iloc[0] else "n/a",
        f"from {usd_m(tot.iloc[0])}", GOOD)
    kpi(c[2], f"Largest donor {y1}", top.index[0] if len(top) else "–",
        f"{top.iloc[0] / top.sum() * 100:.1f}% of filtered aid" if len(top) else "", COL["Aid"])
    kpi(c[3], f"Donors giving aid {y1}", f"{(top > 0).sum()}", "with any disbursement", "#8C6BB1")
    st.write("")

    c1, c2 = grid()
    with c1:
        chart(vbar(Y, tot.values, "#2F6EBA", [f"{v/1000:,.2f}bn" if v >= 1000 else f"{v:,.0f}m" for v in tot.values],
                   "US$ million", hover="%{x}: US$ %{y:,.0f}m"),
              "1 · Total aid per year", f"US$ million, constant 2024 prices · {scope}", h=380, legend=False)
    with c2:
        yoy = (tot / tot.shift(1) - 1).dropna() * 100
        chart(pm_bars(list(yoy.index), list(yoy.values), "%", horizontal=False),
              "2 · Year-on-year change", "% change in total aid from the year before", h=380, legend=False)
    c1, c2 = grid()
    with c1:
        d = a.groupby("donor").usd_m.sum().sort_values(ascending=False)
        d10 = d.head(10)
        chart(hb(d10.index, d10.values, [f"{v / d.sum() * 100:.1f}%" for v in d10.values], "#2F6EBA",
                 hover="%{y}: US$ %{x:,.0f}m"),
              f"3 · Top 10 donors, {y0}–{y1}", "Labels: share of all aid in the period", h=420, legend=False)
    with c2:
        s_ = a.groupby("group").usd_m.sum().sort_values(ascending=False).head(10)
        chart(hb(s_.index, s_.values, [f"{v / a.usd_m.sum() * 100:.1f}%" for v in s_.values], "#2E9E6B",
                 hover="%{y}: US$ %{x:,.0f}m"),
              f"4 · Top 10 sectors, {y0}–{y1}", "Labels: share of all aid in the period", h=420, legend=False)
    c1, c2 = grid()
    with c1:
        pick = dons or list(a.groupby("donor").usd_m.sum().nlargest(5).index)
        dt = a[a.donor.isin(pick)].groupby(["year", "donor"]).usd_m.sum().reset_index()
        chart(line(dt, "year", "usd_m", "donor", "US$ million", fmt=",.0f"),
              "5 · How the main donors changed", "US$ million per year · top 5 or the donors you choose", h=400)
    with c2:
        bm = pj.assign(t=pj.bilateral_multilateral.str.startswith("Bilateral").map(
            {True: "Bilateral (single country)", False: "Multilateral (World Bank, ADB, UN…)"}))
        bm = bm.groupby("t").disbursement_usd_m_2024prices.sum()
        chart(donut(bm.index, bm.values, ["#2F6EBA", "#E07B39"], "Who<br>gives"),
              "6 · Countries vs international organisations", f"Share of aid, {y0}–{y1}", h=400)
    c1, c2 = grid()
    with c1:
        gl = pj[pj.flow.isin(["ODA grant", "ODA loan"])].groupby(["year", "flow"]) \
               .disbursement_usd_m_2024prices.sum().reset_index()
        chart(stack(gl, "year", "disbursement_usd_m_2024prices", "flow",
                    {"ODA grant": GOOD, "ODA loan": BAD}),
              "7 · Grants vs loans", "US$ million · loans must be repaid, grants do not", h=400)
    with c2:
        ch = pj.assign(c=(pj.channel_code // 10000).map(CHANNEL_GROUP).fillna("Not reported")) \
               .groupby("c").disbursement_usd_m_2024prices.sum().sort_values(ascending=False)
        chart(hb(ch.index, ch.values, [f"{v / ch.sum() * 100:.1f}%" for v in ch.values], "#3FA7C6",
                 hover="%{y}: US$ %{x:,.0f}m"),
              "8 · Who delivers the aid", f"Channel of delivery, {y0}–{y1}", h=400, legend=False)
    c1, c2 = grid()
    with c1:
        ln = pj[pj.flow.isin(["ODA grant", "ODA loan"])]
        t8 = ln.groupby("donor").disbursement_usd_m_2024prices.sum().nlargest(8).index
        lsh = (ln[ln.donor.isin(t8) & (ln.flow == "ODA loan")].groupby("donor").disbursement_usd_m_2024prices.sum()
               / ln[ln.donor.isin(t8)].groupby("donor").disbursement_usd_m_2024prices.sum() * 100) \
            .reindex(t8).fillna(0).sort_values(ascending=False)
        chart(hb(lsh.index, lsh.values, [f"{v:.0f}%" for v in lsh.values], BAD, "% of donor's aid given as loans",
                 "%{y}: %{x:.0f}% loans"),
              "9 · Which donors lend and which give", f"Share of each top donor's aid given as loans, {y0}–{y1}",
              h=420, legend=False, source="0% = all grants. Loans must be repaid.")
    with c2:
        sh3 = a.groupby(["year", "donor"]).usd_m.sum().groupby(level=0) \
               .apply(lambda s: s.nlargest(3).sum() / s.sum() * 100).reindex(Y)
        chart(line(pd.DataFrame({"year": Y, "share": sh3.values}), "year", "share", None, "%", "%",
                   ["#8C6BB1"]),
              "10 · How concentrated is aid?", "Share of each year's aid from the 3 largest donors", h=420,
              legend=False, source="Higher = Pakistan depends on fewer donors.")

# ==========================================================================
# 2025 AID CUTS
# ==========================================================================
elif page == "2025 aid cuts":
    hero("The 2025 aid cuts",
         "OECD preliminary data show the largest one-year fall in aid on record. What could it mean for Pakistan?",
         ["OECD DAC1 preliminary 2025", "Scenario estimate"])
    scope_ = st.sidebar.selectbox("Aid to Pakistan", ["All sectors", "Education", "Health"])
    base_ = aid if scope_ == "All sectors" else (
        aid[aid.group == "Education"] if scope_ == "Education"
        else aid[aid.group.isin(["Health", "Population & reproductive health"])])
    sc = cut_scenario(base_)
    known, unknown = sc[sc.status == "2025 data available"], sc[sc.status != "2025 data available"]
    dac_row = dac1.set_index("donor_code").loc["DAC"]
    donors_ = dac1[~dac1.donor_code.isin(["DAC"]) & dac1.change_2024_2025_pct.notna()]

    c = st.columns(4)
    kpi(c[0], "DAC donors' total aid, 2025", f"{dac_row.change_2024_2025_pct:+.1f}%", "vs 2024", BAD)
    kpi(c[1], "United States, 2025", f"{CHG.get('United States'):+.1f}%", "largest single cut", BAD)
    kpi(c[2], f"Pakistan: estimated loss · {scope_.lower()}", usd_m(known.loss.sum()),
        f"{known.loss.sum() / sc.aid_2024.sum() * 100:.1f}% of {AID_YEAR} aid", COL["Aid"])
    kpi(c[3], "Aid from donors with no 2025 data", pct(unknown.aid_2024.sum() / sc.aid_2024.sum() * 100),
        "World Bank, ADB, Saudi Arabia, others", "#8C99A6")
    st.write("")
    SRC1 = "Source: OECD DAC1, ODA grant equivalent, constant prices, 2025 preliminary (all recipients)."
    SRC2 = ("Estimate = donor's 2024 aid to Pakistan × (1 + donor's overall 2024→2025 change). "
            "Donors without 2025 data are assumed unchanged.")

    c1, c2 = grid()
    with c1:
        v = [dac_row.oda_2023 / 1000, dac_row.oda_2024 / 1000, dac_row.oda_2025_prelim / 1000]
        chart(vbar(["2023", "2024", "2025*"], v, ["#2F6EBA", "#2F6EBA", BAD], [f"${x:,.0f}bn" for x in v],
                   "US$ billion", hover="%{x}: US$ %{y:,.1f}bn"),
              "1 · Total aid from DAC donors", "US$ billion, all recipients · * preliminary", h=360,
              legend=False, source=SRC1)
    with c2:
        n_cut = (donors_.change_2024_2025_pct < 0).sum()
        chart(donut(["Cut aid", "Raised aid"], [n_cut, len(donors_) - n_cut], [BAD, GOOD],
                    f"{len(donors_)}<br>donors", "donors"),
              "2 · How many donors cut aid in 2025?", "Number of donors with 2025 data", h=360, source=SRC1)
    c1, c2 = grid()
    with c1:
        dd = donors_.sort_values("oda_2024", ascending=False).head(12).sort_values("change_2024_2025_pct")
        chart(pm_bars(list(dd.donor)[::-1], list(dd.change_2024_2025_pct)[::-1]),
              "3 · Change in aid by the largest donors", "2024 → 2025, all recipients (12 largest donors)",
              h=440, legend=False, source=SRC1)
    with c2:
        us_ = base_[(base_.year == AID_YEAR) & (base_.donor == "United States")].groupby("group").usd_m.sum() \
            .sort_values(ascending=False).head(8)
        chart(hb(us_.index, us_.values, [f"US$ {v:,.1f}m" for v in us_.values], BAD, hover="%{y}: US$ %{x:,.1f}m"),
              "4 · What US aid to Pakistan pays for", f"US aid by sector, {AID_YEAR} · the donor with the deepest cut",
              h=440, legend=False, source="Source: OECD CRS.")
    c1, c2 = grid()
    with c1:
        hist = base_.groupby("year").usd_m.sum().reindex(YEARS).fillna(0)
        xs = [str(y) for y in YEARS] + ["2025 est."]
        ys = list(hist.values) + [sc.aid_2025_est.sum()]
        chart(vbar(xs, ys, ["#2F6EBA"] * len(YEARS) + [COL["Aid"]],
                   [f"{v/1000:,.1f}bn" if v >= 1000 else f"{v:,.0f}m" for v in ys], "US$ million",
                   hover="%{x}: US$ %{y:,.0f}m"),
              f"5 · Pakistan's {scope_.lower()} aid, with the 2025 estimate", "US$ million, constant 2024 prices",
              h=360, legend=False, source=SRC2)
    with c2:
        ls = known[known.loss > 0].sort_values("loss", ascending=False).head(10)
        chart(hb(ls.donor, ls.loss, [f"US$ {x:,.1f}m" for x in ls.loss], BAD, hover="%{y}: US$ %{x:,.1f}m"),
              "6 · Where Pakistan's estimated loss comes from", "Estimated loss by donor, US$ million", h=360,
              legend=False, source=SRC2)
    c1, c2 = grid()
    with c1:
        st_ = sc.groupby("status").aid_2024.sum()
        chart(donut(st_.index, st_.values, ["#2F6EBA", "#C9D1DB"], f"{AID_YEAR}<br>aid"),
              "7 · How much of Pakistan's aid is covered?", f"Share of {AID_YEAR} aid from donors with/without 2025 data",
              h=380, source="Multilateral banks (World Bank, ADB) and Saudi Arabia have not reported 2025 yet.")
    with c2:
        ds = base_[base_.year == AID_YEAR].copy()
        ds["loss"] = ds.usd_m * (-ds.donor.map(CHG).fillna(0) / 100)
        lsec = ds.groupby("group").loss.sum().sort_values(ascending=False).head(8)
        lsec = lsec[lsec > 0]
        chart(hb(lsec.index, lsec.values, [f"US$ {x:,.1f}m" for x in lsec.values], COL["Aid"],
                 hover="%{y}: US$ %{x:,.1f}m"),
              "8 · Which sectors are most exposed", "Estimated loss by sector, US$ million", h=380, legend=False,
              source=SRC2)
    c1, c2 = grid()
    with c1:
        us = base_.groupby("year").apply(lambda f: f[f.donor == "United States"].usd_m.sum() / f.usd_m.sum() * 100)
        chart(line(pd.DataFrame({"year": us.index, "share": us.values}), "year", "share", None, "%", "%", [BAD]),
              "9 · Pakistan's reliance on US aid", f"US share of Pakistan's {scope_.lower()} aid", h=360,
              legend=False, source="Source: OECD CRS.")
    with c2:
        G7 = ["United States", "Japan", "Germany", "United Kingdom", "France", "Italy", "Canada"]
        dd_ = dac1[dac1.oda_2025_prelim.notna() & (dac1.donor_code != "DAC")]
        dacm = dac1[dac1.donor_code != "DAC"].donor_code.isin(["AUS", "AUT", "BEL", "CAN", "CZE", "DNK", "EST", "FIN",
               "FRA", "DEU", "GRC", "HUN", "ISL", "IRL", "ISR", "ITA", "JPN", "KOR", "LVA", "LTU", "LUX", "NLD", "NZL",
               "NOR", "POL", "PRT", "SVK", "SVN", "ESP", "SWE", "CHE", "GBR", "USA"])
        dd_ = dd_.assign(grp=[("G7 countries" if d in G7 else "Other DAC members") if m else
                              ("EU Institutions" if d == "EU Institutions" else "Non-DAC donors")
                              for d, m in zip(dd_.donor, dacm.reindex(dd_.index).fillna(False))])
        gg_ = dd_.groupby("grp")[["oda_2024", "oda_2025_prelim"]].sum()
        gch = (gg_.oda_2025_prelim / gg_.oda_2024 - 1) * 100
        gch = gch.reindex(["G7 countries", "Other DAC members", "EU Institutions", "Non-DAC donors"]).dropna()
        chart(pm_bars(list(gch.index), list(gch.values), horizontal=False),
              "10 · Which donor groups cut most", "Change in total aid 2024 → 2025, all recipients", h=360,
              legend=False, source=SRC1 + " Non-DAC = donors reporting 2025 only (Saudi Arabia not yet reported).")

    with st.container(border=True):
        st.markdown("<p class='ct'>All donors to Pakistan: exposure to the 2025 cuts</p>"
                    f"<p class='cs'>{scope_} · US$ million</p>", unsafe_allow_html=True)
        t_ = sc[sc.aid_2024 >= 0.5].copy()
        t_["change_pct"] = t_.change_pct.map(lambda v: f"{v:+.1f}%" if pd.notna(v) else "–")
        t_ = t_.rename(columns={"donor": "Donor", "aid_2024": f"Aid to Pakistan {AID_YEAR}",
                                "change_pct": "Donor's 2025 change", "aid_2025_est": "2025 estimate",
                                "loss": "Estimated loss", "status": "Status"})
        st.dataframe(t_[["Donor", f"Aid to Pakistan {AID_YEAR}", "Donor's 2025 change", "2025 estimate",
                         "Estimated loss", "Status"]], hide_index=True, width="stretch", height=380,
                     column_config={f"Aid to Pakistan {AID_YEAR}": st.column_config.NumberColumn(format="%,.1f"),
                                    "2025 estimate": st.column_config.NumberColumn(format="%,.1f"),
                                    "Estimated loss": st.column_config.NumberColumn(format="%,.1f")})
        st.markdown("<div class='src'>A scenario, not a forecast: donors may protect or cut Pakistan more than "
                    "their average.</div>", unsafe_allow_html=True)

# ==========================================================================
# EDUCATION AID
# ==========================================================================
elif page == "Education aid":
    hero("Education aid in depth",
         "Which levels and activities education aid supports, who gives it and how it is delivered.",
         ["OECD CRS", "Imputed student costs excluded by default"])
    ey0 = st.sidebar.selectbox("From year", YEARS[:-1], index=0, key="ey0")
    ey1 = st.sidebar.selectbox("To year", [y for y in YEARS if y > ey0], key="ey1",
                               index=len([y for y in YEARS if y > ey0]) - 1)
    EY = list(range(ey0, ey1 + 1))
    excl = st.sidebar.selectbox("Imputed student costs", ["Exclude (World Bank)", "Include"],
                                help="Costs of Pakistani students at donor-country universities that some donors "
                                     "count as aid.").startswith("Exclude")
    dist = st.sidebar.selectbox("System-wide education aid", ["Show separately", "Distribute (UNESCO)"],
                                help="UNESCO's GEM Report assigns 50% of aid with no specific level to basic, "
                                     "25% to secondary and 25% to post-secondary.").startswith("Distribute")
    ea = aid[aid.group == "Education"].copy()
    ea["level"] = ea.sector_code.map(LEVEL)
    lv = ea.groupby(["year", "level"]).usd_m.sum().unstack().reindex(YEARS).fillna(0)
    if excl:
        lv["Post-secondary"] -= e02
    if dist:
        sw = lv.pop("System-wide (not level-specific)")
        for k, wgt in UNESCO_SPLIT.items():
            lv[k] += sw * wgt
    lv = lv.loc[EY]
    edu_tot = lv.sum(axis=1)
    order = [x for x in LVL_ORDER if x in lv.columns]
    pe = proj[(proj.purpose_code // 1000 == 11) & proj.year.isin(EY)]

    c = st.columns(4)
    kpi(c[0], f"Education aid {ey1}", usd_m(edu_tot[ey1]), "constant 2024 US$")
    kpi(c[1], f"Change since {ey0}", f"{(edu_tot[ey1] / edu_tot[ey0] - 1) * 100:+.1f}%",
        f"from {usd_m(edu_tot[ey0])}", BAD)
    kpi(c[2], f"Share of sector aid {ey1}", pct(edu_aid_by_year(excl)[ey1] / alloc[ey1] * 100),
        "education / all sector-allocable aid", GOOD)
    kpi(c[3], f"Basic education share {ey1}", pct(lv.loc[ey1, "Basic (primary)"] / edu_tot[ey1] * 100),
        "of education aid", "#2F6EBA")
    st.write("")
    lvl_src = ("System-wide = policy & administration, facilities, teacher training and research for all levels."
               + (" Distributed 50/25/25 (UNESCO GEM method)." if dist else ""))

    c1, c2 = grid()
    with c1:
        long = lv.reset_index().melt(id_vars="year", var_name="level", value_name="usd_m")
        fig = stack(long, "year", "usd_m", "level", LVL_COL, order)
        total_labels(fig, edu_tot, lambda v: f"{v:,.0f}")
        chart(fig, "1 · Education aid by level", "US$ million, constant 2024 prices", h=420, source=lvl_src)
    with c2:
        ch_ = [(lv.loc[ey1, k] / lv.loc[ey0, k] - 1) * 100 if lv.loc[ey0, k] else 0 for k in order]
        chart(pm_bars(order, ch_), f"2 · Which levels gained or lost", f"% change in aid, {ey0} → {ey1}",
              h=420, legend=False, source=lvl_src)
    c1, c2 = grid()
    with c1:
        MOD = {"A02": "Budget support", "B": "Pooled funds & core support", "C01": "Projects",
               "D": "Technical assistance", "E01": "Scholarships", "E02": "Imputed student costs"}
        me = mod[(mod.sector_code == 110) & mod.modality_code.isin(MOD) & mod.year.isin(EY)]
        if excl:
            me = me[me.modality_code != "E02"]
        me = me.groupby("modality_code").usd_million_2024prices.sum().rename(MOD).sort_values(ascending=False)
        chart(hb(me.index, me.values, [f"{v / me.sum() * 100:.1f}%" for v in me.values], "#3FA7C6",
                 hover="%{y}: US$ %{x:,.0f}m"),
              "3 · How education aid is delivered", f"{ey0}–{ey1} total · labels: share", h=380, legend=False,
              source="Comparable to Figure 8 of the World Bank's Education Finance Watch.")
    with c2:
        comp = pd.DataFrame({
            "Education": edu_aid_by_year(excl), "Health & population": health_aid_by_year(),
            "Energy": aid[aid.group == "Energy"].groupby("year").usd_m.sum().reindex(YEARS).fillna(0),
        }).div(alloc, axis=0).loc[EY] * 100
        cl = comp.reset_index().melt(id_vars="year", var_name="sector", value_name="share")
        chart(line(cl, "year", "share", "sector", "", "%", ["#2F6EBA", "#C2417A", "#D4A72C"]),
              "4 · Education vs health vs energy", "% of sector-allocable aid", h=380,
              source="Comparable to Figure 7 of the World Bank's Education Finance Watch.")
    c1, c2 = grid()
    with c1:
        dd = ea[ea.year == ey1].groupby("donor").usd_m.sum().sort_values(ascending=False)
        d8 = dd.head(8)
        chart(hb(d8.index, d8.values, [f"{v / dd.sum() * 100:.1f}%" for v in d8.values], "#2F6EBA",
                 hover="%{y}: US$ %{x:,.1f}m"),
              f"5 · Top donors to education, {ey1}", "Labels: share · includes imputed student costs", h=380,
              legend=False, source=f"Imputed student costs were US$ {e02[ey1]:,.0f}m in {ey1}, not split by donor.")
    with c2:
        gl = pe[pe.flow.isin(["ODA grant", "ODA loan"])].groupby(["year", "flow"]) \
               .disbursement_usd_m_2024prices.sum().reset_index()
        chart(stack(gl, "year", "disbursement_usd_m_2024prices", "flow", {"ODA grant": GOOD, "ODA loan": BAD}),
              "6 · Grants vs loans", "US$ million · loans must be repaid", h=380)
    c1, c2 = grid()
    with c1:
        pu = pe.groupby("purpose").disbursement_usd_m_2024prices.sum().sort_values(ascending=False).head(10)
        chart(hb(pu.index, pu.values, [f"{v / pe.disbursement_usd_m_2024prices.sum() * 100:.1f}%" for v in pu.values],
                 "#8C6BB1", hover="%{y}: US$ %{x:,.0f}m"),
              "7 · What education aid pays for", f"Top 10 activities, {ey0}–{ey1} · labels: share", h=440,
              legend=False, source="Includes imputed student costs (inside 'Higher education').")
    with c2:
        bm = pe.assign(t=pe.bilateral_multilateral.str.startswith("Bilateral").map(
            {True: "Bilateral (single country)", False: "Multilateral (World Bank, ADB, UN…)"}))
        bm = bm.groupby("t").disbursement_usd_m_2024prices.sum()
        chart(donut(bm.index, bm.values, ["#2F6EBA", "#E07B39"], "Who<br>gives"),
              "8 · Countries vs international organisations", f"Share of education aid, {ey0}–{ey1}", h=440)
    c1, c2 = grid()
    with c1:
        ch = pe.assign(c=(pe.channel_code // 10000).map(CHANNEL_GROUP).fillna("Not reported")) \
               .groupby("c").disbursement_usd_m_2024prices.sum().sort_values(ascending=False)
        chart(hb(ch.index, ch.values, [f"{v / ch.sum() * 100:.1f}%" for v in ch.values], "#3FA7C6",
                 hover="%{y}: US$ %{x:,.0f}m"),
              "9 · Who delivers education aid", f"Channel, {ey0}–{ey1}", h=380, legend=False)
    with c2:
        na = pe[pe.disbursement_usd_m_2024prices > 0].groupby("year").size().reindex(EY).fillna(0)
        chart(line(pd.DataFrame({"year": EY, "n": na.values}), "year", "n", None, "activities", "", ["#2F6EBA"],
                   ",.0f"),
              "10 · Number of education aid activities", "Activities with money paid out each year", h=380,
              legend=False, source="One donor activity = one line in the OECD project data.")

# ==========================================================================
# HEALTH AID
# ==========================================================================
elif page == "Health aid":
    hero("Health aid in depth",
         "What health aid pays for, who gives it and on what terms.",
         ["OECD CRS", "Health incl. population & reproductive health"])
    hy0 = st.sidebar.selectbox("From year", YEARS[:-1], index=0, key="hy0")
    hy1 = st.sidebar.selectbox("To year", [y for y in YEARS if y > hy0], key="hy1",
                               index=len([y for y in YEARS if y > hy0]) - 1)
    HY = list(range(hy0, hy1 + 1))
    HAREA = {12250: "Infectious diseases & vaccines", 12262: "Infectious diseases & vaccines",
             12263: "Infectious diseases & vaccines", 13040: "Infectious diseases & vaccines",
             12264: "COVID-19", 12220: "Primary care & facilities", 12230: "Primary care & facilities",
             12191: "Primary care & facilities", 12240: "Nutrition",
             13010: "Reproductive health & family planning", 13020: "Reproductive health & family planning",
             13030: "Reproductive health & family planning", 13081: "Reproductive health & family planning",
             12110: "Health policy & workforce", 12181: "Health policy & workforce",
             12182: "Health policy & workforce", 12261: "Health policy & workforce", 12281: "Health policy & workforce"}
    HORDER = ["Primary care & facilities", "Infectious diseases & vaccines", "COVID-19",
              "Reproductive health & family planning", "Nutrition", "Health policy & workforce", "NCDs & mental health"]
    HCOL = dict(zip(HORDER, ["#2F6EBA", "#C2417A", "#D4A72C", "#8C6BB1", "#2E9E6B", "#3FA7C6", "#9C6B4E"]))
    hp = proj[proj.purpose_code.between(12000, 13999) & proj.year.isin(HY)].copy()
    hp["area"] = hp.purpose_code.map(HAREA).fillna("NCDs & mental health")
    hp = hp.rename(columns={"disbursement_usd_m_2024prices": "usd_m"})
    ht = hp.groupby("year").usd_m.sum().reindex(HY).fillna(0)
    ha = hp[hp.year == hy1].groupby("area").usd_m.sum().sort_values(ascending=False)

    c = st.columns(4)
    kpi(c[0], f"Health aid {hy1}", usd_m(ht[hy1]), "constant 2024 US$", BAD)
    kpi(c[1], f"Change since {hy0}", f"{(ht[hy1] / ht[hy0] - 1) * 100:+.1f}%" if ht[hy0] else "n/a",
        f"from {usd_m(ht[hy0])}", GOOD)
    kpi(c[2], f"Share of sector aid {hy1}", pct(health_aid_by_year()[hy1] / alloc[hy1] * 100),
        "health / all sector-allocable aid", "#2F6EBA")
    kpi(c[3], f"Largest area {hy1}", ha.index[0], f"{ha.iloc[0] / ha.sum() * 100:.1f}% of health aid", "#D4A72C")
    st.write("")

    c1, c2 = grid()
    with c1:
        ar = hp.groupby(["year", "area"]).usd_m.sum().reset_index()
        fig = stack(ar, "year", "usd_m", "area", HCOL, HORDER)
        total_labels(fig, ht, lambda v: f"{v:,.0f}")
        chart(fig, "1 · Health aid by area", "US$ million, constant 2024 prices", h=440,
              source="Infectious diseases & vaccines = immunisation, TB, malaria, HIV and other disease control.")
    with c2:
        a0 = hp[hp.year == hy0].groupby("area").usd_m.sum()
        a1 = hp[hp.year == hy1].groupby("area").usd_m.sum()
        ar2 = [a for a in HORDER if a0.get(a, 0) > 1]
        chart(pm_bars(ar2, [(a1.get(a, 0) / a0[a] - 1) * 100 for a in ar2]),
              "2 · Which areas gained or lost", f"% change in aid, {hy0} → {hy1}", h=440, legend=False,
              source="Areas with less than US$1m in the start year are left out.")
    c1, c2 = grid()
    with c1:
        pu = hp.groupby("purpose").usd_m.sum().sort_values(ascending=False).head(10)
        chart(hb(pu.index, pu.values, [f"{v / hp.usd_m.sum() * 100:.1f}%" for v in pu.values], "#8C6BB1",
                 hover="%{y}: US$ %{x:,.0f}m"),
              "3 · What health aid pays for", f"Top 10 activities, {hy0}–{hy1} · labels: share", h=440, legend=False)
    with c2:
        dd = hp[hp.year == hy1].groupby("donor").usd_m.sum().sort_values(ascending=False)
        d8 = dd.head(8)
        chart(hb(d8.index, d8.values, [f"{v / dd.sum() * 100:.1f}%" for v in d8.values], BAD,
                 hover="%{y}: US$ %{x:,.1f}m"),
              f"4 · Top donors to health, {hy1}", "Labels: share of health aid", h=440, legend=False)
    c1, c2 = grid()
    with c1:
        gl = hp[hp.flow.isin(["ODA grant", "ODA loan"])].groupby(["year", "flow"]).usd_m.sum().reset_index()
        chart(stack(gl, "year", "usd_m", "flow", {"ODA grant": GOOD, "ODA loan": BAD}),
              "5 · Grants vs loans", "US$ million · loans must be repaid", h=380)
    with c2:
        bm = hp.assign(t=hp.bilateral_multilateral.str.startswith("Bilateral").map(
            {True: "Bilateral (single country)", False: "Multilateral (Gavi, Global Fund, World Bank…)"}))
        bm = bm.groupby("t").usd_m.sum()
        chart(donut(bm.index, bm.values, ["#2F6EBA", "#E07B39"], "Who<br>gives"),
              "6 · Countries vs international organisations", f"Share of health aid, {hy0}–{hy1}", h=380)
    c1, c2 = grid()
    with c1:
        ch = hp.assign(c=(hp.channel_code // 10000).map(CHANNEL_GROUP).fillna("Not reported")) \
               .groupby("c").usd_m.sum().sort_values(ascending=False)
        chart(hb(ch.index, ch.values, [f"{v / ch.sum() * 100:.1f}%" for v in ch.values], "#3FA7C6",
                 hover="%{y}: US$ %{x:,.0f}m"),
              "7 · Who delivers health aid", f"Channel, {hy0}–{hy1}", h=380, legend=False)
    with c2:
        t4 = hp.groupby("donor").usd_m.sum().nlargest(4).index
        dt = hp[hp.donor.isin(t4)].groupby(["year", "donor"]).usd_m.sum().reset_index()
        chart(line(dt, "year", "usd_m", "donor", "US$ million", fmt=",.0f"),
              "8 · The 4 largest health donors over time", "US$ million per year", h=380)
    c1, c2 = grid()
    with c1:
        hs = (health_aid_by_year() / alloc * 100).loc[HY]
        chart(line(pd.DataFrame({"year": HY, "s": hs.values}), "year", "s", None, "%", "%", [BAD]),
              "9 · Health's share of sector aid", "% of all sector-allocable aid", h=360, legend=False)
    with c2:
        na = hp[hp.usd_m > 0].groupby("year").size().reindex(HY).fillna(0)
        chart(line(pd.DataFrame({"year": HY, "n": na.values}), "year", "n", None, "activities", "", ["#2F6EBA"],
                   ",.0f"),
              "10 · Number of health aid activities", "Activities with money paid out each year", h=360,
              legend=False)

# ==========================================================================
# PIPELINE & PRIORITIES
# ==========================================================================
elif page == "Pipeline & priorities":
    hero("Aid pipeline and priorities",
         "Promised vs paid aid, and how much aid targets gender equality and climate change.",
         ["OECD CRS", "Commitments & disbursements", "Policy markers"])
    scope = st.sidebar.selectbox("Aid to Pakistan", ["All sectors", "Education", "Health"], key="pp_scope")
    py0 = st.sidebar.selectbox("From year", YEARS[:-1], index=0, key="py0")
    py1 = st.sidebar.selectbox("To year", [y for y in YEARS if y > py0], key="py1",
                               index=len([y for y in YEARS if y > py0]) - 1)
    PY = list(range(py0, py1 + 1))
    pp = proj[proj.year.isin(PY)].copy()
    if scope == "Education":
        pp = pp[pp.purpose_code // 1000 == 11]
    elif scope == "Health":
        pp = pp[pp.purpose_code.between(12000, 13999)]
    pp["group"] = sector3(pp.purpose_code).map(GROUPS).fillna("Other / unallocated")
    if scope != "All sectors":
        pp["group"] = pp.purpose
    D, C = "disbursement_usd_m_2024prices", "commitment_usd_m_2024prices"
    TGT = ["Principal objective", "Significant objective"]

    def mshare(col, f):
        f = f[f[col] != "Not screened"]
        return f[f[col].isin(TGT)][D].sum() / f[D].sum() * 100 if f[D].sum() else float("nan")

    cd = pp.groupby("year")[[C, D]].sum().reindex(PY).fillna(0)
    last = pp[pp.year == py1]
    c = st.columns(4)
    kpi(c[0], f"Promised {py1}", usd_m(cd.loc[py1, C]), "commitments", "#2F6EBA")
    kpi(c[1], f"Paid {py1}", usd_m(cd.loc[py1, D]),
        f"{cd.loc[py1, D] / cd.loc[py1, C] * 100:.0f}% of promised" if cd.loc[py1, C] else "", GOOD)
    kpi(c[2], f"Gender-focused aid {py1}", pct(mshare("gender_marker", last)), "of screened aid", "#8C6BB1")
    kpi(c[3], f"Climate-related aid {py1}", pct(mshare("climate_marker", last)), "of screened aid", GOOD)
    st.write("")
    lbl = "activities" if scope != "All sectors" else "sectors"

    c1, c2 = grid()
    with c1:
        lg = cd.rename(columns={C: "Promised (commitments)", D: "Paid (disbursements)"}).reset_index() \
               .melt(id_vars="year", var_name="type", value_name="usd")
        fig = px.bar(lg, x="year", y="usd", color="type", barmode="group",
                     color_discrete_map={"Promised (commitments)": "#9DB9DD", "Paid (disbursements)": "#2F6EBA"})
        fig.update_traces(marker_line_width=0, hovertemplate="<b>%{fullData.name}</b><br>%{x}: US$ %{y:,.0f}m<extra></extra>")
        fig.update_layout(bargap=0.25, xaxis_title=None, yaxis_title="US$ million", xaxis=dict(dtick=1),
                          yaxis=dict(tickformat=","))
        chart(fig, f"1 · Promised vs paid · {scope.lower()}", "US$ million, constant 2024 prices", h=400,
              source="Commitments are paid out over several years; when they run above payments, more is in the pipeline.")
    with c2:
        dc = last.groupby("donor")[C].sum().sort_values(ascending=False).head(8)
        chart(hb(dc.index, dc.values, [usd_m(v) for v in dc.values], "#9DB9DD", hover="%{y}: US$ %{x:,.0f}m"),
              f"2 · Biggest new promises, {py1}", "Commitments by donor, US$ million", h=400, legend=False)
    c1, c2 = grid()
    with c1:
        cs = last.groupby("group")[C].sum().sort_values(ascending=False).head(8)
        chart(hb(cs.index, cs.values, [usd_m(v) for v in cs.values], "#2F6EBA", hover="%{y}: US$ %{x:,.0f}m"),
              f"3 · What the new promises are for, {py1}", f"Commitments by {lbl[:-1] if lbl.endswith('s') else lbl}, "
              "US$ million", h=420, legend=False)
    with c2:
        cov = pd.DataFrame({"year": PY,
                            "Gender": [(pp[(pp.year == y) & (pp.gender_marker != "Not screened")][D].sum()
                                        / max(pp[pp.year == y][D].sum(), 1e-9)) * 100 for y in PY],
                            "Climate": [(pp[(pp.year == y) & (pp.climate_marker != "Not screened")][D].sum()
                                         / max(pp[pp.year == y][D].sum(), 1e-9)) * 100 for y in PY]}) \
                .melt(id_vars="year", var_name="marker", value_name="share")
        chart(line(cov, "year", "share", "marker", "%", "%", ["#8C6BB1", GOOD]),
              "4 · How much aid is checked for gender and climate", "% of aid that donors screened", h=420,
              source="Shares on this page use only screened aid.")
    c1, c2 = grid()
    with c1:
        gs = pd.DataFrame({"year": PY, "s": [mshare("gender_marker", pp[pp.year == y]) for y in PY]})
        chart(line(gs, "year", "s", None, "%", "%", ["#8C6BB1"]),
              "5 · Aid that targets gender equality", "% of screened aid (main or important objective)", h=380,
              legend=False, source="OECD gender equality policy marker.")
    with c2:
        cs_ = pd.DataFrame({"year": PY, "s": [mshare("climate_marker", pp[pp.year == y]) for y in PY]})
        chart(line(cs_, "year", "s", None, "%", "%", [GOOD]),
              "6 · Aid that targets climate change", "% of screened aid (mitigation or adaptation)", h=380,
              legend=False, source="OECD Rio markers; a project counts once even if it targets both.")
    c1, c2 = grid()
    with c1:
        gd = pp[pp.gender_marker == "Principal objective"].groupby("donor")[D].sum().sort_values(ascending=False).head(8)
        chart(hb(gd.index, gd.values, [usd_m(v) for v in gd.values], "#8C6BB1", hover="%{y}: US$ %{x:,.1f}m"),
              "7 · Donors putting gender first", f"Aid with gender equality as main objective, {py0}–{py1}",
              h=400, legend=False)
    with c2:
        cdn = pp[pp.climate_marker.isin(TGT)].groupby("donor")[D].sum().sort_values(ascending=False).head(8)
        chart(hb(cdn.index, cdn.values, [usd_m(v) for v in cdn.values], GOOD, hover="%{y}: US$ %{x:,.0f}m"),
              "8 · Largest climate donors", f"Climate-targeted aid, {py0}–{py1}", h=400, legend=False)
    c1, c2 = grid()
    with c1:
        ma = pd.DataFrame({
            "year": PY,
            "Mitigation (cutting emissions)": [pp[(pp.year == y) & pp.climate_mitigation_marker.isin(TGT)][D].sum() for y in PY],
            "Adaptation (coping with climate change)": [pp[(pp.year == y) & pp.climate_adaptation_marker.isin(TGT)][D].sum() for y in PY],
        }).melt(id_vars="year", var_name="type", value_name="usd")
        fig = px.bar(ma, x="year", y="usd", color="type", barmode="group",
                     color_discrete_map={"Mitigation (cutting emissions)": "#3FA7C6",
                                         "Adaptation (coping with climate change)": GOOD})
        fig.update_traces(marker_line_width=0, hovertemplate="<b>%{fullData.name}</b><br>%{x}: US$ %{y:,.0f}m<extra></extra>")
        fig.update_layout(bargap=0.25, xaxis_title=None, yaxis_title="US$ million", xaxis=dict(dtick=1),
                          yaxis=dict(tickformat=","))
        chart(fig, "9 · Climate aid: mitigation vs adaptation", "US$ million (a project can count in both)", h=400)
    with c2:
        gsec = pp[pp.gender_marker.isin(TGT)].groupby("group")[D].sum().sort_values(ascending=False).head(8)
        chart(hb(gsec.index, gsec.values, [usd_m(v) for v in gsec.values], "#B39DDB", hover="%{y}: US$ %{x:,.0f}m"),
              f"10 · Where gender-focused aid goes", f"By {lbl[:-1] if lbl.endswith('s') else lbl}, {py0}–{py1}",
              h=400, legend=False)

# ==========================================================================
# GOVERNMENT SPENDING
# ==========================================================================
elif page == "Government spending":
    hero("Government spending on education and health",
         "Federal and provincial spending, from official accounts and the Pakistan Economic Survey.",
         ["Education: PIE (FABS actuals)", "Health: Economic Survey"])
    FYS = ["2018-19", "2019-20", "2020-21", "2021-22", "2022-23", "2023-24", "2024-25", "2025-26"]
    g0 = st.sidebar.selectbox("From year", FYS[:-1], index=1, key="g0")
    opts = FYS[FYS.index(g0) + 1:]
    g1 = st.sidebar.selectbox("To year", opts, key="g1", index=opts.index("2023-24") if "2023-24" in opts else 0)
    GY = FYS[FYS.index(g0):FYS.index(g1) + 1]
    ALLG = ["Federal", "Punjab", "Sindh", "Khyber Pakhtunkhwa", "Balochistan"]
    govs = st.sidebar.multiselect("Governments", ALLG + ["Azad Jammu & Kashmir", "Gilgit Baltistan"],
                                  placeholder="Federal + 4 provinces") or ALLG
    gcol = dict(zip(["Federal", "Punjab", "Sindh", "Khyber Pakhtunkhwa", "Balochistan",
                     "Azad Jammu & Kashmir", "Gilgit Baltistan"], SERIES))
    E = pie[pie.government.isin(govs)].assign(rs_bn=lambda d: d.total_rs_m / 1000)
    H = pes[(pes.sector == "Health") & pes.government.isin(govs)].assign(rs_bn=lambda d: d.total_rs_m / 1000)
    esum = lambda fy: E[E.fiscal_year == fy].rs_bn.sum()
    hsum = lambda fy: H[H.fiscal_year == fy].rs_bn.sum()
    basis = "actual" if g1 <= "2023-24" else "budget allocation"
    note_g = "federal + 4 provinces" if govs == ALLG else ", ".join(govs)

    c = st.columns(4)
    kpi(c[0], f"Education {g1}", bn(esum(g1)) if esum(g1) else "n/a", basis, "#2F6EBA")
    kpi(c[1], f"Education change since {g0}",
        f"{(esum(g1) / esum(g0) - 1) * 100:+.1f}%" if esum(g0) and esum(g1) else "n/a",
        f"from {bn(esum(g0))}" if esum(g0) else "no data for start year", "#3FA7C6")
    kpi(c[2], f"Health {g1}", bn(hsum(g1)) if hsum(g1) else "n/a", "Economic Survey" if hsum(g1) else "not yet published", BAD)
    kpi(c[3], f"Health change since {g0}",
        f"{(hsum(g1) / hsum(g0) - 1) * 100:+.1f}%" if hsum(g0) and hsum(g1) else "n/a",
        f"from {bn(hsum(g0))}" if hsum(g0) else "no data for start year", COL["Aid"])
    st.write("")

    c1, c2 = grid()
    with c1:
        pg = E[E.fiscal_year.isin(GY)].copy()
        pg["label"] = pg.fiscal_year + pg.basis.map(lambda b: "" if b.startswith("Actual") else "*")
        fig = stack(pg, "label", "rs_bn", "government", gcol, list(gcol), "Rs billion")
        total_labels(fig, pg.groupby("label").rs_bn.sum(), lambda v: f"{v:,.0f}")
        chart(fig, "1 · Education spending by government", f"Rs billion · * budget allocation · {note_g}", h=440,
              source="Source: Pakistan Institute of Education, Public Financing in Education 2025-26.")
    with c2:
        hg = H[H.fiscal_year.isin(GY)]
        fig = stack(hg, "fiscal_year", "rs_bn", "government", gcol, list(gcol), "Rs billion")
        total_labels(fig, hg.groupby("fiscal_year").rs_bn.sum(), lambda v: f"{v:,.0f}")
        chart(fig, "2 · Health spending by government", f"Rs billion · {note_g}", h=440,
              source="Source: Pakistan Economic Survey 2024-25 and 2025-26 (federal + 4 provinces only).")
    c1, c2 = grid()
    with c1:
        ev = E[E.fiscal_year == g1].groupby("government").rs_bn.sum().reindex([g for g in gcol if g in govs]).dropna()
        chart(donut(ev.index, ev.values, [gcol[g] for g in ev.index], f"Education<br>{g1}", "Rs bn"),
              "3 · Who spends on education", f"Share of education spending, {g1}", h=400)
    with c2:
        hv = H[H.fiscal_year == g1].groupby("government").rs_bn.sum().reindex([g for g in gcol if g in govs]).dropna()
        hv = hv[hv > 0]
        if hv.empty:
            st.info(f"No health spending data for {g1} yet.")
        else:
            chart(donut(hv.index, hv.values, [gcol[g] for g in hv.index], f"Health<br>{g1}", "Rs bn"),
                  "4 · Who spends on health", f"Share of health spending, {g1}", h=400)
    c1, c2 = grid()
    with c1:
        e0 = E[E.fiscal_year == g0].groupby("government").rs_bn.sum()
        e1 = E[E.fiscal_year == g1].groupby("government").rs_bn.sum()
        gg = [g for g in gcol if g in govs and e0.get(g, 0) > 0 and e1.get(g, 0) > 0]
        chart(pm_bars(gg, [(e1[g] / e0[g] - 1) * 100 for g in gg]),
              "5 · Education: growth by government", f"% change, {g0} → {g1} (not inflation-adjusted)", h=380, legend=False)
    with c2:
        h0 = H[H.fiscal_year == g0].groupby("government").rs_bn.sum()
        h1 = H[H.fiscal_year == g1].groupby("government").rs_bn.sum()
        gh = [g for g in gcol if g in govs and h0.get(g, 0) > 0 and h1.get(g, 0) > 0]
        if gh:
            chart(pm_bars(gh, [(h1[g] / h0[g] - 1) * 100 for g in gh]),
                  "6 · Health: growth by government", f"% change, {g0} → {g1} (not inflation-adjusted)", h=380, legend=False)
        else:
            st.info("Health data not available for the selected years.")
    c1, c2 = grid()
    with c1:
        dv = pes[(pes.government == "Pakistan") & pes.fiscal_year.isin(GY) & (pes.fiscal_year != "2024-25")
                 | ((pes.government == "Pakistan") & (pes.sector == "Health") & pes.fiscal_year.isin(GY))].copy()
        dv["share"] = dv.development_rs_m / dv.total_rs_m * 100
        chart(line(dv, "fiscal_year", "share", "sector", "%", "%", ["#2F6EBA", BAD]),
              "7 · How much goes to development?", "% of spending on new buildings & projects (federal + 4 provinces)",
              h=380, source="Source: Pakistan Economic Survey. Education 2024-25 left out (provisional Punjab figure). Survey "
                     "figures for KP and Federal in 2020-21 and 2021-22 differ from PIE accounts, so treat those years with care.")
    with c2:
        ce = pes[(pes.sector == "Education") & pes.government.isin(govs) & (pes.fiscal_year <= min(g1, "2022-23"))]
        fy_ce = ce.fiscal_year.max()
        ce = ce[ce.fiscal_year == fy_ce].melt(id_vars="government", value_vars=["current_rs_m", "development_rs_m"],
                                              var_name="type", value_name="v")
        ce["type"] = ce.type.map({"current_rs_m": "Running costs (salaries etc.)", "development_rs_m": "Development (new buildings, projects)"})
        ce["v"] = ce.v / 1000
        ce["government"] = ce.government.replace({"Khyber Pakhtunkhwa": "KP"})
        fig = px.bar(ce, x="government", y="v", color="type", barmode="stack",
                     color_discrete_map={"Running costs (salaries etc.)": "#8C99A6",
                                         "Development (new buildings, projects)": "#2F6EBA"})
        fig.update_traces(marker_line_width=0, hovertemplate="<b>%{x}</b>, %{fullData.name}<br>Rs %{y:,.0f} bn<extra></extra>")
        fig.update_layout(bargap=0.35, xaxis_title=None, yaxis_title="Rs billion", yaxis=dict(tickformat=","))
        chart(fig, "8 · Education: running costs vs development", f"Rs billion, {fy_ce}", h=380,
              source="Source: Pakistan Economic Survey. Latest reliable year up to 2022-23 (later Punjab figure is provisional and inconsistent).")
    c1, c2 = grid()
    with c1:
        cht = H[H.fiscal_year == g1] if hsum(g1) else H[H.fiscal_year == H.fiscal_year.max()]
        fy_h = cht.fiscal_year.max()
        cht = cht.melt(id_vars="government", value_vars=["current_rs_m", "development_rs_m"], var_name="type", value_name="v")
        cht["type"] = cht.type.map({"current_rs_m": "Running costs (salaries etc.)", "development_rs_m": "Development (new buildings, projects)"})
        cht["v"] = cht.v / 1000
        cht["government"] = cht.government.replace({"Khyber Pakhtunkhwa": "KP"})
        fig = px.bar(cht, x="government", y="v", color="type", barmode="stack",
                     color_discrete_map={"Running costs (salaries etc.)": "#8C99A6",
                                         "Development (new buildings, projects)": BAD})
        fig.update_traces(marker_line_width=0, hovertemplate="<b>%{x}</b>, %{fullData.name}<br>Rs %{y:,.0f} bn<extra></extra>")
        fig.update_layout(bargap=0.35, xaxis_title=None, yaxis_title="Rs billion", yaxis=dict(tickformat=","))
        chart(fig, "9 · Health: running costs vs development", f"Rs billion, {fy_h}", h=380,
              source="Source: Pakistan Economic Survey.")
    with c2:
        prov = [g for g in ["Punjab", "Sindh", "Khyber Pakhtunkhwa", "Balochistan"] if g in govs]
        pp_ = [E[(E.fiscal_year == g1) & (E.government == g)].rs_bn.sum() * 1e9 / POP_2023[g] for g in prov]
        ph_ = [H[(H.fiscal_year == g1) & (H.government == g)].rs_bn.sum() * 1e9 / POP_2023[g] for g in prov]
        pc = pd.DataFrame({"province": prov * 2, "sector": ["Education"] * len(prov) + ["Health"] * len(prov),
                           "rs": pp_ + ph_})
        pc = pc[pc.rs > 0]
        fig = px.bar(pc, x="province", y="rs", color="sector", barmode="group",
                     color_discrete_map={"Education": "#2F6EBA", "Health": BAD},
                     text=pc.rs.map(lambda v: f"{v:,.0f}"))
        fig.update_traces(marker_line_width=0, textposition="outside", cliponaxis=False, textfont=dict(size=11, color=INK),
                          hovertemplate="<b>%{x}</b>, %{fullData.name}<br>Rs %{y:,.0f} per person<extra></extra>")
        fig.update_layout(bargap=0.3, xaxis_title=None, yaxis_title="Rs per person per year",
                          yaxis=dict(tickformat=",", range=[0, (pc.rs.max() if len(pc) else 1) * 1.18]))
        chart(fig, "10 · Spending per person, by province", f"Rs per person, {g1}", h=380,
              source="Provincial spending ÷ Census 2023 population (PBS). Excludes federal spending.")

# ==========================================================================
# HOUSEHOLD SPENDING
# ==========================================================================
elif page == "Household spending":
    hero("What households pay",
         "Out-of-pocket spending on education and health by income group, province and area.",
         ["HIES 2018-19 & 2024-25", "Rs per household per month"])
    item = st.sidebar.selectbox("Spending on", ["Education", "Health"])
    region = st.sidebar.selectbox("Region", ["Pakistan", "Punjab", "Sindh", "Khyber Pakhtunkhwa", "Balochistan"])
    area_t = st.sidebar.selectbox("Area", ["Total", "Urban", "Rural"])
    lvl = st.sidebar.selectbox("School level (chart 4)", ["All levels", "Primary", "Middle", "Matric"])
    BASE = {"Pakistan": "PAKISTAN", "Punjab": "PUNJAB", "Sindh": "SINDH",
            "Khyber Pakhtunkhwa": "KHYBER PAKHTUNKHWA", "Balochistan": "BALOCHISTAN"}

    def area_code(reg, t):
        b = BASE[reg]
        return b if t == "Total" else ("KP " if b == "KHYBER PAKHTUNKHWA" else b + " ") + t.upper()

    AREA = area_code(region, area_t)
    where = f"{region}{'' if area_t == 'Total' else ' ' + area_t.lower()}"
    Q = ["q1_poorest", "q2", "q3", "q4", "q5_richest"]
    QL = ["Poorest 20%", "2nd 20%", "Middle 20%", "4th 20%", "Richest 20%"]
    get = lambda a, it, y: hies[(hies.area == a) & (hies.item == it) & (hies.year == y)].iloc[0]
    CONS = "Average Monthly Consumption Expenditure"
    r25, r19 = get(AREA, item, "2024-25"), get(AREA, item, "2018-19")
    c25 = get(AREA, CONS, "2024-25")
    real = (r25.total / (r19.total * CPI_FY19_TO_FY25) - 1) * 100

    c = st.columns(4)
    kpi(c[0], f"Average per household · {where}", f"Rs {r25.total:,.0f}", "per month, 2024-25", COL["Households"])
    kpi(c[1], "Share of household budget", pct(r25.total / c25.total * 100), "of total consumption", "#2F6EBA")
    kpi(c[2], "Real change since 2018-19", f"{real:+.1f}%", f"nominal Rs {r19.total:,.0f} → Rs {r25.total:,.0f}",
        GOOD if real >= 0 else BAD)
    kpi(c[3], "Richest vs poorest 20%", f"{r25.q5_richest / r25.q1_poorest:.1f}×",
        f"Rs {r25.q5_richest:,.0f} vs Rs {r25.q1_poorest:,.0f}", COL["Aid"])
    st.write("")
    SRC = "Source: HIES Table 16 (PBS)."
    PROV = ["Pakistan", "Punjab", "Sindh", "Khyber Pakhtunkhwa", "Balochistan"]
    short = lambda p: p.replace("Khyber Pakhtunkhwa", "KP")

    c1, c2 = grid()
    with c1:
        v = [r25[q] for q in Q]
        chart(vbar(QL, v, COL["Households"], [f"Rs {x:,.0f}" for x in v], "Rs per month",
                   hover="%{x}: Rs %{y:,.0f} a month"),
              f"1 · {item} spending by income group", f"Rs per household per month, 2024-25 · {where}", h=380,
              legend=False, source=SRC)
    with c2:
        v = [r25[q] / c25[q] * 100 for q in Q]
        chart(vbar(QL, v, "#2F6EBA", [f"{x:.1f}%" for x in v], "%", "%", "%{x}: %{y:.1f}%"),
              f"2 · {item} as a share of the household budget", f"% of all household spending, 2024-25 · {where}",
              h=380, legend=False, source=SRC)
    c1, c2 = grid()
    with c1:
        types = ["Urban", "Rural"]
        pr = pd.DataFrame([{"area": short(p), "type": t, "rs": get(area_code(p, t), item, "2024-25").total}
                           for p in PROV for t in types])
        fig = px.bar(pr, x="area", y="rs", color="type", barmode="group",
                     text=pr.rs.map(lambda x: f"{x:,.0f}"), color_discrete_map={"Urban": "#2F6EBA", "Rural": GOOD})
        fig.update_traces(textposition="outside", cliponaxis=False, marker_line_width=0, textfont=dict(size=11, color=INK),
                          hovertemplate="<b>%{x}</b>, %{fullData.name}<br>Rs %{y:,.0f} a month<extra></extra>")
        fig.update_layout(bargap=0.3, xaxis_title=None, yaxis_title="Rs per month",
                          yaxis=dict(tickformat=",", range=[0, pr.rs.max() * 1.18]))
        chart(fig, f"3 · {item}: cities vs villages", "Rs per household per month, 2024-25", h=380, source=SRC)
    with c2:
        sc = school[(school.school_type != "Others") & (school.level == lvl)].melt(
            id_vars=["school_type"], value_vars=["total_pct", "urban_pct", "rural_pct"], var_name="area", value_name="pct")
        sc["area"] = sc.area.map({"urban_pct": "Urban", "rural_pct": "Rural", "total_pct": "Pakistan"})
        fig = px.bar(sc, y="area", x="pct", color="school_type", orientation="h",
                     text=sc.pct.map(lambda x: f"{x:.0f}%" if x >= 5 else ""),
                     category_orders={"area": ["Pakistan", "Urban", "Rural"],
                                      "school_type": ["Government", "Private", "Deeni madrassa", "NGO/Trust"]},
                     color_discrete_sequence=["#8C99A6", "#6A3D9A", "#D4A72C", GOOD])
        fig.update_traces(textposition="inside", insidetextanchor="middle", marker_line_width=0,
                          textfont=dict(color="white", size=12),
                          hovertemplate="<b>%{y}</b>, %{fullData.name}: %{x:.0f}%<extra></extra>")
        fig.update_layout(barmode="stack", bargap=0.35, xaxis_title=None, yaxis_title=None,
                          xaxis=dict(range=[0, 100.5], ticksuffix="%", dtick=20, showgrid=True, gridcolor=GRID))
        chart(fig, "4 · Where children go to school", f"% of children in school, {lvl}, 2024-25 (national)",
              h=380, source="Source: HIES 2024-25, Table 12. Not available by province.")
    c1, c2 = grid()
    with c1:
        v = [c25[q] for q in Q]
        chart(vbar(QL, v, "#8C99A6", [f"Rs {x/1000:,.0f}k" for x in v], "Rs per month",
                   hover="%{x}: Rs %{y:,.0f} a month"),
              "5 · Total household spending by income group", f"All items, Rs per month, 2024-25 · {where}", h=380,
              legend=False, source=SRC)
    with c2:
        v = [(r25[q] / (r19[q] * CPI_FY19_TO_FY25) - 1) * 100 for q in Q]
        chart(pm_bars(QL, v, horizontal=False),
              f"6 · {item}: real change by income group", f"2018-19 → 2024-25, after inflation · {where}", h=380,
              legend=False, source="Inflation-adjusted with cumulative CPI ×2.254 (PBS).")
    c1, c2 = grid()
    with c1:
        v = [(get(area_code(p, area_t), item, "2024-25").total /
              (get(area_code(p, area_t), item, "2018-19").total * CPI_FY19_TO_FY25) - 1) * 100 for p in PROV]
        chart(pm_bars([short(p) for p in PROV], v, horizontal=False),
              f"7 · {item}: real change by province", f"2018-19 → 2024-25, after inflation · {area_t.lower()}",
              h=380, legend=False, source="Inflation-adjusted with cumulative CPI ×2.254 (PBS).")
    with c2:
        v = [get(area_code(p, area_t), item, "2024-25").total / get(area_code(p, area_t), CONS, "2024-25").total * 100
             for p in PROV]
        chart(vbar([short(p) for p in PROV], v, "#2F6EBA", [f"{x:.1f}%" for x in v], "%", "%", "%{x}: %{y:.1f}%"),
              f"8 · {item} share of the budget, by province", f"% of household spending, 2024-25 · {area_t.lower()}",
              h=380, legend=False, source=SRC)
    c1, c2 = grid()
    with c1:
        pv = school[(school.school_type == "Private") & (school.level != "All levels")]
        chart(vbar(pv.level, pv.total_pct, "#6A3D9A", [f"{x:.0f}%" for x in pv.total_pct], "%", "%",
                   "%{x}: %{y:.0f}% in private schools"),
              "9 · Private schooling by level", "% of children in private schools, 2024-25 (national)", h=380,
              legend=False, source="Source: HIES 2024-25, Table 12.")
    with c2:
        v = []
        for p in PROV:
            r = get(area_code(p, area_t), item, "2024-25")
            v.append(r.q5_richest / r.q1_poorest)
        chart(vbar([short(p) for p in PROV], v, COL["Aid"], [f"{x:.1f}×" for x in v], "times", "",
                   "%{x}: richest spend %{y:.1f}× the poorest"),
              f"10 · Rich–poor gap in {item.lower()} spending", f"Richest 20% ÷ poorest 20%, 2024-25 · {area_t.lower()}",
              h=380, legend=False, source=SRC)

# ==========================================================================
# METHODOLOGY
# ==========================================================================
else:
    hero("Methodology", "Data sources, choices and known limitations.", ["Follows the World Bank's Education Finance Watch"])
    with st.container(border=True):
        st.markdown(f"""
#### Data sources
| Topic | Source | Years |
|---|---|---|
| International aid | OECD Creditor Reporting System (CRS), October 2026 release | 2015–2024 |
| Government education spending | Pakistan Institute of Education, *Public Financing in Education 2025-26* (FABS actuals; budget allocations for 2024-25 and 2025-26) | 2019-20 to 2025-26 |
| Government health spending | Pakistan Economic Survey 2024-25 (Table 11.4) and 2025-26 (Table 11.5) | 2018-19 to 2024-25 |
| Household spending | HIES 2018-19 and 2024-25, Table 16 (PBS) | 2018-19, 2024-25 |
| School type | HIES 2024-25, Table 12 (PBS) | 2024-25 |
| Number of households | Census 2023 (PBS): {HOUSEHOLDS:,}; Census 2017: 32,205,111 | 2017, 2023 |
| Population (per-person figures) | Census 2023 (PBS): Pakistan 241.5m; Punjab 127.7m; Sindh 55.7m; KP 40.9m; Balochistan 14.9m | 2023 |
| 2025 aid by donor | OECD DAC1, preliminary 2025 (ODA grant equivalent, constant prices) | 2023–2025 |
""")
    with st.container(border=True):
        st.markdown(f"""
#### Choices made
1. **Aid** = official development assistance (ODA), gross **disbursements** (money actually paid), **constant 2024 US$**, all official donors.
2. **Imputed student costs** (costs of Pakistani students at donor-country universities) are **excluded** from education aid by default, as in the World Bank report. A toggle shows them.
3. **System-wide education aid** (OECD "education, level unspecified": policy and administration, facilities, teacher training, research) is shown as its own category. A toggle distributes it **50% basic, 25% secondary, 25% post-secondary**, the method used by UNESCO's GEM Report.
4. **Health aid** includes population & reproductive health.
5. **General budget support** (mainly Saudi Arabia, 2023-24) is not tied to any sector, so it is not counted in education or health aid. It can be hidden on the Aid overview page.
6. **Double counting:** aid given as budget support is already part of government spending. Education received **no** budget support in 2023 or 2024, so the latest year is not double counted.
7. **Years:** OECD uses calendar years; government and HIES use fiscal years (July–June). Calendar year {AID_YEAR} is matched with fiscal year 2024-25.
8. **Currency:** aid converted at Rs {PKR_PER_USD} per US$ (end-2024 interbank rate).
9. **Household totals** = HIES average monthly spending per household × 12 × households (Census 2023).
10. **2018-19 comparison:** households × Census 2017 households (32,205,111); government from Pakistan Economic Survey 2024-25; aid in current US$ converted at Rs 139.86/US$ (end-2018).
11. **Health aid areas** group OECD purpose codes (e.g. infectious diseases = TB, malaria, HIV/STD and other disease control). **Pipeline** compares commitments (promises) with disbursements (payments). **Gender and climate** shares use the OECD policy markers and include only aid that donors screened.
12. **2025 aid cuts:** OECD DAC1 preliminary 2025 data give each donor's overall change in aid (all recipients). The Pakistan estimate applies that change to the donor's 2024 aid to Pakistan. It is a scenario, not observed data.
13. **Inflation:** real changes between 2018-19 and 2024-25 use cumulative CPI growth of ×{CPI_FY19_TO_FY25} (national CPI annual average inflation FY2020–FY2025: 10.7%, 8.9%, 12.2%, 29.2%, 23.4%, 4.5%; PBS, as reported in SBP Annual Report FY25).
""")
    with st.container(border=True):
        st.markdown("""
#### Known limitations
- Government education spending for **2024-25 is a budget allocation**, not actual spending; 2023-24 actual spending can be selected on the *Who pays* page.
- The Pakistan Economic Survey 2025-26 reports Punjab education spending for 2024-25 as Rs 178 bn, below the Rs 382 bn it reported for July–March of the same year, so it is **not used**; PIE data is used instead.
- Pakistan Economic Survey education figures for KP and the federal government in 2020-21 and 2021-22 differ widely from PIE's actual-expenditure accounts. PIE is used for education throughout; Survey education figures appear only in the running-costs/development charts.
- The **2025 aid cuts** for Pakistan are a scenario: each donor's overall 2025 change is applied to its 2024 aid to Pakistan. Multilateral banks and Saudi Arabia have not reported 2025 yet.
- HIES Table 21 (government vs private fee split) is inconsistent with enrolment data and is **not used**.
- Household and government figures cover the federal government and the four provinces (not AJK and Gilgit-Baltistan).
- Some aid flows to non-government providers (NGOs, private schools), so the three sources are not fully separate funding streams.
""")

st.sidebar.markdown(SB_FOOT, unsafe_allow_html=True)
st.markdown(f"<div class='foot'><span>Prepared by <b>{ORG}</b> · Draft for discussion · November 2026</span>"
            f"<span>Data: OECD, PBS, Pakistan Institute of Education, Finance Division</span></div>",
            unsafe_allow_html=True)
