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

    # --- 4. Export Functionality ---
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

    # --- 5. Main Content Logic ---
    if df is not None:
        # Sidebar with Default Selection
        st.sidebar.title("Navigation")
        unique_states = ['All States'] + sorted(df['State'].unique().tolist())
        sel_state = st.sidebar.selectbox("Select State", unique_states, index=0) # Default: All States
        
        state_df = df if sel_state == 'All States' else df[df['State'] == sel_state]
        
        unique_divs = ['📊 Overall Summary'] + sorted(state_df['Session_Division'].unique().tolist())
        sel_div = st.sidebar.selectbox("Select Session Division", unique_divs, index=0) # Default: Summary

        st.title("⚖️ Court Inventory Dashboard")

        # Handle View Logic
        if sel_div == '📊 Overall Summary':
            st.markdown(f'<div class="section-header">🌍 Global Aggregated Summary: {sel_state}</div>', unsafe_allow_html=True)
            display_df = state_df
        else:
            st.markdown(f'<div class="section-header">🏢 District Detail: {sel_div}</div>', unsafe_allow_html=True)
            display_df = state_df[state_df['Session_Division'] == sel_div]

        # DISTRICT TOTALS
        unique_locs = display_df.drop_duplicates(subset=['Location_Name'])
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Courts", int(unique_locs['Total_Courts'].sum()))
        m2.metric("Regular", int(unique_locs['Courts_Count'].sum()))
        m3.metric("Family", int(unique_locs['Family_Courts'].sum()))
        m4.metric("TJOs", int(unique_locs['TJOs'].sum()))

        agg_hw = display_df.groupby('Hardware_Item')[['Distributed_Qty', 'Required_Qty', 'Balance_Qty']].sum().reset_index()
        cols = st.columns(6)
        for idx, row in agg_hw.iterrows():
            with cols[idx % 6]:
                render_glass_card(row['Hardware_Item'], row['Distributed_Qty'], row['Required_Qty'], row['Balance_Qty'])

        # Detailed Table Fix
        st.markdown(f'<div class="section-header">📋 Detailed Records List</div>', unsafe_allow_html=True)
        final_table = display_df[['Session_Division', 'Location_Name', 'Hardware_Item', 'Required_Qty', 'Distributed_Qty', 'Balance_Qty', 'Status']]
        st.dataframe(final_table, use_container_width=True, hide_index=True)

        # Download Center
        st.markdown("### 📥 Download Center")
        c1, c2 = st.columns(2)
        with c1:
            st.download_button(label="Download as CSV", data=final_table.to_csv(index=False), file_name=f"court_data_{sel_div}.csv", mime="text/csv")
        with c2:
            st.download_button(label="Download as Excel", data=to_excel(final_table), file_name=f"court_data_{sel_div}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
