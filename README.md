# 📊 Sistem Dashboard Ekonomi & Kelayakan Hidup

Aplikasi web interaktif berbasis **Python** dan **Streamlit** untuk mencatat, menganalisis, dan memproyeksikan kelayakan finansial individu. Sistem ini membandingkan beban pengeluaran riil masyarakat dengan standar Upah Minimum Regional (UMR) dan estimasi gaji sektoral.

Aplikasi ini terhubung secara *real-time* dengan basis data relasional di **TiDB Serverless (Cloud)**, memungkinkan operasi data yang aman dan terpusat.

🚀 **Jalankan Aplikasi Secara Live Di Sini:** [Sistem Dashboard Kelayakan Ekonomi](https://miniprojectdatabase-cs2zruxzyucegsdpjjpsgs.streamlit.app/)

---
## ✨ Fitur Utama
1. **Manajemen Data Penduduk & Transaksi (CRUD):** Formulir interaktif untuk registrasi data identitas, domisili, profesi, dan rincian pengeluaran.
2. **Simulasi Kelayakan Finansial:** Menghasilkan "Skor Kelayakan" dan memproyeksikan estimasi ekonomi jika pengguna berencana pindah ke provinsi atau profesi lain menggunakan perhitungan *Faktor Redaman*.
3. **Laporan Makroekonomi Daerah:** Dasbor analitik yang menyajikan agregasi data berupa rata-rata pengeluaran per kapita, perbandingan beban ekonomi (*Bar Chart*), dan distribusi kategori pengeluaran (*Pie Chart*).

## 📊 Metrik & Klasifikasi Indikator Kelayakan
Sistem ini mengkalkulasi skor kelayakan finansial menggunakan logika multi-aspek dengan bobot skor maksimal **9**. Klasifikasi akhir ditentukan berdasarkan akumulasi parameter berikut:

* **Layak (Skor 8 - 9):** Pendapatan jauh di atas UMR dan mampu menutup seluruh pengeluaran bulanan dengan rasio tabungan yang sehat.
* **Cukup (Skor 5 - 7):** Pendapatan memenuhi standar standar minimal hidup, namun ruang gerak finansial terbatas untuk alokasi tabungan atau investasi.
* **Tidak Layak (Skor 1 - 4):** Beban pengeluaran melebihi pendapatan riil atau berada di bawah garis batas UMR wilayah setempat.

Untuk rincian parameter bobot penilaian (Aspek Gaji vs UMR, Gaji vs Pengeluaran, dan UMR vs Pengeluaran), silakan merujuk pada dokumentasi tabel kriteria di bawah ini.

### Kriteria Penilaian Skor
<img width="552" height="320" alt="image" src="https://github.com/user-attachments/assets/048f2dd1-7b14-4911-aea8-d59d2f8e58da" />

### Dashboard Simulasi Kelayakan Finansial
<img width="1105" height="532" alt="image" src="https://github.com/user-attachments/assets/5587bdb2-6d50-4fb8-ae9c-f351b797d3c6" />

* Simulasi ketika pindah daerah dan ganti profesi :
  <img width="1202" height="347" alt="image" src="https://github.com/user-attachments/assets/f2cf766a-19d0-4eb6-9b1a-fa7f09eeefd2" />
  * Fitur simulasi memproyeksikan perubahan kelayakan jika pengguna pindah provinsi dan/atau berganti sektor profesi.
    
* Hasil :
  <img width="1087" height="550" alt="image" src="https://github.com/user-attachments/assets/8879a96f-41dc-47b8-94b0-ad4f8a0b843e" />
  <img width="1441" height="227" alt="image" src="https://github.com/user-attachments/assets/66aeca21-e20c-4d0f-a4e0-18bf75ed79d5" />
  * Sistem menampilkan perbandingan Skor Kelayakan Saat Ini vs Skor Proyeksi. Pengguna dapat melihat apakah pindah daerah/profesi akan meningkatkan atau menurunkan kelayakan.

## 🛠️ Tools yang Digunakan
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
git clone https://github.com/elfamada/miniprojectdatabase.git
cd miniprojectdatabase

```

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
