import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# Ρύθμιση σελίδας Streamlit σε wide mode
st.set_page_config(page_title="3D Geotechnical Cross-Section & Slicing", layout="wide")

st.title("📦 Real-Data Τρισδιάστατο (3D) Γεωτεχνικό Μοντέλο (0-450m)")
st.write("Συμπαγής και ημιδιάφανη απεικόνιση των εδαφικών στρώσεων με τις πραγματικές κλίσεις του Υδροφόρου Ορίζοντα, τη δοκιμή CPT στα 280m, τοπικές ανωμαλίες και δυνατότητα δυναμικών τομών.")

# 1. Εισαγωγή Αρχείου Excel
uploaded_file = st.file_uploader("📂 Ανεβάστε το τελικό αρχείο Excel (.xlsx)", type=["xlsx"])

if uploaded_file is not None:
    try:
        # Ανάγνωση των δεδομένων
        df = pd.read_excel(uploaded_file)
        
        # ΑΥΣΤΗΡΟΣ ΚΑΘΑΡΙΣΜΟΣ ΣΤΗΛΩΝ: Αφαιρεί όλα τα διπλά/περιττά κενά για να ταιριάζει με το Excel
        df.columns = [col.strip() for col in df.columns]
        
        # Ομαλοποίηση των ονομάτων στηλών για να αποφευχθούν προβλήματα με κενά
        column_mapping = {}
        for col in df.columns:
            normalized = "".join(col.split()) # Αφαιρεί όλα τα κενά για τη σύγκριση
            if "TestID" in normalized:
                column_mapping[col] = "Test ID"
            elif "Xcoordination" in normalized:
                column_mapping[col] = "X-coordination"
            elif "Depth" in normalized:
                column_mapping[col] = "Depth"
            elif "Ncorrected" in normalized:
                column_mapping[col] = "N-corrected"
            elif "SufromSPT" in normalized:
                column_mapping[col] = "Su(from SPT)"
            elif "SufromVs" in normalized:
                column_mapping[col] = "Su (from Vs)"
            elif "VsfromCPT" in normalized:
                column_mapping[col] = "Vs (from CPT-qc)"
            elif "SufromCPT" in normalized:
                column_mapping[col] = "Su (from CPT-qc)"
            elif col == "Vs":
                column_mapping[col] = "Vs"
                
        df = df.rename(columns=column_mapping)
            
        # Μετατροπή όλων των αριθμητικών στηλών σε float
        fixed_cols = ['X-coordination', 'Depth', 'N-corrected', 'Su(from SPT)', 'Vs', 'Su (from Vs)', 'Vs (from CPT-qc)', 'Su (from CPT-qc)']
        for col in fixed_cols:
            if col in df.columns:
                if df[col].dtype == object:
                    df[col] = df[col].astype(str).str.replace(',', '.', regex=False)
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        st.success("Το αρχείο φορτώθηκε επιτυχώς!")
        
        # --- ΠΛΕΥΡΙΚΟ ΜΕΝΟΥ ΓΙΑ ΔΥΝΑΜΙΚΗ ΤΟΜΗ ---
        st.sidebar.header("✂️ Εργαλεία Γεωτεχνικής Τομής")
        enable_slice = st.sidebar.checkbox("Ενεργοποίηση Δυναμικής Τομής", value=False)
        
        slice_range = st.sidebar.slider(
            "Επιλέξτε τμήμα χάραξης για εμφάνιση (m):",
            min_value=0, max_value=450, value=(0, 450), step=10
        )
        
        min_x, max_x = slice_range if enable_slice else (0, 450)
        
        # Πραγματικά γεωλογικά δεδομένα και νέα ύψη υδροφόρου ανά γεώτρηση/δοκιμή
        x_points = np.array([0, 80, 180, 250, 280, 350, 450])
        z_water_pts = np.array([-1.20, -1.20, -0.30, -0.90, -0.75, -0.60, -0.60]) 
        
        # Όρια στρώσεων βάσει των γεωτρήσεων και της νέας δοκιμής CPT στα 280m
        z_layer1_pts = np.array([-9.5, -9.5, -8.5, -8.0, -10.0, -11.5, -11.5])  
        z_layer2_pts = np.array([-21.0, -21.0, -20.5, -20.0, -21.0, -21.5, -21.5]) 
        z_bottom_pts = np.array([-35.0, -35.0, -35.0, -35.0, -35.0, -35.0, -35.0]) 

        # Δημιουργία πυκνού 3D Grid προσαρμοσμένου στα όρια της τομής
        x_space = np.linspace(min_x, max_x, 40)
        y_space = np.linspace(-10, 10, 5)
        X_grid, Y_grid = np.meshgrid(x_space, y_space)
        
        # Παρεμβολή (Interpolation)
        Z_surface = np.zeros_like(X_grid)
        Z_water = np.tile(np.interp(x_space, x_points, z_water_pts), (len(y_space), 1))
        Z_layer1 = np.tile(np.interp(x_space, x_points, z_layer1_pts), (len(y_space), 1))
        Z_layer2 = np.tile(np.interp(x_space, x_points, z_layer2_pts), (len(y_space), 1))
        Z_bottom = np.tile(np.interp(x_space, x_points, z_bottom_pts), (len(y_space), 1))

        fig_3d = go.Figure()
        
        # --- ΣΧΕΔΙΑΣΗ ΣΤΡΩΣΕΩΝ ΩΣ ΗΜΙΔΙΑΦΑΝΟΙ ΣΥΜΠΑΓΕΙΣ ΟΓΚΟΥΣ ---
        for offset in np.linspace(0, 1, 6):
            Z_fill = Z_surface * (1 - offset) + Z_layer1 * offset
            fig_3d.add_trace(go.Surface(
                x=X_grid, y=Y_grid, z=Z_fill,
                colorscale=[[0, '#d2b48c'], [1, '#d2b48c']], opacity=0.30, showscale=False,
                name='Μαλακή Άργιλος / Ιλύς (CL/ML)', legendgroup='g1', showlegend=bool(offset==0)
            ))
        
        for offset in np.linspace(0, 1, 6):
            Z_fill = Z_layer1 * (1 - offset) + Z_layer2 * offset
            fig_3d.add_trace(go.Surface(
                x=X_grid, y=Y_grid, z=Z_fill,
                colorscale=[[0, '#ebdca5'], [1, '#ebdca5']], opacity=0.30, showscale=False,
                name='Συμπιεστή Άργιλος (CH/MH)', legendgroup='g2', showlegend=bool(offset==0)
            ))
        
        for offset in np.linspace(0, 1, 6):
            Z_fill = Z_layer2 * (1 - offset) + Z_bottom * offset
            fig_3d.add_trace(go.Surface(
                x=X_grid, y=Y_grid, z=Z_fill,
                colorscale=[[0, '#a9a9a9'], [1, '#a9a9a9']], opacity=0.30, showscale=False,
                name='Σκλήρη Μάργα (Stiff Marl)', legendgroup='g3', showlegend=bool(offset==0)
            ))

        # --- ΠΡΟΣΘΗΚΗ ΤΟΠΙΚΩΝ ΓΕΩΤΕΧΝΙΚΩΝ ΑΝΩΜΑΛΙΩΝ ---
        if min_x <= 80 <= max_x:
            x_anom1, y_anom1 = np.meshgrid(np.linspace(max(min_x, 65), min(max_x, 95), 5), np.linspace(-5, 5, 3))
            for idx, z_val in enumerate(np.linspace(-9.5, -6.5, 4)):
                fig_3d.add_trace(go.Surface(
                    x=x_anom1, y=y_anom1, z=np.full_like(x_anom1, z_val),
                    colorscale=[[0, '#ff4d4d'], [1, '#ff4d4d']], opacity=0.8, showscale=False,
                    name='⚠️ Ζώνη Μηδενικής Αντοχής (ΝΓ-1)', legendgroup='anom1', showlegend=bool(idx==0)
                ))

        if min_x <= 280 <= max_x:
            x_anom2, y_anom2 = np.meshgrid(np.linspace(max(min_x, 265), min(max_x, 295), 5), np.linspace(-5, 5, 3))
            for idx, z_val in enumerate(np.linspace(-20.0, -16.0, 4)):
                fig_3d.add_trace(go.Surface(
                    x=x_anom2, y=y_anom2, z=np.full_like(x_anom2, z_val),
                    colorscale=[[0, '#2ecc71'], [1, '#2ecc71']], opacity=0.8, showscale=False,
                    name='💪 Φακός Υψηλής Αντοχής (CPT)', legendgroup='anom2', showlegend=bool(idx==0)
                ))

        # --- ΥΔΡΟΦΟΡΟΣ ΟΡΙΖΟΝΤΑΣ (Διορθωμένο χωρίς διπλό name) ---
        w_mask = (x_points >= min_x) & (x_points <= max_x)
        if np.any(w_mask):
            fig_3d.add_trace(go.Scatter3d(
                x=x_points[w_mask], y=[0] * np.sum(w_mask), z=z_water_pts[w_mask],
                mode='lines+markers+text',
                line=dict(color='rgb(0, 80, 255)', width=12),
                marker=dict(size=8, color='darkblue', symbol='diamond'),
                text=["💧 ΥΔΡΟΦΟΡΟΣ" if i == len(x_points[w_mask])//2 else "" for i in range(len(x_points[w_mask]))],
                textposition="top center",
                name="Υδροφόρος Ορίζοντας"
            ))
        
        # Σχεδιασμός Κατακόρυφων Γεωτρήσεων & CPT
        df_clean = df.dropna(subset=['Test ID', 'X-coordination'])
        unique_tests = df_clean[['Test ID', 'X-coordination']].drop_duplicates()
        
        for idx, row in unique_tests.iterrows():
            t_id = row['Test ID']
            x_pos = row['X-coordination']
            if min_x <= x_pos <= max_x:
                max_depth = df[df['Test ID'] == t_id]['Depth'].max()
                line_color = 'darkblue' if 'CPT' in str(t_id) else 'black'
                fig_3d.add_trace(go.Scatter3d(
                    x=[x_pos, x_pos], y=[0, 0], z=[0, -max_depth],
                    mode='lines+markers+text',
                    line=dict(color=line_color, width=8),
                    marker=dict(size=6, color='darkred'),
                    text=[str(t_id), ""],
                    textposition="top center",
                    name=str(t_id),
                    showlegend=False
                ))
            
        fig_3d.update_layout(
            scene=dict(
                xaxis=dict(title='Μήκος Χ (m)', range=[min_x, max_x]),
                yaxis=dict(title='Πλάτος Υ (m)', range=[-10, 10]),
                zaxis=dict(title='Βάθος Ζ (m)', range=[-35, 5]),
                aspectratio=dict(x=3, y=1, z=2.2)
            ),
            height=700,
            margin=dict(r=10, l=10, b=10, t=10),
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
        )
        
        st.subheader("📦 Τρισδιάστατο Συμπαγές & Διαφανές Μοντέλο (Με δυνατότητα Τομής)")
        st.plotly_chart(fig_3d, use_container_width=True)
        
        # 3. 2D ΔΙΑΓΡΑΜΜΑΤΑ
        st.markdown("---")
        st.subheader("📈 Συγκριτικά Προφίλ Ιδιοτήτων με το Βάθος")
        
        selected_test = st.selectbox("🎯 Επιλέξτε Γεώτρηση ή Δοκιμή:", df['Test ID'].dropna().unique())
        test_data = df[df['Test ID'] == selected_test].sort_values(by='Depth')
        
        col1, col2 = st.columns(2)
        with col1:
            fig_vs = go.Figure()
            if 'CPT' in str(selected_test):
                if 'Vs (from CPT-qc)' in test_data.columns and test_data['Vs (from CPT-qc)'].notna().any():
                    fig_vs.add_trace(go.Scatter(x=test_data['Vs (from CPT-qc)'], y=-test_data['Depth'], mode='lines+markers', name='Vs από CPT-qc (m/s)', line=dict(color='darkcyan', width=3)))
            else:
                if 'Vs' in test_data.columns and test_data['Vs'].notna().any():
                    fig_vs.add_trace(go.Scatter(x=test_data['Vs'], y=-test_data['Depth'], mode='lines+markers', name='Vs από MASW (m/s)', line=dict(color='blue', width=3)))
            
            fig_vs.update_layout(title=f"Κατανομή Ταχύτητας Vs - {selected_test}", xaxis=dict(title="Vs (m/s)"), yaxis=dict(title="Βάθος (m)"), template="plotly_white")
            st.plotly_chart(fig_vs, use_container_width=True)
            
        with col2:
            fig_su = go.Figure()
            if 'CPT' in str(selected_test):
                if 'Su (from CPT-qc)' in test_data.columns and test_data['Su (from CPT-qc)'].notna().any():
                    fig_su.add_trace(go.Scatter(x=test_data['Su (from CPT-qc)'], y=-test_data['Depth'], mode='lines+markers', name='Su από CPT-qc', line=dict(color='red', width=3)))
            else:
                if 'Su(from SPT)' in test_data.columns and test_data['Su(from SPT)'].notna().any():
                    fig_su.add_trace(go.Scatter(x=test_data['Su(from SPT)'], y=-test_data['Depth'], mode='lines+markers', name='Su (από SPT)', line=dict(color='green', width=2)))
                if 'Su (from Vs)' in test_data.columns and test_data['Su (from Vs)'].notna().any():
                    fig_su.add_trace(go.Scatter(x=test_data['Su (from Vs)'], y=-test_data['Depth'], mode='lines+markers', name='Su (από Vs)', line=dict(color='purple', dash='dash', width=2)))
                
            fig_su.update_layout(title=f"Κατανομή Διατμητικής Αντοχής Su - {selected_test}", xaxis=dict(title="Su (kPa)"), yaxis=dict(title="Βάθος (m)"), template="plotly_white")
            st.plotly_chart(fig_su, use_container_width=True)
            
    except Exception as e:
        st.error(f"⚠️ Σφάλμα κατά την επεξεργασία: {e}")
else:
    st.info("💡 Η εφαρμογή είναι έτοιμη. Ανεβάστε το νέο αρχείο Excel για να δημιουργηθεί το μοντέλο.")
