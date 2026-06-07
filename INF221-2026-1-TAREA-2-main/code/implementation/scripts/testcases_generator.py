from __future__ import annotations
"""
Este es el script para generar unos pocos casos de prueba (FALTA COMENTAR!!)
"""


import argparse
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Tuple


# Límites del enunciado
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
    n: int
    q_range: Tuple[int, int]
    m_range: Tuple[int, int]
    e_range: Tuple[int, int]
    bonus_range: Tuple[int, int]
    value_range: Tuple[int, int]
    duration_range: Tuple[int, int]
    energy_range: Tuple[int, int]
    count: int
    prefix: str


def clamp(x: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, x))


def make_anime_name(case_prefix: str, anime_idx: int) -> str:
    return f"{case_prefix}_anime_{anime_idx}"


def build_case(rng: random.Random, spec: CaseSpec, case_id: int) -> Tuple[int, int, int, List[Anime]]:


    n = clamp(spec.n, 1, MAX_N)

    q_min, q_max = spec.q_range
    q_min = clamp(q_min, 1, MAX_Q)
    q_max = clamp(q_max, q_min, MAX_Q)

    chapters_per_anime: List[int] = []
    total_q = 0
    for _ in range(n):
        q = rng.randint(q_min, q_max)
        chapters_per_anime.append(q)
        total_q += q

    # Si excede el máximo total permitido, reducimos de a uno.
    while total_q > MAX_TOTAL_Q:
        candidates = [i for i, q in enumerate(chapters_per_anime) if q > 1]
        if not candidates:
            break
        i = rng.choice(candidates)
        chapters_per_anime[i] -= 1
        total_q -= 1

    animes: List[Anime] = []
    sum_duration_full = 0
    sum_energy_full = 0

    for i in range(n):
        q = chapters_per_anime[i]
        chapters: List[Chapter] = []
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

        animes.append(Anime(name=make_anime_name(spec.prefix, i + 1), chapters=chapters, bonus=bonus))
        sum_duration_full += full_duration
        sum_energy_full += full_energy

    def budget_from_total(total: int, low: int, high: int, cap: int) -> int:
        if total <= 0:
            return low
        frac = rng.uniform(0.35, 0.70)
        budget = int(total * frac)
        budget = clamp(budget, low, high)
        return clamp(budget, 1, cap)

    M = budget_from_total(sum_duration_full, spec.m_range[0], spec.m_range[1], MAX_M)
    E = budget_from_total(sum_energy_full, spec.e_range[0], spec.e_range[1], MAX_E)

    # En casos pequeños aseguramos que al menos haya algo visible para comparar.
    if n <= 8:
        M = max(M, min(MAX_M, max(ch.duration for a in animes for ch in a.chapters)))
        E = max(E, min(MAX_E, max(ch.energy for a in animes for ch in a.chapters)))

    return n, M, E, animes


def write_case(path: Path, n: int, M: int, E: int, animes: Iterable[Anime]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        f.write(f"{n} {M} {E}\n")
        for anime in animes:
            f.write(f"{anime.name} {len(anime.chapters)} {anime.bonus}\n")
            for ch in anime.chapters:
                f.write(f"{ch.duration} {ch.energy} {ch.value}\n")

def generate_cases(outdir: Path, seed: int) -> List[Path]:
    rng = random.Random(seed)

    # Casos acotados
    specs = [
        CaseSpec(3, (1, 4), (20, 250), (10, 120), (0, 50), (1, 120), (1, 40), (1, 15), 3, "small3"),
        CaseSpec(5, (1, 5), (30, 350), (15, 160), (0, 80), (1, 150), (1, 50), (1, 20), 3, "small5"),
        CaseSpec(8, (1, 6), (50, 500), (20, 220), (0, 120), (1, 180), (1, 60), (1, 25), 2, "small8"),
        CaseSpec(20, (2, 10), (200, 900), (60, 300), (0, 300), (1, 300), (1, 80), (1, 30), 3, "medium20"),
        CaseSpec(40, (2, 12), (400, 1400), (80, 400), (0, 500), (1, 500), (1, 100), (1, 40), 2, "medium40"),
        CaseSpec(80, (2, 12), (700, 2200), (120, 500), (0, 700), (1, 700), (1, 120), (1, 50), 1, "medium80"),
        CaseSpec(100, (2, 10), (1000, 2600), (150, 500), (0, 900), (1, 900), (1, 140), (1, 60), 1, "large100"),
        CaseSpec(150, (2, 8), (1200, 3000), (180, 500), (0, 1200), (1, 1200), (1, 160), (1, 70), 1, "large150"),
        CaseSpec(200, (1, 6), (1500, 3000), (200, 500), (0, 1500), (1, 1500), (1, 180), (1, 80), 1, "large200"),
    ]

    generated_paths: List[Path] = []
    for spec in specs:
        for i in range(1, spec.count + 1):
            n, M, E, animes = build_case(rng, spec, i)
            filename = f"testcases_{spec.n}_{i}.txt"
            path = outdir / filename
            write_case(path, n, M, E, animes)
            generated_paths.append(path)

    return generated_paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Generador de casos de prueba para AniMaraton")
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
