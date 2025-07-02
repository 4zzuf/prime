# Programa para calcular tres presupuestos (economico, intermedio, premium)
# para un sistema solar fotovoltaico a partir de una lista de equipos y
# sus precios. Cada equipo tiene tres precios: uno economico, uno
# intermedio y uno premium.

from typing import List, Dict

# Definimos la lista de equipos y sus precios en tres categorias
# (economico, intermedio, premium).
# Los precios estan en la moneda que el usuario desee (por ejemplo, USD).

equipos: List[Dict[str, List[float]]] = [
    {"nombre": "Panel solar", "precios": [100.0, 150.0, 200.0]},
    {"nombre": "Inversor", "precios": [200.0, 300.0, 450.0]},
    {"nombre": "Baterias", "precios": [300.0, 500.0, 800.0]},
    {"nombre": "Estructura", "precios": [50.0, 75.0, 120.0]},
]


def calcular_presupuesto(items: List[Dict[str, List[float]]], indice: int) -> float:
    """Calcula el presupuesto sumando el precio indicado por 'indice' en cada item."""
    return sum(item["precios"][indice] for item in items)


if __name__ == "__main__":
    presupuesto_barato = calcular_presupuesto(equipos, 0)
    presupuesto_intermedio = calcular_presupuesto(equipos, 1)
    presupuesto_premium = calcular_presupuesto(equipos, 2)

    print("Presupuesto economico: ${:.2f}".format(presupuesto_barato))
    print("Presupuesto intermedio: ${:.2f}".format(presupuesto_intermedio))
    print("Presupuesto premium:   ${:.2f}".format(presupuesto_premium))
