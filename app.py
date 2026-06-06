import re
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime


st.set_page_config(page_title="Dashboard ACABET", layout="wide")

COLOR_AZUL = "#002B4E"
COLOR_AZUL_GRAFICO = "#003B66"
COLOR_NARANJA = "#FF6A00"

SHEET_ID = "1mkCIQy1PMoHzOLeUZoyRXYEEgwx-i7rZ"

GID_CUENTAS = "1779917486"
GID_PAGOS = "1510429696"
GID_ASISTENCIAS = "1793083906"


st.markdown(
    """
    <style>
    .stApp { background-color: #F2F4F7; }

    [data-testid="stMetric"] {
        background-color: white;
        padding: 18px;
        border-radius: 14px;
        box-shadow: 0px 2px 8px rgba(0,0,0,0.08);
        border-left: 6px solid #FF6A00;
    }

    div[data-testid="stDataFrame"] {
        background-color: white;
        border-radius: 12px;
        padding: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True
)


def obtener_url(gid):
    return f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&gid={gid}"


def cargar_data(gid):
    return pd.read_csv(obtener_url(gid))


def convertir_a_numero(valor):
    if pd.isna(valor):
        return 0.0

    texto = str(valor).strip()
    texto = texto.replace("S/.", "")
    texto = texto.replace("S/", "")
    texto = texto.replace("S", "")
    texto = texto.replace("s/.", "")
    texto = texto.replace("s/", "")
    texto = texto.replace(" ", "")
    texto = texto.replace(",", "")

    texto = re.sub(r"[^0-9.-]", "", texto)

    if texto in ["", "-", ".", "-."]:
        return 0.0

    partes = texto.split(".")

    if len(partes) > 2:
        texto = "".join(partes[:-1]) + "." + partes[-1]

    try:
        return float(texto)
    except:
        return 0.0


def limpiar_numero(columna):
    return columna.apply(convertir_a_numero)


def mostrar_encabezado():
    fecha_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    col_logo, col_titulo = st.columns([1, 4])

    with col_logo:
        st.image("LOGO DE LA EMPRESA.png", width=190)

    with col_titulo:
        st.markdown(
            f"""
            <div style="
                background-color:{COLOR_AZUL};
                padding:26px;
                border-radius:18px;
                border-left:10px solid {COLOR_NARANJA};
                margin-bottom:20px;">
                <div style="color:white; font-size:34px; font-weight:900;">
                    DASHBOARD GENERAL
                </div>
                <div style="color:{COLOR_NARANJA}; font-size:24px; font-weight:800; margin-top:8px;">
                    ACABET E&V CONSTRUCCIONES
                </div>
                <div style="color:white; font-size:16px; font-weight:600; margin-top:10px;">
                    Fecha y hora actual: {fecha_hora}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )


mostrar_encabezado()

tab1, tab2 = st.tabs([
    "💰 Cuentas por pagar",
    "👷 Asistencias y pagos de planilla"
])


with tab1:
    try:
        df = cargar_data(GID_CUENTAS)

        df["MONTO_NUM"] = limpiar_numero(df["MONTO"])
        df["INTERES_NUM"] = limpiar_numero(df["INTERÉS"])
        df["TOTAL_NUM"] = limpiar_numero(df["TOTAL"])

        df["FECHA DE PAGO_DT"] = pd.to_datetime(
            df["FECHA DE PAGO"],
            format="%d/%m/%Y",
            errors="coerce"
        )

        hoy = pd.Timestamp.today().normalize()
        df["DÍAS PARA PAGAR"] = (df["FECHA DE PAGO_DT"] - hoy).dt.days

        st.success("Datos de cuentas por pagar cargados correctamente")

        deuda_total = df["TOTAL_NUM"].sum()
        deuda_pendiente = df[df["ESTADO"] == "PENDIENTE"]["TOTAL_NUM"].sum()
        deuda_pagada = df[df["ESTADO"] == "PAGADO"]["TOTAL_NUM"].sum()

        capital_total = df["MONTO_NUM"].sum()
        interes_total = df["INTERES_NUM"].sum()
        costo_financiero = interes_total / capital_total if capital_total > 0 else 0

        pendientes = len(df[df["ESTADO"] == "PENDIENTE"])
        pagados = len(df[df["ESTADO"] == "PAGADO"])

        st.subheader("Indicadores principales")

        col1, col2, col3 = st.columns(3)
        col1.metric("Deuda Total", f"S/ {deuda_total:,.2f}")
        col2.metric("Pendiente por pagar", f"S/ {deuda_pendiente:,.2f}")
        col3.metric("Ya pagado", f"S/ {deuda_pagada:,.2f}")

        col4, col5, col6 = st.columns(3)
        col4.metric("Préstamos pendientes", pendientes)
        col5.metric("Préstamos pagados", pagados)
        col6.metric("Total registros", len(df))

        st.divider()

        st.subheader("Interés acumulado")

        col_int1, col_int2, col_int3 = st.columns(3)
        col_int1.metric("Capital prestado", f"S/ {capital_total:,.2f}")
        col_int2.metric("Interés total", f"S/ {interes_total:,.2f}")
        col_int3.metric("Costo financiero", f"{costo_financiero:.2%}")

        st.divider()

        top5 = (
            df[(df["ESTADO"] == "PENDIENTE") & (df["DÍAS PARA PAGAR"].notna())]
            .sort_values("DÍAS PARA PAGAR", ascending=True)
            .head(5)
        )

        if len(top5) > 0:
            proximo = top5.iloc[0]
            dias = int(proximo["DÍAS PARA PAGAR"])

            if dias < 0:
                st.error(f"🔴 PAGO VENCIDO | {proximo['PRESTAMISTA']} | S/ {proximo['TOTAL_NUM']:,.2f} | Venció hace {abs(dias)} días")
            elif dias <= 7:
                st.error(f"🔴 PAGO URGENTE | {proximo['PRESTAMISTA']} | S/ {proximo['TOTAL_NUM']:,.2f} | Vence en {dias} días")
            else:
                st.warning(f"⚠️ PRÓXIMO PAGO | {proximo['PRESTAMISTA']} | S/ {proximo['TOTAL_NUM']:,.2f} | Vence en {dias} días")

        st.subheader("Semáforo de vencimientos")

        pendientes_con_fecha = df[(df["ESTADO"] == "PENDIENTE") & (df["DÍAS PARA PAGAR"].notna())]

        vencidos = len(pendientes_con_fecha[pendientes_con_fecha["DÍAS PARA PAGAR"] < 0])
        urgente = len(pendientes_con_fecha[(pendientes_con_fecha["DÍAS PARA PAGAR"] >= 0) & (pendientes_con_fecha["DÍAS PARA PAGAR"] <= 7)])
        pronto = len(pendientes_con_fecha[(pendientes_con_fecha["DÍAS PARA PAGAR"] >= 8) & (pendientes_con_fecha["DÍAS PARA PAGAR"] <= 15)])
        estable = len(pendientes_con_fecha[pendientes_con_fecha["DÍAS PARA PAGAR"] > 15])

        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        col_s1.metric("🔴 Vencidos", vencidos)
        col_s2.metric("🟠 0 a 7 días", urgente)
        col_s3.metric("🟡 8 a 15 días", pronto)
        col_s4.metric("🟢 Más de 15 días", estable)

        st.divider()

        st.subheader("Top 5 pagos más próximos")

        st.dataframe(
            top5[["FECHA DE PAGO", "PRESTAMISTA", "TOTAL", "ESTADO", "DÍAS PARA PAGAR"]],
            use_container_width=True
        )

        st.divider()

        st.subheader("Distribución de deuda")

        grafico_pie = px.pie(
            df,
            names="ESTADO",
            values="TOTAL_NUM",
            color="ESTADO",
            color_discrete_map={
                "PENDIENTE": COLOR_NARANJA,
                "PAGADO": COLOR_AZUL_GRAFICO
            },
            title="Distribución de deuda por estado"
        )

        grafico_pie.update_layout(paper_bgcolor="white", plot_bgcolor="white")
        st.plotly_chart(grafico_pie, use_container_width=True)

        st.divider()

        st.subheader("Deuda por prestamista")

        deuda_prestamista = df.groupby(["PRESTAMISTA", "ESTADO"], as_index=False)["TOTAL_NUM"].sum()

        orden_prestamistas = (
            df.groupby("PRESTAMISTA")["TOTAL_NUM"]
            .sum()
            .sort_values(ascending=False)
            .index
            .tolist()
        )

        grafico_barras = px.bar(
            deuda_prestamista,
            x="PRESTAMISTA",
            y="TOTAL_NUM",
            color="ESTADO",
            text="TOTAL_NUM",
            category_orders={"PRESTAMISTA": orden_prestamistas},
            color_discrete_map={
                "PENDIENTE": COLOR_NARANJA,
                "PAGADO": COLOR_AZUL_GRAFICO
            },
            title="Ranking de prestamistas: de mayor a menor deuda"
        )

        grafico_barras.update_layout(
            barmode="stack",
            paper_bgcolor="white",
            plot_bgcolor="white",
            xaxis_title="Prestamista",
            yaxis_title="Monto total",
            legend_title="Estado"
        )

        grafico_barras.update_traces(
            texttemplate="S/ %{text:,.2f}",
            textposition="inside"
        )

        st.plotly_chart(grafico_barras, use_container_width=True)

        st.divider()

        st.subheader("Detalle completo de cuentas por pagar")

        st.dataframe(
            df[[
                "FECHA DE PRÉSTAMO",
                "FECHA DE PAGO",
                "PRESTAMISTA",
                "MONTO",
                "INTERÉS",
                "TOTAL",
                "ESTADO"
            ]],
            use_container_width=True
        )

    except Exception as e:
        st.error("No se pudo cargar la sección de cuentas por pagar")
        st.write(e)


with tab2:
    try:
        df_pagos = cargar_data(GID_PAGOS)
        df_asistencias = cargar_data(GID_ASISTENCIAS)

        st.success("Datos de asistencias y pagos cargados correctamente")

        st.subheader("Asistencias y pagos de planilla")

        df_pagos["PAGO_SEMANAL_NUM"] = limpiar_numero(df_pagos["PAGO SEMANAL"])
        df_pagos["SUELDO_DIA_NUM"] = limpiar_numero(df_pagos["SUELDO AL DÍA"])

        total_pagado = df_pagos[df_pagos["ESTADO"] == "PAGADO"]["PAGO_SEMANAL_NUM"].sum()
        total_pendiente = df_pagos[df_pagos["ESTADO"] == "PENDIENTE"]["PAGO_SEMANAL_NUM"].sum()
        trabajadores_activos = df_asistencias["TRABAJADOR"].nunique()
        total_asistencias = len(df_asistencias[df_asistencias["¿ASISTIÓ?"] == "SÍ"])
        total_faltas = len(df_asistencias[df_asistencias["¿ASISTIÓ?"] == "NO"])

        st.subheader("Indicadores de personal")

        col1, col2, col3 = st.columns(3)
        col1.metric("Total pagado", f"S/ {total_pagado:,.2f}")
        col2.metric("Total pendiente", f"S/ {total_pendiente:,.2f}")
        col3.metric("Trabajadores activos", trabajadores_activos)

        col4, col5 = st.columns(2)
        col4.metric("Asistencias registradas", total_asistencias)
        col5.metric("Faltas registradas", total_faltas)

        st.divider()

        st.subheader("Pagado por obra")

        df_asistencias_validas = df_asistencias[df_asistencias["¿ASISTIÓ?"] == "SÍ"].copy()
        df_pagos_pagados = df_pagos[df_pagos["ESTADO"] == "PAGADO"].copy()

        df_obra = df_asistencias_validas.merge(
            df_pagos_pagados[["TRABAJADOR", "SEMANA", "SUELDO_DIA_NUM"]],
            on=["TRABAJADOR", "SEMANA"],
            how="left"
        )

        df_obra["SUELDO_DIA_NUM"] = df_obra["SUELDO_DIA_NUM"].fillna(0)

        pagado_por_obra = (
            df_obra
            .groupby("OBRA", as_index=False)["SUELDO_DIA_NUM"]
            .sum()
            .rename(columns={"SUELDO_DIA_NUM": "PAGADO_OBRA"})
            .sort_values("PAGADO_OBRA", ascending=False)
        )

        if len(pagado_por_obra) > 0:
            grafico_pagado_obra = px.bar(
                pagado_por_obra,
                x="OBRA",
                y="PAGADO_OBRA",
                text="PAGADO_OBRA",
                title="Monto pagado por obra",
                color_discrete_sequence=[COLOR_AZUL_GRAFICO]
            )

            grafico_pagado_obra.update_layout(
                paper_bgcolor="white",
                plot_bgcolor="white",
                xaxis_title="Obra",
                yaxis_title="Monto pagado"
            )

            grafico_pagado_obra.update_traces(
                texttemplate="S/ %{text:,.2f}",
                textposition="outside"
            )

            st.plotly_chart(grafico_pagado_obra, use_container_width=True)
            st.dataframe(pagado_por_obra, use_container_width=True)
        else:
            st.info("No hay pagos por obra registrados.")

        st.divider()

        st.subheader("Pagos por semana")

        pagos_semana = (
            df_pagos
            .groupby(["SEMANA", "ESTADO"], as_index=False)["PAGO_SEMANAL_NUM"]
            .sum()
        )

        grafico_pagos_semana = px.bar(
            pagos_semana,
            x="SEMANA",
            y="PAGO_SEMANAL_NUM",
            color="ESTADO",
            text="PAGO_SEMANAL_NUM",
            color_discrete_map={
                "PENDIENTE": COLOR_NARANJA,
                "PAGADO": COLOR_AZUL_GRAFICO
            },
            title="Pagos semanales por estado"
        )

        grafico_pagos_semana.update_layout(
            barmode="stack",
            paper_bgcolor="white",
            plot_bgcolor="white",
            xaxis_title="Semana",
            yaxis_title="Monto pagado / pendiente",
            legend_title="Estado"
        )

        grafico_pagos_semana.update_traces(
            texttemplate="S/ %{text:,.2f}",
            textposition="inside"
        )

        st.plotly_chart(grafico_pagos_semana, use_container_width=True)

        st.divider()

        st.subheader("Trabajadores con inasistencias")

        inasistencias = (
            df_asistencias[df_asistencias["¿ASISTIÓ?"] == "NO"]
            .groupby("TRABAJADOR", as_index=False)
            .size()
            .rename(columns={"size": "INASISTENCIAS"})
            .sort_values("INASISTENCIAS", ascending=False)
        )

        if len(inasistencias) > 0:
            grafico_inasistencias = px.bar(
                inasistencias,
                x="TRABAJADOR",
                y="INASISTENCIAS",
                text="INASISTENCIAS",
                title="Ranking de trabajadores con inasistencias",
                color_discrete_sequence=[COLOR_AZUL_GRAFICO]
            )

            grafico_inasistencias.update_layout(
                paper_bgcolor="white",
                plot_bgcolor="white",
                xaxis_title="Trabajador",
                yaxis_title="Cantidad de inasistencias"
            )

            grafico_inasistencias.update_traces(textposition="outside")

            st.plotly_chart(grafico_inasistencias, use_container_width=True)
            st.dataframe(inasistencias, use_container_width=True)
        else:
            st.info("No hay inasistencias registradas.")

        st.divider()

        st.subheader("Pagos pendientes")

        pagos_pendientes = df_pagos[df_pagos["ESTADO"] == "PENDIENTE"]

        st.dataframe(
            pagos_pendientes[[
                "TRABAJADOR",
                "SUELDO AL DÍA",
                "SEMANA",
                "PAGO SEMANAL",
                "ESTADO",
                "OBSERVACIONES"
            ]],
            use_container_width=True
        )

        st.divider()

        st.subheader("Resumen completo de pagos semanales")

        st.dataframe(
            df_pagos[[
                "TRABAJADOR",
                "SUELDO AL DÍA",
                "SEMANA",
                "PAGO SEMANAL",
                "ESTADO",
                "OBSERVACIONES"
            ]],
            use_container_width=True
        )

        st.divider()

        st.subheader("Detalle completo de asistencias")

        st.dataframe(
            df_asistencias[[
                "FECHA",
                "TRABAJADOR",
                "OBRA",
                "SEMANA",
                "¿ASISTIÓ?",
                "HORAS EXTRAS",
                "DESCUENTOS"
            ]],
            use_container_width=True
        )

    except Exception as e:
        st.error("No se pudo cargar la sección de asistencias y pagos")
        st.write(e)
