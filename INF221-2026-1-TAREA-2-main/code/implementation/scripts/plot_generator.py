from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

"""
Este script se encarga de generar automáticamente los gráficos a partir de 
las mediciones obtenidas en el archivo measurements.csv, procesando los datos 
con pandas para calcular promedios y luego utilizando matplotlib para crear 
visualizaciones como curvas de tiempo y memoria en función de distintos parámetros 
(n, capítulos, M, E), además de gráficos comparativos por algoritmo y un análisis de 
calidad donde se comparan los resultados de los algoritmos greedy con la solución 
óptima (programación dinámica), guardando todos los gráficos generados en la carpeta de
'data/plots/'.
Para compilar, se abre una terminal en la carpeta 'scripts/' y se ejecuta el 
siguiente comando:
python plot_generator.py --measurements ../data/measurements/measurements.csv --outputs ../data/outputs --outdir ../data/plots
"""

def default_paths(script_dir: Path):
    repo_root = script_dir.parents[3]
    impl_dir = repo_root / "code" / "implementation"
    return (
        impl_dir / "data" / "measurements" / "measurements.csv",
        impl_dir / "data" / "outputs",
        impl_dir / "data" / "plots",
    )


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
        "case",
        "algorithm",
        "n",
        "M",
        "E",
        "total_chapters",
        "total_duration",
        "total_energy",
        "time_ms",
        "memory_kb",
        "return_code",
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Faltan columnas en measurements.csv: {sorted(missing)}")

    for col in ["n", "M", "E", "total_chapters", "total_duration", "total_energy", "time_ms", "memory_kb"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def save_lineplot(
    df: pd.DataFrame,
    x_col: str,
    value_col: str,
    title: str,
    xlabel: str,
    ylabel: str,
    out_path: Path,
    logy: bool = False,
) -> None:
    agg = (
        df[df["return_code"] >= -1]
        .dropna(subset=[x_col, value_col])
        .groupby([x_col, "algorithm"], as_index=False)
        .agg(**{value_col: (value_col, "mean")})
        .sort_values(x_col)
    )

    plt.figure(figsize=(9, 5))
    for algo in ("brute", "dp", "greedy1", "greedy2"):
        sub = agg[agg["algorithm"] == algo]
        if not sub.empty:
            plt.plot(sub[x_col], sub[value_col], marker="o", linewidth=2, label=algo)

    if logy:
        plt.yscale("log")

    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=180)
    plt.close()


def save_grouped_bar(df: pd.DataFrame, value_col: str, title: str, ylabel: str, out_path: Path) -> None:
    agg = (
        df[df["return_code"] >= -1]
        .dropna(subset=[value_col])
        .groupby("algorithm", as_index=False)
        .agg(**{value_col: (value_col, "mean")})
    )

    order = ["brute", "dp", "greedy1", "greedy2"]
    agg["algorithm"] = pd.Categorical(agg["algorithm"], categories=order, ordered=True)
    agg = agg.sort_values("algorithm")

    plt.figure(figsize=(7.5, 5))
    plt.bar(agg["algorithm"].astype(str), agg[value_col])
    plt.xlabel("Algoritmo")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(True, axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_path, dpi=180)
    plt.close()


def save_quality_plot(df: pd.DataFrame, outputs_dir: Path, out_path: Path) -> bool:
    rows = []
    cases = df[["case", "n"]].drop_duplicates()

    for _, row in cases.iterrows():
        case = row["case"]
        n = row["n"]

        dp_val = read_single_number(outputs_dir / "dp" / f"{case}.txt")
        if dp_val is None or dp_val == 0:
            continue

        for algo in ("greedy1", "greedy2"):
            g_val = read_single_number(outputs_dir / algo / f"{case}.txt")
            if g_val is None:
                continue
            rows.append(
                {
                    "n": n,
                    "algorithm": algo,
                    "quality": float(g_val) / float(dp_val),
                }
            )

    if not rows:
        return False

    qdf = pd.DataFrame(rows)
    agg = qdf.groupby(["n", "algorithm"], as_index=False).agg(quality=("quality", "mean")).sort_values("n")

    plt.figure(figsize=(9, 5))
    for algo in ("greedy1", "greedy2"):
        sub = agg[agg["algorithm"] == algo]
        if not sub.empty:
            plt.plot(sub["n"], sub["quality"], marker="o", linewidth=2, label=algo)

    plt.axhline(1.0, linestyle="--", linewidth=1)
    plt.xlabel("Cantidad de animes (n)")
    plt.ylabel("calidad = greedy / óptimo")
    plt.title("Calidad de los greedy respecto del óptimo (DP)")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=180)
    plt.close()
    return True


def save_family_plots(df: pd.DataFrame, outdir: Path) -> None:
    save_lineplot(df, "n", "time_ms", "Tiempo de ejecución según cantidad de animes", "Cantidad de animes (n)", "Tiempo promedio (ms)", outdir / "tiempo_vs_n.png", logy=True)
    save_lineplot(df, "n", "memory_kb", "Uso de memoria según cantidad de animes", "Cantidad de animes (n)", "Memoria promedio (KB)", outdir / "memoria_vs_n.png")

    save_lineplot(df, "total_chapters", "time_ms", "Tiempo de ejecución según cantidad total de capítulos", "Capítulos totales", "Tiempo promedio (ms)", outdir / "tiempo_vs_capitulos.png", logy=True)
    save_lineplot(df, "total_chapters", "memory_kb", "Uso de memoria según cantidad total de capítulos", "Capítulos totales", "Memoria promedio (KB)", outdir / "memoria_vs_capitulos.png")

    save_lineplot(df, "M", "time_ms", "Tiempo de ejecución según minutos disponibles", "Minutos disponibles (M)", "Tiempo promedio (ms)", outdir / "tiempo_vs_M.png", logy=True)
    save_lineplot(df, "M", "memory_kb", "Uso de memoria según minutos disponibles", "Minutos disponibles (M)", "Memoria promedio (KB)", outdir / "memoria_vs_M.png")

    save_lineplot(df, "E", "time_ms", "Tiempo de ejecución según energía disponible", "Energía disponible (E)", "Tiempo promedio (ms)", outdir / "tiempo_vs_E.png", logy=True)
    save_lineplot(df, "E", "memory_kb", "Uso de memoria según energía disponible", "Energía disponible (E)", "Memoria promedio (KB)", outdir / "memoria_vs_E.png")

    save_grouped_bar(df, "time_ms", "Tiempo promedio por algoritmo", "Tiempo promedio (ms)", outdir / "tiempo_por_algoritmo.png")
    save_grouped_bar(df, "memory_kb", "Memoria promedio por algoritmo", "Memoria promedio (KB)", outdir / "memoria_por_algoritmo.png")


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
        raise FileNotFoundError(f"No encontré el CSV en: {measurements_path}")

    df = load_measurements(measurements_path)

    save_family_plots(df, outdir)

    if outputs_dir.exists():
        ok = save_quality_plot(df, outputs_dir, outdir / "calidad_greedy_vs_optimo.png")
        if not ok:
            print("No fue posible generar la calidad greedy vs óptimo con los outputs entregados.")
    else:
        print("No se encontró carpeta outputs; se omite el gráfico de calidad.")

    print(f"Gráficos generados en: {outdir.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
