# Características modernas del lector — contrato (2026)

Capa opcional sobre el port fiel. Regla de oro: **nada de esto modifica los
manifests, behaviors ni la estética replicada de los números**; son servicios
del lanzador y del motor. Todo en español de cara al usuario, estética Win95
(usar `theme.*`).

## CLI (`ernreader/__main__.py`, ya implementado — no tocar)

```
python -m ernreader [--data DIR] [--scale FACTOR|auto] [--no-restore]
```

- `--scale`: factor de escalado de la interfaz. `auto` (default) lo detecta
  del DPI del display; un número (`1`, `1.5`, `2`…) lo fija.
- `--no-restore`: no ofrecer la restauración de la última sesión.

`Launcher(data_dir, scale="auto", restore=True)` recibe ambos.

## 1. Escalado HiDPI (`theme.py` + `engine.py`) — agente A

Interfaz (los stubs ya existen en `theme.py`; completar sin cambiar firmas):

- `theme.init_scale(root, requested)`: llamada por el Launcher tras crear el
  Tk root, ANTES de construir UI. `requested` es `"auto"` o float en string.
  Con `auto`: factor = `root.winfo_fpixels('1i')/96`, redondeado al 0.25 más
  cercano, clamp [1.0, 3.0]. Guarda el factor en `theme.SCALE`.
- `theme.s(px)`: `int(round(px * SCALE))`. Todo tamaño en píxeles "de diseño"
  (los del manifest, pensados para 96dpi) pasa por aquí al renderizar.
- Fuentes: los tamaños en puntos se multiplican por SCALE en
  `theme.resolve_font` / `theme.ui_font` (Tk no escala puntos con nuestro
  factor propio).

En `engine.py`, aplicar `theme.s()` de forma CONSISTENTE: geometría del
Toplevel (client_w/h y posición centrada), `_place_kwargs`, wraplength,
coordenadas de Line/Shape y BorderWidth, tamaño del base_canvas, y las
IMÁGENES: cada PIL Image se redimensiona por SCALE (NEAREST para conservar
el pixel art nítido — nada de suavizado). El muestreo de fondo de
`_sample_bg` sigue trabajando en coordenadas de diseño (la copia PIL no se
escala). El autofill de textbox opera en píxeles reales (event.width ya viene
escalado; convertir con cuidado). El degradado usa el tamaño real del canvas:
no necesita cambios.

Criterio de aceptación: con `--scale 2` los formularios miden exactamente el
doble, el texto es proporcional, el pixel art se ve nítido (bloques 2x2), y
con `--scale 1` un screenshot es IDÉNTICO al de antes del cambio (verificar
con captura + compare). `python3 tests/test_engine.py` pasa en ambos modos
(los tests corren con SCALE=1 por defecto).

## 2. Búsqueda de texto completo (`ernreader/search.py` + launcher) — agente B

- Índice: al primer uso (lazy), recorrer los manifests de todos los números:
  cada control con `text_file` o `text` largo (>200 chars) es un documento
  con (issue_id, form_name, título = caption del form o nombre, ruta o texto).
  Normalización para buscar: minúsculas + sin acentos (NFD, quitar
  combining). Búsqueda por subcadena del término normalizado; si hay varios
  términos separados por espacios, TODOS deben aparecer (AND).
- UI: ventana "Buscar en la colección" estilo Win95 (`theme.*`): Entry +
  botón "Buscar", lista de resultados "Año/Nº · título del form — …snippet…"
  (snippet: ~80 chars alrededor de la primera coincidencia, con el término
  resaltado no hace falta), contador "N resultados". Doble clic o Enter en un
  resultado abre ESE formulario de ESE número vía el Launcher.
- Launcher: botón "Buscar…" junto a "Salir" + atajo global Ctrl+F (bind en el
  root). Nuevo método `Launcher.open_issue_form(issue_id, form_name)`: crea
  la IssueSession como `open_issue` pero llama `session.show_form(form)` en
  vez de `start()`; el retorno al lanzador funciona igual. La ventana de
  búsqueda puede permanecer abierta mientras se lee (no modal).
- Usa `theme.s()` para las medidas de la ventana de búsqueda.

## 3. Persistencia de sesión (`ernreader/state.py` + launcher) — agente B

- Archivo: `~/.local/share/ernreader/state.json` (respetar `XDG_DATA_HOME`;
  en Windows `%APPDATA%/ernreader/state.json`). Crear directorio si falta.
- Guardar: `{"last_issue": "ERNSC2-3", "open_forms": ["Forma1", "anarquia"],
  "ts": <epoch>}` — actualizar al abrir un número y al volver al lanzador
  (en `on_closed`), y al cerrar la app (protocol WM_DELETE_WINDOW del root).
  Fallos de IO: log a stderr y seguir (nunca romper la app por esto).
- Restaurar: si existe estado y `restore=True`, el lanzador muestra arriba de
  la lista una fila destacada "Continuar donde te quedaste: Año X, Nº Y"
  que al hacer clic reabre ese número con sus formularios abiertos (el
  startup_form primero para que el orden de ventanas sea sensato). Nada se
  reabre automáticamente sin clic del usuario.

## 4. Accesibilidad de teclado — agente B (dentro de search/launcher)

- Lanzador: las filas de números navegables con Tab/flechas y activables con
  Enter (además del clic). Foco visible (highlightthickness en la fila
  enfocada).
- Búsqueda: Entry con foco al abrir, Enter busca, flechas mueven por
  resultados, Enter abre, Escape cierra la ventana.
- Lectores: el Text del artículo debe poder recibir foco con Tab y permitir
  scroll con teclado (ya casi lo da Tk; verificar takefocus).
- README: sección breve "Accesibilidad" con lo que hay y las limitaciones
  (arte ASCII y lectores de pantalla).
