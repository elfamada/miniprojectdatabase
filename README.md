# 📊 Sistem Dashboard Ekonomi & Kelayakan Hidup

Aplikasi web interaktif berbasis **Python** dan **Streamlit** untuk mencatat, menganalisis, dan memproyeksikan kelayakan finansial individu. Sistem ini membandingkan beban pengeluaran riil masyarakat dengan standar Upah Minimum Regional (UMR) dan estimasi gaji sektoral.

Aplikasi ini terhubung secara *real-time* dengan basis data relasional di **TiDB Serverless (Cloud)**, memungkinkan operasi data yang aman dan terpusat.

🚀 **Jalankan Aplikasi Secara Live Di Sini:** [Sistem Dashboard Kelayakan Ekonomi](https://miniprojectdatabase-cs2zruxzyucegsdpjjpsgs.streamlit.app/)

---

## ✨ Fitur Utama
... (lanjutkan ke bawah seperti draf sebelumnya) ...
## ✨ Fitur Utama
1. **Manajemen Data Penduduk & Transaksi (CRUD):** Formulir interaktif untuk registrasi data identitas, domisili, profesi, dan rincian pengeluaran.
2. **Simulasi Kelayakan Finansial:** Menghasilkan "Skor Kelayakan" dan memproyeksikan estimasi ekonomi jika pengguna berencana pindah ke provinsi atau profesi lain menggunakan perhitungan *Faktor Redaman*.
3. **Laporan Makroekonomi Daerah:** Dasbor analitik yang menyajikan agregasi data berupa rata-rata pengeluaran per kapita, perbandingan beban ekonomi (*Bar Chart*), dan distribusi kategori pengeluaran (*Pie Chart*).

## 🛠️ Teknologi yang Digunakan
* **Front-End & Komputasi:** [Streamlit](https://streamlit.io/), Python (Pandas, Matplotlib)
* **Back-End Database:** TiDB Serverless (MySQL Compatible)
* **Database Management:** DBeaver, PyMySQL

---

## 🚀 Cara Menjalankan Aplikasi Secara Lokal

Ikuti langkah-langkah di bawah ini untuk menjalankan *dashboard* ini di komputermu sendiri.

### 1. Prasyarat (*Prerequisites*)
Pastikan kamu telah menginstal:
* **Python** (Versi 3.9 atau lebih baru)
* **Git**

### 2. Kloning Repositori
Buka terminal (Command Prompt/PowerShell/Terminal) dan jalankan perintah berikut:
```bash
git clone [https://github.com/](https://github.com/)[username-github-kamu]/[nama-repositori-kamu].git
cd [nama-repositori-kamu]

```

*(Catatan: Ganti URL di atas dengan tautan repositori GitHub milikmu).*

### 3. Instalasi Dependensi

Instal semua *library* pendukung yang dibutuhkan menggunakan `pip`:

```bash
pip install -r requirements.txt

```

### 4. Konfigurasi Koneksi Database

Sistem ini membutuhkan koneksi ke *database* TiDB. Kamu perlu mengatur *secrets management* lokal untuk Streamlit:

1. Buat folder baru bernama `.streamlit` di dalam folder proyek ini.
2. Di dalam folder `.streamlit`, buat file bernama `secrets.toml`.
3. Isi file `secrets.toml` dengan format kredensial database kamu:
```toml
[mysql]
host = "gateway01.ap-southeast-1.prod.aws.tidbcloud.com"
port = 4000
database = "project-ekonomi-db"
user = "username_kamu"
password = "password_kamu"

```


4. Pastikan file sertifikat keamanan `isrgrootx1.pem` sudah berada di dalam folder utama proyek ini agar koneksi SSL berhasil.

### 5. Jalankan Aplikasi

Setelah semua siap, jalankan aplikasi Streamlit dengan perintah:

```bash
streamlit run app.py

```

Aplikasi akan secara otomatis terbuka di *browser* pada alamat `http://localhost:8501`.

---

## 📂 Struktur Repositori Utama

* `app.py` — Skrip utama yang berisi logika antarmuka UI/UX, routing halaman, dan fungsi komputasi.
* `requirements.txt` — Daftar pustaka Python yang dibutuhkan (streamlit, pandas, pymysql, matplotlib).
* `isrgrootx1.pem` — Sertifikat SSL untuk mengamankan koneksi ke *database cloud*.
* `README.md` — Dokumentasi proyek ini.

---

**Dikembangkan oleh:** [Kelompok 4 - Database untuk Sains Data ATA 25/26]
* Alya Nashwa Fathurohman 
* Elfa Nusuki Amada 
* Febinadia Salsabila 
* Siti Nurul Fajriah
* Anasya Numa Idellie P.K 
