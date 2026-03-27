from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


# Rutas base del proyecto.
# BASE_DIR apunta a la carpeta donde vive este script.
# INPUT_DIR es la carpeta fija donde deben estar los archivos .md.
# OUTPUT_DIR es la carpeta fija donde se escribirán los .epub.
BASE_DIR = Path(__file__).resolve().parent
INPUT_DIR = BASE_DIR / "input_md"
OUTPUT_DIR = BASE_DIR / "output_epub"

# Ubicaciones locales opcionales donde también se puede buscar Pandoc
# antes de intentar encontrarlo en el PATH del sistema.
LOCAL_PANDOC_CANDIDATES = [
    BASE_DIR / "tools" / "pandoc" / "pandoc.exe",
]


def parse_args() -> argparse.Namespace:
    """
    Define y procesa los argumentos de línea de comandos.

    Parámetros:
    - filename: nombre del archivo Markdown dentro de input_md/
    - --title: título opcional del EPUB
    - --author: autor opcional del EPUB
    - --lang: idioma opcional del EPUB
    - --force: fuerza la reconversión aunque el EPUB ya exista y esté actualizado
    """
    parser = argparse.ArgumentParser(
        description="Convierte un archivo Markdown ubicado en input_md/ a EPUB en output_epub/ usando Pandoc."
    )
    parser.add_argument("filename", help="Nombre del archivo Markdown, por ejemplo: documento.md")
    parser.add_argument("--title", help="Título del EPUB")
    parser.add_argument("--author", default="Autor desconocido", help="Autor del EPUB")
    parser.add_argument("--lang", default="es", help="Idioma del EPUB")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Fuerza la reconversión incluso si el EPUB ya existe y está actualizado.",
    )
    return parser.parse_args()


def resolve_pandoc() -> str | None:
    """
    Intenta localizar el ejecutable de Pandoc en este orden:

    1. Variable de entorno PANDOC_PATH
    2. Rutas locales definidas en LOCAL_PANDOC_CANDIDATES
    3. PATH del sistema usando shutil.which("pandoc")

    Devuelve la ruta al ejecutable si lo encuentra, o None si no está disponible.
    """
    env_path = os.environ.get("PANDOC_PATH", "").strip()
    if env_path:
        candidate = Path(env_path).expanduser()
        if candidate.exists() and candidate.is_file():
            return str(candidate)

    for candidate in LOCAL_PANDOC_CANDIDATES:
        if candidate.exists() and candidate.is_file():
            return str(candidate)

    return shutil.which("pandoc")


def validate_pandoc(pandoc_path: str) -> bool:
    """
    Verifica que Pandoc realmente pueda ejecutarse.

    Ejecuta 'pandoc --version' y devuelve True si responde correctamente.
    Si falla la ejecución o el binario no es válido, devuelve False.
    """
    try:
        result = subprocess.run(
            [pandoc_path, "--version"],
            capture_output=True,
            text=True,
            check=True,
        )
        return bool(result.stdout.strip())
    except (subprocess.CalledProcessError, OSError):
        return False


def build_command(
    pandoc_path: str,
    input_file: Path,
    output_file: Path,
    title: str,
    author: str,
    lang: str,
) -> list[str]:
    """
    Construye el comando de Pandoc que hará la conversión de Markdown a EPUB.

    Opciones incluidas:
    - --toc: agrega tabla de contenido
    - --standalone: genera un archivo EPUB completo
    - --epub-chapter-level=2: usa encabezados hasta nivel 2 para separar capítulos
    - --metadata: define título, autor e idioma del EPUB
    """
    return [
        pandoc_path,
        input_file.name,
        "-o",
        str(output_file),
        "--toc",
        "--standalone",
        "--split-level=2",
        "--mathml",
        "--metadata",
        f"title={title}",
        "--metadata",
        f"author={author}",
        "--metadata",
        f"lang={lang}",
    ]


def main() -> int:
    """
    Orquesta el flujo completo de conversión:

    1. Lee argumentos.
    2. Valida carpetas de entrada y salida.
    3. Localiza y valida Pandoc.
    4. Valida que el archivo .md exista.
    5. Determina si hace falta reconvertir.
    6. Ejecuta Pandoc.
    7. Reporta advertencias o errores.
    """
    args = parse_args()

    # Verifica que exista la carpeta de entrada.
    if not INPUT_DIR.is_dir():
        print(f"Error: la carpeta de entrada no existe: {INPUT_DIR}", file=sys.stderr)
        return 1

    # Crea la carpeta de salida si no existe.
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Localiza Pandoc.
    pandoc_path = resolve_pandoc()
    if pandoc_path is None:
        print(
            "Error: no se encontró Pandoc. Define PANDOC_PATH, coloca pandoc.exe en tools/pandoc/ o instálalo en PATH.",
            file=sys.stderr,
        )
        return 1

    # Verifica que Pandoc realmente pueda ejecutarse.
    if not validate_pandoc(pandoc_path):
        print(
            f"Error: se encontró Pandoc pero no pudo ejecutarse correctamente: {pandoc_path}",
            file=sys.stderr,
        )
        return 1

    # Normaliza el nombre de archivo para evitar rutas arbitrarias
    # y exige extensión .md.
    input_name = Path(args.filename).name
    if Path(input_name).suffix.lower() != ".md":
        print("Error: el archivo debe tener extensión .md", file=sys.stderr)
        return 1

    # Construye la ruta completa del archivo fuente dentro de input_md/.
    input_file = INPUT_DIR / input_name
    if not input_file.is_file():
        print(f"Error: no se encontró el archivo Markdown: {input_file}", file=sys.stderr)
        return 1

    # Define el archivo EPUB de salida con el mismo nombre base del .md.
    output_file = OUTPUT_DIR / f"{input_file.stem}.epub"

    # Si no se pasa título, usa el nombre base del archivo.
    title = args.title or input_file.stem

    # Si el EPUB ya existe y no se forzó reconversión, compara fechas
    # para evitar trabajo innecesario.
    if output_file.exists() and not args.force:
        input_mtime = input_file.stat().st_mtime
        output_mtime = output_file.stat().st_mtime
        if output_mtime >= input_mtime:
            print(f"EPUB ya actualizado, no se requiere conversión: {output_file}")
            return 0

    # Construye el comando final de Pandoc.
    command = build_command(
        pandoc_path=pandoc_path,
        input_file=input_file,
        output_file=output_file,
        title=title,
        author=args.author,
        lang=args.lang,
    )

    try:
        # Ejecuta Pandoc desde la carpeta del archivo de entrada.
        # Esto ayuda a que las rutas relativas dentro del Markdown
        # (por ejemplo imágenes) se resuelvan correctamente.
        result = subprocess.run(
            command,
            cwd=input_file.parent,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        # Error devuelto por Pandoc durante la conversión.
        print(
            f"Error: Pandoc falló durante la conversión (código {exc.returncode}).",
            file=sys.stderr,
        )
        if exc.stderr:
            print("\n--- Detalle de Pandoc ---", file=sys.stderr)
            print(exc.stderr.strip(), file=sys.stderr)
        return exc.returncode or 1
    except OSError as exc:
        # Error del sistema al intentar ejecutar Pandoc.
        print(f"Error: no se pudo ejecutar Pandoc: {exc}", file=sys.stderr)
        return 1

    # Si Pandoc emitió advertencias no bloqueantes, las muestra.
    if result.stderr.strip():
        print("\nAdvertencias de Pandoc:")
        print(result.stderr.strip())

    print(f"EPUB generado correctamente: {output_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())