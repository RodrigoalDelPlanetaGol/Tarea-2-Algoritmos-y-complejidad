"""Validador de depuración para AniMarathon.

Este script sirve para comprobar rápidamente que los ejecutables:
  - leen bien la entrada,
  - entregan una salida numérica,
  - y coinciden con una referencia conocida en un caso de prueba manual.

Importante:
  - Como los algoritmos finales imprimen solo la satisfacción máxima,
    este script no puede reconstruir la selección exacta de capítulos.
  - Por lo mismo, no puede verificar directamente desde fuera si un
    algoritmo escogió capítulos aislados o si saltó capítulos.
  - Lo que sí verifica es la consistencia del resultado final, que en la
    práctica es la forma razonable de depurar antes de integrar todo en
    general.cpp.

Ubicación recomendada dentro del repositorio:
    code/implementation/scripts/validate_animarathon.py

Uso sugerido desde esa carpeta:
    python validate_animarathon.py

También puedes pasar rutas explícitas:
    python validate_animarathon.py --brute ../algorithms/brute-force.exe \
        --dp ../algorithms/dynamic-programming.exe --greedy1 ../algorithms/greedy1.exe \
        --greedy2 ../algorithms/greedy2.exe

El caso de referencia incorporado es el ejemplo del enunciado, cuya respuesta
correcta es 260.
"""

from __future__ import annotations

import argparse
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional


REFERENCE_INPUT = """4 240 90
shonen_quest 3 25
45 18 40
50 22 45
55 25 60
romcom_days 2 15
30 10 25
35 12 30
mecha_nova 2 50
60 30 65
70 35 75
slice_cafe 1 5
25 8 18
"""

REFERENCE_OUTPUT = "260"


@dataclass
class RunResult:
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False


def resolve_exec(path_like: str, base_dir: Path) -> Path:
    path = Path(path_like)
    if not path.is_absolute():
        path = (base_dir / path).resolve()
    return path


def run_executable(exe: Path, input_text: str, timeout: int = 30) -> RunResult:
    try:
        proc = subprocess.run(
            [str(exe)],
            input=input_text.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
        return RunResult(
            returncode=proc.returncode,
            stdout=proc.stdout.decode("utf-8", errors="replace"),
            stderr=proc.stderr.decode("utf-8", errors="replace"),
            timed_out=False,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return RunResult(returncode=-1, stdout=stdout, stderr=stderr, timed_out=True)


def normalize_output(text: str) -> str:
    return text.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Validador de depuración para AniMarathon")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout por ejecución en segundos")
    parser.add_argument("--brute", type=str, default="brute-force.exe", help="Ruta del ejecutable brute-force")
    parser.add_argument("--dp", type=str, default="dynamic-programming.exe", help="Ruta del ejecutable DP")
    parser.add_argument("--greedy1", type=str, default="greedy1.exe", help="Ruta del ejecutable greedy1")
    parser.add_argument("--greedy2", type=str, default="greedy2.exe", help="Ruta del ejecutable greedy2")
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    executables: Dict[str, Path] = {
        "brute": resolve_exec(args.brute, script_dir),
        "dp": resolve_exec(args.dp, script_dir),
        "greedy1": resolve_exec(args.greedy1, script_dir),
        "greedy2": resolve_exec(args.greedy2, script_dir),
    }

    missing = [name for name, path in executables.items() if not path.exists()]
    if missing:
        print("No se encontraron estos ejecutables:")
        for name in missing:
            print(f"  - {name}: {executables[name]}")
        return 1

    print("== Caso de referencia del enunciado ==")
    print(f"Salida esperada: {REFERENCE_OUTPUT}\n")

    all_ok = True
    for name, exe in executables.items():
        res = run_executable(exe, REFERENCE_INPUT, timeout=args.timeout)
        out = normalize_output(res.stdout) if not res.timed_out and res.returncode == 0 else f"<ERROR rc={res.returncode} timeout={res.timed_out}>"

        print(f"[{name}]")
        print(f"salida:   {out}")
        if res.stderr.strip():
            print(f"stderr:   {res.stderr.strip()}")

        if out != REFERENCE_OUTPUT:
            all_ok = False
            print("resultado: FAIL")
        else:
            print("resultado: OK")
        print()

    if all_ok:
        print("Todos los algoritmos coinciden con el caso de referencia.")
        return 0

    print("Al menos un algoritmo no coincide con la referencia.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
