import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Resumen Cuentas por Pagar ACABET", layout="wide")

COLOR_AZUL = "#002B4E"
COLOR_NARANJA = "#FF6A00"
COLOR_GRIS = "#F2F4F7"

st.markdown(
    """
    <style>
    .stApp {
        background-color: #F2F4F7;
    }

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

    .card-acabet {
        background-color: white;
        padding: 18px;
        border-radius: 14px;
        box-shadow: 0px 2px 8px rgba(0,0,0,0.08);
        border-left: 6px solid #002B4E;
        margin-bottom: 16px;
    }

    .calendar-card {
        background-color: white;
        padding: 20px;
        border-radius: 14px;
        box-shadow: 0px 2px 8px rgba(0,0,0,0.08);
        border-left: 6px solid #FF6A00;
        margin-bottom: 16px;
    }

    .calendar-line {
        font-size: 16px;
        margin-bottom: 6px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

sheet_id = "1mkCIQy1PMoHzOLeUZoyRXYEEgwx-i7rZ"
gid = "1779917486"

url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&gid={gid}"

fecha_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")


def limpiar_soles(columna):
    return (
        columna.astype(str)
        .str.replace("S/.", "", regex=False)
        .str.replace("S/", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.replace("-", "0", regex=False)
        .str.replace("None", "0", regex=False)
        .str.strip()
        .replace("", "0")
        .astype(float)
    )


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
            margin-bottom:20px;
        ">
            <h1 style="color:white; margin:0; font-size:34px;">
                RESUMEN CUENTAS POR PAGAR
            </h1>
            <h2 style="color:{COLOR_NARANJA}; margin:8px 0 8px 0; font-size:24px;">
                ACABET E&V CONSTRUCCIONES
            </h2>
            <p style="color:white; font-size:16px; margin:0;">
                Fecha y hora actual: {fecha_hora}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )


try:
    df = pd.read_csv(url)

    df["MONTO_NUM"] = limpiar_soles(df["MONTO"])
    df["INTERES_NUM"] = limpiar_soles(df["INTERÉS"])
    df["TOTAL_NUM"] = limpiar_soles(df["TOTAL"])

    df["FECHA DE PAGO_DT"] = pd.to_datetime(
        df["FECHA DE PAGO"],
        format="%d/%m/%Y",
        errors="coerce"
    )

    hoy = pd.Timestamp.today().normalize()
    df["DÍAS PARA PAGAR"] = (df["FECHA DE PAGO_DT"] - hoy).dt.days

    st.success("Datos cargados correctamente desde Google Sheets")

    deuda_total = df["TOTAL_NUM"].sum()
    deuda_pendiente = df[df["ESTADO"] == "PENDIENTE"]["TOTAL_NUM"].sum()
    deuda_pagada = df[df["ESTADO"] == "PAGADO"]["TOTAL_NUM"].sum()

    capital_total = df["MONTO_NUM"].sum()
    interes_total = df["INTERES_NUM"].sum()
    costo_financiero = (interes_total / capital_total) if capital_total > 0 else 0

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

    st.subheader("Interés pagado acumulado")

    col_int1, col_int2, col_int3 = st.columns(3)
    col_int1.metric("Capital prestado", f"S/ {capital_total:,.2f}")
    col_int2.metric("Interés total", f"S/ {interes_total:,.2f}")
    col_int3.metric("Costo financiero", f"{costo_financiero:.2%}")

    st.divider()

    top5 = (
        df[
            (df["ESTADO"] == "PENDIENTE")
            & (df["DÍAS PARA PAGAR"].notna())
        ]
        .sort_values("DÍAS PARA PAGAR", ascending=True)
        .head(5)
    )

    if len(top5) > 0:
        proximo = top5.iloc[0]
        dias = int(proximo["DÍAS PARA PAGAR"])

        if dias < 0:
            st.error(
                f"🔴 PAGO VENCIDO | {proximo['PRESTAMISTA']} | "
                f"S/ {proximo['TOTAL_NUM']:,.2f} | "
                f"Venció hace {abs(dias)} días"
            )
        elif dias <= 7:
            st.error(
                f"🔴 PAGO URGENTE | {proximo['PRESTAMISTA']} | "
                f"S/ {proximo['TOTAL_NUM']:,.2f} | "
                f"Vence en {dias} días"
            )
        else:
            st.warning(
                f"⚠️ PRÓXIMO PAGO | {proximo['PRESTAMISTA']} | "
                f"S/ {proximo['TOTAL_NUM']:,.2f} | "
                f"Vence en {dias} días"
            )

    st.subheader("Semáforo de vencimientos")

    pendientes_con_fecha = df[
        (df["ESTADO"] == "PENDIENTE")
        & (df["DÍAS PARA PAGAR"].notna())
    ]

    vencidos = len(pendientes_con_fecha[pendientes_con_fecha["DÍAS PARA PAGAR"] < 0])
    urgente = len(
        pendientes_con_fecha[
            (pendientes_con_fecha["DÍAS PARA PAGAR"] >= 0)
            & (pendientes_con_fecha["DÍAS PARA PAGAR"] <= 7)
        ]
    )
    pronto = len(
        pendientes_con_fecha[
            (pendientes_con_fecha["DÍAS PARA PAGAR"] >= 8)
            & (pendientes_con_fecha["DÍAS PARA PAGAR"] <= 15)
        ]
    )
    estable = len(pendientes_con_fecha[pendientes_con_fecha["DÍAS PARA PAGAR"] > 15])

    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    col_s1.metric("🔴 Vencidos", vencidos)
    col_s2.metric("🟠 0 a 7 días", urgente)
    col_s3.metric("🟡 8 a 15 días", pronto)
    col_s4.metric("🟢 Más de 15 días", estable)

    st.divider()

    st.subheader("Calendario de pagos")

    calendario = (
        pendientes_con_fecha
        .sort_values("FECHA DE PAGO_DT")
        .copy()
    )

    if len(calendario) > 0:
        calendario["MES"] = calendario["FECHA DE PAGO_DT"].dt.strftime("%B %Y")
        calendario["DIA"] = calendario["FECHA DE PAGO_DT"].dt.day

        meses_es = {
            "January": "Enero",
            "February": "Febrero",
            "March": "Marzo",
            "April": "Abril",
            "May": "Mayo",
            "June": "Junio",
            "July": "Julio",
            "August": "Agosto",
            "September": "Septiembre",
            "October": "Octubre",
            "November": "Noviembre",
            "December": "Diciembre",
        }

        for mes in calendario["MES"].unique():
            mes_es = mes
            for en, es in meses_es.items():
                mes_es = mes_es.replace(en, es)

            st.markdown(
                f"""
                <div class="calendar-card">
                    <h4 style="color:{COLOR_AZUL}; margin-top:0;">📅 {mes_es}</h4>
                """,
                unsafe_allow_html=True
            )

            pagos_mes = calendario[calendario["MES"] == mes]

            for _, fila in pagos_mes.iterrows():
                st.markdown(
                    f"""
                    <div class="calendar-line">
                        <b>{int(fila['DIA'])}</b> → {fila['PRESTAMISTA']} | 
                        <span style="color:{COLOR_NARANJA}; font-weight:bold;">
                            S/ {fila['TOTAL_NUM']:,.2f}
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No hay pagos pendientes con fecha registrada.")

    st.divider()

    st.subheader("Top 5 pagos más próximos")

    st.dataframe(
        top5[
            [
                "FECHA DE PAGO",
                "PRESTAMISTA",
                "TOTAL",
                "ESTADO",
                "DÍAS PARA PAGAR"
            ]
        ],
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
            "PAGADO": COLOR_AZUL
        },
        title="Distribución de deuda por estado"
    )

    grafico_pie.update_layout(
        paper_bgcolor="white",
        plot_bgcolor="white"
    )

    st.plotly_chart(grafico_pie, use_container_width=True)

    st.divider()

    st.subheader("Deuda por prestamista")

    deuda_prestamista = (
        df.groupby(["PRESTAMISTA", "ESTADO"], as_index=False)["TOTAL_NUM"]
        .sum()
    )

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
            "PAGADO": COLOR_AZUL
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
        df[
            [
                "FECHA DE PRÉSTAMO",
                "FECHA DE PAGO",
                "PRESTAMISTA",
                "MONTO",
                "INTERÉS",
                "TOTAL",
                "ESTADO"
            ]
        ],
        use_container_width=True
    )

except Exception as e:
    st.error("No se pudo cargar el Google Sheet")
    st.write(e)