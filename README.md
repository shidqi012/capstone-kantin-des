# 🍽️ Simulasi Antrian Kantin Jam Sibuk

**Capstone Project — Simulasi Sistem Unit 12**
Program Studi: Sistem Informasi

## Deskripsi

Studi simulasi **Discrete Event Simulation (DES)** untuk menganalisis dampak penambahan petugas pelayanan dan perubahan kebijakan antrean terhadap waktu tunggu pelanggan di kantin pada jam sibuk. Simulasi dilakukan untuk membantu pengelola kantin menentukan konfigurasi layanan yang paling efektif dalam mengurangi antrean, meningkatkan tingkat pelayanan, dan meminimalkan pelanggan yang meninggalkan antrean.

## Anggota Tim

| Nama          | NIM        | Peran                                       |
| ------------- | ---------- | ------------------------------------------- |
| Shidqi Andira | 2313000001 | Project Lead / Simulation Modeler           |
| Dela          | 2313000017 | Data Analyst / Documentation & Presentation |

### Deskripsi Peran

**Project Lead / Simulation Modeler (Shidqi Andira)**

* Menentukan ruang lingkup simulasi.
* Membuat model konseptual sistem antrean kantin.
* Mengembangkan kode simulasi menggunakan Python dan SimPy.
* Melakukan validasi model dan pengujian skenario.
* Mengintegrasikan hasil simulasi.

**Data Analyst / Documentation & Presentation (Dela)**

* Mengumpulkan dan mengolah data observasi.
* Melakukan analisis KPI hasil simulasi.
* Menyusun laporan proyek dan dokumentasi GitHub.
* Membuat visualisasi hasil simulasi.
* Menyiapkan presentasi akhir proyek.

## Cara Menjalankan Simulasi

### 1. Install Dependencies

```bash
pip install simpy numpy scipy pandas matplotlib
```

### 2. Jalankan Simulasi

```bash
python kantin_simulasi.py
```

### 3. Output

Program akan menghasilkan:

* Tabel KPI setiap skenario
* File hasil_simulasi_kantin.csv
* Grafik perbandingan kinerja setiap skenario

## Skenario yang Diuji

### S0 — Baseline

* 2 petugas pelayanan
* Sistem FCFS (First Come First Served)
* Kapasitas antrean 15 pelanggan

### S1 — Tambah Petugas

* 3 petugas pelayanan
* Sistem FCFS
* Kapasitas antrean 15 pelanggan

### S2 — Priority Queue

* 2 petugas pelayanan
* Priority Queue
* Kapasitas antrean 15 pelanggan

### S3 — Penambahan Kapasitas Antrean

* 2 petugas pelayanan
* Sistem FCFS
* Kapasitas antrean 25 pelanggan

### S4 — Optimal Combination

* 3 petugas pelayanan
* Priority Queue
* Kapasitas antrean 25 pelanggan

## KPI yang Diukur

* Average Waiting Time (Menit)
* Service Level (%)
* Drop Rate (%)
* Throughput
* Utilization Server (%)
* Queue Length P90

## Tools

* Python 3.x
* SimPy (Discrete Event Simulation Engine)
* NumPy
* Pandas
* SciPy
* Matplotlib
* GitHub

## Tujuan Simulasi

Menentukan konfigurasi layanan kantin yang paling optimal berdasarkan hasil simulasi sehingga:

* Waktu tunggu pelanggan dapat diminimalkan.
* Tingkat pelayanan meningkat.
* Jumlah pelanggan yang meninggalkan antrean berkurang.
* Utilisasi petugas tetap berada pada tingkat yang efisien.
* Pengelola kantin memiliki dasar kuantitatif dalam pengambilan keputusan operasional.
