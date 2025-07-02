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
    seleccionar_cargas_gui,

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
    """Abre una interfaz grafica para la simulacion."""

    if not os.path.exists(FILE):
        crear_excel_de_ejemplo(FILE)
        print(f"Se creó el archivo '{FILE}' con datos de ejemplo.")

    if not os.path.exists(LOADS_FILE):
        crear_excel_cargas_de_ejemplo(LOADS_FILE)
        print(f"Se creó el archivo '{LOADS_FILE}' con datos de ejemplo.")

    datos = leer_datos(FILE)
    cargas_base = leer_cargas(LOADS_FILE)

    try:
        from PyQt5 import QtCore, QtGui, QtWidgets
    except Exception as exc:  # pragma: no cover - dependencias ausentes
        print(f"No se pudo abrir la interfaz grafica: {exc}")
        return

    app = QtWidgets.QApplication([])
    ventana = QtWidgets.QWidget()
    ventana.setWindowTitle("Simulador Solar")

    layout_principal = QtWidgets.QHBoxLayout(ventana)

    headers = ["Usar", "Aparato", "Cantidad", "Carga(W)", "HorasDia", "HorasNoche"]
    tabla = QtWidgets.QTableWidget(len(cargas_base), len(headers))
    tabla.setHorizontalHeaderLabels(headers)
    ventana.resize(1100, 700)
    for fila, carga in enumerate(cargas_base):
        chk = QtWidgets.QTableWidgetItem()
        chk.setCheckState(QtCore.Qt.Checked)
        tabla.setItem(fila, 0, chk)
        tabla.setItem(fila, 1, QtWidgets.QTableWidgetItem(carga["aparato"]))
        tabla.setItem(fila, 2, QtWidgets.QTableWidgetItem(str(carga["cantidad"])))
        tabla.setItem(fila, 3, QtWidgets.QTableWidgetItem(str(carga["carga"])))
        tabla.setItem(fila, 4, QtWidgets.QTableWidgetItem(str(carga["horas_dia"])))
        tabla.setItem(fila, 5, QtWidgets.QTableWidgetItem(str(carga["horas_noche"])))

    # ----- Lado izquierdo -----
    layout_izq = QtWidgets.QVBoxLayout()
    layout_izq.addWidget(tabla)
    btn_toggle = QtWidgets.QPushButton("Marcar/Desmarcar todo")
    layout_izq.addWidget(btn_toggle)
    layout_principal.addLayout(layout_izq)

    # ----- Lado derecho -----
    layout_der = QtWidgets.QVBoxLayout()
    btn_ejecutar = QtWidgets.QPushButton("Ejecutar simulacion")
    layout_der.addWidget(btn_ejecutar)
    btn_costo = QtWidgets.QPushButton("Costo acumulado")
    btn_anual = QtWidgets.QPushButton("Costo anual")
    btn_ahorro = QtWidgets.QPushButton("Ahorro")
    btn_sistemas = QtWidgets.QPushButton("Sistemas")
    for b in (btn_costo, btn_anual, btn_ahorro, btn_sistemas):
        b.setEnabled(False)
        layout_der.addWidget(b)

    salida = QtWidgets.QTextEdit()
    salida.setReadOnly(True)
    layout_der.addWidget(salida)

    layout_der.addStretch(1)
    layout_principal.addLayout(layout_der)

    def toggle_checks() -> None:
        """Marca o desmarca todas las cargas."""
        any_unchecked = any(
            tabla.item(r, 0).checkState() != QtCore.Qt.Checked
            for r in range(tabla.rowCount())
        )
        nuevo = QtCore.Qt.Checked if any_unchecked else QtCore.Qt.Unchecked
        for r in range(tabla.rowCount()):
            tabla.item(r, 0).setCheckState(nuevo)

    resultados: Dict[str, Dict[str, Tuple[str, float]]] = {}
    daily_kwh: float = 0.0

    def ejecutar() -> None:
        nonlocal resultados, daily_kwh
        cargas: list[dict[str, float]] = []
        for row in range(tabla.rowCount()):
            if tabla.item(row, 0).checkState() != QtCore.Qt.Checked:
                continue
            aparato = tabla.item(row, 1).text()
            cantidad = float(tabla.item(row, 2).text() or 0)
            carga_w = float(tabla.item(row, 3).text() or 0)
            horas_dia = float(tabla.item(row, 4).text() or 0)
            horas_noche = float(tabla.item(row, 5).text() or 0)
            cargas.append(
                {
                    "aparato": aparato,
                    "cantidad": cantidad,
                    "carga": carga_w,
                    "horas_dia": horas_dia,
                    "horas_noche": horas_noche,
                }
            )

        curva = curva_irradiacion_cusco()
        pot_panel, cap_bat = calcular_necesidades(cargas, curva)
        demanda_max = potencia_maxima_demanda(cargas)
        resultados = calcular_kit(datos, pot_panel, cap_bat, demanda_max)
        daily_kwh = energia_diaria_kwh(cargas, curva)
        cap_gel = cap_bat / 0.5
        cap_li = cap_bat / 0.9
        texto = (
            f"Consumo diario: {daily_kwh:.2f} kWh\n"
            f"Potencia de panel requerida: {pot_panel:.2f} W\n"
            "Capacidad de bateria requerida:\n"
            f"  Si es de Gel/Agm : {cap_gel:.2f} Ah\n"
            f"  Si es de litio: {cap_li:.2f} Ah"
        )
        salida.setPlainText(texto)

        # Graficos para la categoria Barato por defecto
        pres = resultados[CATEGORIES[0]]
        costo, _, _, _ = calcular_amortizacion(pres, daily_kwh)
        graficar_costo_acumulado(costo, daily_kwh, "resultado")
        graficar_costo_anual(costo, daily_kwh, "resultado")
        graficar_ahorro_largo_plazo(costo, daily_kwh, "resultado")

        for b in (btn_costo, btn_anual, btn_ahorro, btn_sistemas):
            b.setEnabled(True)

        mostrar_sistemas()

    def mostrar_imagen(ruta: str) -> None:
        dlg = QtWidgets.QDialog(ventana)
        dlg.resize(600, 400)
        lbl = QtWidgets.QLabel()
        pix = QtGui.QPixmap(ruta)
        lbl.setPixmap(pix)
        lay = QtWidgets.QVBoxLayout(dlg)
        lay.addWidget(lbl)
        dlg.exec_()

    def mostrar_sistemas() -> None:
        html = ""
        for cat in CATEGORIES:
            pres = resultados.get(cat, {})
            if not pres:
                continue
            costo, costo_kwh, payback, ahorro = calcular_amortizacion(pres, daily_kwh)
            html += f"<h3>{cat}</h3>"
            html += "<table border='1' cellspacing='0' cellpadding='2'>"
            for comp, (desc, precio) in pres.items():
                html += f"<tr><td>{comp}</td><td>{desc}</td><td>{precio:.2f} PEN</td></tr>"
            html += f"<tr><td colspan='2'><b>Total</b></td><td>{costo:.2f} PEN</td></tr>"
            html += f"<tr><td colspan='2'>Costo kWh</td><td>{costo_kwh:.2f} PEN</td></tr>"
            html += f"<tr><td colspan='2'>Payback</td><td>{payback:.2f} años</td></tr>"
            html += f"<tr><td colspan='2'>Ahorro {VIDA_UTIL_ANIOS} años</td><td>{ahorro:.2f} PEN</td></tr>"
            html += "</table><br>"

        dlg = QtWidgets.QDialog(ventana)
        dlg.setWindowTitle("Sistemas recomendados")
        dlg.resize(700, 500)
        lay = QtWidgets.QVBoxLayout(dlg)
        txt = QtWidgets.QTextBrowser()
        txt.setHtml(html)
        lay.addWidget(txt)
        dlg.exec_()

    btn_toggle.clicked.connect(toggle_checks)
    btn_ejecutar.clicked.connect(ejecutar)
    btn_costo.clicked.connect(lambda: mostrar_imagen("costo_resultado.png"))
    btn_anual.clicked.connect(lambda: mostrar_imagen("costo_anual_resultado.png"))
    btn_ahorro.clicked.connect(lambda: mostrar_imagen("ahorro_resultado.png"))
    btn_sistemas.clicked.connect(mostrar_sistemas)

    ventana.show()
    app.exec_()


if __name__ == "__main__":
    main()
