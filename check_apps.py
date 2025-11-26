#!/usr/bin/env python
"""
Script de inspección de apps Django del proyecto.

Uso:
    python check_apps.py
"""

import os
import sys
from pathlib import Path
import importlib

import django

# ==============================
# CONFIGURACIÓN DJANGO
# ==============================
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pepsico_taller.settings")
django.setup()

from django.apps import apps  # noqa: E402


# ==============================
# APPS CUSTOM QUE NOS IMPORTAN
# ==============================
CUSTOM_APPS = [
    "autenticacion",
    "vehiculos",
    "ordenestrabajo",
    "talleres",
    "documentos",
    "reportes",
    "chat",
    "utils",
    "common",
]


def list_modules_for_app(app_label: str):
    try:
        app_config = apps.get_app_config(app_label)
    except LookupError:
        print(f"❌  App '{app_label}' no está en INSTALLED_APPS")
        print("-" * 80)
        return

    app_name = app_config.name
    app_path = Path(app_config.path)

    print("=" * 80)
    print(f"APP: {app_label}")
    print(f"Python package : {app_name}")
    print(f"Ruta en disco  : {app_path}")
    print("-" * 80)

    # ------------------------------
    # Módulos .py en la raíz del app
    # ------------------------------
    py_files = sorted(
        p.name for p in app_path.glob("*.py") if p.name != "__init__.py"
    )

    if py_files:
        print("Módulos en la raíz del app:")
        for fname in py_files:
            mod_name = fname[:-3]  # sin .py
            full_mod_path = f"{app_name}.{mod_name}"
            ok = True
            try:
                importlib.import_module(full_mod_path)
            except Exception as e:
                ok = False
                print(f"  ⚠️  {fname:<25}  (ERROR al importar: {e})")
            if ok:
                print(f"  ✅ {fname}")
    else:
        print("Módulos en la raíz del app: (ninguno)")

    print()

    # ------------------------------
    # Migraciones
    # ------------------------------
    migrations_dir = app_path / "migrations"
    if migrations_dir.exists():
        migration_files = sorted(
            p.name for p in migrations_dir.glob("*.py") if p.name != "__init__.py"
        )
        print("Migraciones:")
        if migration_files:
            for mf in migration_files:
                print(f"  - {mf}")
        else:
            print("  (sin migraciones .py)")
    else:
        print("Migraciones: (no hay carpeta migrations)")

    print("=" * 80)
    print()


def main():
    print("\nINSPECCIÓN DE APPS DJANGO\n")
    for label in CUSTOM_APPS:
        list_modules_for_app(label)


if __name__ == "__main__":
    main()
