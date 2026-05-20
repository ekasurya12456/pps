import streamlit as st
import pandas as pd
import plotly.express as px
import io

# Konfigurasi Halaman
st.set_page_config(page_title="Dashboard Monitoring Investasi PPS 2026", layout="wide")

# Menyembunyikan elemen default Streamlit (Header & Footer)
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

st.title("📊 Dashboard Monitoring Investasi 2026 - Divisi PPS (Editable)")
st.markdown("Monitoring & Pengeditan Rencana Anggaran (CAPEX) PLTA Siguragura & Tangga")

# Nama file CSV yang akan dibaca otomatis (Pastikan namanya sama persis di GitHub)
FILE_NAME = "Monitoring investasi 2026 - PPS (Update).xlsx - PPS.csv"

# 1. Inisialisasi Session State
if "sheets_data" not in st.session_state:
    st.session_state.sheets_data = {}
if "active_sheet" not in st.session_state:
    st.session_state.active_sheet = ""

# 2. Membaca file otomatis saat aplikasi pertama kali dibuka
if not st.session_state.sheets_data:
    try:
        # Mencoba membaca CSV
        df = pd.read_csv(FILE_NAME)
        
        # Mengecek apakah butuh skip baris (jika file mentah)
        if 'Item Investasi' not in df.columns:
            df = pd.read_csv(FILE_NAME, skiprows=3)
            
        # Membersihkan spasi di nama kolom
        df.columns = df.columns.str.strip()
        
        # Menyimpan ke memori aplikasi
        st.session_state.sheets_data["PPS Data"] = df
        st.session_state.active_sheet = "PPS Data"
        
    except FileNotFoundError:
        st.error(f"❌ File '{FILE_NAME}' tidak ditemukan di sistem. Pastikan Anda sudah mengunggahnya ke GitHub dengan nama yang sama persis.")
        st.stop()

# 3. Proses Manajemen Data & Tampilan
if st.session_state.sheets_data:
    
    # ==================== SIDEBAR: MANAJEMEN SHEET & KOLOM ====================
    st.sidebar.header("📁 Manajemen Sheet & Kolom")
    
    daftar_sheet = list(st.session_state.sheets_data.keys())
    st.session_state.active_sheet = st.sidebar.selectbox(
        "Pilih Sheet yang Ingin Diedit/Dilihat:", 
        daftar_sheet, 
        index=daftar_sheet.index(st.session_state.active_sheet)
    )
    
    df_aktif = st.session_state.sheets_data[st.session_state.active_sheet]
    
    st.sidebar.divider()
    
    st.sidebar.subheader("✨ Tambah Sheet Baru")
    new_sheet_name = st.sidebar.text_input("Nama Sheet Baru:", key="new_sheet")
    if st.sidebar.button("Tambah Sheet"):
        if new_sheet_name and new_sheet_name not in st.session_state.sheets_data:
            st.session_state.sheets_data[new_sheet_name] = pd.DataFrame(columns=df_aktif.columns)
            st.session_state.active_sheet = new_sheet_name
            st.rerun()
            
    st.sidebar.divider()
    
    st.sidebar.subheader("➕ Tambah Kolom Baru")
    new_col_name = st.sidebar.text_input("Nama Kolom Baru:", key="new_col")
    if st.sidebar.button("Tambah Kolom"):
        if new_col_name and new_col_name not in df_aktif.columns:
            df_aktif[new_col_name] = ""
            st.session_state.sheets_data[st.session_state.active_sheet] = df_aktif
            st.rerun()

    st.sidebar.divider()

    # ==================== AREA UTAMA: INPUT & EDIT DATA ====================
    st.subheader(f"📝 Manajemen Data Sheet: {st.session_state.active_sheet}")
    st.caption("Tips: Klik sel untuk mengubah nilai. Gulir ke paling bawah tabel untuk menambah baris baru. Pilih baris lalu tekan Delete untuk menghapus.")
    
    df_edited = st.data_editor(df_aktif, num_rows="dynamic", use_container_width=True)
    st.session_state.sheets_data[st.session_state.active_sheet] = df_edited
    
    # Standarisasi kolom untuk grafik
    df_edited.columns = df_edited.columns.str.strip()
    rkap_col = [col for col in df_edited.columns if 'RKAP' in str(col)]
    capex_col = [col for col in df_edited.columns if 'Total CAPEX Overall' in str(col)]
    
    if rkap_col:
        df_edited.rename(columns={rkap_col[0]: 'RKAP 2026'}, inplace=True)
    if capex_col:
        df_edited.rename(columns={capex_col[0]: 'Total CAPEX Overall (Versi 2026)'}, inplace=True)

    if 'RKAP 2026' in df_edited.columns:
        df_edited['RKAP 2026'] = pd.to_numeric(df_edited['RKAP 2026'], errors='coerce').fillna(0)
    if 'Total CAPEX Overall (Versi 2026)' in df_edited.columns:
        df_edited['Total CAPEX Overall (Versi 2026)'] = pd.to_numeric(df_edited['Total CAPEX Overall (Versi 2026)'], errors='coerce').fillna(0)

    # ==================== FILTER & VISUALISASI ====================
    st.divider()
    st.subheader("📊 Visualisasi Hasil Update")

    df_filtered = df_edited.copy()
    if "L2" in df_edited.columns and "L3" in df_edited.columns:
        st.sidebar.header("Filter Visualisasi")
        kategori_l2 = st.sidebar.multiselect("Pilih Kategori (L2):", options=df_edited["L2"].dropna().unique(), default=df_edited["L2"].dropna().unique())
        status_capex = st.sidebar.multiselect("Status Item (L3):", options=df_edited["L3"].dropna().unique(), default=df_edited["L3"].dropna().unique())
        df_filtered = df_edited[(df_edited["L2"].isin(kategori_l2)) & (df_edited["L3"].isin(status_capex))]

    if 'RKAP 2026' in df_filtered.columns and 'Total CAPEX Overall (Versi 2026)' in df_filtered.columns:
        col1, col2, col3 = st.columns(3)
        col1.metric("Total RKAP 2026 (Th.USD)", f"{df_filtered['RKAP 2026'].sum():,.2f}")
        col2.metric("Total CAPEX Overall (Th.USD)", f"{df_filtered['Total CAPEX Overall (Versi 2026)'].sum():,.2f}")
        col3.metric("Jumlah Item Investasi", len(df_filtered))

        col_chart1, col_chart2 = st.columns(2)
        if 'L3' in df_filtered.columns:
            with col_chart1:
                st.subheader("Distribusi Anggaran (L3)")
                fig_pie = px.pie(df_filtered, names='L3', values='RKAP 2026', hole=0.4, color_discrete_sequence=px.colors.sequential.Teal)
                st.plotly_chart(fig_pie, use_container_width=True)

        if 'Item Investasi' in df_filtered.columns:
            with col_chart2:
                st.subheader("Top 5 Item Investasi")
                top_5 = df_filtered.nlargest(5, 'RKAP 2026')
                fig_bar = px.bar(top_5, x='RKAP 2026', y='Item Investasi', orientation='h', color='RKAP 2026', color_continuous_scale='Blues')
                fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_bar, use_container_width=True)

        bulan_cols = ["2026-01-01", "2026-02-01", "2026-03-01", "2026-04-01", "2026-05-01", "2026-06-01", "2026-07-01", "2026-08-01", "2026-09-01", "2026-10-01", "2026-11-01", "2026-12-01"]
        bulan_tersedia = [col for col in bulan_cols if col in df_filtered.columns]
        
        if bulan_tersedia:
            st.subheader("📈 Rencana Serapan Anggaran per Bulan (2026)")
            for col in bulan_tersedia:
                df_filtered.loc[:, col] = pd.to_numeric(df_filtered[col], errors='coerce').fillna(0)
            total_per_bulan = df_filtered[bulan_tersedia].sum().reset_index()
            total_per_bulan.columns = ['Bulan', 'Total Anggaran']
            total_per_bulan['Bulan'] = pd.to_datetime(total_per_bulan['Bulan']).dt.strftime('%b %Y')

            fig_timeline = px.bar(total_per_bulan, x='Bulan', y='Total Anggaran', text='Total Anggaran', color_discrete_sequence=['#2CA02C'])
            fig_timeline.update_traces(texttemplate='%{text:,.1f}', textposition='outside')
            st.plotly_chart(fig_timeline, use_container_width=True)
    else:
        st.warning("Grafik tidak dapat ditampilkan karena kolom nominal angka tidak ada.")

    # ==================== TOMBOL SIMPAN ====================
    st.sidebar.divider()
    st.sidebar.header("💾 Simpan Hasil Kerja")
    
    output_excel = io.BytesIO()
    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
        for sheet_name, sheet_df in st.session_state.sheets_data.items():
            sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    st.sidebar.download_button(
        label="📥 Download & Save File Excel (.xlsx)",
        data=output_excel.getvalue(),
        file_name="Monitoring_Investasi_PPS_Updated.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
