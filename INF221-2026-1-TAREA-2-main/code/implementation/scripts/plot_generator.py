#!/usr/bin/env python3
from __future__ import annotations

"""Genera gráficos para la Tarea 2 de Algoritmos y Complejidad (AniMarathon).

Este script asume que `general.cpp` ya generó un `measurements.csv` con las
columnas:
case,algorithm,n,M,E,total_chapters,total_duration,total_energy,time_ms,
memory_kb,return_code,ok,skipped,output_file,stderr_file

Gráficos que produce:
- tiempo_vs_n.png
- memoria_vs_n.png
- tiempo_vs_capitulos.png
- memoria_vs_capitulos.png
- tiempo_vs_M.png
- memoria_vs_M.png
- tiempo_vs_E.png
- memoria_vs_E.png
- tiempo_por_algoritmo.png
- memoria_por_algoritmo.png
- calidad_greedy_vs_optimo.png

Notas:
- En los gráficos de tiempo se usa escala logarítmica en Y para que los valores
  muy grandes de brute-force no aplasten al resto.
- Las etiquetas y títulos indican claramente la variable del eje X.
"""

import argparse
import re
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import pandas as pd

ALG_ORDER = ["brute", "dp", "greedy1", "greedy2"]


def default_paths(script_dir: Path):
    repo_root = script_dir.parents[2]
    impl_dir = repo_root / "code" / "implementation"
    return (
        impl_dir / "data" / "measurements" / "measurements.csv",
        impl_dir / "data" / "outputs",
        impl_dir / "data" / "plots",
    )


def parse_case_n(case_name: str) -> int:
    m = re.match(r"testcases_(\d+)_\d+$", case_name)
    if not m:
        raise ValueError(f"No pude extraer n desde el caso: {case_name}")
    return int(m.group(1))


def read_single_number(path: Path):
    try:
        text = path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return None
    if not text:
        return None
    token = text.split()[0]
    try:
        return int(token)
    except ValueError:
        try:
            return float(token)
        except ValueError:
            return None


def load_measurements(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {
        "case", "algorithm", "n", "M", "E", "total_chapters",
        "time_ms", "memory_kb", "return_code"
    }
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Faltan columnas en measurements.csv: {sorted(missing)}")
    return df


def _agg_mean(df: pd.DataFrame, x_col: str, y_col: str) -> pd.DataFrame:
    # Excluye registros omitidos/skipped y errores.
    valid = df[df["return_code"] >= -1].copy()
    valid = valid[pd.notna(valid[x_col])]
    return (
        valid.groupby([x_col, "algorithm"], as_index=False)
        .agg(**{y_col: (y_col, "mean")})
        .sort_values([x_col, "algorithm"])
    )


def save_lineplot(
    df: pd.DataFrame,
    x_col: str,
    x_label: str,
    title: str,
    y_col: str,
    y_label: str,
    out_path: Path,
    logy: bool = False,
) -> None:
    agg = _agg_mean(df, x_col=x_col, y_col=y_col)

    plt.figure(figsize=(9, 5.5))
    for algo in ALG_ORDER:
        sub = agg[agg["algorithm"] == algo].sort_values(x_col)
        if sub.empty:
            continue
        plt.plot(sub[x_col], sub[y_col], marker="o", linewidth=2, label=algo)

    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.title(title)
    plt.grid(True, alpha=0.3)
    if logy:
        plt.yscale("log")
        plt.ylabel(f"{y_label} (escala logarítmica)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=180)
    plt.close()


def save_barplot(df: pd.DataFrame, y_col: str, title: str, y_label: str, out_path: Path) -> None:
    valid = df[df["return_code"] >= -1].copy()
    agg = valid.groupby("algorithm", as_index=False).agg(**{y_col: (y_col, "mean")})
    agg["algorithm"] = pd.Categorical(agg["algorithm"], categories=ALG_ORDER, ordered=True)
    agg = agg.sort_values("algorithm")

    plt.figure(figsize=(7, 5))
    plt.bar(agg["algorithm"].astype(str), agg[y_col])
    plt.xlabel("Algoritmo")
    plt.ylabel(y_label)
    plt.title(title)
    plt.grid(True, axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_path, dpi=180)
    plt.close()


def save_quality_plot(measurements: pd.DataFrame, outputs_dir: Path, out_path: Path) -> bool:
    rows = []
    for case in measurements["case"].drop_duplicates():
        dp_val = read_single_number(outputs_dir / "dp" / f"{case}.txt")
        if dp_val is None or dp_val == 0:
            continue
        n = parse_case_n(case)
        for algo in ("greedy1", "greedy2"):
            g_val = read_single_number(outputs_dir / algo / f"{case}.txt")
            if g_val is None:
                continue
            rows.append({"n": n, "algorithm": algo, "quality": g_val / dp_val})

    if not rows:
        return False

    qdf = pd.DataFrame(rows)
    agg = qdf.groupby(["n", "algorithm"], as_index=False).agg(quality=("quality", "mean"))

    plt.figure(figsize=(9, 5.5))
    for algo in ("greedy1", "greedy2"):
        sub = agg[agg["algorithm"] == algo].sort_values("n")
        if not sub.empty:
            plt.plot(sub["n"], sub["quality"], marker="o", linewidth=2, label=algo)

    plt.axhline(1.0, linestyle="--", linewidth=1)
    plt.xlabel("Cantidad de animes (n)")
    plt.ylabel("Calidad = greedy / óptimo")
    plt.title("Calidad de solución de greedy respecto del óptimo (DP)")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=180)
    plt.close()
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Generador de gráficos para AniMarathon")
    parser.add_argument("--measurements", type=Path, default=None, help="Ruta a measurements.csv")
    parser.add_argument("--outputs", type=Path, default=None, help="Carpeta data/outputs")
    parser.add_argument("--outdir", type=Path, default=None, help="Carpeta destino de PNG")
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    default_measurements, default_outputs, default_outdir = default_paths(script_dir)

    measurements_path = args.measurements or default_measurements
    outputs_dir = args.outputs or default_outputs
    outdir = args.outdir or default_outdir
    outdir.mkdir(parents=True, exist_ok=True)

    if not measurements_path.exists():
        raise FileNotFoundError(f"No encontré measurements.csv en: {measurements_path}")

    df = load_measurements(measurements_path)

    # Gráficos por tamaño de entrada
    save_lineplot(
        df, "n", "Cantidad de animes (n)",
        "Tiempo de ejecución según cantidad de animes",
        "time_ms", "Tiempo promedio (ms)",
        outdir / "tiempo_vs_n.png",
        logy=True,
    )
    save_lineplot(
        df, "n", "Cantidad de animes (n)",
        "Uso de memoria según cantidad de animes",
        "memory_kb", "Memoria promedio (KB)",
        outdir / "memoria_vs_n.png",
        logy=False,
    )

    # Gráficos por cantidad de capítulos
    save_lineplot(
        df, "total_chapters", "Cantidad total de capítulos",
        "Tiempo de ejecución según cantidad total de capítulos",
        "time_ms", "Tiempo promedio (ms)",
        outdir / "tiempo_vs_capitulos.png",
        logy=True,
    )
    save_lineplot(
        df, "total_chapters", "Cantidad total de capítulos",
        "Uso de memoria según cantidad total de capítulos",
        "memory_kb", "Memoria promedio (KB)",
        outdir / "memoria_vs_capitulos.png",
        logy=False,
    )

    # Gráficos por minutos disponibles
    save_lineplot(
        df, "M", "Minutos disponibles (M)",
        "Tiempo de ejecución según minutos disponibles",
        "time_ms", "Tiempo promedio (ms)",
        outdir / "tiempo_vs_M.png",
        logy=True,
    )
    save_lineplot(
        df, "M", "Minutos disponibles (M)",
        "Uso de memoria según minutos disponibles",
        "memory_kb", "Memoria promedio (KB)",
        outdir / "memoria_vs_M.png",
        logy=False,
    )

    # Gráficos por energía disponible
    save_lineplot(
        df, "E", "Energía disponible (E)",
        "Tiempo de ejecución según energía disponible",
        "time_ms", "Tiempo promedio (ms)",
        outdir / "tiempo_vs_E.png",
        logy=True,
    )
    save_lineplot(
        df, "E", "Energía disponible (E)",
        "Uso de memoria según energía disponible",
        "memory_kb", "Memoria promedio (KB)",
        outdir / "memoria_vs_E.png",
        logy=False,
    )

    # Resumen por algoritmo
    save_barplot(
        df, "time_ms",
        "Tiempo promedio por algoritmo (promedio global sobre casos ejecutados)",
        "Tiempo promedio (ms)",
        outdir / "tiempo_por_algoritmo.png",
    )
    save_barplot(
        df, "memory_kb",
        "Memoria promedio por algoritmo (promedio global sobre casos ejecutados)",
        "Memoria promedio (KB)",
        outdir / "memoria_por_algoritmo.png",
    )

    # Calidad greedy vs óptimo
    if outputs_dir.exists():
        save_quality_plot(df, outputs_dir, outdir / "calidad_greedy_vs_optimo.png")

    print(f"Gráficos generados en: {outdir.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
