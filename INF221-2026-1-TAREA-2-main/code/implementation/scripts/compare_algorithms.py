"""

Este script ejecuta varios binarios sobre todos los archivos .txt de una carpeta
(y compara sus salidas). Está pensado para usarse antes de integrar todo en
`general.cpp`, de modo que se pueda validar cada algoritmo por separado.

"""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple


@dataclass
class RunResult:
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False


def normalize_output(text: str) -> str:
    return text.strip()


def run_executable(exe: Path, input_file: Path, timeout: int) -> RunResult:
    try:
        with input_file.open("rb") as f:
            proc = subprocess.run(
                [str(exe)],
                stdin=f,
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
        stdout = ""
        stderr = ""
        if exc.stdout:
            stdout = exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else str(exc.stdout)
        if exc.stderr:
            stderr = exc.stderr.decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else str(exc.stderr)
        return RunResult(returncode=-1, stdout=stdout, stderr=stderr, timed_out=True)


def resolve_exec(path_like: str, base_dir: Path) -> Path:
    path = Path(path_like)
    if not path.is_absolute():
        path = (base_dir / path).resolve()
    return path


def find_input_files(inputs_dir: Path) -> List[Path]:
    if not inputs_dir.exists():
        return []
    return sorted(p for p in inputs_dir.iterdir() if p.is_file() and p.suffix.lower() == ".txt")


def main() -> int:
    parser = argparse.ArgumentParser(description="Compara salidas de algoritmos para AniMarathon")
    parser.add_argument(
        "--inputs",
        type=str,
        default=None,
        help="Carpeta con archivos .txt de entrada. Por defecto: code/implementation/data/inputs",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Tiempo máximo por ejecución (segundos)",
    )
    parser.add_argument(
        "--brute",
        type=str,
        default="brute-force.exe",
        help="Ruta del ejecutable de fuerza bruta",
    )
    parser.add_argument(
        "--dp",
        type=str,
        default="dynamic-programming.exe",
        help="Ruta del ejecutable de programación dinámica",
    )
    parser.add_argument(
        "--greedy1",
        type=str,
        default="greedy1.exe",
        help="Ruta del ejecutable greedy 1",
    )
    parser.add_argument(
        "--greedy2",
        type=str,
        default="greedy2.exe",
        help="Ruta del ejecutable greedy 2",
    )
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    default_inputs = script_dir.parent / "data" / "inputs"
    inputs_dir = Path(args.inputs).resolve() if args.inputs else default_inputs.resolve()

    executables = {
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
        print("\nCompila primero los programas o pasa sus rutas correctas con --brute/--dp/--greedy1/--greedy2.")
        return 1

    input_files = find_input_files(inputs_dir)
    if not input_files:
        print(f"No se encontraron archivos .txt en: {inputs_dir}")
        return 1

    print(f"Usando inputs desde: {inputs_dir}")
    print("Ejecutables:")
    for name, path in executables.items():
        print(f"  - {name}: {path}")
    print()

    all_ok = True
    for input_file in input_files:
        print(f"=== {input_file.name} ===")

        results: Dict[str, RunResult] = {}
        outputs: Dict[str, str] = {}

        for name, exe in executables.items():
            res = run_executable(exe, input_file, args.timeout)
            results[name] = res

            if res.timed_out:
                outputs[name] = "<TIMEOUT>"
            elif res.returncode != 0:
                outputs[name] = f"<ERROR rc={res.returncode}>"
            else:
                outputs[name] = normalize_output(res.stdout)

        for name in ["brute", "dp", "greedy1", "greedy2"]:
            print(f"{name:8s}: {outputs[name]}")

        brute_out = outputs["brute"]
        dp_out = outputs["dp"]
        if brute_out != dp_out:
            all_ok = False
            print("  -> ERROR: brute force y DP no coinciden")
        else:
            print("  -> OK: brute force y DP coinciden")

        print()

    if all_ok:
        print("Todas las comparaciones brute force vs DP coinciden en los archivos evaluados.")
        return 0

    print("Hubo diferencias entre brute force y DP en al menos un archivo.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
