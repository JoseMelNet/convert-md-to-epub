# Convert Markdown to EPUB

Utilidad local y simple para convertir archivos `.md` a `.epub` usando Pandoc.
El EPUB generado incluye una imagen de portada automatica para que se vea como miniatura en bibliotecas compatibles, sin agregar una portada HTML dentro del contenido del libro.

## Estructura del proyecto

```text
Convert_md_to_epub/
|-- input_md/
|-- output_epub/
|-- md_to_epub.py
|-- README.md
|-- requirements.txt
`-- .gitignore
```

## Requisito

Necesitas `Pandoc` para generar el EPUB. El script intenta encontrarlo en este orden:

1. Variable de entorno `PANDOC_PATH`
2. Archivo local `tools/pandoc/pandoc.exe`
3. `pandoc` disponible en `PATH`

Tambien necesitas instalar las dependencias de Python:

```powershell
pip install -r requirements.txt
```

### Opcion recomendada en Windows sin depender de PATH

Coloca `pandoc.exe` en:

```text
tools/pandoc/pandoc.exe
```

### Opcion por variable de entorno

```powershell
$env:PANDOC_PATH = "C:\ruta\a\pandoc.exe"
python md_to_epub.py documento.md
```

### Opcion tradicional por PATH

Puedes verificarlo con:

```powershell
pandoc --version
```

## Uso

Coloca tus archivos Markdown dentro de la carpeta `input_md/`.

Ejecuta el script pasando solo el nombre del archivo:

```powershell
python md_to_epub.py documento.md
```

El script tomara:

- entrada: `input_md/documento.md`
- salida: `output_epub/documento.epub`

Si el archivo `.epub` ya existe y es mas reciente que el `.md`, el script no reconvierte el archivo.

## Metadatos opcionales

Puedes definir metadatos del EPUB con estos parametros:

```powershell
python md_to_epub.py documento.md --title "Mi libro" --author "Jose" --lang es
```

Valores por defecto:

- `title`: nombre base del archivo
- `author`: `Autor desconocido`
- `lang`: `es`

## Reconversion forzada

Si quieres regenerar el EPUB aunque ya exista y este actualizado, usa:

```powershell
python md_to_epub.py documento.md --force
```

## Detalles de conversion

La conversion usa Pandoc con estas opciones:

- `--toc`
- `--standalone`
- `--split-level=2`
- `--mathml`
- `--epub-cover-image`
- `--metadata title=...`
- `--metadata author=...`
- `--metadata lang=...`

## Portada automatica

En cada conversion el script genera una imagen PNG temporal de portada con estas caracteristicas:

- formato vertical de `1600 x 2400`
- fondo claro
- titulo centrado con ajuste automatico de lineas
- autor en la parte inferior

Esa imagen se usa como portada real del EPUB para mostrar la miniatura del libro en la biblioteca del lector.
No se genera `cover.html` ni se inserta una portada interna dentro del contenido del libro.

## Donde poner los archivos `.md`

Todos los archivos Markdown deben ir en:

```text
input_md/
```

## Donde aparece el `.epub`

Los archivos EPUB generados se guardan en:

```text
output_epub/
```
