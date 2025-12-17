import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Merged List PO", layout="wide")
st.title("Laporan Pengeluaran Pesanan Tempatan")

st.markdown("""
<style>
/* Main app background */
html, body, [data-testid="stAppViewContainer"] {
    background-color: white;
}

/* Optional: keep content area readable */
[data-testid="stVerticalBlock"] {
    padding-top: 0.5rem;
}
</style>
""", unsafe_allow_html=True)


BOX_STYLE = """
<div style="
    background: white;
    padding: 14px 14px 6px 14px;
    border-radius: 12px;
    outline: black;
    border: 5px solid rgba(0,0,0,0.30);
    box-shadow: 0 4px 12px rgba(0,0,0,0.04);
">
"""
BOX_END = "</div>"



LISTPO_PATH = "List_PO_EXTRACT.csv"
DIMPTJ_PATH = "DimPTJ.csv"

# =========================
# LOAD & MERGE
# =========================
@st.cache_data
def load_merged():
    listpo = pd.read_csv(LISTPO_PATH, encoding="utf-8-sig")
    dimptj = pd.read_csv(DIMPTJ_PATH, encoding="utf-8-sig")

    # clean headers
    listpo.columns = listpo.columns.str.strip()
    dimptj.columns = dimptj.columns.str.strip()

    # merge
    df = listpo.merge(
        dimptj,
        left_on="PTJ",
        right_on="PTJ NO",
        how="left"
    )

    # type fixes
    df["Total_Amount"] = pd.to_numeric(df["Total_Amount"], errors="coerce").fillna(0)
    df["PO_Date"] = pd.to_datetime(df["PO_Date"], format="%d.%m.%Y", errors="coerce")

    return df

df = load_merged()
df["Year"] = df["PO_Date"].dt.year


# =========================
# SIDEBAR FILTERS
# =========================
st.sidebar.header("Filters")


# ---- PTJ code restriction (background rule) ----
allowed_ptj_codes = ["PL", "SD", "TW", "BT", "MR", "SI"]

df_view = df[df["PTJ_y"].isin(allowed_ptj_codes)]

# ---- Bahagian/Unit slicer (rename label to PTJ) ----
ptj_options = sorted(df_view["BAHAGIAN/UNIT"].dropna().unique().tolist())

selected_ptj = st.sidebar.multiselect(
    "PTJ",
    ptj_options,
    default=ptj_options
)

# =========================
# APPLY FILTERS
# =========================


if selected_ptj:
    df_view = df_view[df_view["BAHAGIAN/UNIT"].isin(selected_ptj)]

# =========================
# SUMMARY CARDS
# =========================
c1, c2 = st.columns(2)

with c1:
    st.markdown("""
    <div style="background:white;padding:16px;border-radius:14px;
                box-shadow:0 6px 18px rgba(0,0,0,0.08);">
        <div style="color:#6B7280;font-size:13px;">Total PO</div>
        <div style="font-size:28px;font-weight:700;color:#241571;">
            {po}
        </div>
    </div>
    """.format(po=df_view["PO"].nunique()), unsafe_allow_html=True)

with c2:
    st.markdown("""
    <div style="background:white;padding:16px;border-radius:14px;
                box-shadow:0 6px 18px rgba(0,0,0,0.08);">
        <div style="color:#6B7280;font-size:13px;">Total Amount (RM)</div>
        <div style="font-size:28px;font-weight:700;color:#241571;">
            {amt}
        </div>
    </div>
    """.format(amt=f"{df_view['Total_Amount'].sum():,.2f}"), unsafe_allow_html=True)

# =========================
# 3 CHARTS (ONE ROW): PO COUNT BY PTJ, FIXED YEARS
# =========================
st.markdown("### Total PO (Count) Mengikut PTJ")

years_to_show = [2023, 2024, 2025]
cols = st.columns(3)

for col, yr in zip(cols, years_to_show):
    d = df[df["PTJ_y"].isin(allowed_ptj_codes)].copy()
    d = d[d["Year"] == yr]

    ptj_cnt = (
        d.groupby("PTJ_y", as_index=False)
        .agg(Total_PO=("PO", "nunique"))
        .sort_values("Total_PO", ascending=False)
    )

    with col:
        fig = px.bar(
            ptj_cnt,
            x="PTJ_y",
            y="Total_PO",
            text="Total_PO",
            title=str(yr),
        )

        fig.update_layout(
            bargap=0.4,
            title=dict(x=0.5),
            xaxis=dict(title=None, showgrid=False, zeroline=False, tickfont=dict(size=13)),
            yaxis=dict(title=None, showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="white",
            margin=dict(l=16, r=16, t=36, b=16),

            # ✅ outline box
            shapes=[
                dict(
                    type="rect",
                    xref="paper",
                    yref="paper",
                    x0=0, y0=0,
                    x1=1, y1=1,
                    line=dict(color="rgba(0,0,0,0.18)", width=1),
                    fillcolor="rgba(0,0,0,0)",
                    layer="below"
                )
            ],
        )

        fig.update_traces(
            marker_color="#98fb98",
            marker_line_width=0,
            marker_cornerradius="50%",
            textposition="outside",
            cliponaxis=False,
        )

        st.plotly_chart(fig, use_container_width=True)




# =========================
# TABLE PREP (DISPLAY ONLY)
# =========================
table_df = df_view.copy()

# Date: show date only (no time)
table_df["PO_Date"] = table_df["PO_Date"].dt.strftime("%d.%m.%Y")

# Currency formatting
table_df["Total_Amount"] = table_df["Total_Amount"].map(lambda x: f"RM {x:,.2f}")

# Keep only required columns
table_df = table_df[[
    "PO",
    "Vendor",
    "PO_Date",
    "Total_Amount"
]]
# Index start from 1
table_df = table_df.reset_index(drop=True)
table_df.index = table_df.index + 1
# =========================
# SHOW TABLE
# =========================
st.markdown("Senarai Pesanan Tempatan")

st.dataframe(
    table_df,
    use_container_width=True
)

