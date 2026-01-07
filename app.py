import streamlit as st
import pandas as pd

# --- 1. Page Configuration ---
st.set_page_config(page_title="Court Hardware Dashboard", layout="wide")

# ==========================================
# 🔒 PASSWORD PROTECTION SECTION
# ==========================================
def check_password():
    def password_entered():
        # You can change the password below
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
        /* Global Background Gradient */
        .stApp {
            background: linear-gradient(135deg, #e0eafc 0%, #cfdef3 100%);
        }

        /* Glass Card Effect */
        .glass-card {
            background: rgba(255, 255, 255, 0.45);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.7);
            border-radius: 20px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.08);
            transition: all 0.3s ease;
        }
        
        .glass-card:hover {
            transform: translateY(-5px);
            background: rgba(255, 255, 255, 0.6);
            box-shadow: 0 12px 40px 0 rgba(31, 38, 135, 0.15);
        }

        /* Text Styles */
        .card-title {
            color: #555;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            font-weight: 700;
            margin-bottom: 10px;
        }
        .card-value {
            color: #111;
            font-size: 24px;
            font-weight: 800;
            margin-bottom: 15px;
        }
        
        /* Modern Pill Badges */
        .badge {
            padding: 6px 14px;
            border-radius: 30px;
            font-size: 11px;
            font-weight: 700;
            display: inline-block;
            text-transform: uppercase;
        }
        .badge-green { background: rgba(40, 167, 69, 0.15); color: #155724; border: 1px solid rgba(40, 167, 69, 0.2); }
        .badge-red { background: rgba(220, 53, 69, 0.15); color: #721c24; border: 1px solid rgba(220, 53, 69, 0.2); }
        .badge-grey { background: rgba(108, 117, 125, 0.15); color: #383d41; border: 1px solid rgba(108, 117, 125, 0.2); }

        /* Metric widget custom styling */
        [data-testid="stMetricValue"] { font-weight: 800 !important; color: #1a1a1a !important; }
        [data-testid="stMetricLabel"] { color: #444 !important; font-weight: 600 !important; font-size: 14px !important; }
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
                if col in df.columns:
                    df[col] = df[col].astype(str).str.strip()
            
            if 'State' in df.columns: df['State'] = df['State'].replace('nan', pd.NA).ffill()
            if 'Session_Division' in df.columns: df['Session_Division'] = df['Session_Division'].replace('nan', pd.NA).ffill()

            cols_to_numeric = ['Required_Qty', 'Distributed_Qty', 'Balance_Qty', 'Courts_Count', 'Family_Courts', 'TJOs', 'Total_Courts']
            for col in cols_to_numeric:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            return df
        except Exception as e:
            st.error(f"Error loading data: {e}")
            return None

    df = load_data()

    # --- 4. Helper Function to Render Glass Cards ---
    def render_glass_card(title, value_top, value_bottom, balance):
        if balance > 0:
            badge_class, status_text = "badge-green", "Surplus"
        elif balance < 0:
            badge_class, status_text = "badge-red", "Shortfall"
        else:
            badge_class, status_text = "badge-grey", "Balanced"

        html_code = f"""
        <div class="glass-card">
            <div class="card-title">{title}</div>
            <div class="card-value">{int(value_top)} / {int(value_bottom)}</div>
            <span class="badge {badge_class}">{status_text}: {int(abs(balance))}</span>
        </div>
        """
        st.markdown(html_code, unsafe_allow_html=True)

    # --- 5. Main App Layout ---
    st.title("🏛️ Court Inventory Dashboard")

    if df is not None and not df.empty:
        st.sidebar.header("🔍 Filters")
        
        if 'State' in df.columns:
            selected_state = st.sidebar.selectbox("Select State", ['All States'] + sorted(df['State'].unique().tolist()))
            state_df = df[df['State'] == selected_state] if selected_state != 'All States' else df
        else:
            state_df = df

        if 'Location_Name' in state_df.columns:
            selected_location = st.selectbox("Select Location", ['📊 Overall Summary'] + sorted(state_df['Location_Name'].unique().tolist()))
            st.markdown("---")

            if selected_location == '📊 Overall Summary':
                st.subheader(f"Status: {selected_state}")
                unique_locs_df = state_df.drop_duplicates(subset=['Location_Name'])
                
                # Metrics Row
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Total Courts", int(unique_locs_df['Total_Courts'].sum()))
                m2.metric("Regular Courts", int(unique_locs_df['Courts_Count'].sum()))
                m3.metric("Family Courts", int(unique_locs_df['Family_Courts'].sum()))
                m4.metric("TJOs", int(unique_locs_df['TJOs'].sum()))
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Hardware Cards
                summary_df = state_df.groupby('Hardware_Item')[['Required_Qty', 'Distributed_Qty', 'Balance_Qty']].sum().reset_index()
                cols = st.columns(4)
                for index, row in summary_df.iterrows():
                    with cols[index % 4]:
                        render_glass_card(row['Hardware_Item'], row['Distributed_Qty'], row['Required_Qty'], row['Balance_Qty'])

            else:
                loc_data = state_df[state_df['Location_Name'] == selected_location]
                if not loc_data.empty:
                    meta = loc_data.iloc[0]
                    c1, c2, c3, c4, c5 = st.columns(5)
                    c1.info(f"**Type:** {meta.get('Location_Type', 'N/A')}")
                    c2.warning(f"**Total:** {int(meta.get('Total_Courts', 0))}")
                    c3.warning(f"**Reg:** {int(meta.get('Courts_Count', 0))}")
                    c4.warning(f"**Family:** {int(meta.get('Family_Courts', 0))}")
                    c5.warning(f"**TJOs:** {int(meta.get('TJOs', 0))}")

                    st.markdown("<br>", unsafe_allow_html=True)
                    cols = st.columns(4)
                    for index, (i, row) in enumerate(loc_data.iterrows()):
                        with cols[index % 4]:
                            render_glass_card(row['Hardware_Item'], row['Distributed_Qty'], row['Required_Qty'], row['Balance_Qty'])
                    
                    st.markdown("### 📋 Detailed Records")
                    st.dataframe(loc_data[['Hardware_Item', 'Required_Qty', 'Distributed_Qty', 'Balance_Qty', 'Status']], use_container_width=True, hide_index=True)

    else:
        st.error("Missing Data Error.")