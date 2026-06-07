# app.py
# BIM-SAP Material Procurement Sync
# Streamlit Enterprise Prototype

import streamlit as st
import pandas as pd
import numpy as np

# ---------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="BIM-SAP Material Procurement Sync",
    page_icon="🏗️",
    layout="wide"
)

st.title("🏗️ BIM-SAP Material Procurement Sync")
st.caption(
    "Identify material shortages by comparing BIM project requirements "
    "against SAP enterprise inventory records."
)

# ---------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------
def load_csv_clean(uploaded_file):
    """
    Read CSV and clean whitespace issues.
    """
    df = pd.read_csv(uploaded_file, skipinitialspace=True)

    df.columns = df.columns.str.strip()

    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].astype(str).str.strip()

    return df


def create_demo_data():
    """
    Create demonstration BIM and SAP datasets in memory.
    """

    bim_df = pd.DataFrame(
        {
            "ElementID": [
                "B001",
                "B002",
                "C001",
                "C002",
                "W001",
                "W002",
                "F001",
            ],
            "Category": [
                "Beam",
                "Beam",
                "Column",
                "Column",
                "Wall",
                "Wall",
                "Foundation",
            ],
            "MaterialName": [
                "Concrete C40",
                "Concrete C40",
                "Concrete C50",
                "Concrete C50",
                "Masonry Block",
                "Masonry Block",
                "Reinforced Concrete",
            ],
            "Volume_m3": [
                50,
                45,
                30,
                40,
                70,
                60,
                120,
            ],
            "StructuralRating": [
                "High",
                "High",
                "High",
                "High",
                "Medium",
                "Medium",
                "Critical",
            ],
        }
    )

    sap_df = pd.DataFrame(
        {
            "MaterialID": [
                "MAT001",
                "MAT002",
                "MAT003",
                "MAT004",
            ],
            "MaterialName": [
                "Concrete C40",
                "Concrete C50",
                "Masonry Block",
                "Reinforced Concrete",
            ],
            "AvailableStock_m3": [
                70,
                100,
                50,
                90,
            ],
            "UnitCost_AUD": [
                180,
                220,
                80,
                250,
            ],
            "LeadTime_Days": [
                7,
                14,
                5,
                21,
            ],
        }
    )

    return bim_df, sap_df


def process_material_analysis(bim_df, sap_df):
    """
    Aggregate BIM quantities and compare with SAP inventory.
    """

    required_materials = (
        bim_df.groupby("MaterialName", as_index=False)
        .agg(Total_Volume_Required=("Volume_m3", "sum"))
    )

    merged_df = required_materials.merge(
        sap_df,
        how="left",
        on="MaterialName"
    )

    merged_df["AvailableStock_m3"] = (
        merged_df["AvailableStock_m3"]
        .fillna(0)
    )

    merged_df["UnitCost_AUD"] = (
        merged_df["UnitCost_AUD"]
        .fillna(0)
    )

    merged_df["LeadTime_Days"] = (
        merged_df["LeadTime_Days"]
        .fillna(0)
    )

    merged_df["Material_Shortage"] = (
        merged_df["Total_Volume_Required"]
        - merged_df["AvailableStock_m3"]
    )

    merged_df["Material_Shortage"] = (
        merged_df["Material_Shortage"]
        .clip(lower=0)
    )

    merged_df["Total_Procurement_Cost"] = (
        merged_df["Material_Shortage"]
        * merged_df["UnitCost_AUD"]
    )

    return merged_df


def highlight_shortages(row):
    """
    Highlight rows with shortages.
    """

    if row["Material_Shortage"] > 0:
        return ["background-color: #ffdddd"] * len(row)

    return [""] * len(row)


# ---------------------------------------------------------
# Sidebar Inputs
# ---------------------------------------------------------
st.sidebar.header("Data Sources")

bim_file = st.sidebar.file_uploader(
    "Upload BIM Schedule CSV",
    type=["csv"]
)

sap_file = st.sidebar.file_uploader(
    "Upload SAP Enterprise Ledger CSV",
    type=["csv"]
)

load_demo = st.sidebar.button(
    "Load Demonstration Datasets",
    use_container_width=True
)

# ---------------------------------------------------------
# Data Loading Logic
# ---------------------------------------------------------
bim_df = None
sap_df = None

if bim_file is not None and sap_file is not None:
    try:
        bim_df = load_csv_clean(bim_file)
        sap_df = load_csv_clean(sap_file)

    except Exception as ex:
        st.error(f"Error reading files: {ex}")

elif load_demo:
    bim_df, sap_df = create_demo_data()

# ---------------------------------------------------------
# Main Processing
# ---------------------------------------------------------
if bim_df is not None and sap_df is not None:

    results_df = process_material_analysis(
        bim_df,
        sap_df
    )

    # -----------------------------------------------------
    # Metrics
    # -----------------------------------------------------
    total_project_cost = (
        results_df["Total_Procurement_Cost"]
        .sum()
    )

    shortage_count = (
        results_df["Material_Shortage"] > 0
    ).sum()

    max_lead_time = (
        results_df["LeadTime_Days"]
        .max()
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Total Project Cost",
        f"AUD ${total_project_cost:,.2f}"
    )

    col2.metric(
        "Structural Items with Shortages",
        int(shortage_count)
    )

    col3.metric(
        "Maximum Delivery Lead Time",
        f"{int(max_lead_time)} Days"
    )

    st.divider()

    # -----------------------------------------------------
    # Data Preview
    # -----------------------------------------------------
    with st.expander("BIM Schedule Data", expanded=False):
        st.dataframe(
            bim_df,
            use_container_width=True
        )

    with st.expander("SAP Enterprise Ledger", expanded=False):
        st.dataframe(
            sap_df,
            use_container_width=True
        )

    # -----------------------------------------------------
    # Results Table
    # -----------------------------------------------------
    st.subheader("Material Procurement Analysis")

    styled_df = (
        results_df.style
        .apply(highlight_shortages, axis=1)
        .format(
            {
                "Total_Volume_Required": "{:,.2f}",
                "AvailableStock_m3": "{:,.2f}",
                "Material_Shortage": "{:,.2f}",
                "UnitCost_AUD": "${:,.2f}",
                "Total_Procurement_Cost": "${:,.2f}",
            }
        )
    )

    st.dataframe(
        styled_df,
        use_container_width=True,
        height=500
    )

else:
    st.info(
        """
        Upload both CSV files using the sidebar,
        or click **Load Demonstration Datasets**
        to explore the prototype.
        """
    )

    st.markdown(
        """
        ### Expected BIM Schedule Schema

        | Column |
        |----------|
        | ElementID |
        | Category |
        | MaterialName |
        | Volume_m3 |
        | StructuralRating |

        ### Expected SAP Ledger Schema

        | Column |
        |----------|
        | MaterialID |
        | MaterialName |
        | AvailableStock_m3 |
        | UnitCost_AUD |
        | LeadTime_Days |
        """
    )
