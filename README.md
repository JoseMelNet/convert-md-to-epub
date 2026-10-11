# Convert Markdown to EPUB

Utilidad local y simple para convertir archivos `.md` a `.epub` usando Pandoc.
El EPUB generado incluye una imagen de portada automatica para que se vea como miniatura en bibliotecas compatibles, sin agregar una portada HTML dentro del contenido del libro.

## Estructura del proyecto

```text
Convert_md_to_epub/
|-- input_md/
|-- output_epub/
|-- .env.example
|-- kindle_email.py
|-- md_to_epub.py
|-- README.md
|-- requirements.txt
`-- .gitignore
```

## Requisito

Necesitas `Pandoc` para generar el EPUB. El script intenta encontrarlo en este orden:

1. Variable de entorno `PANDOC_PATH`
2. Archivo local `tools/pandoc/pandoc.exe` (o `tools/pandoc/pandoc` en Linux)
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

## Uso desde el servidor Linux

En el servidor de casa (`~/projects/convert-md-to-epub`) ya esta preparado:

- Pandoc 3.11 oficial en `~/.local/bin/pandoc` (sin sudo), que el script encuentra por `PATH`.
- Pillow en un entorno propio `.venv/`, creado con `uv`, sin tocar el Python del sistema.
- `.env` con las credenciales SMTP, en `chmod 600` y fuera de git.

Si hay que montarlo de nuevo:

```bash
uv venv .venv && uv pip install --python .venv/bin/python -r requirements.txt
curl -LO https://github.com/jgm/pandoc/releases/download/3.11/pandoc-3.11-linux-amd64.tar.gz
tar xzf pandoc-3.11-linux-amd64.tar.gz && cp pandoc-3.11/bin/pandoc ~/.local/bin/
cp .env.example .env && chmod 600 .env   # y llenarlo a mano
```

Traer un documento del PC Windows (zbook) y enviarlo al Kindle:

```bash
scp "zbook:C:/Users/josem/ruta/con espacios/documento.md" input_md/
.venv/bin/python md_to_epub.py documento.md --title "Titulo" --author "Autor" --send-kindle
```

La primera vez que Amazon recibe de un remitente puede pedir confirmacion por correo.

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

## Envio automatico a Kindle

Puedes enviar el `.epub` generado a tu direccion `Send to Kindle` usando SMTP.

Antes de usarlo:

- identifica tu correo Kindle en Amazon
- autoriza el correo remitente en la configuracion de documentos personales de Amazon
- usa una cuenta SMTP valida, normalmente con app password si tu proveedor lo exige

### Archivo .env

El script carga automaticamente un archivo `.env` ubicado en la raiz del proyecto.

Puedes crear tu archivo a partir de `.env.example` y dejar algo asi:

```dotenv
RECIPIENT_EMAIL=tu_usuario@kindle.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=tu_correo@gmail.com
SMTP_PASSWORD=tu_app_password
SENDER_EMAIL=tu_correo@gmail.com
```

Luego solo ejecutas:

```powershell
python md_to_epub.py documento.md --send-kindle
```

### Variables de entorno

```powershell
$env:RECIPIENT_EMAIL = "tu_usuario@kindle.com"
$env:SMTP_HOST = "smtp.gmail.com"
$env:SMTP_PORT = "587"
$env:SMTP_USERNAME = "tu_correo@gmail.com"
$env:SMTP_PASSWORD = "tu_app_password"
$env:SENDER_EMAIL = "tu_correo@gmail.com"
```

Luego ejecuta:

```powershell
python md_to_epub.py documento.md --send-kindle
```

### Parametros directos

```powershell
python md_to_epub.py documento.md --send-kindle `
  --kindle-email "tu_usuario@kindle.com" `
  --smtp-host "smtp.gmail.com" `
  --smtp-port 587 `
  --smtp-username "tu_correo@gmail.com" `
  --smtp-password "tu_app_password" `
  --sender-email "tu_correo@gmail.com"
```

Notas:

- por defecto el script usa `STARTTLS`
- si tu servidor requiere SSL directo, agrega `--smtp-ssl`
- si el `.epub` ya estaba generado y actualizado, `--send-kindle` lo envia igual sin reconvertir

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
