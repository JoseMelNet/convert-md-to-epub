from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


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


def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for font_name in ("arial.ttf", "Arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(font_name, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


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


def wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    max_width: int,
) -> list[str]:
    words = text.split()
    if not words:
        return [""]

    lines: list[str] = []
    current_line = words[0]

    for word in words[1:]:
        candidate = f"{current_line} {word}"
        bbox = draw.textbbox((0, 0), candidate, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current_line = candidate
        else:
            lines.append(current_line)
            current_line = word

    lines.append(current_line)
    return lines


def fit_title_lines(
    draw: ImageDraw.ImageDraw,
    title: str,
    max_width: int,
) -> tuple[list[str], ImageFont.FreeTypeFont | ImageFont.ImageFont]:
    cleaned_title = " ".join(title.split())
    if not cleaned_title:
        cleaned_title = "Sin titulo"

    for font_size in range(110, 47, -6):
        font = load_font(font_size)
        lines = wrap_text(draw, cleaned_title, font, max_width)
        if len(lines) <= 6:
            return lines, font

    font = load_font(48)
    shortened = textwrap.shorten(cleaned_title, width=90, placeholder="...")
    return wrap_text(draw, shortened, font, max_width), font


def create_cover_image(title: str, author: str) -> Path:
    width, height = 1600, 2400
    background_color = "#efe4d1"
    text_color = "#2f241f"
    accent_color = "#c9b08a"

    image = Image.new("RGB", (width, height), background_color)
    draw = ImageDraw.Draw(image)

    title_area_width = width - 240
    title_lines, title_font = fit_title_lines(draw, title, title_area_width)
    author_font = load_font(52)

    title_line_height = draw.textbbox((0, 0), "Ag", font=title_font)[3]
    title_block_height = len(title_lines) * title_line_height + max(0, len(title_lines) - 1) * 24
    title_start_y = max(280, (height - title_block_height) // 2 - 160)

    draw.rounded_rectangle(
        (120, 180, width - 120, height - 180),
        radius=36,
        outline=accent_color,
        width=6,
    )

    current_y = title_start_y
    for line in title_lines:
        bbox = draw.textbbox((0, 0), line, font=title_font)
        line_width = bbox[2] - bbox[0]
        draw.text(((width - line_width) / 2, current_y), line, fill=text_color, font=title_font)
        current_y += title_line_height + 24

    author_text = author.strip() or "Autor desconocido"
    author_bbox = draw.textbbox((0, 0), author_text, font=author_font)
    author_width = author_bbox[2] - author_bbox[0]
    author_height = author_bbox[3] - author_bbox[1]
    author_y = height - 320 - author_height

    draw.line((250, author_y - 70, width - 250, author_y - 70), fill=accent_color, width=4)
    draw.text(((width - author_width) / 2, author_y), author_text, fill=text_color, font=author_font)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
        cover_path = Path(temp_file.name)

    image.save(cover_path, format="PNG")
    return cover_path


def build_command(
    pandoc_path: str,
    input_file: Path,
    output_file: Path,
    cover_image_file: Path,
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
    - --epub-cover-image: agrega una miniatura real de portada al EPUB
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
        "--epub-cover-image",
        str(cover_image_file),
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

    cover_image_file = create_cover_image(title, args.author)

    # Construye el comando final de Pandoc.
    command = build_command(
        pandoc_path=pandoc_path,
        input_file=input_file,
        output_file=output_file,
        cover_image_file=cover_image_file,
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
    finally:
        if cover_image_file.exists():
            cover_image_file.unlink()

    # Si Pandoc emitió advertencias no bloqueantes, las muestra.
    if result.stderr.strip():
        print("\nAdvertencias de Pandoc:")
        print(result.stderr.strip())

    print(f"EPUB generado correctamente: {output_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
