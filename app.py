import streamlit as st
import pymysql 
import pandas as pd
import random
import struct
from datetime import date

# ==============================================================================
# KONFIGURASI HALAMAN & KONEKSI DATABASE (TiDB)
# ==============================================================================
st.set_page_config(page_title="Dashboard Ekonomi & Biaya Hidup", layout="wide")

@st.cache_resource(ttl=300)
def init_connection():
    # Sesuaikan Host, User, dan Password dengan detail TiDB kamu
    return pymysql.connect(
        host="gateway01.ap-southeast-1.prod.alicloud.tidbcloud.com", 
        port=4000,
        user="3PvGrNdx75VzPfT.root", 
        password="n1zUMUL3OXtWwOhU", 
        database="test", 
        ssl={"ca": "isrgrootx1.pem"}, 
        autocommit=True 
    )

try:
    conn = init_connection()
except Exception as e:
    st.error(f"Gagal terhubung ke database cloud TiDB: {e}")
    st.stop()

def run_query(query, params=None):
    global conn
    try:
        # Pengecekan koneksi (ping) untuk memastikan koneksi tidak terputus (MySQL server has gone away)
        conn.ping(reconnect=True) 
        with conn.cursor() as cur:
            cur.execute(query, params)
            if cur.description:
                colnames = [desc[0] for desc in cur.description]
                return pd.DataFrame(cur.fetchall(), columns=colnames)
            return None
    except Exception as e:
        st.cache_resource.clear()
        st.warning("⚠️ Koneksi ke server cloud sempat tertidur. Sistem sedang memulihkan koneksi...")
        st.rerun()
        
# ==============================================================================
# FUNGSI PENDUKUNG
# ==============================================================================

def get_next_id_penduduk():
    result = run_query("SELECT COALESCE(MAX(id_penduduk), 0) + 1 AS next_id FROM Penduduk;")
    if result is not None and not result.empty:
        return int(result['next_id'].values[0])
    return 100001

def hitung_skor_kelayakan(gaji_sektor, umr, total_pengeluaran):
    if gaji_sektor < umr:
        skor_umr = 1
    elif gaji_sektor == umr:
        skor_umr = 2
    else:
        skor_umr = 3

    rasio_pasar = gaji_sektor / umr if umr > 0 else 1
    if rasio_pasar < 1.0:
        skor_pasar = 1
    elif rasio_pasar < 1.5:
        skor_pasar = 2
    else:
        skor_pasar = 3

    rasio_pengeluaran = (total_pengeluaran / gaji_sektor * 100) if gaji_sektor > 0 else 100
    if rasio_pengeluaran >= 90:
        skor_pengeluaran = 1
    elif rasio_pengeluaran >= 60:
        skor_pengeluaran = 2
    else:
        skor_pengeluaran = 3

    total_skor = skor_umr + skor_pasar + skor_pengeluaran

    if total_skor <= 4:
        kategori  = "Tidak Layak"
        warna     = "🔴"
        deskripsi = (
            f"Kondisi kritis. Pendapatan berada di bawah standar UMR atau "
            f"pengeluaran menghabiskan ≥90% gaji. "
            f"Rasio pengeluaran saat ini: **{rasio_pengeluaran:.1f}%**."
        )
    elif total_skor <= 7:
        kategori  = "Cukup"
        warna     = "🟡"
        deskripsi = (
            f"Kondisi aman namun terbatas. Gaji memenuhi UMR dan mampu menutup kebutuhan pokok, "
            f"namun ruang menabung masih mepet. "
            f"Rasio pengeluaran saat ini: **{rasio_pengeluaran:.1f}%**."
        )
    else:
        kategori  = "Layak"
        warna     = "🟢"
        deskripsi = (
            f"Kondisi finansial ideal (sejahtera). Gaji di atas UMR/pasar dan "
            f"pengeluaran terkendali dengan baik. "
            f"Rasio pengeluaran saat ini: **{rasio_pengeluaran:.1f}%**."
        )

    return {
        "total_skor"        : total_skor,
        "kategori"          : kategori,
        "warna"             : warna,
        "deskripsi"         : deskripsi,
        "skor_umr"          : skor_umr,
        "skor_pasar"        : skor_pasar,
        "skor_pengeluaran"  : skor_pengeluaran,
        "rasio_pengeluaran" : rasio_pengeluaran,
    }
def tampilkan_hasil_kelayakan(hasil):
    """Menampilkan kartu kelayakan beserta rincian skor."""
    if hasil["kategori"] == "Layak":
        st.success(f"{hasil['warna']} **Kesimpulan: {hasil['kategori']}** — Skor Total: **{hasil['total_skor']}/9**")
    elif hasil["kategori"] == "Cukup":
        st.warning(f"{hasil['warna']} **Kesimpulan: {hasil['kategori']}** — Skor Total: **{hasil['total_skor']}/9**")
    else:
        st.error(f"{hasil['warna']} **Kesimpulan: {hasil['kategori']}** — Skor Total: **{hasil['total_skor']}/9**")

    st.write(hasil["deskripsi"])

    df_skor = pd.DataFrame({
        "Aspek Penilaian": [
            "Gaji vs UMR Daerah",
            "Gaji vs Standar Pasar (1.5× UMR)",
            "Efisiensi Pengeluaran (Rasio Belanja/Gaji)",
        ],
        "Skor (maks. 3)": [
            hasil["skor_umr"],
            hasil["skor_pasar"],
            hasil["skor_pengeluaran"],
        ],
        "Keterangan": [
            "Baik" if hasil["skor_umr"] == 3 else ("Pas UMR" if hasil["skor_umr"] == 2 else "Di bawah UMR"),
            "Di atas pasar" if hasil["skor_pasar"] == 3 else ("Setara pasar" if hasil["skor_pasar"] == 2 else "Di bawah pasar"),
            f"Rasio {hasil['rasio_pengeluaran']:.1f}% — "
            f"{'Hemat (<60%)' if hasil['skor_pengeluaran'] == 3 else ('Sedang (60-90%)' if hasil['skor_pengeluaran'] == 2 else 'Boros (≥90%)')}",
        ],
    })
    st.dataframe(df_skor, use_container_width=True, hide_index=True)
    progress_val = hasil["total_skor"] / 9
    st.progress(progress_val, text=f"Skor {hasil['total_skor']}/9 → {hasil['kategori']}")
    
# ==============================================================================
# NAVIGASI SIDEBAR
# ==============================================================================
st.sidebar.title("📌 Navigasi Sistem")

# Berikan nilai default awal jika aplikasi baru pertama dibuka
if "halaman_aktif" not in st.session_state:
    st.session_state["halaman_aktif"] = "🏠 Beranda"

# Gunakan list agar penamaan selalu konsisten dan tidak salah spasi
DAFTAR_HALAMAN = [
    "🏠 Beranda",
    "📝 Input Penduduk Baru",
    "🔄 Update & Simulasi Pindah",
    "📋 Kelayakan Penduduk",
    "📊 Report & Analisis Daerah",
]

menu = st.sidebar.radio(
    "Pilih Halaman:",
    DAFTAR_HALAMAN,
    key="halaman_aktif" # agar tombol di beranda bisa mengontrol sidebar
)

# Tarik data master untuk dropdown
df_provinsi = run_query("SELECT id_provinsi, nama_provinsi, umr FROM Provinsi ORDER BY nama_provinsi;")
df_profesi  = run_query("SELECT id_profesi, sektor_profesi, estimasi_gaji FROM Profesi ORDER BY sektor_profesi;")
df_kategori = run_query("SELECT id_kategori, nama_kategori, deskripsi FROM Kategori_Biaya ORDER BY id_kategori;")

# Reset data sesi update jika user berpindah dari halaman Update
if menu != DAFTAR_HALAMAN[2] and "upd_data" in st.session_state:
    del st.session_state["upd_data"]

if df_provinsi is None or df_provinsi.empty or df_profesi is None or df_profesi.empty or df_kategori is None or df_kategori.empty:
    st.error("🚨 PERINGATAN: Tabel master (Provinsi/Profesi/Kategori) di database TiDB masih kosong!")
    st.info("Silakan cek kembali proses eksekusi file .sql kamu di DBeaver.")
    st.stop()

# ==============================================================================
# HALAMAN 0 — BERANDA
# ==============================================================================

# 👇 1. Buat fungsi callback kecil ini di luar kolom
def ganti_halaman(nama_halaman):
    st.session_state["halaman_aktif"] = nama_halaman

if menu == DAFTAR_HALAMAN[0]: 
    st.title("🏠 Dashboard Ekonomi & Biaya Kelayakan Hidup")
    st.markdown(
        "Selamat datang di sistem analisis ekonomi dan biaya hidup berbasis data real-time. "
        "Pilih menu di bawah untuk mulai menggunakan sistem."
    )
    st.markdown("---")

    col1, col2 = st.columns(2)
    col3, col4 = st.columns(2)

    with col1:
        st.markdown("### 📝 Input Penduduk Baru")
        st.write("Daftarkan data penduduk baru beserta rincian pengeluaran bulanan mereka. ID penduduk digenerate otomatis dan unik.")
        # 👇 2. Tombol diubah: hapus 'if', gunakan 'on_click' dan 'args'
        st.button(
            "Buka Halaman Input →", 
            use_container_width=True, 
            key="btn_input", 
            on_click=ganti_halaman, 
            args=(DAFTAR_HALAMAN[1],) 
        )

    with col2:
        st.markdown("### 🔄 Update & Simulasi Pindah Provinsi")
        st.write("Perbarui data penduduk yang sudah ada. Simulasikan dampak pindah provinsi terhadap kelayakan hidup berdasarkan UMR baru dan proyeksi pengeluaran.")
        st.button(
            "Buka Halaman Update →", 
            use_container_width=True, 
            key="btn_update", 
            on_click=ganti_halaman, 
            args=(DAFTAR_HALAMAN[2],)
        )

    with col3:
        st.markdown("### 📋 Kelayakan Penduduk")
        st.write("Cek status kelayakan hidup seorang penduduk berdasarkan ID-nya. Data dianalisis berdasarkan gaji sektoral, UMR, pengeluaran, serta Faktor Alpha (α).")
        st.button(
            "Buka Halaman Kelayakan →", 
            use_container_width=True, 
            key="btn_layak", 
            on_click=ganti_halaman, 
            args=(DAFTAR_HALAMAN[3],)
        )

    with col4:
        st.markdown("### 📊 Report & Analisis Daerah")
        st.write("Lihat laporan makroekonomi agregat per provinsi: grafik UMR vs pengeluaran, distribusi kategori belanja, dan tren keuangan masyarakat.")
        st.button(
            "Buka Halaman Report →", 
            use_container_width=True, 
            key="btn_report", 
            on_click=ganti_halaman, 
            args=(DAFTAR_HALAMAN[4],)
        )

    st.markdown("---")
    # Statistik ringkas di beranda
    res_total = run_query("SELECT COUNT(*) as total FROM Penduduk;")
    res_prov  = run_query("SELECT COUNT(*) as total FROM Provinsi;")
    total_penduduk = int(res_total['total'].values[0]) if res_total is not None and not res_total.empty else 0
    total_prov_db  = int(res_prov['total'].values[0])  if res_prov  is not None and not res_prov.empty  else 0

    s1, s2, s3 = st.columns(3)
    s1.metric("Total Penduduk Terdata", f"{total_penduduk:,} Orang")
    s2.metric("Provinsi Terdaftar",     f"{total_prov_db} Provinsi")
    s3.metric("Tanggal Akses",          str(date.today()))
# ==============================================================================
# HALAMAN 1 — INPUT PENDUDUK BARU
# ==============================================================================
elif menu == "📝 Input Penduduk Baru":
    st.button("⬅️ Kembali ke Beranda", on_click=ganti_halaman, args=(DAFTAR_HALAMAN[0],), key="back_input")
    st.title("📝 Input Data Penduduk Baru")
    st.write("Formulir untuk mendaftarkan penduduk baru beserta rincian pengeluaran bulanannya.")

    if 'temp_pengeluaran' not in st.session_state:
        st.session_state.temp_pengeluaran = {}

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("A. Identitas Penduduk")

        # ID otomatis — hanya ditampilkan, tidak bisa diedit
        next_id = get_next_id_penduduk()
        st.markdown(
            f"""
            <div style="
                background: #1e3a5f;
                border: 1.5px solid #2e86de;
                border-radius: 8px;
                padding: 10px 16px;
                margin-bottom: 12px;
            ">
                <span style="color:#a8c6e8; font-size:13px;">🆔 ID Penduduk (Otomatis & Unik)</span><br>
                <span style="color:#ffffff; font-size:22px; font-weight:700; letter-spacing:2px;">{next_id}</span><br>
                <span style="color:#7f9fc0; font-size:11px;">Digenerate otomatis dari database — tidak dapat diubah</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        nama_penduduk = st.text_input("Nama Lengkap Penduduk", placeholder="Contoh: Budi Santoso")
        usia = st.number_input("Usia (Tahun)", min_value=15, max_value=90, value=25)

        pilihan_prov = st.selectbox("Domisili Provinsi", df_provinsi['nama_provinsi'])
        row_prov = df_provinsi[df_provinsi['nama_provinsi'] == pilihan_prov].iloc[0]
        st.caption(f"UMR Provinsi terpilih: Rp{int(row_prov['umr']):,}")

        pilihan_prof = st.selectbox("Sektor Profesi", df_profesi['sektor_profesi'])
        row_prof = df_profesi[df_profesi['sektor_profesi'] == pilihan_prof].iloc[0]
        st.caption(f"Estimasi Gaji Sektoral (BPS): Rp{int(row_prof['estimasi_gaji']):,}")

    with col2:
        st.subheader("B. Rincian Pengeluaran Bulanan")

        pilihan_kat = st.selectbox("Pilih Kategori Pengeluaran", df_kategori['nama_kategori'])
        row_kat = df_kategori[df_kategori['nama_kategori'] == pilihan_kat].iloc[0]
        st.info(f"**Deskripsi:** {row_kat['deskripsi']}")

        nominal_input = st.number_input("Nominal Pengeluaran (Rp)", min_value=0, step=50000, value=0)

        c1, c2 = st.columns(2)
        with c1:
            if st.button("➕ Tambah Kategori"):
                if nominal_input > 0:
                    st.session_state.temp_pengeluaran[int(row_kat['id_kategori'])] = int(nominal_input)
                    st.toast(f"Ditambahkan: {pilihan_kat}")
                else:
                    st.warning("Nominal harus lebih dari 0.")
        with c2:
            if st.button("🎲 Auto-Generate Biaya"):
                gaji = row_prof['estimasi_gaji']
                st.session_state.temp_pengeluaran = {
                    301: int(gaji * random.uniform(0.25, 0.35)),
                    302: int(gaji * random.uniform(0.20, 0.30)),
                    303: int(gaji * random.uniform(0.08, 0.15)),
                    307: int(gaji * random.uniform(0.05, 0.10)),
                    310: int(gaji * random.uniform(0.05, 0.12)),
                }
                st.toast("Pengeluaran otomatis dibuat!")

        if st.session_state.temp_pengeluaran:
            rows_tmp = []
            total_tmp = 0
            for k_id, nom in st.session_state.temp_pengeluaran.items():
                nama_k_arr = df_kategori[df_kategori['id_kategori'] == k_id]['nama_kategori'].values
                nama_k = nama_k_arr[0] if len(nama_k_arr) > 0 else f"ID {k_id}"
                rows_tmp.append({"Kategori": nama_k, "Nominal": f"Rp{nom:,}"})
                total_tmp += nom
            st.table(pd.DataFrame(rows_tmp))
            st.metric("Total Sementara", f"Rp{total_tmp:,}")

            if st.button("🗑️ Kosongkan"):
                st.session_state.temp_pengeluaran = {}
                st.rerun()

    st.markdown("---")
    if st.button("💾 SIMPAN KE DATABASE", use_container_width=True):
        if not nama_penduduk.strip():
            st.error("Nama penduduk tidak boleh kosong!")
        elif not st.session_state.temp_pengeluaran:
            st.error("Masukkan minimal satu pengeluaran sebelum menyimpan!")
        else:
            try:
                id_final = get_next_id_penduduk()
                # TIDAK PERLU MENGUBAH %s KARENA PYMYSQL JUGA MENGGUNAKAN %s
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO Penduduk (id_penduduk, nama_penduduk, usia, id_provinsi, id_profesi) "
                        "VALUES (%s, %s, %s, %s, %s);",
                        (id_final, nama_penduduk.strip(), int(usia),
                         int(row_prov['id_provinsi']), int(row_prof['id_profesi']))
                    )
                    for k_id, nom in st.session_state.temp_pengeluaran.items():
                        cur.execute(
                            "INSERT INTO Pengeluaran (tanggal_catat, nominal, id_penduduk, id_kategori) "
                            "VALUES (%s, %s, %s, %s);",
                            (date.today(), int(nom), id_final, int(k_id))
                        )
                st.success(f"✅ Data **{nama_penduduk}** berhasil disimpan dengan ID **{id_final}**.")
                st.info("🔒 Simpan ID ini untuk keperluan pengecekan kelayakan atau update data di kemudian hari.")
                st.session_state.temp_pengeluaran = {}
            except Exception as ex:
                st.error(f"Gagal menyimpan. Transaksi dibatalkan. Error: {ex}")

# ==============================================================================
# HALAMAN 2 — UPDATE & SIMULASI PINDAH PROVINSI
# ==============================================================================
elif menu == "🔄 Update & Simulasi Pindah":
    st.button("⬅️ Kembali ke Beranda", on_click=ganti_halaman, args=(DAFTAR_HALAMAN[0],), key="back_update")
    st.title("🔄 Update Data & Simulasi Pindah Provinsi")
    st.write(
        "Masukkan ID Penduduk untuk memperbarui data atau mensimulasikan dampak pindah provinsi "
        "terhadap proyeksi pengeluaran dan kelayakan hidup."
    )

    id_input_upd = st.number_input(
        "🔑 Masukkan ID Penduduk", min_value=1, step=1, value=1,
        help="ID penduduk diberikan saat pertama kali mendaftar."
    )

    if st.button("🔍 Cari Data Penduduk", key="cari_upd"):
        q = """
            SELECT pen.id_penduduk, pen.nama_penduduk, pen.usia,
                   prov.id_provinsi, prov.nama_provinsi, prov.umr,
                   prof.id_profesi, prof.sektor_profesi, prof.estimasi_gaji,
                   COALESCE(SUM(peng.nominal), 0) AS total_pengeluaran
            FROM Penduduk pen
            JOIN Provinsi prov ON pen.id_provinsi = prov.id_provinsi
            JOIN Profesi prof  ON pen.id_profesi  = prof.id_profesi
            LEFT JOIN Pengeluaran peng ON pen.id_penduduk = peng.id_penduduk
            WHERE pen.id_penduduk = %s
            GROUP BY pen.id_penduduk, pen.nama_penduduk, pen.usia,
                     prov.id_provinsi, prov.nama_provinsi, prov.umr,
                     prof.id_profesi, prof.sektor_profesi, prof.estimasi_gaji;
        """
        df_found = run_query(q, (int(id_input_upd),))
        if df_found is not None and not df_found.empty:
            st.session_state["upd_data"] = df_found.iloc[0].to_dict()
        else:
            st.error("ID Penduduk tidak ditemukan. Pastikan ID sudah benar.")
            if "upd_data" in st.session_state:
                del st.session_state["upd_data"]

    if "upd_data" in st.session_state:
        d = st.session_state["upd_data"]

        st.markdown("---")
        st.markdown(f"**Penduduk ditemukan:** {d['nama_penduduk']} | Usia: {d['usia']} thn")

        tab_update, tab_simulasi = st.tabs(["✏️ Update Data", "🗺️ Simulasi Pindah Provinsi"])

        # --- TAB UPDATE DATA ---
        with tab_update:
            st.subheader("✏️ Perbarui Informasi Penduduk")
            nama_baru = st.text_input("Nama Lengkap", value=d['nama_penduduk'])
            usia_baru = st.number_input("Usia", min_value=15, max_value=90, value=int(d['usia']))

            st.markdown("#### Opsi Pembaruan Spesifik")
            # Cekbox untuk menampilkan dropdown jika ingin diubah
            ubah_prov = st.checkbox("🏙️ Ubah Domisili Provinsi")
            if ubah_prov:
                sorted_prov_names = df_provinsi['nama_provinsi'].tolist()
                idx_default_prov = sorted_prov_names.index(d['nama_provinsi']) if d['nama_provinsi'] in sorted_prov_names else 0
                pilihan_prov_upd = st.selectbox("Pilih Provinsi Baru", df_provinsi['nama_provinsi'], index=idx_default_prov, key="prov_upd")
                row_prov_upd = df_provinsi[df_provinsi['nama_provinsi'] == pilihan_prov_upd].iloc[0]
                id_prov_final = int(row_prov_upd['id_provinsi'])
            else:
                id_prov_final = int(d['id_provinsi'])

            ubah_prof = st.checkbox("💼 Ubah Sektor Profesi")
            if ubah_prof:
                sorted_prof_names = df_profesi['sektor_profesi'].tolist()
                idx_default_prof = sorted_prof_names.index(d['sektor_profesi']) if d['sektor_profesi'] in sorted_prof_names else 0
                pilihan_prof_upd = st.selectbox("Pilih Profesi Baru", df_profesi['sektor_profesi'], index=idx_default_prof, key="prof_upd")
                row_prof_upd = df_profesi[df_profesi['sektor_profesi'] == pilihan_prof_upd].iloc[0]
                id_prof_final = int(row_prof_upd['id_profesi'])
            else:
                id_prof_final = int(d['id_profesi'])

            st.markdown("---")
            if st.button("💾 Simpan Perubahan Data", use_container_width=True):
                try:
                    with conn.cursor() as cur:
                        cur.execute(
                            "UPDATE Penduduk SET nama_penduduk=%s, usia=%s, id_provinsi=%s, id_profesi=%s "
                            "WHERE id_penduduk=%s;",
                            (nama_baru.strip(), int(usia_baru), id_prov_final, id_prof_final, int(d['id_penduduk']))
                        )
                    st.success("✅ Data berhasil diperbarui!")
                    del st.session_state["upd_data"] # Reset session agar memuat data terbaru
                    st.rerun()
                except Exception as ex:
                    st.error(f"Gagal update. Error: {ex}")

        # --- TAB SIMULASI ---
        with tab_simulasi:
            st.subheader("🗺️ Simulasi Perubahan Karir & Domisili")
            
            umr_lama  = float(d['umr'])
            gaji_sek  = float(d['estimasi_gaji'])
            pengeluaran_lama = float(d['total_pengeluaran'])

            st.info(
                f"**Kondisi Saat Ini**\n\n"
                f"🏙️ Provinsi: **{d['nama_provinsi']}** (UMR: Rp{umr_lama:,.0f})\n\n"
                f"💼 Profesi: **{d['sektor_profesi']}** (Gaji: Rp{gaji_sek:,.0f})\n\n"
                f"🛍️ Pengeluaran Bulanan: **Rp{pengeluaran_lama:,.0f}**"
            )

            st.markdown("#### ⚙️ Pilih Skenario Simulasi")
            c_sim1, c_sim2 = st.columns(2)
            with c_sim1:
                sim_prov = st.checkbox("✈️ Simulasi Pindah Provinsi")
            with c_sim2:
                sim_prof = st.checkbox("🏢 Simulasi Ganti Profesi")

            # Nilai default jika tidak dicentang
            umr_baru = umr_lama
            nama_prov_baru = d['nama_provinsi']
            gaji_dasar_baru = gaji_sek
            nama_prof_baru = d['sektor_profesi']

            if sim_prov:
                pilihan_prov_sim = st.selectbox("🏙️ Pilih Provinsi Tujuan", df_provinsi['nama_provinsi'], key="prov_sim")
                row_prov_sim = df_provinsi[df_provinsi['nama_provinsi'] == pilihan_prov_sim].iloc[0]
                umr_baru = float(row_prov_sim['umr'])
                nama_prov_baru = row_prov_sim['nama_provinsi']

            if sim_prof:
                pilihan_prof_sim = st.selectbox("💼 Pilih Profesi Tujuan", df_profesi['sektor_profesi'], key="prof_sim")
                row_prof_sim = df_profesi[df_profesi['sektor_profesi'] == pilihan_prof_sim].iloc[0]
                gaji_dasar_baru = float(row_prof_sim['estimasi_gaji'])
                nama_prof_baru = row_prof_sim['sektor_profesi']

            if not sim_prov and not sim_prof:
                st.warning("👈 Silakan centang setidaknya satu skenario simulasi di atas untuk melihat proyeksi.")
            else:
                # 1. Hitung delta UMR
                if umr_lama > 0:
                    delta_umr = (umr_baru - umr_lama) / umr_lama
                else:
                    delta_umr = 0
                persen_perubahan_umr = delta_umr * 100

                # 2. Proyeksi Pengeluaran (Naik mengikuti delta UMR)
                pengeluaran_proyeksi = pengeluaran_lama * (1 + delta_umr)

                # 3. Proyeksi Gaji Sistem (Menggunakan gaji_dasar profesi baru/lama dikali alpha dari inflasi kota)
                alpha = 0.5
                gaji_proyeksi_sistem = gaji_dasar_baru * (1 + (delta_umr * alpha))

                st.markdown("---")
                st.markdown("#### 💰 Penyesuaian Gaji")
                punya_tawaran = st.checkbox("Saya sudah tahu/memiliki tawaran nominal gaji baru")
                
                if punya_tawaran:
                    gaji_final = st.number_input(
                        "Masukkan Nominal Gaji Baru (Rp)", 
                        min_value=0, 
                        value=int(gaji_proyeksi_sistem),
                        step=100000
                    )
                    keterangan_gaji = "Gaji Faktual (Input Manual)"
                else:
                    gaji_final = gaji_proyeksi_sistem
                    keterangan_gaji = "Estimasi Gaji (Diredam α=0.5)"

                st.markdown("---")
                st.markdown("#### 📊 Hasil Proyeksi")

                pm1, pm2, pm3 = st.columns(3)
                pm1.metric(
                    "Perubahan UMR", 
                    f"Rp{umr_baru:,.0f}", 
                    delta=f"{persen_perubahan_umr:+.1f}%" if sim_prov else "Tetap"
                )
                pm2.metric(
                    "Proyeksi Pengeluaran Baru", 
                    f"Rp{pengeluaran_proyeksi:,.0f}", 
                    delta=f"Rp{pengeluaran_proyeksi - pengeluaran_lama:+,.0f}" if sim_prov else "Tetap"
                )
                pm3.metric(
                    keterangan_gaji, 
                    f"Rp{gaji_final:,.0f}", 
                    delta=f"Rp{gaji_final - gaji_sek:+,.0f}"
                )

                arah_pengeluaran = "naik" if pengeluaran_proyeksi > pengeluaran_lama else "turun"
                
                # Teks penjelasan otomatis menyesuaikan kondisi yang dipilih
                if sim_prov and sim_prof:
                    st.caption(f"Pindah ke **{nama_prov_baru}** & ganti profesi jadi **{nama_prof_baru}**. Pengeluaran {arah_pengeluaran} mengikuti UMR baru. Gaji disesuaikan dengan profesi baru dan diredam faktor $\\alpha=0.5$.")
                elif sim_prov:
                    st.caption(f"Pindah ke **{nama_prov_baru}** (Profesi sama). Pengeluaran {arah_pengeluaran} mengikuti UMR baru. Gaji diredam faktor $\\alpha=0.5$.")
                elif sim_prof:
                    st.caption(f"Ganti profesi jadi **{nama_prof_baru}** (Kota sama). Pengeluaran tetap, skor kelayakan berubah murni karena perubahan Gaji Dasar.")

                st.markdown("#### ⚖️ Kelayakan Hidup Pasca-Simulasi")
                hasil_sim = hitung_skor_kelayakan(gaji_final, umr_baru, pengeluaran_proyeksi)
                tampilkan_hasil_kelayakan(hasil_sim)

                if pengeluaran_lama > 0:
                    hasil_lama = hitung_skor_kelayakan(gaji_sek, umr_lama, pengeluaran_lama)
                    st.markdown("#### 🔁 Perbandingan Sebelum vs Sesudah")
                    cmp1, cmp2 = st.columns(2)
                    with cmp1:
                        st.markdown(f"**Saat ini**")
                        st.markdown(f"{hasil_lama['warna']} **{hasil_lama['kategori']}** — Skor {hasil_lama['total_skor']}/9")
                    with cmp2:
                        st.markdown(f"**Setelah Simulasi**")
                        st.markdown(f"{hasil_sim['warna']} **{hasil_sim['kategori']}** — Skor {hasil_sim['total_skor']}/9")

# ==============================================================================
# HALAMAN 3 — KELAYAKAN PENDUDUK
# ==============================================================================
elif menu == "📋 Kelayakan Penduduk":
    st.button("⬅️ Kembali ke Beranda", on_click=ganti_halaman, args=(DAFTAR_HALAMAN[0],), key="back_kelayakan")
    st.title("📋 Analisis Kelayakan Hidup Penduduk")
    st.write(
        "Masukkan ID Penduduk untuk melihat analisis kelayakan hidup berdasarkan "
        "gaji sektoral, UMR daerah, total pengeluaran bulanan, dan Faktor Alpha (α)."
    )
    st.caption("Pencarian menggunakan ID.")

    id_input_kel = st.number_input(
        "🔑 Masukkan ID Penduduk",
        min_value=1, step=1, value=1,
        help="ID Penduduk diberikan saat pertama kali mendaftar di sistem ini."
    )

    if st.button("🔍 Cek Kelayakan", use_container_width=True):
        q_kel = """
            SELECT pen.id_penduduk, pen.nama_penduduk, pen.usia,
                   prov.nama_provinsi, prov.umr,
                   prof.sektor_profesi, prof.estimasi_gaji,
                   COALESCE(SUM(peng.nominal), 0) AS total_pengeluaran
            FROM Penduduk pen
            JOIN Provinsi prov ON pen.id_provinsi = prov.id_provinsi
            JOIN Profesi prof  ON pen.id_profesi  = prof.id_profesi
            LEFT JOIN Pengeluaran peng ON pen.id_penduduk = peng.id_penduduk
            WHERE pen.id_penduduk = %s
            GROUP BY pen.id_penduduk, pen.nama_penduduk, pen.usia,
                     prov.nama_provinsi, prov.umr,
                     prof.sektor_profesi, prof.estimasi_gaji;
        """
        df_kel = run_query(q_kel, (int(id_input_kel),))

        if df_kel is None or df_kel.empty:
            st.error("ID Penduduk tidak ditemukan. Pastikan ID sudah benar.")
        else:
            r = df_kel.iloc[0]
            gaji        = float(r['estimasi_gaji'])
            umr         = float(r['umr'])
            total_bel   = float(r['total_pengeluaran'])

            st.markdown("---")
            st.markdown(
                f"**👤 {r['nama_penduduk']}** | Usia: {r['usia']} thn | "
                f"Provinsi: {r['nama_provinsi']} | Profesi: {r['sektor_profesi']}"
            )

            m1, m2, m3 = st.columns(3)
            m1.metric("Estimasi Gaji",      f"Rp{gaji:,.0f}")
            m2.metric("UMR Daerah",         f"Rp{umr:,.0f}")
            m3.metric("Total Pengeluaran",  f"Rp{total_bel:,.0f}")

            st.markdown("---")

            if total_bel == 0:
                st.warning("Belum ada data pengeluaran tercatat untuk penduduk ini. Kelayakan dihitung berdasarkan gaji vs UMR saja.")

            hasil = hitung_skor_kelayakan(gaji, umr, total_bel)
            tampilkan_hasil_kelayakan(hasil)

            st.markdown("---")
            st.subheader("📂 Rincian Pengeluaran per Kategori")
            q_detail_kel = """
                SELECT k.nama_kategori AS "Kategori", p.nominal AS "Nominal (Rp)", p.tanggal_catat AS "Tanggal"
                FROM Pengeluaran p
                JOIN Kategori_Biaya k ON p.id_kategori = k.id_kategori
                WHERE p.id_penduduk = %s
                ORDER BY p.nominal DESC;
            """
            df_detail_kel = run_query(q_detail_kel, (int(id_input_kel),))
            if df_detail_kel is not None and not df_detail_kel.empty:
                df_detail_kel["Nominal (Rp)"] = df_detail_kel["Nominal (Rp)"].apply(lambda x: f"Rp{int(x):,}")
                st.dataframe(df_detail_kel, use_container_width=True, hide_index=True)
            else:
                st.info("Tidak ada rincian pengeluaran tercatat.")

# ==============================================================================
# HALAMAN 4 — REPORT & ANALISIS DAERAH
# ==============================================================================
elif menu == "📊 Report & Analisis Daerah":
    st.button("⬅️ Kembali ke Beranda", on_click=ganti_halaman, args=(DAFTAR_HALAMAN[0],), key="back_report")
    st.title("📊 Dashboard Laporan Makroekonomi Daerah")
    st.write("Analisis agregasi real-time data pengeluaran masyarakat berbanding standar upah daerah.")

    res_total_warga       = run_query("SELECT COUNT(*) as total FROM Penduduk;")
    res_rata_pengeluaran  = run_query("SELECT AVG(nominal) as rata FROM Pengeluaran;")
    res_total_pengeluaran = run_query("SELECT SUM(nominal) as total FROM Pengeluaran;")

    total_warga       = int(res_total_warga['total'].values[0])   if res_total_warga        is not None and not res_total_warga.empty        else 0
    rata_nasional     = float(res_rata_pengeluaran['rata'].values[0])  if res_rata_pengeluaran  is not None and res_rata_pengeluaran['rata'].values[0]  is not None else 0
    total_pengeluaran = float(res_total_pengeluaran['total'].values[0]) if res_total_pengeluaran is not None and res_total_pengeluaran['total'].values[0] is not None else 0

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Responden Terdata",           f"{total_warga:,} Orang")
    m2.metric("Rata-rata Pengeluaran per Transaksi", f"Rp{int(rata_nasional):,}")
    m3.metric("Total Pengeluaran Nasional",        f"Rp{int(total_pengeluaran):,}")

    st.markdown("---")
    st.subheader("A. Grafik Perbandingan Komparasi Finansial Daerah")

    query_prov_chart = """
        SELECT
            pr.nama_provinsi,
            pr.umr,
            COALESCE(AVG(sub.total_belanja), 0)  AS rata_pengeluaran_warga,
            COALESCE(COUNT(sub.id_penduduk), 0)  AS jumlah_penduduk
        FROM Provinsi pr
        LEFT JOIN (
            SELECT p.id_provinsi, p.id_penduduk, SUM(peng.nominal) AS total_belanja
            FROM Penduduk p
            JOIN Pengeluaran peng ON p.id_penduduk = peng.id_penduduk
            GROUP BY p.id_provinsi, p.id_penduduk
        ) sub ON pr.id_provinsi = sub.id_provinsi
        GROUP BY pr.id_provinsi, pr.nama_provinsi, pr.umr
        ORDER BY pr.nama_provinsi;
    """
    df_chart = run_query(query_prov_chart)

    if df_chart is not None and not df_chart.empty and total_warga > 0:
        df_chart['umr']                    = df_chart['umr'].astype(float)
        df_chart['rata_pengeluaran_warga'] = df_chart['rata_pengeluaran_warga'].astype(float)

        tab1, tab2 = st.tabs(["📊 UMR vs Rata-rata Pengeluaran", "👤 Jumlah Penduduk per Provinsi"])

        with tab1:
            df_melted = df_chart.melt(
                id_vars=["nama_provinsi"],
                value_vars=["umr", "rata_pengeluaran_warga"],
                var_name="Metrik Finansial",
                value_name="Nilai (Rupiah)"
            )
            df_melted["Metrik Finansial"] = df_melted["Metrik Finansial"].map({
                "umr": "UMR Provinsi",
                "rata_pengeluaran_warga": "Rata-rata Pengeluaran Warga"
            })
            st.bar_chart(
                data=df_melted, x="nama_provinsi", y="Nilai (Rupiah)",
                color="Metrik Finansial", stack=False, use_container_width=True
            )
            st.caption("Perbandingan UMR daerah dengan rata-rata total pengeluaran bulanan per orang.")

        with tab2:
            df_jumlah = df_chart[["nama_provinsi", "jumlah_penduduk"]].copy()
            df_jumlah.columns = ["Provinsi", "Jumlah Penduduk"]
            st.bar_chart(data=df_jumlah, x="Provinsi", y="Jumlah Penduduk", use_container_width=True)
            st.caption("Distribusi jumlah responden yang terdata per provinsi.")

        st.write("**Tabel Ringkasan Komparasi Finansial:**")
        df_tbl = df_chart.copy()
        df_tbl.columns = ["Provinsi", "UMR (Rp)", "Rata-rata Pengeluaran (Rp)", "Jumlah Penduduk"]
        df_tbl["UMR (Rp)"]                   = df_tbl["UMR (Rp)"].apply(lambda x: f"Rp{int(x):,}")
        df_tbl["Rata-rata Pengeluaran (Rp)"] = df_tbl["Rata-rata Pengeluaran (Rp)"].apply(lambda x: f"Rp{int(x):,}")
        st.dataframe(df_tbl, use_container_width=True, hide_index=True)
    else:
        st.info("📈 Grafik akan muncul setelah data simulasi penduduk terisi.")

    st.markdown("---")
    st.subheader("B. Laporan Detail Struktur Pengeluaran per Daerah")
    pilihan_daerah = st.selectbox("Pilih Provinsi", df_provinsi['nama_provinsi'])

    row_prov_rpt  = df_provinsi[df_provinsi['nama_provinsi'] == pilihan_daerah].iloc[0]
    umr_daerah_rpt = float(row_prov_rpt['umr'])

    query_detail = """
        SELECT
            k.nama_kategori              AS "Kategori Pengeluaran",
            COUNT(p.id_pengeluaran)      AS "Jumlah Transaksi",
            SUM(p.nominal)               AS "Total Pengeluaran (Rp)",
            AVG(p.nominal)               AS "Rata-rata (Rp)",
            MIN(p.nominal)               AS "Min (Rp)",
            MAX(p.nominal)               AS "Maks (Rp)"
        FROM Pengeluaran p
        JOIN Kategori_Biaya k ON p.id_kategori  = k.id_kategori
        JOIN Penduduk pen     ON p.id_penduduk   = pen.id_penduduk
        JOIN Provinsi prov    ON pen.id_provinsi = prov.id_provinsi
        WHERE prov.nama_provinsi = %s
        GROUP BY k.nama_kategori
        ORDER BY SUM(p.nominal) DESC;
    """
    df_detail = run_query(query_detail, (pilihan_daerah,))

    if df_detail is not None and not df_detail.empty:
        total_daerah = df_detail["Total Pengeluaran (Rp)"].sum()

        ic1, ic2, ic3 = st.columns(3)
        ic1.metric("UMR Daerah",               f"Rp{umr_daerah_rpt:,.0f}")
        ic2.metric("Total Pengeluaran Kumulatif", f"Rp{int(total_daerah):,}")
        ic3.metric("Kategori Aktif",            f"{len(df_detail)}")

        rep1, rep2 = st.columns([1.2, 0.8])
        with rep1:
            st.write(f"**Tabel Alokasi — Provinsi {pilihan_daerah}:**")
            df_fmt = df_detail.copy()
            df_fmt["% dari Total"] = (df_fmt["Total Pengeluaran (Rp)"] / total_daerah * 100).round(1).astype(str) + "%"
            for col in ["Total Pengeluaran (Rp)", "Rata-rata (Rp)", "Min (Rp)", "Maks (Rp)"]:
                df_fmt[col] = df_fmt[col].apply(lambda x: f"Rp{int(x):,}")
            st.dataframe(df_fmt, use_container_width=True, hide_index=True)

        with rep2:
            st.write("**Distribusi Proporsi (%):**")
            df_pct = df_detail.copy()
            df_pct["Persentase (%)"] = (df_pct["Total Pengeluaran (Rp)"] / total_daerah * 100).round(2)
            df_pct = df_pct.rename(columns={"Kategori Pengeluaran": "Kategori"})
            st.bar_chart(
                data=df_pct[["Kategori", "Persentase (%)"]],
                x="Kategori", y="Persentase (%)", use_container_width=True
            )
            st.caption("Proporsi tiap kategori terhadap total pengeluaran daerah.")

        kat_terbesar = df_detail.iloc[0]["Kategori Pengeluaran"]
        val_terbesar = int(df_detail.iloc[0]["Total Pengeluaran (Rp)"])
        st.info(f"💡 Pengeluaran terbesar di **{pilihan_daerah}**: **{kat_terbesar}** — Rp{val_terbesar:,}")
    else:
        st.warning(f"⚠️ Belum ada data transaksi untuk daerah **{pilihan_daerah}**.")
        st.caption("Isi data terlebih dahulu melalui halaman Input Penduduk Baru.")
