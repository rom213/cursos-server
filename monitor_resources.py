"""
=============================================================================
 MONITOREO DE RECURSOS — ISO/IEC 25023
 Plataforma: Cursos Estudia y Trabaja
=============================================================================

 Métrica ISO 25023 implementada:

 UTILIZACIÓN DE RECURSOS (Performance Efficiency - Resource Utilisation)
    Fórmula:  U = (R_used / R_total) × 100

    Para CPU:
        U_cpu = porcentaje de uso del CPU promedio sobre todos los núcleos

    Para Memoria RAM:
        U_mem = (RAM_usada / RAM_total) × 100

 Este script se ejecuta en paralelo con las pruebas de Locust para
 capturar el consumo de recursos del servidor durante la carga.

 Uso:
    python monitor_resources.py --duration 60 --interval 1
    python monitor_resources.py --duration 120 --interval 2 --output reporte_recursos.csv

 Dependencias:
    pip install psutil
=============================================================================
"""

import argparse
import csv
import os
import sys
import time
from datetime import datetime

try:
    import psutil
except ImportError:
    print("ERROR: La librería 'psutil' no está instalada.")
    print("Instálala con: pip install psutil")
    sys.exit(1)


# =========================================================================
# FUNCIONES DE MEDICIÓN ISO 25023
# =========================================================================
def get_cpu_utilization():
    """
    ISO 25023 — Utilización de CPU
    U_cpu = (R_used / R_total) × 100

    psutil.cpu_percent() retorna directamente el porcentaje de uso
    promediado sobre todos los núcleos del procesador.
    """
    return psutil.cpu_percent(interval=None)


def get_memory_utilization():
    """
    ISO 25023 — Utilización de Memoria RAM
    U_mem = (R_used / R_total) × 100

    Retorna un diccionario con:
        - percent: U_mem (porcentaje de uso)
        - used_gb: RAM usada en GB
        - total_gb: RAM total en GB
        - available_gb: RAM disponible en GB
    """
    mem = psutil.virtual_memory()
    return {
        "percent": mem.percent,
        "used_gb": round(mem.used / (1024 ** 3), 2),
        "total_gb": round(mem.total / (1024 ** 3), 2),
        "available_gb": round(mem.available / (1024 ** 3), 2),
    }


def get_disk_utilization():
    """
    ISO 25023 — Utilización de Disco (complementario)
    U_disk = (R_used / R_total) × 100
    """
    disk = psutil.disk_usage("/")
    return {
        "percent": disk.percent,
        "used_gb": round(disk.used / (1024 ** 3), 2),
        "total_gb": round(disk.total / (1024 ** 3), 2),
    }


def get_process_info(process_name="python"):
    """
    Busca procesos que contengan el nombre dado y retorna
    su consumo de CPU y RAM. Útil para monitorear el proceso
    del servidor Flask específicamente.
    """
    processes = []
    for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
        try:
            if process_name.lower() in proc.info["name"].lower():
                processes.append({
                    "pid": proc.info["pid"],
                    "name": proc.info["name"],
                    "cpu_percent": proc.info["cpu_percent"],
                    "memory_percent": round(proc.info["memory_percent"], 2),
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return processes


# =========================================================================
# RECOLECTOR DE DATOS CON SALIDA CSV
# =========================================================================
def monitor_loop(duration_seconds, interval_seconds, output_file):
    """
    Bucle principal de monitoreo que recolecta métricas cada
    `interval_seconds` durante `duration_seconds`.

    Escribe los resultados en un archivo CSV y los muestra en consola.
    """
    csv_path = os.path.abspath(output_file)
    print("\n" + "=" * 70)
    print("  ISO/IEC 25023 — MONITOREO DE RECURSOS INICIADO")
    print("=" * 70)
    print(f"  Duración:     {duration_seconds} segundos")
    print(f"  Intervalo:    {interval_seconds} segundo(s)")
    print(f"  Archivo CSV:  {csv_path}")
    print("=" * 70 + "\n")

    # Encabezados para el CSV
    fieldnames = [
        "timestamp",
        "cpu_percent",
        "mem_percent",
        "mem_used_gb",
        "mem_total_gb",
        "mem_available_gb",
        "disk_percent",
    ]

    # Inicializar CPU measurement (la primera llamada siempre da 0)
    psutil.cpu_percent(interval=None)

    # Abrir CSV para escritura
    with open(csv_path, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        # Variables para cálculo de promedios
        cpu_samples = []
        mem_samples = []

        start_time = time.time()
        elapsed = 0.0

        print(f"  {'Timestamp':<22} │ {'CPU %':>7} │ {'RAM %':>7} │ "
              f"{'RAM Usada':>10} │ {'RAM Disp.':>10}")
        print("  " + "─" * 22 + "─┼─" + "─" * 7 + "─┼─" + "─" * 7
              + "─┼─" + "─" * 10 + "─┼─" + "─" * 10)

        while elapsed < duration_seconds:
            # Métricas ISO 25023
            cpu_util = get_cpu_utilization()
            mem_util = get_memory_utilization()
            disk_util = get_disk_utilization()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Acumular muestras
            cpu_samples.append(cpu_util)
            mem_samples.append(mem_util["percent"])

            # Escribir fila en CSV
            row = {
                "timestamp": now,
                "cpu_percent": cpu_util,
                "mem_percent": mem_util["percent"],
                "mem_used_gb": mem_util["used_gb"],
                "mem_total_gb": mem_util["total_gb"],
                "mem_available_gb": mem_util["available_gb"],
                "disk_percent": disk_util["percent"],
            }
            writer.writerow(row)
            csvfile.flush()

            # Mostrar en consola
            print(
                f"  {now:<22} │ {cpu_util:>6.1f}% │ "
                f"{mem_util['percent']:>6.1f}% │ "
                f"{mem_util['used_gb']:>8.2f}GB │ "
                f"{mem_util['available_gb']:>8.2f}GB"
            )

            time.sleep(interval_seconds)
            elapsed = time.time() - start_time

    # ── Resumen final: Promedios ISO 25023 ──────────────────────────────
    avg_cpu = sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0
    avg_mem = sum(mem_samples) / len(mem_samples) if mem_samples else 0
    max_cpu = max(cpu_samples) if cpu_samples else 0
    max_mem = max(mem_samples) if mem_samples else 0

    print("\n" + "=" * 70)
    print("  RESUMEN ISO/IEC 25023 — UTILIZACIÓN DE RECURSOS")
    print("=" * 70)
    print(f"""
  ┌─────────────────────────────────────────────────────────────────┐
  │  Fórmula: U = (R_used / R_total) × 100                        │
  ├─────────────────────────────────────────────────────────────────┤
  │  CPU                                                           │
  │    U_cpu (promedio) = {avg_cpu:.2f}%                            │
  │    U_cpu (máximo)   = {max_cpu:.2f}%                            │
  │    Muestras         = {len(cpu_samples)}                        │
  ├─────────────────────────────────────────────────────────────────┤
  │  MEMORIA RAM                                                   │
  │    U_mem (promedio) = {avg_mem:.2f}%                            │
  │    U_mem (máximo)   = {max_mem:.2f}%                            │
  │    RAM Total        = {mem_util['total_gb']:.2f} GB             │
  └─────────────────────────────────────────────────────────────────┘
    """)
    print(f"  Datos exportados a: {csv_path}")
    print("=" * 70 + "\n")


# =========================================================================
# PUNTO DE ENTRADA
# =========================================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="ISO 25023 — Monitor de Utilización de Recursos"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=60,
        help="Duración del monitoreo en segundos (default: 60)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=1,
        help="Intervalo de muestreo en segundos (default: 1)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="resource_metrics.csv",
        help="Archivo CSV de salida (default: resource_metrics.csv)"
    )
    args = parser.parse_args()

    try:
        monitor_loop(args.duration, args.interval, args.output)
    except KeyboardInterrupt:
        print("\n  Monitoreo detenido por el usuario (Ctrl+C)")
        sys.exit(0)
