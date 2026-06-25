from __future__ import annotations
"""
Este script construye casos de prueba siguiendo el formato del enunciado,
con el objetivo de evaluar el comportamiento de los algoritmos implementados.
En lugar de generar casos completamente aleatorios, se definen "familias" de
instancias donde se controla una variable a la vez (por ejemplo, la cantidad
de animes, capítulos, minutos o energía disponible). Esto permite luego analizar
los resultados de forma más clara en los gráficos.
Para ejecutar este código, abrir una terminal en la carpeta 'scripts/' y ejecutar el comando 
python testcases_generator.py.
"""

import argparse
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Tuple


MAX_N = 200
MAX_Q = 30
MAX_TOTAL_Q = 700
MAX_M = 3000
MAX_E = 500
MAX_T = 300
MAX_C = 100
MAX_V = 10**9
MAX_B = 10**9


@dataclass(frozen=True)
class Chapter:
    duration: int
    energy: int
    value: int


@dataclass(frozen=True)
class Anime:
    name: str
    chapters: List[Chapter]
    bonus: int


@dataclass(frozen=True)
class CaseSpec:
    family: str
    label: str
    n: int
    q_range: Tuple[int, int]
    m_value: int
    e_value: int
    bonus_range: Tuple[int, int]
    value_range: Tuple[int, int]
    duration_range: Tuple[int, int]
    energy_range: Tuple[int, int]
    count: int


def clamp(x: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, x))


def make_anime_name(case_prefix: str, anime_idx: int) -> str:
    return f"{case_prefix}_anime_{anime_idx}"


def build_case(rng: random.Random, spec: CaseSpec, case_id: int) -> tuple[int, int, int, list[Anime]]:
    n = clamp(spec.n, 1, MAX_N)

    q_min, q_max = spec.q_range
    q_min = clamp(q_min, 1, MAX_Q)
    q_max = clamp(q_max, q_min, MAX_Q)

    chapters_per_anime: list[int] = []
    total_q = 0
    for _ in range(n):
        q = rng.randint(q_min, q_max)
        chapters_per_anime.append(q)
        total_q += q

    while total_q > MAX_TOTAL_Q:
        candidates = [i for i, q in enumerate(chapters_per_anime) if q > 1]
        if not candidates:
            break
        i = rng.choice(candidates)
        chapters_per_anime[i] -= 1
        total_q -= 1

    animes: list[Anime] = []
    sum_duration_full = 0
    sum_energy_full = 0

    for i in range(n):
        q = chapters_per_anime[i]
        chapters: list[Chapter] = []
        full_duration = 0
        full_energy = 0
        full_value = 0

        for _ in range(q):
            duration = clamp(rng.randint(*spec.duration_range), 1, MAX_T)
            energy = clamp(rng.randint(*spec.energy_range), 1, MAX_C)
            value = clamp(rng.randint(*spec.value_range), 1, MAX_V)
            chapters.append(Chapter(duration=duration, energy=energy, value=value))
            full_duration += duration
            full_energy += energy
            full_value += value

        bonus_low, bonus_high = spec.bonus_range
        bonus_low = clamp(bonus_low, 0, MAX_B)
        bonus_high = clamp(bonus_high, bonus_low, MAX_B)
        bonus = clamp(rng.randint(bonus_low, bonus_high) + rng.randint(0, max(1, full_value // 4)), 0, MAX_B)

        animes.append(Anime(name=make_anime_name(spec.family, i + 1), chapters=chapters, bonus=bonus))
        sum_duration_full += full_duration
        sum_energy_full += full_energy

    M = clamp(spec.m_value, 1, MAX_M)
    E = clamp(spec.e_value, 1, MAX_E)

    if n <= 8:
        max_duration = max(ch.duration for anime in animes for ch in anime.chapters)
        max_energy = max(ch.energy for anime in animes for ch in anime.chapters)
        M = max(M, min(MAX_M, max_duration))
        E = max(E, min(MAX_E, max_energy))

    M = clamp(M, 1, MAX_M)
    E = clamp(E, 1, MAX_E)

    return n, M, E, animes


def write_case(path: Path, n: int, M: int, E: int, animes: Iterable[Anime]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        f.write(f"{n} {M} {E}\n")
        for anime in animes:
            f.write(f"{anime.name} {len(anime.chapters)} {anime.bonus}\n")
            for ch in anime.chapters:
                f.write(f"{ch.duration} {ch.energy} {ch.value}\n")


def generate_cases(outdir: Path, seed: int) -> list[Path]:
    rng = random.Random(seed)

    specs = [
        CaseSpec("small", "n03", 3, (1, 4), 240, 90, (0, 50), (1, 120), (1, 40), (1, 15), 2),
        CaseSpec("small", "n05", 5, (1, 5), 260, 100, (0, 80), (1, 150), (1, 50), (1, 20), 2),
        CaseSpec("small", "n08", 8, (1, 6), 320, 120, (0, 120), (1, 180), (1, 60), (1, 25), 2),

        CaseSpec("vary_n", "n03", 3, (2, 5), 1200, 220, (0, 200), (1, 200), (1, 80), (1, 30), 1),
        CaseSpec("vary_n", "n05", 5, (2, 5), 1200, 220, (0, 200), (1, 200), (1, 80), (1, 30), 1),
        CaseSpec("vary_n", "n08", 8, (2, 5), 1200, 220, (0, 200), (1, 200), (1, 80), (1, 30), 1),
        CaseSpec("vary_n", "n20", 20, (2, 5), 1200, 220, (0, 200), (1, 200), (1, 80), (1, 30), 1),
        CaseSpec("vary_n", "n40", 40, (2, 5), 1200, 220, (0, 200), (1, 200), (1, 80), (1, 30), 1),
        CaseSpec("vary_n", "n80", 80, (2, 5), 1200, 220, (0, 200), (1, 200), (1, 80), (1, 30), 1),
        CaseSpec("vary_n", "n100", 100, (2, 5), 1200, 220, (0, 200), (1, 200), (1, 80), (1, 30), 1),
        CaseSpec("vary_n", "n150", 150, (2, 5), 1200, 220, (0, 200), (1, 200), (1, 80), (1, 30), 1),
        CaseSpec("vary_n", "n200", 200, (1, 4), 1200, 220, (0, 200), (1, 200), (1, 80), (1, 30), 1),

        CaseSpec("vary_q", "q02", 40, (1, 2), 1500, 250, (0, 300), (1, 300), (1, 80), (1, 30), 1),
        CaseSpec("vary_q", "q04", 40, (1, 4), 1500, 250, (0, 300), (1, 300), (1, 80), (1, 30), 1),
        CaseSpec("vary_q", "q06", 40, (1, 6), 1500, 250, (0, 300), (1, 300), (1, 80), (1, 30), 1),
        CaseSpec("vary_q", "q08", 40, (1, 8), 1500, 250, (0, 300), (1, 300), (1, 80), (1, 30), 1),
        CaseSpec("vary_q", "q10", 40, (1, 10), 1500, 250, (0, 300), (1, 300), (1, 80), (1, 30), 1),
        CaseSpec("vary_q", "q12", 40, (1, 12), 1500, 250, (0, 300), (1, 300), (1, 80), (1, 30), 1),

        CaseSpec("vary_m", "m0200", 40, (2, 5), 200, 300, (0, 300), (1, 300), (1, 80), (1, 30), 1),
        CaseSpec("vary_m", "m0500", 40, (2, 5), 500, 300, (0, 300), (1, 300), (1, 80), (1, 30), 1),
        CaseSpec("vary_m", "m0800", 40, (2, 5), 800, 300, (0, 300), (1, 300), (1, 80), (1, 30), 1),
        CaseSpec("vary_m", "m1200", 40, (2, 5), 1200, 300, (0, 300), (1, 300), (1, 80), (1, 30), 1),
        CaseSpec("vary_m", "m1800", 40, (2, 5), 1800, 300, (0, 300), (1, 300), (1, 80), (1, 30), 1),
        CaseSpec("vary_m", "m2500", 40, (2, 5), 2500, 300, (0, 300), (1, 300), (1, 80), (1, 30), 1),
        CaseSpec("vary_m", "m3000", 40, (2, 5), 3000, 300, (0, 300), (1, 300), (1, 80), (1, 30), 1),

        CaseSpec("vary_e", "e0020", 40, (2, 5), 1500, 20, (0, 300), (1, 300), (1, 80), (1, 30), 1),
        CaseSpec("vary_e", "e0050", 40, (2, 5), 1500, 50, (0, 300), (1, 300), (1, 80), (1, 30), 1),
        CaseSpec("vary_e", "e0100", 40, (2, 5), 1500, 100, (0, 300), (1, 300), (1, 80), (1, 30), 1),
        CaseSpec("vary_e", "e0150", 40, (2, 5), 1500, 150, (0, 300), (1, 300), (1, 80), (1, 30), 1),
        CaseSpec("vary_e", "e0200", 40, (2, 5), 1500, 200, (0, 300), (1, 300), (1, 80), (1, 30), 1),
        CaseSpec("vary_e", "e0300", 40, (2, 5), 1500, 300, (0, 300), (1, 300), (1, 80), (1, 30), 1),
        CaseSpec("vary_e", "e0500", 40, (2, 5), 1500, 500, (0, 300), (1, 300), (1, 80), (1, 30), 1),
    ]

    generated_paths: list[Path] = []
    case_counter_by_n: dict[int, int] = {}

    for spec in specs:
        for _ in range(spec.count):
            n, M, E, animes = build_case(rng, spec, 1)
            case_counter_by_n[n] = case_counter_by_n.get(n, 0) + 1
            case_id = case_counter_by_n[n]
            filename = f"testcases_{n}_{case_id}.txt"
            path = outdir / filename
            write_case(path, n, M, E, animes)
            generated_paths.append(path)

    return generated_paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Generador de casos de prueba para AniMarathon")
    parser.add_argument("--seed", type=int, default=2212026, help="Semilla para reproducibilidad")
    parser.add_argument(
        "--outdir",
        type=str,
        default=None,
        help="Directorio destino. Por defecto: code/implementation/data/inputs relativo al script.",
    )
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    default_outdir = script_dir.parent / "data" / "inputs"
    outdir = Path(args.outdir).resolve() if args.outdir else default_outdir.resolve()

    paths = generate_cases(outdir, args.seed)
    print(f"Generados {len(paths)} archivos en: {outdir}")
    for p in paths:
        print(p.name)


if __name__ == "__main__":
    main()

