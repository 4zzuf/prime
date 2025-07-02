"""Calcula presupuestos y necesidades para sistemas fotovoltaicos."""

from __future__ import annotations

import os
from typing import Dict, List, Tuple

try:
    from openpyxl import Workbook, load_workbook
except ImportError:  # pragma: no cover - dependency may not be installed
    Workbook = None  # type: ignore
    load_workbook = None  # type: ignore

FILE = "equipos.xlsx"
LOADS_FILE = "cargas.xlsx"
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

            ("Barato", "Eco20", "20W", 60),
            ("Barato", "Eco30", "30W", 70),
            ("Barato", "Eco50", "50W", 100),
            ("Intermedio", "Mid100", "100W", 180),
            ("Intermedio", "Mid150", "150W", 230),
            ("Intermedio", "Mid200", "200W", 280),
            ("Premium", "Pro605", "605W", 800),
        ],
        "Inversores": [
            ("Barato", "Mod500", "Onda modificada 500W", 150),
            ("Barato", "Mod1000", "Onda modificada 1000W", 200),
            ("Intermedio", "Pura1500", "Onda pura 1500W", 350),
            ("Intermedio", "Pura1800", "Onda pura 1800W", 420),
            ("Premium", "Hibrido4000", "Híbrido 4000W", 900),
        ],
        "Baterias": [
            ("Barato", "AGM7", "AGM 7Ah", 40),
            ("Barato", "AGM26", "AGM 26Ah", 70),
            ("Barato", "AGM40", "AGM 40Ah", 100),
            ("Barato", "AGM75", "AGM 75Ah", 150),
            ("Intermedio", "Gel100", "Gel 100Ah", 250),
            ("Intermedio", "Gel150", "Gel 150Ah", 320),
            ("Intermedio", "Gel200", "Gel 200Ah", 400),
            ("Intermedio", "Gel300", "Gel 300Ah", 600),
            ("Premium", "Li100", "Litio 100Ah", 800),
            ("Premium", "Li200", "Litio 200Ah", 1400),
        ],
        "Controladores": [
            ("Barato", "PWM10", "PWM 10A", 30),
            ("Barato", "PWM20", "PWM 20A", 45),
            ("Barato", "PWM30", "PWM 30A", 60),
            ("Intermedio", "MPPT15", "MPPT 15A", 120),
            ("Premium", "MPPT20", "MPPT 20A", 180),

        ],
    }

    for nombre, filas in datos.items():
        ws = wb.create_sheet(title=nombre)

        ws.append(["Categoria", "Marca", "Detalle", "Precio"])

        for fila in filas:
            ws.append(fila)

    wb.save(filename)


def crear_excel_cargas_de_ejemplo(filename: str) -> None:
    """Crea un archivo Excel con cargas de ejemplo."""

    if Workbook is None:
        raise ImportError("openpyxl no esta instalado")

    wb = Workbook()
    ws = wb.active
    ws.title = "Cargas"

    ws.append([
        "Aparato",
        "Cantidad",
        "Carga",
        "InicioAM",
        "FinAM",
        "InicioPM",
        "FinPM",
    ])
    ejemplo = [
        ("Foco LED", 4, 10, 6, 8, 18, 20),
        ("Laptop", 1, 100, 9, 12, 0, 0),
        ("Televisor", 1, 80, 0, 0, 19, 22),

    ]
    for fila in ejemplo:
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

        for row in ws.iter_rows(min_row=2, values_only=True):
            if len(row) < 4:
                continue
            categoria, marca, detalle, precio = row
            if categoria in CATEGORIES:
                nombre = f"{marca} {detalle}"
                datos[hoja][categoria].append((nombre, float(precio)))
    return datos

def leer_cargas(filename: str) -> List[Dict[str, float]]:
    """Lee el excel de cargas y devuelve una lista de diccionarios."""

    if load_workbook is None:
        raise ImportError("openpyxl no esta instalado")

    wb = load_workbook(filename)
    ws = wb.active
    cargas = []
    for row in ws.iter_rows(min_row=2, values_only=True):

        (
            aparato,
            cantidad,
            carga,
            inicio_am,
            fin_am,
            inicio_pm,
            fin_pm,
        ) = row

        cargas.append(
            {
                "aparato": str(aparato),
                "cantidad": float(cantidad),
                "carga": float(carga),
                "inicio_am": float(inicio_am),
                "fin_am": float(fin_am),
                "inicio_pm": float(inicio_pm),
                "fin_pm": float(fin_pm),

            }
        )
    return cargas


def curva_irradiacion_cusco() -> Dict[int, float]:
    """Devuelve una curva horaria de irradiación típica de Cusco."""

    # Valores aproximados en W/m^2 de 6 AM a 6 PM
    valores = [
        0,
        100,
        300,
        500,
        700,
        850,
        950,
        1000,
        950,
        800,
        600,
        400,
        200,
        0,
    ]
    horas = list(range(6, 20))
    return dict(zip(horas, valores))


def horas_solares_efectivas(curva: Dict[int, float]) -> float:
    """Calcula las horas solares equivalentes de la curva."""

    total = sum(curva.values())  # Wh/m^2 suponiendo paso de 1 h
    return total / 1000


def energia_dia_noche(
    cargas: List[Dict[str, float]], curva: Dict[int, float]
) -> Tuple[float, float]:
    """Separa la energia de las cargas en horas con y sin sol."""

    energia_dia = 0.0
    energia_noche = 0.0

    for carga in cargas:
        potencia = carga["carga"] * carga["cantidad"]
        for inicio, fin in [
            (carga["inicio_am"], carga["fin_am"]),
            (carga["inicio_pm"], carga["fin_pm"]),
        ]:
            if fin <= inicio:
                continue
            for hora in range(int(inicio), int(fin)):
                if curva.get(hora, 0) > 0:
                    energia_dia += potencia
                else:
                    energia_noche += potencia

    return energia_dia, energia_noche


def calcular_necesidades(
    cargas: List[Dict[str, float]], curva: Dict[int, float]
) -> Tuple[float, float]:
    """Calcula potencia de panel y capacidad de bateria necesarias."""

    energia_dia, energia_noche = energia_dia_noche(cargas, curva)
    hs = horas_solares_efectivas(curva)
    potencia_panel = (energia_dia + energia_noche) / hs if hs else 0
    capacidad_bateria = energia_noche / 12  # Ah para bateria de 12V
    return potencia_panel, capacidad_bateria


def elegir_componente(opciones: Dict[str, List[Tuple[str, float]]], categoria: str) -> Tuple[str, float]:

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

    if not os.path.exists(LOADS_FILE):
        crear_excel_cargas_de_ejemplo(LOADS_FILE)
        print(f"Se creó el archivo '{LOADS_FILE}' con datos de ejemplo.")

    datos = leer_datos(FILE)
    cargas = leer_cargas(LOADS_FILE)
    curva = curva_irradiacion_cusco()
    potencia_panel, capacidad_bateria = calcular_necesidades(cargas, curva)
    presupuestos = calcular_presupuestos(datos)

    imprimir_presupuestos(presupuestos)
    print("Requerimientos del sistema:")
    print(f"  Potencia de panel requerida: {potencia_panel:.2f} W")
    print(f"  Capacidad de batería requerida: {capacidad_bateria:.2f} Ah")


if __name__ == "__main__":
    main()
