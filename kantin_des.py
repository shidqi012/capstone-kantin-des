"""
=============================================================
  SIMULASI ANTRIAN PENDAFTARAN KLINIK - Discrete Event Simulation
  Capstone Project - Simulasi Sistem Unit 12
  
  Topik: Antrian Pendaftaran Pasien pada Jam Sibuk
  Metode: DES (Discrete Event Simulation) dengan SimPy
  
  Cara pakai:
    python clinic_des.py
  
  Requirements:
    pip install simpy numpy scipy pandas matplotlib
=============================================================
"""

import simpy
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
import json

# ─────────────────────────────────────────────────────────────
# 1. PARAMETER INPUT (bisa di-override per skenario)
# ─────────────────────────────────────────────────────────────
DEFAULT_PARAMS = {
    "arrival_rate"   : 12,    # λ = pasien per jam (jam sibuk)
    "service_rate"   : 12,    # μ = pasien per jam (= 1/5 menit per pasien)
    "num_servers"    : 1,     # c = jumlah petugas pendaftaran
    "queue_capacity" : 20,    # K = kapasitas antrian maksimum (pasien)
    "sim_duration"   : 180,   # T = durasi simulasi dalam MENIT
    "policy"         : "FCFS",# "FCFS" atau "PRIORITY"
    "random_seed"    : 42,
}

# Konversi ke menit (SimPy pakai satuan menit di sini)
# arrival_rate 12/jam = 12/60 per menit = 0.2 per menit
# inter_arrival = 1 / arrival_rate = 5 menit rata-rata


# ─────────────────────────────────────────────────────────────
# 2. STRUKTUR DATA HASIL SIMULASI
# ─────────────────────────────────────────────────────────────
class SimulationResults:
    def __init__(self):
        self.wait_times    = []   # Wq per pasien (menit)
        self.service_times = []   # Ws per pasien (menit)
        self.total_patients     = 0
        self.served_patients    = 0
        self.dropped_patients   = 0  # balk (antrian penuh)
        self.server_busy_time   = 0  # total waktu petugas sibuk (menit)
        self.sim_duration       = 0

    @property
    def drop_rate(self):
        if self.total_patients == 0:
            return 0
        return self.dropped_patients / self.total_patients * 100

    @property
    def avg_wait_time(self):
        if not self.wait_times:
            return 0
        return np.mean(self.wait_times)

    @property
    def p90_wait_time(self):
        if not self.wait_times:
            return 0
        return np.percentile(self.wait_times, 90)

    @property
    def throughput_per_hour(self):
        if self.sim_duration == 0:
            return 0
        return self.served_patients / (self.sim_duration / 60)

    @property
    def server_utilization(self):
        """Utilisasi petugas = total waktu sibuk / (jumlah server * durasi sim)"""
        # Dihitung di level simulasi
        return self.server_busy_time

    @property
    def service_level(self):
        """% pasien dilayani dalam < 15 menit"""
        if not self.wait_times:
            return 0
        within_sla = sum(1 for w in self.wait_times if w <= 15)
        return within_sla / len(self.wait_times) * 100


# ─────────────────────────────────────────────────────────────
# 3. PROSES DES (SimPy)
# ─────────────────────────────────────────────────────────────
def patient_arrival(env, results, server_resource, params, patient_id):
    """Proses setiap pasien yang tiba."""
    arrival_time = env.now

    # Cek kapasitas antrian (BALK jika penuh)
    if len(server_resource.queue) >= params["queue_capacity"]:
        results.dropped_patients += 1
        return  # pasien pergi (balk)

    # Masuk antrian, tunggu server tersedia
    with server_resource.request() as req:
        yield req
        wait_time = env.now - arrival_time
        results.wait_times.append(wait_time)

        # Layanan pendaftaran
        service_time = np.random.exponential(60 / params["service_rate"])
        yield env.timeout(service_time)

        results.service_times.append(service_time)
        results.served_patients += 1


def run_arrivals(env, results, server_resource, params):
    """Generator: hasilkan pasien satu per satu berdasarkan Poisson arrival."""
    patient_id = 0
    arrival_rate_per_min = params["arrival_rate"] / 60  # konversi ke per menit

    while True:
        # Inter-arrival time: Exponential distribution (Poisson process)
        inter_arrival = np.random.exponential(1 / arrival_rate_per_min)
        yield env.timeout(inter_arrival)

        results.total_patients += 1
        patient_id += 1
        env.process(patient_arrival(env, results, server_resource, params, patient_id))


# ─────────────────────────────────────────────────────────────
# 4. FUNGSI SATU REPLIKASI
# ─────────────────────────────────────────────────────────────
def run_single_replication(params, seed=None):
    """Jalankan satu replikasi simulasi dengan parameter tertentu."""
    if seed is not None:
        np.random.seed(seed)

    env = simpy.Environment()
    results = SimulationResults()
    results.sim_duration = params["sim_duration"]

    # Resource = petugas pendaftaran (c servers)
    server_resource = simpy.Resource(env, capacity=params["num_servers"])

    # Mulai proses arrival
    env.process(run_arrivals(env, results, server_resource, params))

    # Jalankan simulasi
    env.run(until=params["sim_duration"])

    # Hitung utilisasi: total waktu server sibuk / (c * T)
    # Estimasi dari service times yang selesai
    total_service = sum(results.service_times)
    results.server_busy_time = min(
        total_service / (params["num_servers"] * params["sim_duration"]) * 100, 100
    )

    return results


# ─────────────────────────────────────────────────────────────
# 5. FUNGSI BANYAK REPLIKASI (dengan CI)
# ─────────────────────────────────────────────────────────────
def run_scenario(params, n_replications=30, scenario_name="Baseline"):
    """
    Jalankan n_replications replikasi untuk satu skenario.
    Return: dict dengan rata-rata, std, dan CI 95% untuk tiap KPI.
    """
    print(f"\n{'='*55}")
    print(f"  Skenario: {scenario_name}")
    print(f"  Params  : {n_replications} replikasi, c={params['num_servers']} server, "
          f"λ={params['arrival_rate']}/jam, K={params['queue_capacity']}")
    print(f"{'='*55}")

    metrics = {
        "avg_wait_time"       : [],
        "p90_wait_time"       : [],
        "drop_rate"           : [],
        "service_level"       : [],
        "throughput_per_hour" : [],
        "server_utilization"  : [],
        "served_patients"     : [],
    }

    for rep in range(n_replications):
        seed = 100 * rep + hash(scenario_name) % 1000
        r = run_single_replication(params, seed=seed)

        metrics["avg_wait_time"].append(r.avg_wait_time)
        metrics["p90_wait_time"].append(r.p90_wait_time)
        metrics["drop_rate"].append(r.drop_rate)
        metrics["service_level"].append(r.service_level)
        metrics["throughput_per_hour"].append(r.throughput_per_hour)
        metrics["server_utilization"].append(r.server_busy_time)
        metrics["served_patients"].append(r.served_patients)

    # Ringkasan statistik
    summary = {}
    for key, values in metrics.items():
        arr = np.array(values)
        mean = np.mean(arr)
        std  = np.std(arr, ddof=1)
        ci   = stats.t.interval(0.95, df=len(arr)-1, loc=mean, scale=stats.sem(arr))
        summary[key] = {
            "mean"  : round(mean, 3),
            "std"   : round(std, 3),
            "ci_low": round(ci[0], 3),
            "ci_hi" : round(ci[1], 3),
        }

    # Print ringkasan
    print(f"\n  📊 HASIL ({n_replications} replikasi):")
    print(f"  ┌─────────────────────────────────────────────────┐")
    print(f"  │ Rata-rata waktu tunggu  : {summary['avg_wait_time']['mean']:6.2f} mnt "
          f"[{summary['avg_wait_time']['ci_low']:.2f} – {summary['avg_wait_time']['ci_hi']:.2f}]")
    print(f"  │ Waktu tunggu P90        : {summary['p90_wait_time']['mean']:6.2f} mnt")
    print(f"  │ Drop rate               : {summary['drop_rate']['mean']:6.2f} %")
    print(f"  │ Service level (<15 mnt) : {summary['service_level']['mean']:6.2f} %")
    print(f"  │ Throughput              : {summary['throughput_per_hour']['mean']:6.2f} pasien/jam")
    print(f"  │ Utilisasi petugas       : {summary['server_utilization']['mean']:6.2f} %")
    print(f"  └─────────────────────────────────────────────────┘")

    # Evaluasi target KPI
    kpi_ok = []
    kpi_ok.append(("Wq < 15 mnt", summary['avg_wait_time']['mean'] < 15))
    kpi_ok.append(("Drop rate < 5%", summary['drop_rate']['mean'] < 5))
    kpi_ok.append(("SvcLevel > 90%", summary['service_level']['mean'] > 90))
    kpi_ok.append(("Utilisasi > 60%", summary['server_utilization']['mean'] > 60))

    print(f"\n  🎯 EVALUASI TARGET KPI:")
    for name, passed in kpi_ok:
        icon = "✅" if passed else "❌"
        print(f"  {icon} {name}")

    return summary, metrics


# ─────────────────────────────────────────────────────────────
# 6. DEFINISI SKENARIO (S0 – S4)
# ─────────────────────────────────────────────────────────────
SCENARIOS = {
    "S0_Baseline": {
        **DEFAULT_PARAMS,
        "num_servers"   : 1,
        "queue_capacity": 20,
        "policy"        : "FCFS",
    },
    "S1_Tambah_Petugas": {
        **DEFAULT_PARAMS,
        "num_servers"   : 2,
        "queue_capacity": 20,
        "policy"        : "FCFS",
    },
    "S2_Priority_Queue": {
        # Simulasi sederhana: priority direpresentasikan dengan service time lebih cepat
        # untuk subset pasien prioritas (lansia/darurat ~20% dari total)
        **DEFAULT_PARAMS,
        "num_servers"   : 1,
        "queue_capacity": 20,
        "policy"        : "PRIORITY",
    },
    "S3_Capacity_Limit": {
        **DEFAULT_PARAMS,
        "num_servers"   : 1,
        "queue_capacity": 10,   # batasi antrian jadi 10
        "policy"        : "FCFS",
    },
    "S4_Optimal_Combo": {
        **DEFAULT_PARAMS,
        "num_servers"   : 2,
        "queue_capacity": 20,
        "policy"        : "PRIORITY",
    },
}


# ─────────────────────────────────────────────────────────────
# 7. VISUALISASI HASIL
# ─────────────────────────────────────────────────────────────
def plot_comparison(all_summaries):
    """Plot perbandingan KPI antar skenario."""
    scenario_names = list(all_summaries.keys())
    short_names = [s.split("_")[0] for s in scenario_names]

    fig, axes = plt.subplots(2, 3, figsize=(15, 9))
    fig.suptitle("Perbandingan KPI Antar Skenario — Simulasi Antrian Klinik",
                 fontsize=14, fontweight='bold')

    kpis = [
        ("avg_wait_time",       "Rata-rata Waktu Tunggu (mnt)", "blue",   15,  "< 15"),
        ("drop_rate",           "Drop Rate (%)",                "red",    5,   "< 5%"),
        ("service_level",       "Service Level (%)",            "green",  90,  "> 90%"),
        ("throughput_per_hour", "Throughput (pasien/jam)",      "orange", None, None),
        ("server_utilization",  "Utilisasi Petugas (%)",        "purple", 60,  "> 60%"),
        ("p90_wait_time",       "Waktu Tunggu P90 (mnt)",      "teal",   None, None),
    ]

    for ax, (kpi, title, color, threshold, label) in zip(axes.flatten(), kpis):
        means  = [all_summaries[s][kpi]["mean"]   for s in scenario_names]
        ci_low = [all_summaries[s][kpi]["mean"] - all_summaries[s][kpi]["ci_low"] for s in scenario_names]
        ci_hi  = [all_summaries[s][kpi]["ci_hi"]  - all_summaries[s][kpi]["mean"] for s in scenario_names]

        bars = ax.bar(short_names, means, color=color, alpha=0.75,
                      yerr=[ci_low, ci_hi], capsize=5, error_kw={"elinewidth": 1.5})
        ax.set_title(title, fontsize=11, fontweight='bold')
        ax.set_xlabel("Skenario")

        if threshold is not None:
            ax.axhline(y=threshold, color='red', linestyle='--', linewidth=1.5,
                       label=f"Target {label}")
            ax.legend(fontsize=9)

        # Annotate values
        for bar, val in zip(bars, means):
            ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + max(means)*0.01,
                    f'{val:.1f}', ha='center', va='bottom', fontsize=9, fontweight='bold')

        ax.set_ylim(bottom=0)

    plt.tight_layout()
    plt.savefig("results_comparison.png", dpi=150, bbox_inches='tight')
    print("\n  📊 Grafik tersimpan: results_comparison.png")
    plt.show()


# ─────────────────────────────────────────────────────────────
# 8. MAIN — Jalankan semua skenario
# ─────────────────────────────────────────────────────────────
def main():
    print("\n" + "="*60)
    print("  🏥 SIMULASI ANTRIAN PENDAFTARAN KLINIK")
    print("     Capstone Project — Simulasi Sistem Unit 12")
    print("     Metode: Discrete Event Simulation (SimPy)")
    print("="*60)

    N_REPLICATIONS = 30  # Jumlah replikasi per skenario

    all_summaries = {}
    all_metrics   = {}

    for scenario_name, params in SCENARIOS.items():
        summary, metrics = run_scenario(
            params,
            n_replications=N_REPLICATIONS,
            scenario_name=scenario_name
        )
        all_summaries[scenario_name] = summary
        all_metrics[scenario_name]   = metrics

    # ── Tabel Ringkasan Akhir ──
    print("\n\n" + "="*75)
    print("  📋 TABEL RINGKASAN SEMUA SKENARIO")
    print("="*75)
    header = f"{'Skenario':<25} {'Wq (mnt)':>10} {'Drop%':>8} {'SvcLvl%':>9} {'Util%':>8} {'TP/jam':>8}"
    print(header)
    print("-"*75)
    for s in SCENARIOS:
        sm = all_summaries[s]
        short = s.split("_", 1)[1][:22]
        print(f"{short:<25} "
              f"{sm['avg_wait_time']['mean']:>10.2f} "
              f"{sm['drop_rate']['mean']:>8.2f} "
              f"{sm['service_level']['mean']:>9.2f} "
              f"{sm['server_utilization']['mean']:>8.2f} "
              f"{sm['throughput_per_hour']['mean']:>8.2f}")
    print("="*75)
    print("  Target KPI: Wq < 15 mnt | Drop% < 5 | SvcLvl% > 90 | Util% > 60")
    print("="*75)

    # Simpan hasil ke CSV
    rows = []
    for s, sm in all_summaries.items():
        row = {"scenario": s}
        for kpi, vals in sm.items():
            for stat, v in vals.items():
                row[f"{kpi}_{stat}"] = v
        rows.append(row)
    df = pd.DataFrame(rows)
    df.to_csv("simulation_results.csv", index=False)
    print("\n  💾 Hasil lengkap tersimpan: simulation_results.csv")

    # Plot perbandingan
    try:
        plot_comparison(all_summaries)
    except Exception as e:
        print(f"\n  (Grafik tidak dapat ditampilkan: {e})")

    print("\n  ✅ Simulasi selesai.")
    return all_summaries


if __name__ == "__main__":
    main()
