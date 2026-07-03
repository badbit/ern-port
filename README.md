# El Radiaktivo Newz

> *"El Radiaktivo Newz, [mes] [año]. Número [n], Año [I/II]"*
> — de los créditos originales de cada número

**El Radiaktivo Newz** (también conocida en sus primeros números como *El
Radiactivo News*) fue una e-zine hacker mexicana publicada entre **1998 y
2000**. Se distribuía como un ejecutable autocontenido hecho en **Visual
Basic 4 / Visual Basic 6**: una pequeña aplicación de escritorio, con su
propio look Win95, menús, botones y ventanas, en lugar de un simple
documento de texto. Se publicaron 10 números (Año I, números 1 a 6, y Año
II, números 2 a 5).

Este repositorio es un **port funcional a Python 3 / Tkinter** de esos 10
números, hecho en 2026 como trabajo de **preservación histórica**: el
objetivo no es "modernizar" la revista ni reinterpretarla, sino conseguir
que vuelva a arrancar, tal cual era, en un sistema operativo actual —sin
máquina virtual de Windows, sin VB6 Runtime, sin depender de que Windows
9x siga vivo en algún disco duro.

## Qué NO cambia

El port preserva con fidelidad el original:

- **Los layouts** de cada ventana, con las mismas coordenadas, tamaños y
  proporciones que el .frm original (convertidas de twips a píxeles).
- **Los textos**, incluido el **arte ASCII** de los artículos, carácter por
  carácter — no se re-envuelven líneas ni se "limpian" espacios.
- **Los easter eggs** y comportamientos de la interfaz (botones que hacen
  cosas raras, mensajes ocultos, etc.), traducidos del código VB original a
  un pequeño lenguaje de acciones declarativas (ver `docs/PORTING.md`).
- **Los colores** de la época: la paleta gris/azul marino de Windows 95/98,
  reproducida tal cual el .frm la definía (incluyendo colores de sistema
  como `ButtonFace` o `Highlight`).

Nada de esto se ha "arreglado" ni embellecido. Si un número tenía un botón
que no hacía nada o un texto con una errata, sigue teniéndolo aquí.

## Instalación y ejecución

Requisitos en cualquier plataforma: **Python 3.10 o superior** y la
librería **Pillow** (la única dependencia externa; Tkinter viene incluido
en Python salvo en algunas distribuciones de Linux, ver más abajo).

### Linux

En la mayoría de distribuciones, Python 3 ya viene instalado, pero
**Tkinter suele empaquetarse aparte**:

```bash
# Debian / Ubuntu / Mint
sudo apt install python3 python3-tk python3-pip

# Fedora
sudo dnf install python3 python3-tkinter python3-pip

# Arch / Manjaro
sudo pacman -S python tk python-pip
```

Después, desde la raíz del repositorio:

```bash
python3 -m pip install --user -r requirements.txt
python3 -m ernreader
```

O, más cómodo, usando el script de arranque incluido (detecta Python,
comprueba Pillow y la instala si hace falta, preguntando primero):

```bash
./run.sh
```

### Windows

1. Instala Python 3.10+ desde [python.org](https://www.python.org/downloads/).
   Durante la instalación, marca la casilla **"Add python.exe to PATH"**.
   El instalador oficial de Windows ya incluye Tkinter (Tcl/Tk), no hace
   falta nada aparte.
2. Instala Pillow (o deja que `run.bat` lo haga por ti):

   ```bat
   py -3 -m pip install --user -r requirements.txt
   ```
3. Ejecuta:

   ```bat
   py -3 -m ernreader
   ```

   O simplemente haz doble clic en **`run.bat`** (detecta Python, revisa
   Pillow y te pregunta antes de instalar nada).

### macOS

El Python del sistema en macOS moderno no siempre trae Tkinter con buen
soporte; se recomienda instalar Python vía Homebrew, que sí lo incluye:

```bash
brew install python-tk
python3 -m pip install --user -r requirements.txt
python3 -m ernreader
```

O bien:

```bash
./run.sh
```

### Argumentos

Por defecto el lanzador busca los números en `data/`. Para usar otra
carpeta de datos (por ejemplo al probar una extracción parcial):

```bash
python3 -m ernreader --data data
```

## Estructura del repositorio

```
ern/
├── ERNSC1-1 … ERNSC2-5/   # Fuente VB original (solo lectura, no se toca)
├── docs/PORTING.md        # Arquitectura completa del pipeline de port
├── tools/                 # Extracción y validación (no se ejecutan al leer la revista)
│   ├── extract_vb.py      #   .vbp/.frm/.frx  ->  data/<ISSUE>/manifest.json + assets/ + text/
│   ├── convert_emf.py     #   post-proceso: rasteriza fondos EMF/WMF que Pillow no soporta
│   └── validate.py        #   comprueba consistencia de todo lo extraído
├── data/                  # Los 10 números ya extraídos (esto es lo que lee ernreader)
│   └── <ISSUE>/
│       ├── manifest.json  #   formularios, controles, menús y código VB por número
│       ├── behavior.json  #   eventos VB traducidos a acciones declarativas
│       ├── assets/        #   imágenes (iconos, fondos) convertidas a PNG
│       └── text/          #   artículos largos y arte ASCII, en UTF-8
├── ernreader/             # El lector en sí (Python 3 / Tkinter)
│   ├── __main__.py        #   `python -m ernreader` -> abre el lanzador
│   ├── launcher.py        #   ventana de colección: elige uno de los 10 números
│   ├── engine.py          #   renderiza formularios Win95 desde manifest.json
│   ├── actions.py         #   intérprete de behavior.json (los "easter eggs")
│   └── theme.py           #   colores de sistema Win95, mapeo de fuentes, estilos
├── tests/                 # Suite de pruebas del motor
└── README.md               # Este documento
```

- **`tools/`** solo hace falta si quieres *regenerar* `data/` desde las
  carpetas `ERNSC*`; para leer la revista no se necesita.
- **`ernreader/`** es la aplicación: no conoce Visual Basic, solo sabe leer
  el `manifest.json`/`behavior.json` de cada número.
- **`data/`** es, en la práctica, el contenido de la revista ya extraído:
  se versiona en el repositorio junto con el código porque es parte del
  producto final, no un artefacto de compilación.

Para el detalle técnico completo del formato de `manifest.json`,
`behavior.json` y las decisiones de mapeo VB → Tkinter, ver
[`docs/PORTING.md`](docs/PORTING.md).

## Regenerar los datos desde el fuente

Los 10 números ya vienen extraídos en `data/`, pero si tocas el extractor
o quieres reproducir el proceso desde cero:

```bash
# 1. Extraer todos los números (.vbp/.frm/.frx -> data/<ISSUE>/)
python3 tools/extract_vb.py --all

# (o un solo número, para iterar más rápido)
python3 tools/extract_vb.py --issue ERNSC1-1

# 2. Post-proceso: rasterizar los fondos en formato EMF/WMF que Pillow no
#    sabe abrir directamente. Requiere LibreOffice instalado (usa su modo
#    headless para la conversión); si no lo tienes, este paso se puede
#    omitir y esos fondos concretos quedarán sin imagen.
python3 tools/convert_emf.py
```

El extractor es idempotente: se puede volver a correr sobre `data/` las
veces que haga falta sin acumular basura.

**Nota:** no existe fuente para el **Año II Nº1** — del autor solo se
conserva el `.exe` compilado, no el proyecto VB. Por eso el lanzador
muestra 10 números en vez de 11 (Año I: 1–6, Año II: 2–5).

## Validar y testear

```bash
# Suite de pruebas del motor (mapeo de controles, intérprete de acciones,
# ciclo de vida de ventanas, etc.)
python3 tests/test_engine.py

# Validación de consistencia de los datos extraídos: formularios, texto
# y assets referenciados existen en disco, offsets .frx resueltos, eventos
# de behavior.json apuntan a controles/formularios reales, etc.
python3 tools/validate.py
```

`validate.py` termina con código de salida distinto de cero si encuentra
algo roto; las advertencias informativas (código huérfano de VB que
referencia controles que ya no existen, herencia real de los .frm
originales) no cuentan como fallo.

## Estado del port

**Funciona:** los 10 números arrancan, el lanzador lista los números
leyendo `version_comments` de cada `manifest.json`, se navega entre
formularios, los textos largos y el arte ASCII se muestran íntegros, los
menús y atajos de teclado están operativos, y el intérprete de
`behavior.json` cubre la gran mayoría de los eventos originales (mostrar
formularios, guardar texto, cambiar propiedades, relojes, animaciones,
`MsgBox`, abrir URLs, etc.). Lo que no se pudo traducir a una acción
declarativa queda marcado como `unsupported` con el código VB crudo
adjunto, y se loguea por stderr sin interrumpir la ejecución.

**Limitaciones conocidas:**

- En algunos números, el **bitmap de título estilizado** (el logo/banner
  hecho a mano en el .frm original) aparece recortado respecto al
  original.
- En los números **Año II Nº4 y Nº5**, algunas **ventanas de splash/intro**
  se solapan en vez de mostrarse en la secuencia exacta del original.
- Los **controles OCX poco comunes** (por ejemplo `StatusBar` o
  `ProgressBar` de terceros) no tienen equivalente directo en Tkinter; se
  muestran como un **placeholder visible** (`[NombreDelTipo]`) en lugar de
  fallar o desaparecer silenciosamente.
- La **transparencia** de controles con `BackStyle=0` se **aproxima**
  heredando el color de fondo del contenedor padre, en vez de un
  compositing real; en la mayoría de los casos es indistinguible del
  original, pero puede notarse sobre fondos con imagen.

Ninguna de estas limitaciones impide leer o navegar ningún número
completo; son matices visuales de fidelidad, documentados aquí para quien
quiera seguir puliéndolos.

## Créditos

**El Radiaktivo Newz** es obra de **BadBit** y el resto del **El
Radiaktivo Newz Team**, autores originales de la revista entre 1998 y
2000 (créditos tomados de los propios proyectos VB: `VersionCompanyName`,
`VersionLegalCopyright` y `VersionProductName` de cada `.vbp`, que a lo
largo de los números citan variamente "BadBit.net", "BadBit Corp." y "El
Radiaktivo Newz Team").

El port a Python 3 / Tkinter para sistemas operativos modernos (Linux,
Windows, macOS) se realizó en 2026, como proyecto de preservación de este
pedazo de historia de la escena hacker mexicana.

---

*Licencia: GNU General Public License v2.0 (GPLv2), la misma con la que
BadBit / El Radiaktivo Newz Team publicó originalmente el código fuente
de esta revista. Ver el archivo `LICENSE`.*
