"""Calcula presupuestos y necesidades para sistemas fotovoltaicos."""

from __future__ import annotations

import os
from typing import Dict, List, Tuple
import math
import re

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
            # Solo se consideran opciones de 100W en adelante
            ("Barato", "Basic100", "100W", 150),
            ("Intermedio", "Mid200", "200W", 250),
            ("Premium", "Top300", "300W", 400),
        ],
        "Inversores": [
            ("Barato", "Mod500", "Onda modificada 500W", 150),
            ("Barato", "Mod1000", "Onda modificada 1000W", 200),
            ("Intermedio", "Pura1500", "Onda pura 1500W", 350),
            ("Intermedio", "Pura1800", "Onda pura 1800W", 420),
            ("Premium", "Hibrido4000", "Híbrido 4000W", 900),
            ("Premium", "Hibrido3000", "Híbrido 3000W", 700),
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
            ("Barato", "AGM60", "AGM 60Ah", 160),
            ("Intermedio", "Gel100", "Gel 100Ah", 240),
            ("Premium", "Li200", "Litio 200Ah", 400),
        ],
        "Controladores": [
            ("Barato", "PWM10", "PWM 10A", 30),
            ("Barato", "PWM20", "PWM 20A", 45),
            ("Barato", "PWM30", "PWM 30A", 60),
            ("Intermedio", "MPPT15", "MPPT 15A", 120),
            ("Premium", "MPPT20", "MPPT 20A", 180),
            ("Barato", "PWM10", "PWM 10A", 50),
            ("Intermedio", "PWM20", "PWM 20A", 100),
            ("Premium", "MPPT30", "MPPT 30A", 150),

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

def _extraer_numero(texto: str) -> float:
    """Extrae el primer numero encontrado en un texto."""

    m = re.search(r"([0-9]+(?:\.[0-9]+)?)", texto)
    return float(m.group(1)) if m else 0.0


def leer_datos(filename: str) -> Dict[str, Dict[str, List[Tuple[str, float, float]]]]:
    """Lee el archivo Excel y organiza los datos por componente y categoria.

    Devuelve nombre, capacidad (W, Ah o A) y precio.
    """

    if load_workbook is None:
        raise ImportError("openpyxl no esta instalado")

    wb = load_workbook(filename)
    datos: Dict[str, Dict[str, List[Tuple[str, float, float]]]] = {}
    for hoja in SHEETS:
        ws = wb[hoja]
        datos[hoja] = {cat: [] for cat in CATEGORIES}

        for row in ws.iter_rows(min_row=2, values_only=True):
            if len(row) < 4:
                continue
            categoria, marca, detalle, precio = row
            if categoria in CATEGORIES:
                nombre = f"{marca} {detalle}"
                capacidad = _extraer_numero(str(detalle))
                datos[hoja][categoria].append((nombre, capacidad, float(precio)))
    return datos

def leer_cargas(filename: str) -> List[Dict[str, float]]:
    """Lee el excel de cargas y devuelve una lista de diccionarios."""

    if load_workbook is None:
        raise ImportError("openpyxl no esta instalado")

    wb = load_workbook(filename)
    ws = wb.active
    cargas = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row:
            continue

        valores = list(row)
        if len(valores) < 7:
            valores.extend([0.0] * (7 - len(valores)))

        (
            aparato,
            cantidad,
            carga,
            inicio_am,
            fin_am,
            inicio_pm,
            fin_pm,
        ) = valores[:7]

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


def potencia_maxima_demanda(cargas: List[Dict[str, float]]) -> float:
    """Calcula la potencia simultanea maxima de las cargas."""

    demanda_por_hora = {h: 0.0 for h in range(24)}
    for carga in cargas:
        potencia = carga["carga"] * carga["cantidad"]
        for inicio, fin in [
            (carga["inicio_am"], carga["fin_am"]),
            (carga["inicio_pm"], carga["fin_pm"]),
        ]:
            for hora in range(int(inicio), int(fin)):
                demanda_por_hora[hora] += potencia
    return max(demanda_por_hora.values())


def calcular_kit(
    datos: Dict[str, Dict[str, List[Tuple[str, float, float]]]],
    potencia_panel: float,
    capacidad_bateria: float,
    demanda_maxima: float,
) -> Dict[str, Dict[str, Tuple[str, float]]]:
    """Selecciona componentes suficientes para cubrir las necesidades."""

    resultados: Dict[str, Dict[str, Tuple[str, float]]] = {
        cat: {} for cat in CATEGORIES
    }

    for categoria in CATEGORIES:
        # Paneles
        mejor_total = math.inf
        mejor_desc = "Sin datos"
        for nombre, capacidad, precio in datos["Paneles"].get(categoria, []):
            if capacidad <= 0:
                continue
            cantidad = math.ceil(potencia_panel / capacidad)
            total = cantidad * precio
            if total < mejor_total:
                mejor_total = total
                mejor_desc = f"{cantidad} x {nombre}"
        resultados[categoria]["Paneles"] = (mejor_desc, mejor_total if mejor_total < math.inf else 0.0)

        # Baterias
        mejor_total = math.inf
        mejor_desc = "Sin datos"
        for nombre, capacidad, precio in datos["Baterias"].get(categoria, []):
            if capacidad <= 0:
                continue
            cantidad = math.ceil(capacidad_bateria / capacidad)
            total = cantidad * precio
            if total < mejor_total:
                mejor_total = total
                mejor_desc = f"{cantidad} x {nombre}"
        resultados[categoria]["Baterias"] = (mejor_desc, mejor_total if mejor_total < math.inf else 0.0)

        # Inversores
        mejor_precio = math.inf
        mejor_desc = "Sin datos"
        for nombre, capacidad, precio in datos["Inversores"].get(categoria, []):
            if capacidad >= demanda_maxima and precio < mejor_precio:
                mejor_precio = precio
                mejor_desc = nombre
        resultados[categoria]["Inversores"] = (mejor_desc, mejor_precio if mejor_precio < math.inf else 0.0)

        # Controladores: se elige el mas barato
        mejor_precio = math.inf
        mejor_desc = "Sin datos"
        for nombre, capacidad, precio in datos["Controladores"].get(categoria, []):
            if precio < mejor_precio:
                mejor_precio = precio
                mejor_desc = nombre
        resultados[categoria]["Controladores"] = (mejor_desc, mejor_precio if mejor_precio < math.inf else 0.0)

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
    demanda_maxima = potencia_maxima_demanda(cargas)
    presupuestos = calcular_kit(datos, potencia_panel, capacidad_bateria, demanda_maxima)

    imprimir_presupuestos(presupuestos)
    print("Requerimientos del sistema:")
    print(f"  Potencia de panel requerida: {potencia_panel:.2f} W")
    print(f"  Capacidad de batería requerida: {capacidad_bateria:.2f} Ah")


if __name__ == "__main__":
    main()
