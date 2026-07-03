# Port de El Radiaktivo Newz — Arquitectura y contrato de datos

Port de la e-zine ERN (VB4/VB6, 1998–2000) a **Python 3.10+ / Tkinter**, prioridad Linux > Windows > macOS. Una sola aplicación con lanzador para los 10 números, **fidelidad total** al original.

## Estructura del repositorio

```
ern/
├── ERNSC1-1 … ERNSC2-5/   # Fuente original VB (NO TOCAR, solo lectura)
├── docs/PORTING.md         # Este documento (contrato entre fases)
├── tools/
│   └── extract_vb.py       # Fase 1: extractor .vbp/.frm/.frx → data/
├── data/
│   └── <ISSUE>/            # p.ej. ERNSC1-1
│       ├── manifest.json   # Formularios, controles, menús, código VB
│       ├── behavior.json   # Fase 3: eventos VB → acciones declarativas
│       ├── assets/         # PNG extraídos de .frx/.bmp/.ico
│       └── text/           # Textos largos de artículos (UTF-8)
├── ernreader/              # Fase 2: paquete Python (motor + lanzador)
│   ├── __init__.py
│   ├── __main__.py         # python -m ernreader → lanzador
│   ├── launcher.py         # Ventana de colección (elige número)
│   ├── engine.py           # Renderiza formularios desde manifest.json
│   ├── actions.py          # Intérprete de behavior.json
│   └── theme.py            # Look Win95: colores de sistema, fuentes, relieves
└── README.md
```

Dependencias permitidas: **stdlib + Pillow** únicamente.

## Datos del fuente original

- `ERNSC1-1`…`ERNSC2-2`: formato **VB4** (`VERSION 4.00`). `ERNSC2-3`…`ERNSC2-5`: **VB5/6** (`VERSION 5.00`). Los dos difieren en detalles del .frm (VB4 usa `BeginProperty Font {…}` con sintaxis ligeramente distinta, nombres `name` en minúscula, etc.) y en el formato de registros .frx.
- Encoding de .vbp/.frm/.frx: **CP1252**. Todo el output (JSON, .txt) va en **UTF-8**. Los nombres de archivo en disco están en UTF-8 (`Aclaración.frm`) aunque el .vbp los referencie en CP1252 — resolver referencias de forma tolerante (normalizar/transcodificar al buscar el archivo).
- Propiedades largas referencian el .frx: `Text = "anarquia.frx":030A` (offset hex). Ahí viven los textos de artículos (¡preservar el arte ASCII intacto!), iconos y fondos.
- Unidades: **twips**. Conversión: `px = round(twips / 15)` (1440 twips/pulgada @ 96 dpi).

## Fase 1 — Extractor (`tools/extract_vb.py`)

CLI: `python3 tools/extract_vb.py [--issue ERNSC1-1] [--all]` → escribe `data/<ISSUE>/…`. Debe ser **idempotente** y terminar con un resumen por número (formularios, controles, textos, imágenes extraídas, y CERO referencias .frx sin resolver).

### manifest.json

```json
{
  "issue_id": "ERNSC1-1",
  "title": "El Radiactivo News",
  "version_comments": "El Radiactivo News, Agosto 1998. Número 1, Año I",
  "vb_version": 4,
  "startup_form": "Form1",
  "form_order": ["Form1", "Form2", "…"],
  "forms": {
    "Form1": {
      "file": "Form1.frm",
      "caption": "BadBit presenta: EL Radiactivo News",
      "client_w": 437, "client_h": 302,
      "border_style": 1,
      "max_button": false, "min_button": false,
      "back_color": "#800000",
      "fore_color": null,
      "icon": "assets/Form1.icon.png",
      "picture": "assets/Form1.picture.png",
      "font": {"name": "MS Sans Serif", "size": 8, "bold": false, "italic": false, "underline": false},
      "controls": [ /* en orden de aparición en el .frm (z-order) */ ],
      "menu": [
        {"name": "dfdfgrg", "caption": "&Archivo", "children": [
          {"name": "dgtgtg", "caption": "&Extraer", "shortcut": "^E", "children": []},
          {"name": "dfkmo", "caption": "-", "children": []}
        ]}
      ],
      "code": "Private Sub Command1_Click()\n…código VB crudo en UTF-8…\nEnd Sub\n"
    }
  }
}
```

- `startup_form`: de `Startup="…"` en el .vbp; si falta, `IconForm`; si falta, el primer `Form=`. OJO: en VB5 el valor de Startup lleva comillas; en VB4 puede no llevarlas. Si `Startup` apunta al *nombre interno* del form (Attribute VB_Name) y no al archivo, resolver por nombre interno.
- Claves de `forms`: el **nombre interno** (`Attribute VB_Name`), no el nombre de archivo.

### Objeto control

```json
{
  "type": "CommandButton",
  "name": "Command1",
  "index": null,
  "x": 208, "y": 264, "w": 105, "h": 25,
  "caption": "Aclaración",
  "text": null,
  "text_file": null,
  "picture": null,
  "font": {"name": "Courier New", "size": 9, "bold": false, "italic": false, "underline": false},
  "fore_color": "#FFFFFF", "back_color": "#000000", "back_style": 1,
  "border_style": null, "alignment": 0,
  "multiline": true, "scrollbars": 3, "locked": true,
  "visible": true, "enabled": true,
  "auto_size": false, "word_wrap": true, "stretch": false,
  "interval": null, "tab_index": 1,
  "children": [],
  "raw": {"WhatsThisHelp": "-1"}
}
```

- `type`: último segmento del `Begin VB.CommandButton Command1` (sin prefijo `VB.`). Tipos esperados: CommandButton, Label, TextBox, Image, PictureBox, Frame, Timer, Line, Shape, CheckBox, OptionButton, ListBox, ComboBox, HScrollBar, VScrollBar, FileListBox, DirListBox, DriveListBox, CommonDialog (y OCX raros: registrarlos con su nombre y `raw`, no fallar).
- Campos no aplicables al tipo → `null`/ausentes. Propiedades no mapeadas → `raw` (strings crudos).
- `index`: para control arrays (`Index = 0`).
- Controles anidados (dentro de Frame/PictureBox) → `children` del contenedor, coordenadas relativas al contenedor (así vienen en el .frm).
- Texto corto inline en `text`/`caption`; texto de .frx o >200 chars → archivo `text/<Form>_<control>.txt` (UTF-8, **preservar CRLF→LF pero nada más**; ni trim ni re-wrap) y ruta en `text_file`.
- `Line`/`Shape`: guardar `x1,y1,x2,y2` / `shape` en `raw`.

### Colores

- `&H00BBGGRR&` → `"#RRGGBB"`.
- Colores de sistema `&H8000000X&` → resolver a la paleta clásica Win95 y emitir hex. Tabla mínima: 05 Window `#FFFFFF`, 08 WindowText `#000000`, 0F ButtonFace `#C0C0C0`, 12 ButtonText `#000000`, 0D Highlight `#000080`, 0E HighlightText `#FFFFFF`, 10 ButtonShadow `#808080`, 14 ButtonHighlight `#FFFFFF`, 01 Desktop `#008080`, 02 ActiveTitle `#000080`, 0A InactiveTitle `#808080`. Guardar también el valor original en `raw["_color_<prop>"]`.

### FRX

Registros referenciados como `"archivo.frx":OFFSETHEX`. Formatos (validar empíricamente, difieren entre VB4 y VB5/6):

- **Texto largo** (VB5/6): en el offset, longitud de 4 bytes little-endian + bytes CP1252. En VB4 puede ser longitud de 2 bytes o record con cabecera distinta — **verificar contra los datos reales**: la longitud extraída debe caer dentro del archivo y el contenido decodificar como texto plausible; si el heurístico de 4 bytes da longitud absurda, probar 2 bytes, y probar cabecera de 12 bytes.
- **Imágenes** (Icon/Picture): record con cabecera (habitualmente 12 bytes: `lt`+tamaños, o 8 bytes en VB4) seguida de payload BMP (`BM`), ICO (`\x00\x00\x01\x00`), WMF, GIF o JPEG. Estrategia robusta: leer tamaño del record y buscar la firma conocida en los primeros ~24 bytes tras el offset. Convertir todo a **PNG** con Pillow (ICO: el frame de mayor tamaño; preservar transparencia). Un registro de imagen vacío (tamaño 0) → `null`.
- Los .bmp sueltos de las carpetas también se convierten a PNG en assets si algún control los referencia; si no, ignorarlos.
- Nombre de asset: `assets/<Form>.<prop>.png` para forms, `assets/<Form>.<control>.<prop>.png` para controles.

### Código VB

Todo lo que sigue tras la última línea `Attribute …` del .frm es código de eventos → campo `code` (UTF-8, tal cual). El extractor NO interpreta el código.

## Fase 2 — Motor Tkinter (`ernreader/`)

- `python -m ernreader` abre el **lanzador**: ventana estilo Win95 (fondo `#C0C0C0`, botones raised, tipografía de 8pt) listando los 10 números con título y fecha (de `version_comments`). Al elegir uno se abre su `startup_form`.
- Cada formulario VB → `tk.Toplevel` con `place()` en píxeles según el manifest (client_w/client_h exactos, `resizable` según border_style: 1=Fixed → no redimensionable, 2=Sizable → sí).
- Mapeo de controles: CommandButton→`tk.Button`; Label→`tk.Label` (anchor según alignment, `wraplength` si word_wrap); TextBox multiline→`tk.Text` (readonly si locked, scrollbars según `scrollbars`: 1=H,2=V,3=ambos) y single-line→`tk.Entry`; Image/PictureBox→`tk.Label` con imagen (PIL.ImageTk; PictureBox puede ser contenedor→`tk.Frame`); Frame→`tk.LabelFrame`; Timer→`widget.after(interval)`; CheckBox/OptionButton→tk equivalentes con estilo clásico; Line/Shape→`tk.Canvas` a pantalla completa del form por debajo de los widgets, o canvas individual.
- Fondos de formulario (`picture`): label de fondo a tamaño completo, o canvas. Los controles `BackStyle=0` (transparente) sobre fondo: aproximar poniendo el mismo color de fondo del form; documentar la limitación.
- Fuentes: mapa en `theme.py` — "MS Sans Serif"→("Liberation Sans" o "DejaVu Sans", tamaño equivalente), "Courier New"→("Courier New" si existe, si no "Liberation Mono"/"DejaVu Sans Mono"), "FixedSys"/"Terminal"→mono, "Times New Roman"→serif. Tamaños VB son en puntos: usar tal cual (negativo en Tk = píxeles; usar positivo=puntos).
- Menús VB → `tk.Menu` del Toplevel; shortcuts `^E` → `Control-e` bind + accelerator visible; caption `-` → separador; `&X` → underline en la letra X.
- El motor lee `behavior.json` y conecta eventos vía `actions.py`. Si un evento no tiene entrada → no-op silencioso con log en stderr.
- Cerrar la última ventana de un número vuelve al lanzador. `quit` (End de VB) cierra el número, no la app entera.

## Fase 3 — behavior.json

Traducción del campo `code` de cada form a acciones declarativas:

```json
{
  "forms": {
    "anarquia": {
      "on_load": [],
      "events": {
        "dgtgtg.Click": [{"op": "save_text", "source": "txtEdit", "suggest_name": "pedo.txt"}],
        "fkvmori.Click": [{"op": "close"}]
      }
    }
  }
}
```

Vocabulario de ops (implementado por `actions.py`):

| op | args | VB equivalente |
|---|---|---|
| `show_form` | `form`, `modal?` | `Form2.Show [1]` |
| `close` | `form?` (default: el propio) | `Unload Me` / `Me.Hide` |
| `quit` | — | `End` |
| `save_text` | `source` (control), `suggest_name?` | `Open … For Output / Print #1, txtEdit.Text` (en el port: diálogo Guardar como) |
| `set_prop` | `target` ("Form.Control" o "Control"), `prop` (caption/text/visible/enabled/fore_color/back_color/left/top), `value` | asignaciones |
| `msgbox` | `text`, `title?`, `icon?` | `MsgBox` |
| `clock` | `target`, `what` ("time"/"date") | `Label1.Caption = Time$` en Timer |
| `move_by` | `target`, `dx`, `dy`, `wrap?` | animaciones con Move/Left=Left+n en Timer |
| `open_url` | `url` | ShellExecute a web/mailto |
| `beep` | — | `Beep` |
| `sequence`/condicionales | usar lista de ops; para `If` simples: `{"op":"toggle_visible","target":…}` |
| `unsupported` | `code` (VB crudo), `note` | todo lo que no encaje — el motor lo loguea y no revienta |

Regla de oro: **ante la duda, `unsupported` con el código crudo** — nunca inventar semántica. Un pase posterior revisa los `unsupported`.

## Fase 4 — Validación

Script `tools/validate.py`: por cada número comprueba (a) nº de forms en manifest == nº de `Form=` del .vbp resolubles, (b) todo `text_file`/`picture`/`icon` referenciado existe en disco, (c) cero offsets .frx sin extraer, (d) todo evento `<ctrl>.Click` de behavior.json referencia un control existente, (e) todo `show_form` apunta a un form existente, (f) recuento de `Private Sub` en `code` vs eventos mapeados+unsupported. Salida: tabla y exit code ≠0 si algo falla.
