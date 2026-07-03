#!/usr/bin/env bash
# run.sh -- lanzador de El Radiaktivo Newz para Linux y macOS.
#
# Busca un intérprete Python 3.10+, comprueba que Pillow (la única
# dependencia externa) esté instalada -- y si no, la instala pidiendo
# confirmación -- y arranca el lector con `python -m ernreader`.

set -u

# Nos colocamos en el directorio del script, sea cual sea el cwd desde el
# que se invoque (p.ej. doble clic, otro directorio, etc.).
cd "$(dirname "${BASH_SOURCE[0]}")" || exit 1

echo "== El Radiaktivo Newz -- lanzador (Linux/macOS) =="

# --- 1. Buscar un intérprete Python 3 ----------------------------------
PYTHON=""
for candidato in python3 python; do
    if command -v "$candidato" >/dev/null 2>&1; then
        PYTHON="$candidato"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    echo "ERROR: no se encontró 'python3' (ni 'python') en el PATH." >&2
    echo "Instala Python 3.10 o superior:" >&2
    echo "  - Debian/Ubuntu:  sudo apt install python3 python3-tk python3-pip" >&2
    echo "  - Fedora:         sudo dnf install python3 python3-tkinter python3-pip" >&2
    echo "  - Arch:           sudo pacman -S python tk python-pip" >&2
    echo "  - macOS (Homebrew): brew install python-tk" >&2
    exit 1
fi

VERSION=$("$PYTHON" -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null)
echo "Usando $PYTHON (Python $VERSION)"

MAYOR=$("$PYTHON" -c 'import sys; print(sys.version_info[0])')
MENOR=$("$PYTHON" -c 'import sys; print(sys.version_info[1])')
if [ "$MAYOR" -lt 3 ] || { [ "$MAYOR" -eq 3 ] && [ "$MENOR" -lt 10 ]; }; then
    echo "AVISO: se recomienda Python 3.10 o superior; tienes $VERSION." >&2
    echo "El programa intentará arrancar de todos modos." >&2
fi

# --- 2. Comprobar Tkinter -----------------------------------------------
if ! "$PYTHON" -c "import tkinter" >/dev/null 2>&1; then
    echo "ERROR: el módulo 'tkinter' no está disponible en este Python." >&2
    echo "En Linux normalmente falta el paquete del sistema:" >&2
    echo "  - Debian/Ubuntu:  sudo apt install python3-tk" >&2
    echo "  - Fedora:         sudo dnf install python3-tkinter" >&2
    echo "  - Arch:           sudo pacman -S tk" >&2
    echo "  - macOS (Homebrew): brew install python-tk" >&2
    exit 1
fi

# --- 3. Comprobar / instalar Pillow --------------------------------------
if ! "$PYTHON" -c "import PIL" >/dev/null 2>&1; then
    echo "Falta la dependencia 'Pillow' (necesaria para las imágenes de la revista)."
    read -r -p "¿Instalarla ahora con 'pip install pillow'? [S/n] " respuesta
    case "$respuesta" in
        [nN]*)
            echo "Cancelado. Instala Pillow manualmente y vuelve a ejecutar run.sh." >&2
            exit 1
            ;;
        *)
            "$PYTHON" -m pip install --user pillow
            if ! "$PYTHON" -c "import PIL" >/dev/null 2>&1; then
                echo "ERROR: no se pudo instalar/importar Pillow." >&2
                echo "Prueba manualmente: $PYTHON -m pip install --user pillow" >&2
                exit 1
            fi
            ;;
    esac
fi

# --- 4. Arrancar ----------------------------------------------------------
echo "Arrancando El Radiaktivo Newz..."
exec "$PYTHON" -m ernreader "$@"
