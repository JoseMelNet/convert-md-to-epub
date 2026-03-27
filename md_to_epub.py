from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
INPUT_DIR = BASE_DIR / "input_md"
OUTPUT_DIR = BASE_DIR / "output_epub"
LOCAL_PANDOC_CANDIDATES = [
    Path(r"C:\Users\josem\AppData\Local\Pandoc\pandoc.exe"),
    BASE_DIR / "tools" / "pandoc" / "pandoc.exe",
    BASE_DIR / "pandoc.exe",
    BASE_DIR / "pandoc" / "pandoc.exe",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convierte un archivo Markdown ubicado en input_md/ a EPUB en output_epub/ usando Pandoc."
    )
    parser.add_argument("filename", help="Nombre del archivo Markdown, por ejemplo: documento.md")
    parser.add_argument("--title", help="Titulo del EPUB")
    parser.add_argument("--author", default="Autor desconocido", help="Autor del EPUB")
    parser.add_argument("--lang", default="es", help="Idioma del EPUB")
    return parser.parse_args()


def resolve_pandoc() -> str | None:
    env_path = os.environ.get("PANDOC_PATH", "").strip()
    if env_path:
        candidate = Path(env_path).expanduser()
        if candidate.exists() and candidate.is_file():
            return str(candidate)

    for candidate in LOCAL_PANDOC_CANDIDATES:
        if candidate.exists() and candidate.is_file():
            return str(candidate)

    return shutil.which("pandoc")


def main() -> int:
    args = parse_args()

    if INPUT_DIR.exists() is False or INPUT_DIR.is_dir() is False:
        print(f"Error: la carpeta de entrada no existe: {INPUT_DIR}", file=sys.stderr)
        return 1

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    pandoc_path = resolve_pandoc()
    if pandoc_path is None:
        print(
            "Error: no se encontro Pandoc. Define PANDOC_PATH, coloca pandoc.exe en tools/pandoc/ o instalalo en PATH.",
            file=sys.stderr,
        )
        return 1

    input_name = Path(args.filename).name
    if Path(input_name).suffix.lower() != ".md":
        print("Error: el archivo debe tener extension .md", file=sys.stderr)
        return 1

    input_file = INPUT_DIR / input_name
    if input_file.exists() is False or input_file.is_file() is False:
        print(f"Error: no se encontro el archivo Markdown: {input_file}", file=sys.stderr)
        return 1

    output_file = OUTPUT_DIR / f"{input_file.stem}.epub"
    title = args.title or input_file.stem

    command = [
        pandoc_path,
        str(input_file),
        "-o",
        str(output_file),
        "--toc",
        "--standalone",
        "--metadata",
        f"title={title}",
        "--metadata",
        f"author={args.author}",
        "--metadata",
        f"lang={args.lang}",
    ]

    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as exc:
        print(f"Error: Pandoc fallo durante la conversion (codigo {exc.returncode}).", file=sys.stderr)
        return exc.returncode or 1
    except OSError as exc:
        print(f"Error: no se pudo ejecutar Pandoc: {exc}", file=sys.stderr)
        return 1

    print(f"EPUB generado correctamente: {output_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
