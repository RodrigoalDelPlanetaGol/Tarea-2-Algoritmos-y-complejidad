#!/usr/bin/env python3
"""
plot_generator.py

Genera gráficos para la Tarea 2 de Algoritmos y Complejidad (AniMarathon).

Entradas esperadas:
- measurements.csv con columnas:
    case,algorithm,time_ms,memory_kb,return_code,ok,output_file,stderr_file
- opcionalmente, la carpeta data/outputs/ con subcarpetas:
    brute/, dp/, greedy1/, greedy2/
  y un archivo .txt por caso en cada carpeta, conteniendo solo un número:
    la satisfacción total obtenida por ese algoritmo.

Salidas:
- tiempo_vs_n.png
- memoria_vs_n.png
- calidad_greedy_vs_optimo.png (si se entrega --outputs)

Uso sugerido:
    python plot_generator.py --measurements data/measurements/measurements.csv --outdir data/plots
    python plot_generator.py --measurements data/measurements/measurements.csv --outputs data/outputs --outdir data/plots
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import pandas as pd
import matplotlib.pyplot as plt


def parse_case_n(case_name: str) -> int:
    m = re.match(r"testcases_(\d+)_\d+$", case_name)
    if not m:
        raise ValueError(f"No pude extraer n desde el nombre del caso: {case_name}")
    return int(m.group(1))


def read_single_number(path: Path):
    try:
        text = path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return None
    if not text:
        return None
    try:
        return int(text.split()[0])
    except ValueError:
        try:
            return float(text.split()[0])
        except ValueError:
            return None


def load_measurements(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    if "case" not in df.columns or "algorithm" not in df.columns:
        raise ValueError("El CSV no tiene las columnas esperadas.")
    df["n"] = df["case"].map(parse_case_n)
    return df


def save_lineplot(df: pd.DataFrame, value_col: str, title: str, ylabel: str, out_path: Path,
                  algorithms=("brute", "dp", "greedy1", "greedy2")) -> None:
    # Promedio por n, porque cada tamaño puede tener varias instancias.
    agg = (
        df[df["return_code"] >= -1]
        .groupby(["n", "algorithm"], as_index=False)
        .agg(**{value_col: (value_col, "mean")})
    )

    plt.figure(figsize=(8, 5))
    for algo in algorithms:
        sub = agg[agg["algorithm"] == algo].sort_values("n")
        if sub.empty:
            continue
        plt.plot(sub["n"], sub[value_col], marker="o", linewidth=2, label=algo)

    plt.xlabel("Cantidad de animes (n)")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=180)
    plt.close()


def load_output_values(outputs_dir: Path, case_names) -> pd.DataFrame:
    rows = []
    for case in case_names:
        for algo in ("dp", "greedy1", "greedy2"):
            path = outputs_dir / algo / f"{case}.txt"
            val = read_single_number(path)
            rows.append({"case": case, "algorithm": algo, "value": val})
    return pd.DataFrame(rows)


def save_quality_plot(measurements: pd.DataFrame, outputs_dir: Path, out_path: Path) -> bool:
    # Tomamos dp como óptimo de referencia.
    values = load_output_values(outputs_dir, measurements["case"].unique())
    if values["value"].isna().all():
        return False

    pivot = values.pivot(index="case", columns="algorithm", values="value").reset_index()
    pivot["n"] = pivot["case"].map(parse_case_n)

    # Unimos con el caso para comparar greedy / dp.
    quality_rows = []
    for _, row in pivot.iterrows():
        opt = row.get("dp")
        if pd.isna(opt) or opt == 0:
            continue
        for algo in ("greedy1", "greedy2"):
            g = row.get(algo)
            if pd.isna(g):
                continue
            quality_rows.append({
                "n": row["n"],
                "algorithm": algo,
                "quality": float(g) / float(opt),
            })

    qdf = pd.DataFrame(quality_rows)
    if qdf.empty:
        return False

    agg = qdf.groupby(["n", "algorithm"], as_index=False).agg(quality=("quality", "mean"))

    plt.figure(figsize=(8, 5))
    for algo in ("greedy1", "greedy2"):
        sub = agg[agg["algorithm"] == algo].sort_values("n")
        if sub.empty:
            continue
        plt.plot(sub["n"], sub["quality"], marker="o", linewidth=2, label=algo)

    plt.axhline(1.0, linestyle="--", linewidth=1)
    plt.xlabel("Cantidad de animes (n)")
    plt.ylabel("calidad = greedy / óptimo")
    plt.title("Calidad de solución de greedy respecto del óptimo (DP)")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=180)
    plt.close()
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Generador de gráficos para AniMarathon")
    parser.add_argument(
        "--measurements",
        type=Path,
        required=True,
        help="Ruta al archivo measurements.csv",
    )
    parser.add_argument(
        "--outputs",
        type=Path,
        default=None,
        help="Carpeta data/outputs para calcular calidad greedy/óptimo",
    )
    parser.add_argument(
        "--outdir",
        type=Path,
        default=Path("data/plots"),
        help="Carpeta destino de los PNG",
    )
    args = parser.parse_args()

    args.outdir.mkdir(parents=True, exist_ok=True)

    df = load_measurements(args.measurements)

    save_lineplot(
        df=df,
        value_col="time_ms",
        title="Tiempo de ejecución según tamaño de entrada",
        ylabel="Tiempo promedio (ms)",
        out_path=args.outdir / "tiempo_vs_n.png",
    )

    save_lineplot(
        df=df,
        value_col="memory_kb",
        title="Uso de memoria según tamaño de entrada",
        ylabel="Memoria promedio (KB)",
        out_path=args.outdir / "memoria_vs_n.png",
    )

    if args.outputs is not None and args.outputs.exists():
        ok = save_quality_plot(
            measurements=df,
            outputs_dir=args.outputs,
            out_path=args.outdir / "calidad_greedy_vs_optimo.png",
        )
        if ok:
            print("Calidad generada.")
        else:
            print("No fue posible generar la calidad con los outputs entregados.")

    print(f"Gráficos generados en: {args.outdir.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
