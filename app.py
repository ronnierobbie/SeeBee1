import streamlit as st
import pandas as pd
from io import BytesIO

# --- 1. Page Configuration ---
st.set_page_config(page_title="Court Inventory Dashboard", layout="wide")

# ==========================================
# 🔒 PASSWORD PROTECTION SECTION
# ==========================================
def check_password():
    def password_entered():
        if st.session_state["password"] == "court2026": 
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Please enter the dashboard password:", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Please enter the dashboard password:", type="password", on_change=password_entered, key="password")
        st.error("😕 Password incorrect")
        return False
    else:
        return True

if check_password():
    # ==========================================
    # ✨ MODERN GLASSMORPHISM UI STYLING
    # ==========================================
    st.markdown("""
    <style>
        .stApp { background: linear-gradient(135deg, #e0eafc 0%, #cfdef3 100%); }
        .glass-card {
            background: rgba(255, 255, 255, 0.45);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.7);
            border-radius: 20px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.08);
        }
        .section-header {
            color: #2c3e50; font-weight: 800; padding: 10px 0;
            border-bottom: 2px solid rgba(255,255,255,0.5);
            margin: 30px 0 20px 0; font-size: 24px;
        }
        .card-title { color: #555; font-size: 11px; text-transform: uppercase; font-weight: 700; margin-bottom: 8px; }
        .card-value { color: #111; font-size: 18px; font-weight: 800; margin-bottom: 12px; }
        .badge { padding: 5px 12px; border-radius: 20px; font-size: 10px; font-weight: 700; display: inline-block; }
        .badge-green { background: rgba(40, 167, 69, 0.15); color: #155724; border: 1px solid rgba(40, 167, 69, 0.2); }
        .badge-red { background: rgba(220, 53, 69, 0.15); color: #721c24; border: 1px solid rgba(220, 53, 69, 0.2); }
        .badge-grey { background: rgba(108, 117, 125, 0.15); color: #383d41; border: 1px solid rgba(108, 117, 125, 0.2); }
    </style>
    """, unsafe_allow_html=True)

    # --- 3. Data Loading ---
    @st.cache_data
    def load_data():
        try:
            df = pd.read_excel('data.xlsx', sheet_name='Tooli')
            df.columns = df.columns.str.strip()
            string_cols = ['State', 'Session_Division', 'Location_Name', 'Location_Type', 'Hardware_Item', 'Status']
            for col in string_cols:
                if col in df.columns: df[col] = df[col].astype(str).str.strip()
            
            if 'State' in df.columns: df['State'] = df['State'].replace('nan', pd.NA).ffill()
            if 'Session_Division' in df.columns: df['Session_Division'] = df['Session_Division'].replace('nan', pd.NA).ffill()

            numeric_cols = ['Required_Qty', 'Distributed_Qty', 'Balance_Qty', 'Courts_Count', 'Family_Courts', 'TJOs', 'Total_Courts']
            for col in numeric_cols:
                if col in df.columns: df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            return df
        except Exception as e:
            st.error(f"Error loading data: {e}")
            return None

    df = load_data()

    # --- 4. Export Helper ---
    def to_excel(df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Dashboard_Data')
        return output.getvalue()

    def render_glass_card(title, value_top, value_bottom, balance):
        if balance > 0: b_class, b_text = "badge-green", "Surplus"
        elif balance < 0: b_class, b_text = "badge-red", "Shortfall"
        else: b_class, b_text = "badge-grey", "Balanced"
        html = f"""<div class="glass-card"><div class="card-title">{title}</div><div class="card-value">{int(value_top)} / {int(value_bottom)}</div><span class="badge {b_class}">{b_text}: {int(abs(balance))}</span></div>"""
        st.markdown(html, unsafe_allow_html=True)

    # --- 5. Navigation & Display ---
    if df is not None:
        st.sidebar.title("Navigation")
        
        # State Filter - Defaults to All States
        unique_states = ['All States'] + sorted(df['State'].unique().tolist())
        sel_state = st.sidebar.selectbox("Select State", unique_states, index=0)
        state_df = df if sel_state == 'All States' else df[df['State'] == sel_state]
        
        # Location/Division Filter - Defaults to Summary
        unique_locs = ['📊 Overall Summary'] + sorted(state_df['Location_Name'].unique().tolist())
        sel_loc = st.sidebar.selectbox("Select Location", unique_locs, index=0)

        st.title("🏛️ Court Inventory Dashboard")

        # Filtering Logic
        if sel_loc == '📊 Overall Summary':
            st.markdown(f'<div class="section-header">🌍 Overall Summary: {sel_state}</div>', unsafe_allow_html=True)
            display_df = state_df
        else:
            st.markdown(f'<div class="section-header">📍 Location Detail: {sel_loc}</div>', unsafe_allow_html=True)
            display_df = state_df[state_df['Location_Name'] == sel_loc]

        # --- Aggregated Metrics ---
        court_counts_df = display_df.drop_duplicates(subset=['Location_Name'])
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Courts", int(court_counts_df['Total_Courts'].sum()))
        m2.metric("Regular", int(court_counts_df['Courts_Count'].sum()))
        m3.metric("Family", int(court_counts_df['Family_Courts'].sum()))
        m4.metric("TJOs", int(court_counts_df['TJOs'].sum()))

        st.markdown("<br>", unsafe_allow_html=True)

        # --- Hardware Visual Cards ---
        hw_summary = display_df.groupby('Hardware_Item')[['Distributed_Qty', 'Required_Qty', 'Balance_Qty']].sum().reset_index()
        cols = st.columns(6) # Using 6 columns to fit all hardware types in one row
        for idx, row in hw_summary.iterrows():
            with cols[idx % 6]:
                render_glass_card(row['Hardware_Item'], row['Distributed_Qty'], row['Required_Qty'], row['Balance_Qty'])

        # --- THE TABLE: Detailed Hardware Records ---
        st.markdown(f'<div class="section-header">📋 Detailed Hardware Records</div>', unsafe_allow_html=True)
        
        # Selecting columns as per your request
        table_data = display_df[['Session_Division', 'Location_Name', 'Hardware_Item', 'Required_Qty', 'Distributed_Qty', 'Balance_Qty', 'Status']]
        
        # Styling for the table status column
        def highlight_status(val):
            if val == 'Shortfall': return 'background-color: #ffcccc; color: darkred'
            elif val == 'Surplus': return 'background-color: #ccffcc; color: darkgreen'
            elif val == 'OK': return 'background-color: #f0f0f0; color: grey'
            return ''

        st.dataframe(
            table_data.style.map(highlight_status, subset=['Status']),
            use_container_width=True,
            hide_index=True
        )

        # --- Download Center ---
        st.markdown("### 📥 Download Center")
        c1, c2 = st.columns(2)
        with c1:
            st.download_button(label="Download CSV", data=table_data.to_csv(index=False), file_name="inventory_report.csv", mime="text/csv")
        with c2:
            st.download_button(label="Download Excel", data=to_excel(table_data), file_name="inventory_report.xlsx")

    else:
        st.error("Error: Could not load data from data.xlsx.")
