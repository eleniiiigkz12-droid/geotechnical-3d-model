import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# Ρύθμιση σελίδας Streamlit σε wide mode για να χωράνε τα γραφήματα
st.set_page_config(page_title="3D Γεωτεχνικό Μοντέλο Έργου", layout="wide")

st.title("📦 Τρισδιάστατο (3D) Γεωτεχνικό Μοντέλο & Μηκοτομή Έργου (0-450m)")
st.write("Αναπτυχθηκε για τη συνδυαστικη αξιολογηση και οπτικοποιηση δεδομενων SPT, CPT και MASW κατα μηκος της χαραξης.")

# 1. Εισαγωγή Αρχείου Excel
uploaded_file = st.file_uploader("📂 Ανεβάστε το τελικό αρχείο Excel (.xlsx)", type=["xlsx"])

if uploaded_file is not None:
    try:
        # Ανάγνωση των δεδομένων από το Excel (διαβάζει όλες τις στήλες ως κείμενο αρχικά για να διορθώσει τα κόμματα)
        df = pd.read_excel(uploaded_file, dtype=str)
        
        # Αντικατάσταση του κόμματος με τελεία για τους δεκαδικούς αριθμούς και μετατροπή σε αριθμητικά δεδομένα
        cols_to_convert = ['X-coordination', 'Depth', 'N-corrected', 'Su(from SPT)', 'Vs', 'Su(from Vs)', 'CPT-qc', 'Su(from CPT-qc)']
        for col in cols_to_convert:
            if col in df.columns:
                df[col] = df[col].str.replace(',', '.', regex=False)
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        st.success("Το αρχείο φορτώθηκε και επεξεργάστηκε επιτυχώς!")
        
        # Προεπισκόπηση του πίνακα δεδομένων
        with st.expander("🔍 Προεπισκόπηση Πίνακα Δεδομένων Excel"):
            st.dataframe(df.head(15))
            
        # 2. Σχεδιασμός Τρισδιάστατου (3D) Γεωτεχνικού Μοντέλου
        st.subheader("📦 Τρισδιάστατο (3D) Μοντέλο Υπεδάφους και Στρωματογραφίας")
        st.write("💡 Μπορείτε να περιστρέψετε το μοντέλο με το ποντίκι σας, να κάνετε zoom και να δείτε πού τρυπάνε οι δοκιμές το έδαφος.")
        
        # Δημιουργία πλέγματος (Grid) για τις 3D επιφάνειες των στρώσεων
        x_space = np.linspace(0, 450, 50)
        y_space = np.linspace(-20, 20, 10)  # Υποτιθέμενο σταθερό πλάτος ζώνης έργου 40 μέτρων
        X_grid, Y_grid = np.meshgrid(x_space, y_space)
        
        fig_3d = go.Figure()
        
        # Προσθήκη 3D Επιφανειών για τις εδαφικές στρώσεις (Βάσει των γενικών ορίων)
        # Επιφάνεια 1: Φυσικό Έδαφος (Z = 0)
        fig_3d.add_trace(go.Surface(
            x=X_grid, y=Y_grid, z=np.zeros_like(X_grid),
            colorscale=[[0, 'rgba(210, 180, 140, 0.6)'], [1, 'rgba(210, 180, 140, 0.6)']],
            showscale=False, name='Μαλακή Άργιλος / Ιλύς (CL/ML)'
        ))
        
        # Επιφάνεια 2: Όριο Μαλακής/Συμπιεστής Αργίλου (Z = -9μ)
        fig_3d.add_trace(go.Surface(
            x=X_grid, y=Y_grid, z=np.full_like(X_grid, -9),
            colorscale=[[0, 'rgba(240, 230, 140, 0.6)'], [1, 'rgba(240, 230, 140, 0.6)']],
            showscale=False, name='Συμπιεστή Άργιλος (CH/MH)'
        ))
        
        # Επιφάνεια 3: Όριο Συμπιεστής Αργίλου/Μάργας (Z = -21μ)
        fig_3d.add_trace(go.Surface(
            x=X_grid, y=Y_grid, z=np.full_like(X_grid, -21),
            colorscale=[[0, 'rgba(169, 169, 169, 0.6)'], [1, 'rgba(169, 169, 169, 0.6)']],
            showscale=False, name='Σκλήρη Μάργα (Stiff Marl)'
        ))
        
        # Εύρεση των μοναδικών δοκιμών (Test ID) και των θέσεών τους (X-coordination)
        df_clean = df.dropna(subset=['Test ID', 'X-coordination'])
        unique_tests = df_clean[['Test ID', 'X-coordination']].drop_duplicates()
        
        # Τοποθέτηση των δοκιμών/γεωτρήσεων ως 3D κατακόρυφοι "πάσσαλοι"
        for idx, row in unique_tests.iterrows():
            test_id = row['Test ID']
            x_pos = row['X-coordination']
            
            # Εύρεση του μέγιστου βάθους της συγκεκριμένης δοκιμής
            max_depth = df[df['Test ID'] == test_id]['Depth'].max()
            if np.isnan(max_depth):
                max_depth = 20.0  # Default βάθος αν δεν βρεθεί τιμή
            
            fig_3d.add_trace(go.Scatter3d(
                x=[x_pos, x_pos], y=[0, 0], z=[0, -max_depth],
                mode='lines+markers',
                line=dict(color='black', width=7),
                marker=dict(size=4, color='darkred'),
                name=str(test_id),
                hoverinfo='text',
                hovertext=f"Δοκιμή: {test_id}<br>Θέση X: {x_pos}m<br>Τελικό Βάθος: {max_depth}m"
            ))
            
        # Ρυθμίσεις εμφάνισης του 3D διαγράμματος
        fig_3d.update_layout(
            scene=dict(
                xaxis=dict(title='Μήκος Χ (m)', range=[0, 450]),
                yaxis=dict(title='Πλάτος Υ (m)', range=[-20, 20]),
                zaxis=dict(title='Βάθος Ζ (m)', range=[-35, 2]),
                aspectratio=dict(x=3, y=1, z=1)
            ),
            height=600,
            margin=dict(r=10, l=10, b=10, t=10)
        )
        
        st.plotly_chart(fig_3d, use_container_width=True)
        
        # 3. Διαδραστική Επιλογή Δοκιμής και Σχεδιασμός 2D Διαγραμμάτων Βάθους
        st.markdown("---")
        st.subheader("📈 Συγκριτικά Προφίλ Ιδιοτήτων με το Βάθος")
        
        # Dropdown μενού για να επιλέγει ο χρήστης ποιο σημείο θέλει να μελετήσει
        selected_test = st.selectbox("🎯 Επιλέξτε Γεώτρηση ή Δοκιμή για προβολή των διαγραμμάτων της:", df['Test ID'].dropna().unique())
        
        # Φιλτράρισμα δεδομένων για την επιλεγμένη δοκιμή
        test_data = df[df['Test ID'] == selected_test].sort_values(by='Depth')
        
        # Δημιουργία 2 στηλών στην οθόνη για τα 2 παράλληλα γραφήματα
        col1, col2 = st.columns(2)
        
        with col1:
            # Γράφημα Α: Προφίλ Ταχυτήτων Vs
            fig_vs = go.Figure()
            
            # Σχεδιασμός Vs
            if 'Vs' in test_data.columns and test_data['Vs'].notna().any():
                fig_vs.add_trace(go.Scatter(
                    x=test_data['Vs'], y=-test_data['Depth'],
                    mode='lines+markers', name='Ταχύτητα Vs (m/s)', line=dict(color='blue', width=2)
                ))
                
            fig_vs.update_layout(
                title=f"Μεταβολή Ταχύτητας Vs με το Βάθος - {selected_test}",
                xaxis=dict(title="Vs (m/s)"),
                yaxis=dict(title="Βάθος (m)", range=[-35, 0]),
                template="plotly_white",
                height=500
            )
            st.plotly_chart(fig_vs, use_container_width=True)
            
        with col2:
            # Γράφημα Β: Προφίλ Διατμητικής Αντοχής Su
            fig_su = go.Figure()
            
            # Έλεγχος και σχεδιασμός Su από SPT
            if 'Su(from SPT)' in test_data.columns and test_data['Su(from SPT)'].notna().any():
                fig_su.add_trace(go.Scatter(
                    x=test_data['Su(from SPT)'], y=-test_data['Depth'],
                    mode='lines+markers', name='Su (από SPT)', line=dict(color='green', width=2)
                ))
            # Έλεγχος και σχεδιασμός Su από Vs
            if 'Su(from Vs)' in test_data.columns and test_data['Su(from Vs)'].notna().any():
                fig_su.add_trace(go.Scatter(
                    x=test_data['Su(from Vs)'], y=-test_data['Depth'],
                    mode='lines+markers', name='Su (από Vs)', line=dict(color='purple', width=2, dash='dash')
                ))
            # Έλεγχος και σχεδιασμός Su από CPT-qc
            if 'Su(from CPT-qc)' in test_data.columns and test_data['Su(from CPT-qc)'].notna().any():
                fig_su.add_trace(go.Scatter(
                    x=test_data['Su(from CPT-qc)'], y=-test_data['Depth'],
                    mode='lines+markers', name='Su (από CPT)', line=dict(color='red', width=2)
                ))
                
            fig_su.update_layout(
                title=f"Μεταβολή Διατμητικής Αντοχής Su με το Βάθος - {selected_test}",
                xaxis=dict(title="Su (kPa)"),
                yaxis=dict(title="Βάθος (m)", range=[-35, 0]),
                template="plotly_white",
                height=500
            )
            st.plotly_chart(fig_su, use_container_width=True)
            
    except Exception as e:
        st.error(f"⚠️ Παρουσιάστηκε σφάλμα κατά την επεξεργασία του αρχείου: {e}")
else:
    st.info("💡 Η εφαρμογή είναι έτοιμη. Ανεβάστε το τελικό αρχείο Excel (.xlsx) για να δημιουργηθεί το 3D μοντέλο και τα προφίλ βάθους.")
