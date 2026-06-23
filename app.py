import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# Ρύθμιση σελίδας Streamlit σε wide mode
st.set_page_config(page_title="3D Geotechnical Cross-Section & Slicing", layout="wide")

st.title("📦 Real-Data Τρισδιάστατο (3D) Γεωτεχνικό Μοντέλο (0-450m)")
st.write("Συμπαγής και ημιδιάφανη απεικόνιση των εδαφικών στρώσεων με Mesh3d, αποτύπωση πραγματικών κλίσεων/μεταβολών, τη δοκιμή CPT στα 280m, τοπικές ανωμαλίες και δυνατότητα δυναμικών τομών.")

# 1. Εισαγωγή Αρχείου Excel
uploaded_file = st.file_uploader("📂 Ανεβάστε το τελικό αρχείο Excel (.xlsx)", type=["xlsx"])

if uploaded_file is not None:
    try:
        # Ανάγνωση των δεδομένων
        df = pd.read_excel(uploaded_file)
        
        # Καθαρισμός στηλών από κενά στην αρχή και στο τέλος
        df.columns = [col.strip() for col in df.columns]
        
        # ΕΞΥΠΝΗ ΟΜΑΛΟΠΟΙΗΣΗ ΣΤΗΛΩΝ
        column_mapping = {}
        for col in df.columns:
            col_lower = col.lower()
            if "test" in col_lower and "id" in col_lower:
                column_mapping[col] = "Test ID"
            elif "x-coordin" in col_lower or "x coordin" in col_lower:
                column_mapping[col] = "X-coordination"
            elif "depth" in col_lower:
                column_mapping[col] = "Depth"
            elif "n-correct" in col_lower or "n correct" in col_lower:
                column_mapping[col] = "N-corrected"
            elif "spt" in col_lower:
                column_mapping[col] = "Su(from SPT)"
            elif "cpt" in col_lower and "su" in col_lower:
                column_mapping[col] = "Su (from CPT-qc)"
            elif "cpt" in col_lower and "vs" in col_lower:
                column_mapping[col] = "Vs (from CPT-qc)"
            elif "vs" in col_lower and "su" in col_lower:
                column_mapping[col] = "Su (from Vs)"
            elif col_lower == "vs":
                column_mapping[col] = "Vs"
                
        df = df.rename(columns=column_mapping)
            
        # Μετατροπή των στηλών που υπάρχουν όντως στο DataFrame σε αριθμούς
        for col in df.columns:
            if col in ['X-coordination', 'Depth', 'N-corrected', 'Su(from SPT)', 'Vs', 'Su (from Vs)', 'Vs (from CPT-qc)', 'Su (from CPT-qc)']:
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

        # Πυκνό πλέγμα σημείων (150 σημεία) για να αποτυπωθούν οι πραγματικές καμπύλες και αλλαγές πάχους
        x_space = np.linspace(min_x, max_x, 150)
        y_edges = np.array([-10, 10])
        
        # Υπολογισμός των υψών οροφής και πυθμένα με ρεαλιστική παρεμβολή
        z_surf_line = np.zeros_like(x_space)
        z_l1_line = np.interp(x_space, x_points, z_layer1_pts)
        z_l2_line = np.interp(x_space, x_points, z_layer2_pts)
        z_bot_line = np.interp(x_space, x_points, z_bottom_pts)

        # Συνάρτηση που δημιουργεί τις 3D συντεταγμένες για καμπύλες στρώσεις (Mesh3d)
        def create_curved_mesh(x_s, y_e, z_top_l, z_bot_l):
            n = len(x_s)
            # Κόμβοι οροφής (Y = -10 και Y = 10)
            x_top_y1 = x_s
            y_top_y1 = np.full(n, y_e[0])
            z_top_y1 = z_top_l
            
            x_top_y2 = x_s
            y_top_y2 = np.full(n, y_e[1])
            z_top_y2 = z_top_l
            
            # Κόμβοι πυθμένα (Y = -10 και Y = 10)
            x_bot_y1 = x_s
            y_bot_y1 = np.full(n, y_e[0])
            z_bot_y1 = z_bot_l
            
            x_bot_y2 = x_s
            y_bot_y2 = np.full(n, y_e[1])
            z_bot_y2 = z_bot_l
            
            x_nodes = np.concatenate([x_top_y1, x_top_y2, x_bot_y1, x_bot_y2])
            y_nodes = np.concatenate([y_top_y1, y_top_y2, y_bot_y1, y_bot_y2])
            z_nodes = np.concatenate([z_top_y1, z_top_y2, z_bot_y1, z_bot_y2])
            return x_nodes, y_nodes, z_nodes

        fig_3d = go.Figure()
        
        # --- ΣΧΕΔΙΑΣΗ ΣΤΡΩΣΕΩΝ ΩΣ ΣΥΜΠΑΓΕΙΣ ΚΑΜΠΥΛΩΤΕΣ ΟΓΚΟΥΣ ΜΕ MESH3D (Διορθώθηκαν όλες οι κλήσεις συναρτήσεων) ---
        
        # Στρώση 1: Μαλακή Άργιλος / Ιλύς (CL/ML) - Καφέ
        x_m1, y_m1, z_m1 = create_curved_mesh(x_space, y_edges, z_surf_line, z_l1_line)
        fig_3d.add_trace(go.Mesh3d(
            x=x_m1, y=y_m1, z=z_m1, color='#d2b48c', opacity=0.45, alphahull=0,
            name='Μαλακή Άργιλος / Ιλύς (CL/ML)', legendgroup='g1', showlegend=True
        ))
        
        # Στρώση 2: Συμπιεστή Άργιλος (CH/MH) - Κίτρινο
        x_m2, y_m2, z_m2 = create_curved_mesh(x_space, y_edges, z_l1_line, z_l2_line)
        fig_3d.add_trace(go.Mesh3d(
            x=x_m2, y=y_m2, z=z_m2, color='#ebdca5', opacity=0.45, alphahull=0,
            name='Συμπιεστή Άργιλος (CH/MH)', legendgroup='g2', showlegend=True
        ))
        
        # Στρώση 3: Σκληρή Μάζα (Stiff Marl) - Γκρι
        x_m3, y_m3, z_m3 = create_curved_mesh(x_space, y_edges, z_l2_line, z_bot_line)
        fig_3d.add_trace(go.Mesh3d(
            x=x_m3, y=y_m3, z=z_m3, color='#a9a9a9', opacity=0.45, alphahull=0,
            name='Σκλήρη Μάζα (Stiff Marl)', legendgroup='g3', showlegend=True
        ))

        # --- ΠΡΟΣΘΗΚΗ ΤΟΠΙΚΩΝ ΓΕΩΤΕΧΝΙΚΩΝ ΑΝΩΜΑΛΙΩΝ ---
        if min_x <= 80 <= max_x:
            x_a1 = np.array([65, 95, 65, 95, 65, 95, 65, 95])
            y_a1 = np.array([-5, -5, 5, 5, -5, -5, 5, 5])
            z_a1 = np.array([-6.5, -6.5, -6.5, -6.5, -9.5, -9.5, -9.5, -9.5])
            fig_3d.add_trace(go.Mesh3d(
                x=x_a1, y=y_a1, z=z_a1, color='#ff4d4d', opacity=0.85, alphahull=0,
                name='⚠️ Ζώνη Μηδενικής Αντοχής (ΝΓ-1)', legendgroup='anom1', showlegend=True
            ))

        if min_x <= 280 <= max_x:
            x_a2 = np.array([265, 295, 265, 295, 265, 295, 265, 295])
            y_a2 = np.array([-5, -5, 5, 5, -5, -5, 5, 5])
            z_a2 = np.array([-16.0, -16.0, -16.0, -16.0, -20.0, -20.0, -20.0, -20.0])
            fig_3d.add_trace(go.Mesh3d(
                x=x_a2, y=y_a2, z=z_a2, color='#2ecc71', opacity=0.85, alphahull=0,
                name='💪 Φακός Υψηλής Αντοχής (CPT)', legendgroup='anom2', showlegend=True
            ))

        # --- ΥΔΡΟΦΟΡΟΣ ΟΡΙΖΟΝΤΑΣ ---
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
        
        # 3. 2D ΔΙΑΓΡΑΜΜΑΤΑ (Διορθώθηκε η άνω-κάτω τελεία στο else:)
        st.markdown("---")
        st.subheader("📈 Συγκριτικά Προφίλ Ιδιοτήτων με το Βάθος")
        
        selected_test = st.selectbox("🎯 Επιλέξτε Γεώτρηση ή Δοκιμή:", df['Test ID'].dropna().unique())
        test_data = df[df['Test ID'] == selected_test].sort_values(by='Depth')
        
        col1, col2 = st.columns(2)
        with col1:
            fig_vs = go.Figure()
            if 'CPT' in str(selected_test):
                if 'Vs (from CPT-qc)' in test_data.columns:
                    cpt_vs_data = test_data.dropna(subset=['Vs (from CPT-qc)'])
                    if not cpt_vs_data.empty:
                        fig_vs.add_trace(go.Scatter(x=cpt_vs_data['Vs (from CPT-qc)'], y=-cpt_vs_data['Depth'], mode='lines+markers', name='Vs από CPT-qc (m/s)', line=dict(color='darkcyan', width=3)))
            else:
                if 'Vs' in test_data.columns:
                    masw_vs_data = test_data.dropna(subset=['Vs'])
                    if not masw_vs_data.empty:
                        fig_vs.add_trace(go.Scatter(x=masw_vs_data['Vs'], y=-masw_vs_data['Depth'], mode='lines+markers', name='Vs από MASW (m/s)', line=dict(color='blue', width=3)))
            
            fig_vs.update_layout(title=f"Κατανομή Ταχύτητας Vs - {selected_test}", xaxis=dict(title="Vs (m/s)"), yaxis=dict(title="Βάθος (m)"), template="plotly_white")
            st.plotly_chart(fig_vs, use_container_width=True)
            
        with col2:
            fig_su = go.Figure()
            if 'CPT' in str(selected_test):
                if 'Su (from CPT-qc)' in test_data.columns:
                    cpt_su_data = test_data.dropna(subset=['Su (from CPT-qc)'])
                    if not cpt_su_data.empty:
                        fig_su.add_trace(go.Scatter(x=cpt_su_data['Su (from CPT-qc)'], y=-cpt_su_data['Depth'], mode='lines+markers', name='Su από CPT-qc (kPa)', line=dict(color='red', width=3)))
            else:
                if 'Su(from SPT)' in test_data.columns:
                    spt_su_data = test_data.dropna(subset=['Su(from SPT)'])
                    if not spt_su_data.empty:
                        fig_su.add_trace(go.Scatter(x=spt_su_data['Su(from SPT)'], y=-spt_su_data['Depth'], mode='lines+markers', name='Su (από SPT)', line=dict(color='green', width=2)))
                
                if 'Su (from Vs)' in test_data.columns:
                    vs_su_data = test_data.dropna(subset=['Su (from Vs)'])
                    if not vs_su_data.empty:
                        fig_su.add_trace(go.Scatter(x=vs_su_data['Su (from Vs)'], y=-vs_su_data['Depth'], mode='lines+markers', name='Su (από Vs)', line=dict(color='purple', dash='dash', width=2)))
                
            fig_su.update_layout(title=f"Κατανομή Διατμητικής Αντοχής Su - {selected_test}", xaxis=dict(title="Su (kPa)"), yaxis=dict(title="Βάθος (m)"), template="plotly_white")
            st.plotly_chart(fig_su, use_container_width=True)
            
    except Exception as e:
        st.error(f"⚠️ Σφάλμα κατά την επεξεργασία: {e}")
else:
    st.info("💡 Η εφαρμογή είναι έτοιμη. Ανεβάστε το νέο αρχείο Excel για να δημιουργηθεί το μοντέλο.")
