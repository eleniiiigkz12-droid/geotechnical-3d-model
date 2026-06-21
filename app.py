import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# Ρύθμιση σελίδας Streamlit σε wide mode
st.set_page_config(page_title="3D Stratigraphic Model", layout="wide")

st.title("📦 Real-Data Τρισδιάστατο (3D) Γεωτεχνικό Μοντέλο (0-450m)")
st.write("Συμπαγής και ημιδιάφανη απεικόνιση των εδαφικών στρώσεων με τις πραγματικές κλίσεις του Υδροφόρου Ορίζοντα.")

# 1. Εισαγωγή Αρχείου Excel
uploaded_file = st.file_uploader("📂 Ανεβάστε το τελικό αρχείο Excel (.xlsx)", type=["xlsx"])

if uploaded_file is not None:
    try:
        # Ανάγνωση των δεδομένων
        df = pd.read_excel(uploaded_file)
        
        # Καθαρισμός στηλών από κενά
        for col in df.columns:
            df = df.rename(columns={col: col.strip()})
            
        fixed_cols = ['X-coordination', 'Depth', 'N-corrected', 'Su(from SPT)', 'Vs', 'Su ( from Vs )', 'CPT-qc', 'Su ( from CPT-qc)']
        for col in fixed_cols:
            if col in df.columns:
                if df[col].dtype == object:
                    df[col] = df[col].astype(str).str.replace(',', '.', regex=False)
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        st.success("Το αρχείο φορτώθηκε επιτυχώς!")
        
        # Πραγματικά γεωλογικά δεδομένα και νέα ύψη υδροφόρου ανά γεώτρηση
        # Θέσεις Χ: ΝΓ1=80m, Γ1=180m, ΓΕ1=250m, ΝΓ2=350m (με προσθήκη των άκρων 0m και 450m)
        x_points = np.array([0, 80, 180, 250, 350, 450])
        z_water_pts = np.array([-1.20, -1.20, -0.30, -0.90, -0.60, -0.60]) # Τα πραγματικά σου υψόμετρα
        
        # Όρια στρώσεων βάσει των γεωτρήσεων
        z_layer1_pts = np.array([-9.5, -9.5, -8.5, -8.0, -11.5, -11.5])  
        z_layer2_pts = np.array([-21.0, -21.0, -20.5, -20.0, -21.5, -21.5]) 
        z_bottom_pts = np.array([-35.0, -35.0, -35.0, -35.0, -35.0, -35.0]) 

        # Δημιουργία πυκνού 3D Grid για τέλειο γέμισμα των όγκων
        x_space = np.linspace(0, 450, 40)
        y_space = np.linspace(-10, 10, 5)
        X_grid, Y_grid = np.meshgrid(x_space, y_space)
        
        # Παρεμβολή (Interpolation) για να ενωθούν ομαλά όλα τα ενδιάμεσα κενά
        Z_surface = np.zeros_like(X_grid)
        Z_water = np.tile(np.interp(x_space, x_points, z_water_pts), (len(y_space), 1))
        Z_layer1 = np.tile(np.interp(x_space, x_points, z_layer1_pts), (len(y_space), 1))
        Z_layer2 = np.tile(np.interp(x_space, x_points, z_layer2_pts), (len(y_space), 1))
        Z_bottom = np.tile(np.interp(x_space, x_points, z_bottom_pts), (len(y_space), 1))

        fig_3d = go.Figure()
        
        # --- ΣΧΕΔΙΑΣΗ ΣΤΡΩΣΕΩΝ ΩΣ ΗΜΙΔΙΑΦΑΝΟΙ ΣΥΜΠΑΓΕΙΣ ΟΓΚΟΥΣ (ΧΩΡΙΣ ΚΕΝΑ) ---
        # Χρησιμοποιούμε πολλαπλές ενδιάμεσες επιφάνειες για να "γεμίσει" το κενό εσωτερικά
        
        # Στρώση 1: Μαλακή Άργιλος / Ιλύς (Από 0m έως τη βάση της 1ης στρώσης)
        for offset in np.linspace(0, 1, 6):
            Z_fill = Z_surface * (1 - offset) + Z_layer1 * offset
            fig_3d.add_trace(go.Surface(
                x=X_grid, y=Y_grid, z=Z_fill,
                colorscale=[[0, '#d2b48c'], [1, '#d2b48c']], opacity=0.35, showscale=False,
                name='Μαλακή Άργιλος / Ιλύς (CL/ML)', legendgroup='g1', showlegend=(offset==0)
            ))
        
        # Στρώση 2: Συμπιεστή Άργιλος (Από τη βάση της 1ης έως τη βάση της 2ης)
        for offset in np.linspace(0, 1, 6):
            Z_fill = Z_layer1 * (1 - offset) + Z_layer2 * offset
            fig_3d.add_trace(go.Surface(
                x=X_grid, y=Y_grid, z=Z_fill,
                colorscale=[[0, '#ebdca5'], [1, '#ebdca5']], opacity=0.35, showscale=False,
                name='Συμπιεστή Άργιλος (CH/MH)', legendgroup='g2', showlegend=(offset==0)
            ))
        
        # Στρώση 3: Σκληρή Μάργα (Από τη βάση της 2ης έως τον πυθμένα στα -35m)
        for offset in np.linspace(0, 1, 6):
            Z_fill = Z_layer2 * (1 - offset) + Z_bottom * offset
            fig_3d.add_trace(go.Surface(
                x=X_grid, y=Y_grid, z=Z_fill,
                colorscale=[[0, '#a9a9a9'], [1, '#a9a9a9']], opacity=0.35, showscale=False,
                name='Σκλήρη Μάργα (Stiff Marl)', legendgroup='g3', showlegend=(offset==0)
            ))

        # --- ΥΔΡΟΦΟΡΟΣ ΟΡΙΖΟΝΤΑΣ (Ως παχιά, έντονη μπλε 3D γραμμή με τα πραγματικά ύψη) ---
        fig_3d.add_trace(go.Scatter3d(
            x=x_points[1:-1], # Σχεδίαση μόνο στα σημεία των πραγματικών γεωτρήσεων
            y=[0]*4,
            z=z_water_pts[1:-1],
            mode='lines+markers+text',
            line=dict(color='rgb(0, 80, 255)', width=12),
            marker=dict(size=8, color='darkblue', symbol='diamond'),
            name='Υδροφόρος Ορίζοντας',
            text=["", "💧 ΥΔΡΟΦΟΡΟΣ ΟΡΙΖΟΝΤΑΣ", "", ""], 
            textposition="top center",
            textfont=dict(size=15, color="darkblue")
        ))
        
        # Σχεδιασμός Κατακόρυφων Γεωτρήσεων (Φαίνονται τέλεια λόγω της διαφάνειας του εδάφους)
        df_clean = df.dropna(subset=['Test ID', 'X-coordination'])
        unique_tests = df_clean[['Test ID', 'X-coordination']].drop_duplicates()
        
        for idx, row in unique_tests.iterrows():
            test_id = row['Test ID']
            x_pos = row['X-coordination']
            max_depth = df[df['Test ID'] == test_id]['Depth'].max()
            
            fig_3d.add_trace(go.Scatter3d(
                x=[x_pos, x_pos], y=[0, 0], z=[0, -max_depth],
                mode='lines+markers+text',
                line=dict(color='black', width=8),
                marker=dict(size=6, color='darkred'),
                text=[str(test_id), ""],
                textposition="top center",
                name=str(test_id),
                showlegend=False
            ))
            
        fig_3d.update_layout(
            scene=dict(
                xaxis=dict(title='Μήκος Χ (m)', range=[0, 450]),
                yaxis=dict(title='Πλάτος Υ (m)', range=[-10, 10]),
                zaxis=dict(title='Βάθος Ζ (m)', range=[-35, 5]),
                # 3D Υπερύψωση για να είναι πεντακάθαρη η διακύμανση του υδροφόρου
                aspectratio=dict(x=3, y=1, z=2.2)
            ),
            height=700,
            margin=dict(r=10, l=10, b=10, t=10),
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
        )
        
        st.subheader("📦 Τρισδιάστατο Συμπαγές & Διαφανές Μοντέλο")
        st.plotly_chart(fig_3d, use_container_width=True)
        
        # 3. 2D Διαγράμματα
        st.markdown("---")
        st.subheader("📈 Συγκριτικά Προφίλ Ιδιοτήτων με το Βάθος")
        selected_test = st.selectbox("🎯 Επιλέξτε Γεώτρηση ή Δοκιμή:", df['Test ID'].dropna().unique())
        test_data = df[df['Test ID'] == selected_test].sort_values(by='Depth')
        
        col1, col2 = st.columns(2)
        with col1:
            fig_vs = go.Figure()
            if 'Vs' in test_data.columns and test_data['Vs'].notna().any():
                fig_vs.add_trace(go.Scatter(x=test_data['Vs'], y=-test_data['Depth'], mode='lines+markers', name='Vs (m/s)', line=dict(color='blue')))
            fig_vs.update_layout(title=f"Vs - {selected_test}", xaxis=dict(title="Vs (m/s)"), yaxis=dict(title="Βάθος (m)"), template="plotly_white")
            st.plotly_chart(fig_vs, use_container_width=True)
            
        with col2:
            fig_su = go.Figure()
            if 'Su(from SPT)' in test_data.columns and test_data['Su(from SPT)'].notna().any():
                fig_su.add_trace(go.Scatter(x=test_data['Su(from SPT)'], y=-test_data['Depth'], mode='lines+markers', name='Su (SPT)', line=dict(color='green')))
            if 'Su ( from Vs )' in test_data.columns and test_data['Su ( from Vs )'].notna().any():
                fig_su.add_trace(go.Scatter(x=test_data['Su ( from Vs )'], y=-test_data['Depth'], mode='lines+markers', name='Su (Vs)', line=dict(color='purple', dash='dash')))
            if 'Su ( from CPT-qc)' in test_data.columns and test_data['Su ( from CPT-qc)'].notna().any():
                fig_su.add_trace(go.Scatter(x=test_data['Su ( from CPT-qc)'], y=-test_data['Depth'], mode='lines+markers', name='Su (CPT)', line=dict(color='red')))
            fig_su.update_layout(title=f"Su - {selected_test}", xaxis=dict(title="Su (kPa)"), yaxis=dict(title="Βάθος (m)"), template="plotly_white")
            st.plotly_chart(fig_su, use_container_width=True)
            
    except Exception as e:
        st.error(f"⚠️ Σφάλμα κατά την επεξεργασία: {e}")
else:
    st.info("💡 Η εφαρμογή είναι έτοιμη. Ανεβάστε το αρχείο Excel για να δημιουργηθεί το μοντέλο.")
