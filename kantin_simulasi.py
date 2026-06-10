"""
=============================================================
  SIMULASI ANTRIAN KANTIN JAM SIBUK
  Discrete Event Simulation (DES)

  Capstone Project - Simulasi Sistem Unit 12

  Topik:
  Antrian Pelanggan Kantin pada Jam Istirahat

  Kelompok:
  Shidqi Andira (2313000001)
  Dela (2313000017)

  Cara Menjalankan:
      python kantin_simulasi.py

  Requirements:
      pip install simpy numpy scipy pandas matplotlib
=============================================================
"""

import simpy
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt

# =====================================================
# PARAMETER DASAR
# =====================================================

DEFAULT_PARAMS = {
    "arrival_rate": 30,      # pelanggan per jam
    "service_rate": 24,      # pelanggan per jam
    "num_servers": 2,
    "queue_capacity": 15,
    "sim_duration": 120,     # menit
    "policy": "FCFS",
    "random_seed": 42
}

# =====================================================
# HASIL SIMULASI
# =====================================================

class SimulationResults:

    def __init__(self):

        self.wait_times = []
        self.service_times = []

        self.total_customers = 0
        self.served_customers = 0
        self.dropped_customers = 0

        self.server_busy_time = 0
        self.sim_duration = 0

    @property
    def drop_rate(self):

        if self.total_customers == 0:
            return 0

        return (
            self.dropped_customers
            / self.total_customers
            * 100
        )

    @property
    def avg_wait_time(self):

        if len(self.wait_times) == 0:
            return 0

        return np.mean(self.wait_times)

    @property
    def p90_wait_time(self):

        if len(self.wait_times) == 0:
            return 0

        return np.percentile(
            self.wait_times,
            90
        )

    @property
    def throughput_per_hour(self):

        if self.sim_duration == 0:
            return 0

        return (
            self.served_customers
            / (self.sim_duration / 60)
        )

    @property
    def service_level(self):

        if len(self.wait_times) == 0:
            return 0

        within_target = sum(
            1
            for w in self.wait_times
            if w <= 10
        )

        return (
            within_target
            / len(self.wait_times)
            * 100
        )

# =====================================================
# PROSES PELANGGAN
# =====================================================

def customer_process(
    env,
    results,
    server_resource,
    params,
    customer_id
):

    arrival_time = env.now

    if len(server_resource.queue) >= params["queue_capacity"]:

        results.dropped_customers += 1
        return

    with server_resource.request() as req:

        yield req

        wait_time = env.now - arrival_time

        results.wait_times.append(
            wait_time
        )

        service_time = np.random.exponential(
            60 / params["service_rate"]
        )

        yield env.timeout(service_time)

        results.service_times.append(
            service_time
        )

        results.served_customers += 1


# =====================================================
# GENERATOR KEDATANGAN
# =====================================================

def generate_arrivals(
    env,
    results,
    server_resource,
    params
):

    customer_id = 0

    arrival_rate_per_min = (
        params["arrival_rate"] / 60
    )

    while True:

        interarrival = np.random.exponential(
            1 / arrival_rate_per_min
        )

        yield env.timeout(
            interarrival
        )

        customer_id += 1

        results.total_customers += 1

        env.process(
            customer_process(
                env,
                results,
                server_resource,
                params,
                customer_id
            )
        )

# =====================================================
# SATU REPLIKASI
# =====================================================

def run_single_replication(
    params,
    seed=None
):

    if seed is not None:
        np.random.seed(seed)

    env = simpy.Environment()

    results = SimulationResults()

    results.sim_duration = (
        params["sim_duration"]
    )

    server_resource = simpy.Resource(
        env,
        capacity=params["num_servers"]
    )

    env.process(
        generate_arrivals(
            env,
            results,
            server_resource,
            params
        )
    )

    env.run(
        until=params["sim_duration"]
    )

    total_service = sum(
        results.service_times
    )

    results.server_busy_time = min(
        (
            total_service
            /
            (
                params["num_servers"]
                * params["sim_duration"]
            )
        )
        * 100,
        100
    )

    return results

# =====================================================
# BANYAK REPLIKASI
# =====================================================

def run_scenario(
    params,
    scenario_name,
    n_replications=30
):

    print("\n" + "=" * 60)
    print("Menjalankan :", scenario_name)
    print("=" * 60)

    metrics = {

        "avg_wait_time": [],
        "p90_wait_time": [],
        "drop_rate": [],
        "service_level": [],
        "throughput": [],
        "utilization": []

    }

    for rep in range(
        n_replications
    ):

        result = run_single_replication(
            params,
            seed=1000 + rep
        )

        metrics[
            "avg_wait_time"
        ].append(
            result.avg_wait_time
        )

        metrics[
            "p90_wait_time"
        ].append(
            result.p90_wait_time
        )

        metrics[
            "drop_rate"
        ].append(
            result.drop_rate
        )

        metrics[
            "service_level"
        ].append(
            result.service_level
        )

        metrics[
            "throughput"
        ].append(
            result.throughput_per_hour
        )

        metrics[
            "utilization"
        ].append(
            result.server_busy_time
        )

    summary = {}

    for key, values in metrics.items():

        arr = np.array(values)

        mean = np.mean(arr)

        ci = stats.t.interval(
            confidence=0.95,
            df=len(arr)-1,
            loc=mean,
            scale=stats.sem(arr)
        )

        summary[key] = {

            "mean":
                round(mean, 2),

            "ci_low":
                round(ci[0], 2),

            "ci_high":
                round(ci[1], 2)
        }

    return summary

# =====================================================
# SKENARIO
# =====================================================

SCENARIOS = {

    "S0_Baseline": {

        **DEFAULT_PARAMS,

        "num_servers": 2,
        "queue_capacity": 15

    },

    "S1_Tambah_Petugas": {

        **DEFAULT_PARAMS,

        "num_servers": 3,
        "queue_capacity": 15

    },

    "S2_Priority_Queue": {

        **DEFAULT_PARAMS,

        "num_servers": 2,
        "queue_capacity": 15

    },

    "S3_Tambah_Kapasitas": {

        **DEFAULT_PARAMS,

        "num_servers": 2,
        "queue_capacity": 25

    },

    "S4_Optimal_Combo": {

        **DEFAULT_PARAMS,

        "num_servers": 3,
        "queue_capacity": 25

    }
}

# =====================================================
# VISUALISASI
# =====================================================

def plot_results(results):

    names = list(
        results.keys()
    )

    waiting = [

        results[s]
        ["avg_wait_time"]
        ["mean"]

        for s in names

    ]

    plt.figure(
        figsize=(10,6)
    )

    plt.bar(
        names,
        waiting
    )

    plt.title(
        "Average Waiting Time"
    )

    plt.ylabel(
        "Menit"
    )

    plt.savefig(
        "hasil_kpi_kantin.png"
    )

    plt.show()

# =====================================================
# MAIN
# =====================================================

def main():

    print(
        "\nSIMULASI ANTRIAN KANTIN JAM SIBUK"
    )

    all_results = {}

    for scenario_name, params in SCENARIOS.items():

        summary = run_scenario(
            params,
            scenario_name,
            n_replications=30
        )

        all_results[
            scenario_name
        ] = summary

    rows = []

    for scenario, data in all_results.items():

        rows.append({

            "Scenario":
                scenario,

            "Average Waiting Time":
                data["avg_wait_time"]["mean"],

            "Drop Rate":
                data["drop_rate"]["mean"],

            "Service Level":
                data["service_level"]["mean"],

            "Throughput":
                data["throughput"]["mean"],

            "Utilization":
                data["utilization"]["mean"]

        })

    df = pd.DataFrame(rows)

    print("\n")
    print(df)

    df.to_csv(
        "hasil_simulasi_kantin.csv",
        index=False
    )

    print(
        "\nFile tersimpan:"
    )

    print(
        "hasil_simulasi_kantin.csv"
    )

    plot_results(
        all_results
    )

if __name__ == "__main__":
    main()
