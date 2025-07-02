"""Calcula presupuestos para sistemas fotovoltaicos leyendo precios desde un
archivo de Excel."""

from __future__ import annotations

import os
from typing import Dict, List, Tuple

try:
    from openpyxl import Workbook, load_workbook
except ImportError:  # pragma: no cover - dependency may not be installed
    Workbook = None  # type: ignore
    load_workbook = None  # type: ignore


FILE = "equipos.xlsx"
SHEETS = ["Paneles", "Inversores", "Baterias", "Controladores"]
CATEGORIES = ["Barato", "Intermedio", "Premium"]


def crear_excel_de_ejemplo(filename: str) -> None:
    """Crea un archivo Excel con datos de ejemplo si no existe."""

    if Workbook is None:
        raise ImportError("openpyxl no esta instalado")

    wb = Workbook()
    # Elimina la hoja predeterminada
    wb.remove(wb.active)

    datos = {
        "Paneles": [
            ("Barato", "PanelCheap", 100),
            ("Intermedio", "PanelMid", 150),
            ("Premium", "PanelPremium", 200),
        ],
        "Inversores": [
            ("Barato", "InvCheap", 180),
            ("Intermedio", "InvMid", 250),
            ("Premium", "InvPremium", 350),
        ],
        "Baterias": [
            ("Barato", "BatCheap", 160),
            ("Intermedio", "BatMid", 240),
            ("Premium", "BatPremium", 400),
        ],
        "Controladores": [
            ("Barato", "CtrlCheap", 50),
            ("Intermedio", "CtrlMid", 100),
            ("Premium", "CtrlPremium", 150),
        ],
    }

    for nombre, filas in datos.items():
        ws = wb.create_sheet(title=nombre)
        ws.append(["Categoria", "Marca", "Precio"])
        for fila in filas:
            ws.append(fila)

    wb.save(filename)


def leer_datos(filename: str) -> Dict[str, Dict[str, List[Tuple[str, float]]]]:
    """Lee el archivo Excel y organiza los datos por componente y categoria."""

    if load_workbook is None:
        raise ImportError("openpyxl no esta instalado")

    wb = load_workbook(filename)
    datos: Dict[str, Dict[str, List[Tuple[str, float]]]] = {}
    for hoja in SHEETS:
        ws = wb[hoja]
        datos[hoja] = {cat: [] for cat in CATEGORIES}
        for categoria, marca, precio in ws.iter_rows(min_row=2, values_only=True):
            if categoria in CATEGORIES:
                datos[hoja][categoria].append((str(marca), float(precio)))
    return datos


def elegir_componente(
    opciones: Dict[str, List[Tuple[str, float]]], categoria: str
) -> Tuple[str, float]:
    """Elige el componente con menor precio dentro de la categoria."""

    candidatos = opciones.get(categoria, [])
    if not candidatos:
        return ("Sin datos", 0.0)
    return min(candidatos, key=lambda x: x[1])


def calcular_presupuestos(
    datos: Dict[str, Dict[str, List[Tuple[str, float]]]]
) -> Dict[str, Dict[str, Tuple[str, float]]]:
    """Calcula el componente seleccionado y su precio para cada presupuesto."""

    resultados: Dict[str, Dict[str, Tuple[str, float]]] = {
        cat: {} for cat in CATEGORIES
    }

    for categoria in CATEGORIES:
        for componente, opciones in datos.items():
            marca, precio = elegir_componente(opciones, categoria)
            resultados[categoria][componente] = (marca, precio)

    return resultados


def imprimir_presupuestos(presupuestos: Dict[str, Dict[str, Tuple[str, float]]]) -> None:
    """Muestra los presupuestos y los componentes utilizados."""

    for categoria in CATEGORIES:
        elementos = presupuestos[categoria]
        total = sum(precio for _, precio in elementos.values())
        print(f"{categoria}: ${total:.2f}")
        for componente, (marca, precio) in elementos.items():
            print(f"  {componente}: {marca} - ${precio:.2f}")
        print()


def main() -> None:
    if not os.path.exists(FILE):
        crear_excel_de_ejemplo(FILE)
        print(f"Se creó el archivo '{FILE}' con datos de ejemplo.")

    datos = leer_datos(FILE)
    presupuestos = calcular_presupuestos(datos)
    imprimir_presupuestos(presupuestos)


if __name__ == "__main__":
    main()

