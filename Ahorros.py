"""Compara costo de red electrica vs sistema solar y genera graficos."""

from __future__ import annotations

import os
from typing import Dict, Tuple

from Precios import (
    FILE,
    LOADS_FILE,
    CATEGORIES,
    crear_excel_de_ejemplo,
    crear_excel_cargas_de_ejemplo,
    leer_datos,
    leer_cargas,
    curva_irradiacion_cusco,
    calcular_necesidades,
    energia_dia_noche,
    potencia_maxima_demanda,
    calcular_kit,
)

COSTO_RED = 0.83  # PEN por kWh
VIDA_UTIL_ANIOS = 20

def energia_diaria_kwh(cargas: list[dict[str, float]], curva: Dict[int, float]) -> float:
    """Suma el consumo diario en kWh a partir de los intervalos."""

    energia_dia, energia_noche = energia_dia_noche(cargas, curva)
    return (energia_dia + energia_noche) / 1000



def calcular_amortizacion(
    presupuesto: Dict[str, Tuple[str, float]], daily_kwh: float
) -> Tuple[float, float, float, float]:
    """Devuelve costo del sistema, costo por kWh, payback y ahorro."""

    costo_sistema = sum(p for _, p in presupuesto.values())
    costo_anual_red = daily_kwh * COSTO_RED * 365
    payback = costo_sistema / costo_anual_red if costo_anual_red else float("inf")
    costo_kwh = (
        costo_sistema / (daily_kwh * 365 * VIDA_UTIL_ANIOS)
        if daily_kwh
        else float("inf")
    )
    ahorro_total = costo_anual_red * VIDA_UTIL_ANIOS - costo_sistema
    return costo_sistema, costo_kwh, payback, ahorro_total


def graficar_costo_acumulado(costo_sistema: float, daily_kwh: float, nombre: str) -> None:
    """Genera un grafico de costo acumulado y lo guarda."""

    try:
        import matplotlib.pyplot as plt
    except Exception as exc:  # pragma: no cover - si matplotlib no esta
        raise ImportError("matplotlib no esta instalado") from exc

    anios = list(range(VIDA_UTIL_ANIOS + 1))
    costo_red = [daily_kwh * COSTO_RED * 365 * a for a in anios]
    costo_solar = [costo_sistema if a > 0 else 0 for a in anios]

    plt.figure()
    plt.plot(anios, costo_red, label="Red electrica")
    plt.plot(anios, costo_solar, label="Sistema solar")
    plt.xlabel("Años")
    plt.ylabel("PEN")
    plt.title(f"Costo acumulado - {nombre}")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f"costo_{nombre}.png")
    plt.close()

def graficar_costo_anual(costo_sistema: float, daily_kwh: float, nombre: str) -> None:
    """Grafica el costo anual de red vs el costo anual amortizado del kit."""

    try:
        import matplotlib.pyplot as plt
    except Exception as exc:  # pragma: no cover - si matplotlib no esta
        raise ImportError("matplotlib no esta instalado") from exc

    anios = list(range(1, VIDA_UTIL_ANIOS + 1))
    costo_red = [daily_kwh * COSTO_RED * 365 for _ in anios]
    costo_solar = [costo_sistema / VIDA_UTIL_ANIOS for _ in anios]

    plt.figure()
    plt.plot(anios, costo_red, label="Red electrica")
    plt.plot(anios, costo_solar, label="Sistema solar (amortizado)")
    plt.xlabel("Años")
    plt.ylabel("PEN por año")
    plt.title(f"Costo anual - {nombre}")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f"costo_anual_{nombre}.png")
    plt.close()


def graficar_ahorro_largo_plazo(costo_sistema: float, daily_kwh: float, nombre: str) -> None:
    """Grafica el ahorro acumulado durante 10 años."""

    try:
        import matplotlib.pyplot as plt
    except Exception as exc:  # pragma: no cover - si matplotlib no esta
        raise ImportError("matplotlib no esta instalado") from exc

    anios = list(range(1, 11))
    costo_red = [daily_kwh * COSTO_RED * 365 * a for a in anios]
    costo_solar = [(costo_sistema / VIDA_UTIL_ANIOS) * a for a in anios]
    ahorro = [cr - cs for cr, cs in zip(costo_red, costo_solar)]

    plt.figure()
    plt.plot(anios, ahorro, label="Ahorro acumulado")
    plt.xlabel("Años")
    plt.ylabel("PEN")
    plt.title(f"Ahorro a largo plazo - {nombre}")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f"ahorro_{nombre}.png")
    plt.close()
    
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

    daily_kwh = energia_diaria_kwh(cargas, curva)

    print(f"Consumo diario: {daily_kwh:.2f} kWh")
    print(f"Potencia de panel requerida: {potencia_panel:.2f} W")
    print(f"Capacidad de batería requerida: {capacidad_bateria:.2f} Ah")

    for categoria in CATEGORIES:
        pres = presupuestos[categoria]
        costo, costo_kwh, payback, ahorro = calcular_amortizacion(pres, daily_kwh)
        print(f"\n{categoria}:")
        print(f"  Costo sistema: {costo:.2f} PEN")
        print(f"  Costo amortizado por kWh: {costo_kwh:.2f} PEN")
        print(f"  Tiempo de amortización: {payback:.2f} años")
        print(f"  Ahorro estimado a {VIDA_UTIL_ANIOS} años: {ahorro:.2f} PEN")
        try:
            graficar_costo_acumulado(costo, daily_kwh, categoria)

            graficar_costo_anual(costo, daily_kwh, categoria)
            graficar_ahorro_largo_plazo(costo, daily_kwh, categoria)
            print(
                f"  Graficos guardados: costo_{categoria}.png, costo_anual_{categoria}.png, ahorro_{categoria}.png"
            )

        except ImportError as exc:
            print(f"  No se pudo generar grafico: {exc}")


if __name__ == "__main__":
    main()
