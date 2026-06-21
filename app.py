import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# Ρύθμιση σελίδας Streamlit σε wide mode
st.set_page_config(page_title="3D Solid Geotechnical Model", layout="wide")

st.title("📦 Real-Data Τρισδιάστατο (3D) Γεωτεχνικό Μοντέλο (0-450m)")
st.write("Συμπαγής τρισδιάστατη απεικόνιση των εδαφικών στρώσεων με πάχος και επισήμανση του Υδροφόρου Ορίζοντα.")

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
        
        # Πραγματικά γεωλογικά δεδομένα από το φύλλο "Γεωτρήσεις"
        x_points = [0, 80, 250, 350, 450]
        z_water_pts = [-2.0, -2.0, -2.2, -1.8, -1.8]
        z_layer1_pts = [-9.5, -9.5, -8.0, -11.5, -11.5]  
        z_layer2_pts = [-21.0, -21.0, -20.0, -21.5, -21.5] 
        z_bottom_pts = [-35.0, -35.0, -35.0, -35.0, -35.0] 

        fig_3d = go.Figure()
        
        # --- ΣΧΕΔΙΑΣΗ ΣΤΡΩΣΕΩΝ ΩΣ ΣΥΜΠΑΓΕΙΣ ΟΓΚΟΥΣ ---
        for y_val in [-5, 5]: 
            
            # Στρώση 1: Μαλακή Άργιλος / Ιλύς
            fig_3d.add_trace(go.Scatter3d(
                x=x_points + x_points[::-1],
                y=[y_val]*5 + [y_val]*5,
                z=[0, 0, 0, 0, 0] + z_layer1_pts[::-1],
                mode='lines',
                fill='toself',
                fillcolor='rgba(210, 180, 140, 0.7)',
                line=dict(color='rgba(139, 115, 85, 0.8)', width=2),
                name='Μαλακή Άργιλος / Ιλύς (CL/ML)'
            ))
            
            # Στρώση 2: Συμπιεστή Άργιλος
            fig_3d.add_trace(go.Scatter3d(
                x=x_points + x_points[::-1],
                y=[y_val]*5 + [y_val]*5,
                z=z_layer1_pts + z_layer2_pts[::-1],
                mode='lines',
                fill='toself',
                fillcolor='rgba(240, 230, 140, 0.7)',
                line=dict(color='rgba(184, 134, 11, 0.8)', width=2),
                name='Συμπιεστή Άργιλος (CH/MH)'
            ))
            
            # Στρώση 3: Σκληρή Μάργα
            fig_3d.add_trace(go.Scatter3d(
                x=x_points + x_points[::-1],
                y=[y_val]*5 + [y_val]*5,
                z=z_layer2_pts + z_bottom_pts[::-1],
                mode='lines',
                fill='toself',
                fillcolor='rgba(169, 169, 169, 0.7)',
                line=dict(color='rgba(105, 105, 105, 0.8)', width=2),
                name='Σκλήρη Μάργα (Stiff Marl)'
            ))

        # --- ΥΔΡΟΦΟΡΟΣ ΟΡΙΖΟΝΤΑΣ ΩΣ ΜΠΛΕ ΓΡΑΜΜΗ ΜΕ ΚΑΘΑΡΗ ΤΑΜΠΕΛΑ ---
        fig_3d.add_trace(go.Scatter3d(
            x=x_points,
            y=[0]*5,
            z=z_water_pts,
            mode='lines+text',
            line=dict(color='rgb(0, 120, 255)', width=8),
            name='Υδροφόρος Ορίζοντας',
            text=["", "", "💧 ΥΔΡΟΦΟΡΟΣ ΟΡΙΖΟΝΤΑΣ", "", ""], 
            textposition="top center",
            textfont=dict(size=14, color="blue")
        ))
        
        # Σχεδιασμός Κατακόρυφων Γεωτρήσεων
        df_clean = df.dropna(subset=['Test ID', 'X-coordination'])
        unique_tests = df_clean[['Test ID', 'X-coordination']].drop_duplicates()
        
        for idx, row in unique_tests.iterrows():
            test_id = row['Test ID']
            x_pos = row['X-coordination']
            max_depth = df[df['Test ID'] == test_id]['Depth'].max()
            
            fig_3d.add_trace(go.Scatter3d(
                x=[x_pos, x_pos], y=[0, 0], z=[0, -max_depth],
                mode='lines+markers+text',
                line=dict(color='black', width=6),
                marker=dict(size=5, color='darkred'),
                text=[str(test_id), ""],
                textposition="top center",
                name=str(test_id)
            ))
            
        fig_3d.update_layout(
            scene=dict(
                xaxis=dict(title='Μήκος Χ (m)', range=[0, 450]),
                yaxis=dict(title='Πλάτος Υ (m)', range=[-10, 10]),
                zaxis=dict(title='Βάθος Ζ (m)', range=[-35, 5]),
                aspectratio=dict(x=3, y=1, z=1.2)
            ),
            height=650,
            margin=dict(r=10, l=10, b=10, t=10),
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
        )
        
        st.subheader("📦 Τρισδιάστατη Γεωτεχνική Μηκοτομή (Solid Layers)")
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
