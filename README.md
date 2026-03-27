# Convert Markdown to EPUB

Utilidad local y simple para convertir archivos `.md` a `.epub` usando Pandoc.

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
2. Ruta fija `C:\Users\josem\AppData\Local\Pandoc\pandoc.exe`
3. Archivo local `tools/pandoc/pandoc.exe`
4. Archivo local `pandoc.exe` en la raiz del proyecto
5. `pandoc` disponible en `PATH`

### Opcion recomendada en Windows sin depender de PATH

Coloca `pandoc.exe` en:

```text
tools/pandoc/pandoc.exe
```

### Opcion por variable de entorno

```powershell
$env:PANDOC_PATH = "C:\ruta\a\pandoc.exe"
python .\md_to_epub.py documento.md
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
python .\md_to_epub.py documento.md
```

El script tomara:

- entrada: `input_md/documento.md`
- salida: `output_epub/documento.epub`

## Metadatos opcionales

Puedes definir metadatos del EPUB con estos parametros:

```powershell
python .\md_to_epub.py documento.md --title "Mi libro" --author "Jose" --lang es
```

Valores por defecto:

- `title`: nombre base del archivo
- `author`: `Autor desconocido`
- `lang`: `es`

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
