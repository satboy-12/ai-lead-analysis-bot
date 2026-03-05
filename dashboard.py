"""Interactive Streamlit dashboard for lead analysis and visualization.

Provides real-time lead data processing, validation, classification,
and visualization capabilities through a user-friendly web interface.
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.figure
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Configuration
PHONE_PATTERN = r"^[6-9]\d{9}$"
EMAIL_PATTERN = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
MAX_ROWS_DISPLAY = 50


def clean_phone_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean phone numbers by removing non-numeric characters.
    
    Args:
        df: Lead data
        
    Returns:
        DataFrame with cleaned phone column
    """
    df_clean = df.copy()
    df_clean["phone"] = df_clean["phone"].astype(str).str.replace(r"\D", "", regex=True)
    return df_clean


def validate_leads(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:  # type: ignore
    """Validate phone numbers and email addresses.
    
    Args:
        df: Lead data
        
    Returns:
        Tuple of (validated DataFrame, duplicate count)
    """
    df_validated = df.copy()
    
    # Remove duplicates
    duplicates_before = len(df_validated)
    df_validated = df_validated.drop_duplicates(subset=["phone", "email"])
    duplicates_removed = duplicates_before - len(df_validated)
    
    # Validate phone and email
    df_validated["phone_valid"] = df_validated["phone"].str.match(PHONE_PATTERN)
    df_validated["email_valid"] = df_validated["email"].str.match(EMAIL_PATTERN)
    
    return df_validated, duplicates_removed


def classify_leads(df: pd.DataFrame) -> pd.DataFrame:
    """Classify leads by quality based on score and call attempts.
    
    Args:
        df: Valid lead data
        
    Returns:
        DataFrame with lead_category column
    """
    df_classified = df.copy()
    
    conditions = [
        (df_classified["lead_score"] >= 80) & (df_classified["call_attempt"] <= 2),
        df_classified["lead_score"].between(50, 79),
        df_classified["lead_score"] < 50
    ]
    
    choices = ["HOT_LEAD", "WARM_LEAD", "COLD_LEAD"]
    df_classified["lead_category"] = np.select(conditions, choices, default="LOW")
    
    return df_classified


def get_lead_statistics(df: pd.DataFrame, valid_df: pd.DataFrame, 
                       best_leads: pd.DataFrame) -> dict[str, int | float]:  # type: ignore
    """Calculate key statistics for display.
    
    Args:
        df: Original data
        valid_df: Valid leads
        best_leads: HOT leads
        
    Returns:
        Dictionary with statistics
    """
    total = len(df)
    valid = len(valid_df)
    valid_percent = (valid / total * 100) if total > 0 else 0
    
    return {
        "total": total,
        "valid": valid,
        "invalid": total - valid,
        "valid_percent": valid_percent,
        "hot_count": (valid_df["lead_category"] == "HOT_LEAD").sum(),
        "warm_count": (valid_df["lead_category"] == "WARM_LEAD").sum(),
        "cold_count": (valid_df["lead_category"] == "COLD_LEAD").sum(),
        "best_count": len(best_leads)
    }


def create_distribution_chart(valid_df: pd.DataFrame) -> matplotlib.figure.Figure:  # type: ignore
    """Create pie chart of lead distribution.
    
    Args:
        valid_df: Valid leads
        
    Returns:
        Matplotlib figure object
    """
    values = [
        (valid_df["lead_category"] == "HOT_LEAD").sum(),
        (valid_df["lead_category"] == "WARM_LEAD").sum(),
        (valid_df["lead_category"] == "COLD_LEAD").sum()
    ]
    
    labels = ["HOT", "WARM", "COLD"]
    colors = ["#FF6B6B", "#FFA500", "#4ECDC4"]
    
    fig, ax = plt.subplots(figsize=(8, 6))  # type: ignore
    ax.pie(values, labels=labels, autopct="%1.1f%%", colors=colors,  # type: ignore
           startangle=90, textprops={"fontsize": 11, "weight": "bold"})
    ax.set_title("Lead Quality Distribution", fontsize=14, weight="bold")  # type: ignore
    
    return fig  # type: ignore


def create_score_distribution_chart(valid_df: pd.DataFrame) -> matplotlib.figure.Figure:
    """Create histogram of lead scores.
    
    Args:
        valid_df: Valid leads
        
    Returns:
        Matplotlib figure object
    """
    fig, ax = plt.subplots(figsize=(10, 6))  # type: ignore
    ax.hist(valid_df["lead_score"], bins=20, color="#3498DB", edgecolor="black", alpha=0.7)  # type: ignore
    ax.set_xlabel("Lead Score", fontsize=11, weight="bold")  # type: ignore
    ax.set_ylabel("Number of Leads", fontsize=11, weight="bold")  # type: ignore
    ax.set_title("Lead Score Distribution", fontsize=14, weight="bold")  # type: ignore
    ax.grid(axis="y", alpha=0.3)  # type: ignore
    
    return fig  # type: ignore


def format_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Format DataFrame for display.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Formatted DataFrame
    """
    df_display = df.copy()
    
    # Select and reorder columns
    display_columns = ["phone", "email", "lead_score", "call_attempt", "lead_category"]
    available_columns = [col for col in display_columns if col in df_display.columns]
    
    return df_display[available_columns]


def main():
    """Main Streamlit application."""
    # Page configuration
    st.set_page_config(
        page_title="Lead Intelligence Dashboard",
        page_icon=":bar_chart:",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Title and description
    st.title("[ANALYTICS] Lead Intelligence Dashboard")
    st.markdown(
        "Analyze, validate, and classify leads with advanced filtering and visualization"
    )
    
    # File uploader
    uploaded_file = st.file_uploader("Upload Leads CSV File", type=["csv"])
    
    if uploaded_file is not None:
        try:
            # Load data
            df = pd.read_csv(uploaded_file)
            logger.info(f"Loaded {len(df)} records from uploaded file")
            
            # Data processing
            df_clean = clean_phone_data(df)
            df_validated, duplicates_removed = validate_leads(df_clean)
            valid_df = df_validated[
                (df_validated["phone_valid"]) & (df_validated["email_valid"])
            ].copy()
            valid_df = classify_leads(valid_df)
            best_leads = valid_df[valid_df["lead_category"] == "HOT_LEAD"]
            
            # Get statistics
            stats = get_lead_statistics(df, valid_df, best_leads)
            
            # Display metrics
            st.subheader("[METRICS] Key Metrics")
            metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
            
            with metric_col1:
                st.metric("Total Leads", f"{stats['total']:,}")
            with metric_col2:
                st.metric(
                    "Valid Leads",
                    f"{stats['valid']:,}",
                    f"{stats['valid_percent']:.1f}% Valid"
                )
            with metric_col3:
                st.metric("🔥 HOT Leads", f"{stats['hot_count']:,}")
            with metric_col4:
                st.metric("Invalid Leads", f"{stats['invalid']:,}")
            
            st.divider()
            
            # Charts
            st.subheader("[CHARTS] Lead Distribution Analysis")
            chart_col1, chart_col2 = st.columns(2)
            
            with chart_col1:
                st.pyplot(create_distribution_chart(valid_df))
            
            with chart_col2:
                st.pyplot(create_score_distribution_chart(valid_df))
            
            st.divider()
            
            # Detailed statistics
            st.subheader("[STATS] Lead Category Breakdown")
            category_col1, category_col2, category_col3 = st.columns(3)
            
            with category_col1:
                st.info(f"[HOT] **HOT Leads**\n\n{stats['hot_count']:,} leads")
            with category_col2:
                st.warning(f"[WARM] **WARM Leads**\n\n{stats['warm_count']:,} leads")
            with category_col3:
                st.info(f"[COLD] **COLD Leads**\n\n{stats['cold_count']:,} leads")
            
            st.divider()
            
            # Best leads section
            st.subheader("[HOT] Hot Leads for Immediate Telecalling")
            
            if len(best_leads) > 0:
                # Display options
                display_count = st.slider(
                    "Number of leads to display",
                    min_value=1,
                    max_value=len(best_leads),
                    value=min(10, len(best_leads))
                )
                
                # Display table
                st.dataframe(  # type: ignore
                    format_dataframe(best_leads.head(display_count)),
                    use_container_width=True,
                    height=300
                )
                
                # Download buttons
                download_col1, download_col2 = st.columns(2)
                
                with download_col1:
                    csv_data = best_leads.to_csv(index=False)
                    st.download_button(
                        label="[DOWNLOAD] Hot Leads (CSV)",
                        data=csv_data,
                        file_name="hot_leads.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                
                with download_col2:
                    csv_all = valid_df.to_csv(index=False)
                    st.download_button(
                        label="[DOWNLOAD] All Valid Leads (CSV)",
                        data=csv_all,
                        file_name="all_valid_leads.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
            else:
                st.warning("No hot leads found in the dataset.")
            
            st.divider()
            
            # AI Insights
            st.subheader("[AI] AI Insights & Recommendations")
            
            insight_text = f"""
            ### Analysis Summary
            
            **Data Processing Results:**
            - Analyzed {stats['total']:,} total leads
            - Identified {stats['valid']:,} valid leads ({stats['valid_percent']:.1f}%)
            - Removed {stats['invalid']:,} invalid leads
            - {duplicates_removed} duplicate records found
            
            **Lead Classification:**
            - **{stats['hot_count']:,} HOT leads** - High conversion probability, immediate contact recommended
            - **{stats['warm_count']:,} WARM leads** - Medium priority, suitable for nurturing campaigns
            - **{stats['cold_count']:,} COLD leads** - Low priority, requires engagement strategy
            
            **Strategic Recommendations:**
            1. [OK] Prioritize HOT leads for immediate telecalling campaigns
            2. [EMAIL] Set up nurturing campaigns for WARM leads
            3. [TRACK] Monitor call attempts and conversion rates by category
            4. [STATS] Use lead scores to optimize timing and messaging
            5. [REVIEW] Re-evaluate COLD leads after 30 days for score changes
            """
            
            st.markdown(insight_text)
            
        except Exception as e:
            logger.error(f"Error processing file: {e}")
            st.error(f"Error processing file: {str(e)}")
            st.info("Please ensure your CSV has 'phone', 'email', 'call_attempt', and 'lead_score' columns.")
    else:
        st.info("[UPLOAD] Upload a CSV file to begin analysis")
        st.markdown(
            """
            ### Expected CSV Format:
            - **phone**: Phone number
            - **email**: Email address
            - **call_attempt**: Number of call attempts (0-5)
            - **lead_score**: Lead quality score (0-100)
            """
        )


if __name__ == "__main__":
    main()