import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(page_title="Dashboard Ekonomi & Biaya Hidup", layout="wide")

# Fungsi untuk mengeksekusi query langsung ke file .db
def run_query(query, params=()):
    # Menyambung ke file .db yang ada di folder yang sama
    conn = sqlite3.connect('ekonomi_biaya_hidup.db')
    
    try:
        if query.strip().upper().startswith("SELECT"):
            # Jika query membaca data (SELECT), gunakan Pandas
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            return df
        else:
            # Jika query mengubah data (INSERT, UPDATE, DELETE)
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            conn.close()
            return True
    except Exception as e:
        st.error(f"Terjadi kesalahan pada database: {e}")
        conn.close()
        return None
# ==============================================================================
# 2. NAVIGASI SIDEBAR
# ==============================================================================
st.sidebar.title("📌 Navigasi Sistem")
menu = st.sidebar.radio("Pilih Halaman:", ["Formulir Simulasi Penduduk", "Report & Analisis Daerah"])

# Tarik data master sekali di awal untuk kebutuhan dropdown aplikasi
df_provinsi = run_query("SELECT id_provinsi, nama_provinsi, umr FROM Provinsi ORDER BY nama_provinsi;")
df_profesi = run_query("SELECT id_profesi, sektor_profesi, estimasi_gaji FROM Profesi ORDER BY sektor_profesi;")
df_kategori = run_query("SELECT id_kategori, nama_kategori, deskripsi FROM Kategori_Biaya ORDER BY id_kategori;")

# Cek apakah data benar-benar ada di database
if df_provinsi is None or df_provinsi.empty or df_profesi.empty or df_kategori.empty:
    st.error("🚨 PERINGATAN: Tabel master (Provinsi/Profesi/Kategori) di database Aiven masih kosong!")
    st.info("Silakan cek kembali proses import data CSV / eksekusi file .sql kamu. Pastikan perintah INSERT INTO berhasil dijalankan.")
    st.stop() # Menghentikan eksekusi kode ke bawah agar tidak muncul tulisan error merah

# ==============================================================================
# HALAMAN 1: FORMULIR SIMULASI PENDUDUK (INPUT DATA)
# ==============================================================================
if menu == "Formulir Simulasi Penduduk":
    st.title("📝 Simulasi Input Pengeluaran Penduduk")
    st.write("Halaman ini digunakan untuk mensimulasikan pencatatan pengeluaran bulanan penduduk.")

    # Inisialisasi session state untuk menampung input pengeluaran sementara di memori browser
    if 'temp_pengeluaran' not in st.session_state:
        st.session_state.temp_pengeluaran = {} # Struktur: {id_kategori: nominal}

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("A. Identitas Penduduk")        
        # Cek ID paling besar yang saat ini ada di database
        df_max_id = run_query("SELECT MAX(id_penduduk) as last_id FROM Penduduk;")
        
        # Ekstrak angkanya. Jika tabel kosong, kembalikan nilai None
        last_id_db = df_max_id['last_id'].values[0] if not df_max_id.empty else None
        
        # Validasi: Jika kosong atau ID terakhir di bawah 2024050, tetapkan baseline ke 2024050
        if pd.isna(last_id_db) or last_id_db < 2024050:
            last_id = 2024050
        else:
            last_id = int(last_id_db)
            
        # Buat ID baru dengan menambah 1 dari ID terakhir
        id_penduduk_baru = last_id + 1
        
        # Tampilkan di layar namun 'disabled' agar tidak bisa diubah manual oleh pengguna
        st.number_input("ID Penduduk (Otomatis & Unik)", value=id_penduduk_baru, disabled=True)
        
        nama_penduduk = st.text_input("Nama Lengkap Penduduk", placeholder="Contoh: Budi Santoso")
        usia = st.number_input("Usia (Tahun)", min_value=15, max_value=90, value=25)
        
        # Dropdown pilihan Provinsi
        pilihan_prov = st.selectbox("Domisili Provinsi", df_provinsi['nama_provinsi'])
        if pilihan_prov: # Pastikan ada yang dipilih
            row_prov = df_provinsi[df_provinsi['nama_provinsi'] == pilihan_prov].iloc[0]
            st.caption(f"UMR Provinsi terpilih: Rp{row_prov['umr']:,}")
        
        # Dropdown pilihan Profesi Sektoral
        pilihan_prof = st.selectbox("Sektor Profesi", df_profesi['sektor_profesi'])
        if pilihan_prof:
            row_prof = df_profesi[df_profesi['sektor_profesi'] == pilihan_prof].iloc[0]
            st.caption(f"Estimasi Gaji Sektoral (BPS): Rp{row_prof['estimasi_gaji']:,}")

    with col2:
        st.subheader("B. Rincian Pengeluaran Bulanan")
        
        # MASUKAN DOSEN #1: Dropdown Kategori dan memunculkan deskripsinya secara dinamis
        pilihan_kat = st.selectbox("Pilih Kategori Pengeluaran", df_kategori['nama_kategori'])
        row_kat = df_kategori[df_kategori['nama_kategori'] == pilihan_kat].iloc[0]
        
        # Menampilkan deskripsi kategori otomatis di kotak informasi
        st.info(f"**Deskripsi Kategori:** {row_kat['deskripsi']}")
        
        nominal_input = st.number_input("Masukkan Nominal Pengeluaran (Rp)", min_value=0, step=50000, value=0)
        
        # Menambahkan baris pengeluaran secara dinamis ke tabel sementara
        c_btn1, c_btn2 = st.columns(2)
        with c_btn1:
            if st.button("➕ Tambah Kategori"):
                if nominal_input > 0:
                    st.session_state.temp_pengeluaran[row_kat['id_kategori']] = nominal_input
                    st.toast(f"Berhasil menambahkan pengeluaran {pilihan_kat}!")
                else:
                    st.warning("Nominal harus lebih besar dari 0.")
                    
        # Tombol Auto-Generate Pengeluaran Acak Berbobot Logis
        with c_btn2:
            if st.button("🎲 Auto-Generate Semua Biaya"):
                gaji_acuan = row_prof['estimasi_gaji']
                # Logika pembagian alokasi acak berdasarkan porsi gaji bulanan
                st.session_state.temp_pengeluaran = {
                    301: int(gaji_acuan * random.uniform(0.25, 0.35)), # Hunian
                    302: int(gaji_acuan * random.uniform(0.20, 0.30)), # Makanan
                    303: int(gaji_acuan * random.uniform(0.08, 0.15)), # Transportasi
                    307: int(gaji_acuan * random.uniform(0.05, 0.10)), # Hiburan
                    310: int(gaji_acuan * random.uniform(0.05, 0.12))  # Tabungan
                }
                st.toast("Pengeluaran otomatis berhasil dibuat!")

        # Menampilkan tabel data pengeluaran sementara yang sedang diisi
        if st.session_state.temp_pengeluaran:
            st.write("**Daftar Pengeluaran Sementara:**")
            data_tabel_temp = []
            total_sementara = 0
            for k_id, nom in st.session_state.temp_pengeluaran.items():
                nama_k = df_kategori[df_kategori['id_kategori'] == k_id]['nama_kategori'].values[0]
                data_tabel_temp.append({"Kategori": nama_k, "Nominal (Rp)": nom})
                total_sementara += nom
                
            st.table(pd.DataFrame(data_tabel_temp))
            st.metric("Total Pengeluaran Saat Ini", f"Rp{total_sementara:,}")
            
            if st.button("🗑️ Kosongkan Pengeluaran"):
                st.session_state.temp_pengeluaran = {}
                st.rerun()

    # BUTTON FINAL: Menyimpan seluruh rangkaian input sekaligus menggunakan skema Transaksi SQL
    st.markdown("---")
    if st.button("💾 SIMPAN SELURUH DATA KE CLOUD DATABASE", use_container_width=True):
        if not nama_penduduk:
            st.error("Nama penduduk tidak boleh kosong!")
        elif not st.session_state.temp_pengeluaran:
            st.error("Masukkan minimal satu kategori pengeluaran sebelum menyimpan!")
        else:
            try:
                with conn.cursor() as cur:
                    # Perintah 1: Insert ke tabel Penduduk
                    cur.execute(
                        "INSERT INTO Penduduk (id_penduduk, nama_penduduk, usia, id_provinsi, id_profesi) VALUES (%s, %s, %s, %s, %s);",
                        (id_penduduk_baru, nama_penduduk, usia, int(row_prov['id_provinsi']), int(row_prof['id_profesi']))
                    )
                    
                    # Perintah 2: Looping insert ke tabel Pengeluaran
                    for k_id, nom in st.session_state.temp_pengeluaran.items():
                        cur.execute(
                            "INSERT INTO Pengeluaran (tanggal_catat, nominal, id_penduduk, id_kategori) VALUES (%s, %s, %s, %s);",
                            (date.today(), nom, id_penduduk_baru, k_id)
                        )
                # Commit transaksi jika seluruh perintah berhasil tanpa kendala
                conn.commit()
                st.success(f"Sukses Besar! Data {nama_penduduk} dan rekam pengeluarannya berhasil disimpan di Aiven Cloud.")
                # Reset penampung memori setelah sukses
                st.session_state.temp_pengeluaran = {}
            except Exception as ex:
                conn.rollback()
                st.error(f"Gagal menyimpan ke database, transaksi di-rollback. Error: {ex}")

# ==============================================================================
# HALAMAN 2: REPORT & ANALISIS DAERAH (VISUALISASI DASHBOARD)
# ==============================================================================
elif menu == "Report & Analisis Daerah":
    st.title("📊 Dashboard Laporan Makroekonomi Daerah")
    st.write("Analisis agregasi real-time data pengeluaran masyarakat berbanding standar upah daerah.")

    # Ambil metrik nasional
    res_total_warga = run_query("SELECT COUNT(*) as total FROM Penduduk;")
    total_warga = res_total_warga['total'].values[0] if not res_total_warga.empty else 0
    
    res_rata_pengeluaran = run_query("SELECT AVG(nominal) as rata FROM Pengeluaran;")
    rata_nasional = res_rata_pengeluaran['rata'].values[0] if not res_rata_pengeluaran.empty and res_rata_pengeluaran['rata'].values[0] is not None else 0

    # Tampilkan Ringkasan Metrik Utama
    m1, m2 = st.columns(2)
    m1.metric("Total Responden Terdata", f"{total_warga} Orang")
    m2.metric("Rata-rata Pengeluaran Item Transaksi", f"Rp{int(rata_nasional):,}")

    st.markdown("---")
    st.subheader("A. Grafik Perbandingan Komparasi Finansial Daerah")
    
    # Query SQL Canggih: Menghitung rata-rata total pengeluaran per orang di tiap provinsi
    query_prov_chart = """
        SELECT pr.nama_provinsi, pr.umr, COALESCE(AVG(sub.total_belanja), 0) as rata_pengeluaran_warga
        FROM Provinsi pr
        LEFT JOIN (
            SELECT p.id_provinsi, p.id_penduduk, SUM(peng.nominal) as total_belanja
            FROM Penduduk p
            JOIN Pengeluaran peng ON p.id_penduduk = peng.id_penduduk
            GROUP BY p.id_provinsi, p.id_penduduk
        ) sub ON pr.id_provinsi = sub.id_provinsi
        GROUP BY pr.id_provinsi, pr.nama_provinsi, pr.umr
        ORDER BY pr.nama_provinsi;
    """
    df_chart = run_query(query_prov_chart)

    if not df_chart.empty and total_warga > 0:
        # Manipulasi dataframe agar format pas untuk diagram batang bersebelahan di Streamlit
        df_chart_melted = df_chart.melt(id_vars=["nama_provinsi"], value_vars=["umr", "rata_pengeluaran_warga"], 
                                         var_name="Metrik Finansial", value_name="Nilai (Rupiah)")
        
        # Menampilkan grafik batang komparasi antar daerah
        st.bar_chart(data=df_chart_melted, x="nama_provinsi", y="Nilai (Rupiah)", color="Metrik Finansial", stack=False)
    else:
        st.info("Grafik analitik makro akan muncul di sini setelah data simulasi penduduk terisi.")

    st.markdown("---")
    # Tampilan report rincian spesifik daerah terpilih
    st.subheader("B. Laporan Detail Struktur Pengeluaran per Daerah")
    pilihan_daerah_report = st.selectbox("Pilih Provinsi yang Ingin Diedit/Dianalisis", df_provinsi['nama_provinsi'])
    
    query_detail_daerah = """
        SELECT k.nama_kategori as "Kategori Pengeluaran", SUM(p.nominal) as "Total Pengeluaran (Rp)", AVG(p.nominal) as "Rata-rata (Rp)"
        FROM Pengeluaran p
        JOIN Kategori_Biaya k ON p.id_kategori = k.id_kategori
        JOIN Penduduk pen ON p.id_penduduk = pen.id_penduduk
        JOIN Provinsi prov ON pen.id_provinsi = prov.id_provinsi
        WHERE prov.nama_provinsi = %s
        GROUP BY k.nama_kategori;
    """
    df_detail_daerah = run_query(query_detail_daerah, (pilihan_daerah_report,))

    if not df_detail_daerah.empty:
        col_rep1, col_rep2 = st.columns([1, 1])
        with col_rep1:
            st.write(f"Tabel Alokasi Pengeluaran Masyarakat Provinsi **{pilihan_daerah_report}**:")
            st.dataframe(df_detail_daerah, use_container_width=True, hide_index=True)
        with col_rep2:
            st.write("Proporsi Distribusi Pengeluaran:")
            # Memanfaatkan bar chart horizontal bawaan streamlit untuk memperlihatkan porsi pengeluaran terbesar daerah
            st.bar_chart(data=df_detail_daerah, x="Kategori Pengeluaran", y="Total Pengeluaran (Rp)")
    else:
        st.warning(f"Belum ada data transaksi penduduk yang tercatat untuk daerah {pilihan_daerah_report}.")
