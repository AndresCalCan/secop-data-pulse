"""
SECOP II Data Pulse - Dashboard Analítico de Contratación Pública en Colombia
Desarrollado con Python, SQL (SQLite), Pandas, Plotly y Streamlit.
"""

import os
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from src.etl import fetch_contracts, transform_contracts, save_to_sqlite
from src.database import (
    get_connection,
    get_kpi_summary,
    get_top_entidades,
    get_top_contratistas_ranking,
    get_distribucion_modalidad,
    get_gasto_por_departamento
)

# Page configuration
st.set_page_config(
    page_title="SECOP II Data Pulse | Colombia",
    page_icon="🇨🇴",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Formatting helpers
def format_cop(value: float) -> str:
    if value >= 1e12:
        return f"${value / 1e12:.2f} Billones COP"
    elif value >= 1e9:
        return f"${value / 1e9:.2f} Mil Millones COP"
    elif value >= 1e6:
        return f"${value / 1e6:.1f} Millones COP"
    return f"${value:,.0f} COP"


# Ensure data directory exists
os.makedirs("data", exist_ok=True)
DB_PATH = "data/secop_contracts.db"


@st.cache_data(ttl=600)
def load_and_sync_data(departamento: str, modalidad: str, limit: int):
    """Fetches data from SODA API, runs ETL, and saves to SQLite."""
    with st.spinner("Descargando y procesando contratos del SECOP II en tiempo real..."):
        raw = fetch_contracts(departamento=departamento, modalidad=modalidad, limit=limit)
        df = transform_contracts(raw)
        save_to_sqlite(df, db_path=DB_PATH)
    return len(df)


# Sidebar Filters
st.sidebar.markdown("## 🇨🇴 SECOP II Analytics")
st.sidebar.caption("Monitor en tiempo real de la base de **Datos Abiertos Colombia**.")

departamentos_comunes = [
    "Todos", "BOGOTÁ D.C.", "ANTIOQUIA", "VALLE DEL CAUCA", 
    "CUNDINAMARCA", "ATLÁNTICO", "SANTANDER", "BOLÍVAR", "CALDAS"
]
sel_depto = st.sidebar.selectbox("Departamento", departamentos_comunes, index=0)

modalidades_comunes = [
    "Todas", "Contratación directa", "Licitación pública", 
    "Selección abreviada de menor cuantía", "Mínima cuantía", "Régimen especial"
]
sel_modalidad = st.sidebar.selectbox("Modalidad de Contratación", modalidades_comunes, index=0)

limit_records = st.sidebar.slider("Registros a consultar de la API", min_value=200, max_value=2500, value=800, step=200)

if st.sidebar.button("🔄 Actualizar Datos desde SECOP II", use_container_width=True):
    st.cache_data.clear()
    load_and_sync_data(sel_depto, sel_modalidad, limit_records)

# Initialize data and ensure database connection is fresh
conn = get_connection(DB_PATH)
try:
    kpi_data = get_kpi_summary(conn)
    if kpi_data["total_contratos"] == 0:
        load_and_sync_data(sel_depto, sel_modalidad, limit_records)
        conn = get_connection(DB_PATH)
        kpi_data = get_kpi_summary(conn)
except Exception:
    load_and_sync_data(sel_depto, sel_modalidad, limit_records)
    conn = get_connection(DB_PATH)
    kpi_data = get_kpi_summary(conn)

# Main Header
st.title("🇨🇴 SECOP II Data Pulse: Monitor de Contratación Pública")
st.caption("Pipeline ETL y Dashboard Analítico desarrollado con **Python + SQLite + Streamlit** consumiendo la API de Socrata (datos.gov.co).")

st.markdown("---")

# Executive KPIs
col1, col2, col3, col4 = st.columns(4)
col1.metric("Contratos Analizados", f"{kpi_data['total_contratos']:,}")
col2.metric("Monto Total Contratado", format_cop(kpi_data['monto_total_cop']))
col3.metric("Promedio por Contrato", format_cop(kpi_data['promedio_contrato_cop']))
col4.metric("Mayor Contrato Adjudicado", format_cop(kpi_data['mayor_contrato_cop']))

st.markdown("---")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Tablero Ejecutivo", 
    "🗺️ Distribución Geográfica", 
    "🔍 Explorador de Contratos", 
    "💻 Arquitectura & SQL"
])

with tab1:
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("🏛️ Entidades con Mayor Inversión Pública")
        df_entidades = get_top_entidades(conn, limit=8)
        if not df_entidades.empty:
            fig_ent = px.bar(
                df_entidades,
                x="total_invertido_cop",
                y="nombre_entidad",
                orientation="h",
                text=df_entidades["total_invertido_cop"].apply(format_cop),
                labels={"total_invertido_cop": "Inversión (COP)", "nombre_entidad": "Entidad Pública"},
                color="total_invertido_cop",
                color_continuous_scale="Blues"
            )
            fig_ent.update_layout(yaxis=dict(autorange="reversed"), showlegend=False, height=420)
            st.plotly_chart(fig_ent, use_container_width=True)
        else:
            st.info("No hay datos para el filtro seleccionado.")

    with col_right:
        st.subheader("⚖️ Distribución por Modalidad de Contratación")
        df_modalidad = get_distribucion_modalidad(conn)
        if not df_modalidad.empty:
            fig_mod = px.pie(
                df_modalidad,
                names="modalidad_de_contratacion",
                values="monto_total",
                hole=0.45,
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            fig_mod.update_traces(textposition='inside', textinfo='percent+label')
            fig_mod.update_layout(height=420, showlegend=False)
            st.plotly_chart(fig_mod, use_container_width=True)
        else:
            st.info("No hay datos de modalidades.")

    st.subheader("🏆 Ranking de Contratistas con Mayor Adjudicación (SQL Window Function)")
    st.markdown("Calculado en la base de datos con `DENSE_RANK() OVER (ORDER BY total_adjudicado_cop DESC)`:")
    df_contratistas = get_top_contratistas_ranking(conn, limit=10)
    if not df_contratistas.empty:
        df_contratistas_view = df_contratistas.copy()
        df_contratistas_view["Total Adjudicado"] = df_contratistas_view["total_adjudicado_cop"].apply(format_cop)
        df_contratistas_view = df_contratistas_view.rename(columns={
            "ranking": "Puesto",
            "proveedor_adjudicado": "Contratista / Proveedor",
            "documento_proveedor": "NIT / Cédula",
            "numero_adjudicaciones": "N° Contratos"
        })[["Puesto", "Contratista / Proveedor", "NIT / Cédula", "N° Contratos", "Total Adjudicado"]]
        st.dataframe(df_contratistas_view, use_container_width=True, hide_index=True)

with tab2:
    st.subheader("📍 Gasto Público por Departamento")
    df_deptos = get_gasto_por_departamento(conn)
    if not df_deptos.empty:
        fig_dept = px.bar(
            df_deptos.head(15),
            x="departamento",
            y="monto_total_cop",
            color="total_contratos",
            text=df_deptos.head(15)["monto_total_cop"].apply(format_cop),
            labels={"departamento": "Departamento", "monto_total_cop": "Monto Total COP", "total_contratos": "N° Contratos"},
            color_continuous_scale="Viridis"
        )
        fig_dept.update_layout(xaxis_tickangle=-45, height=500)
        st.plotly_chart(fig_dept, use_container_width=True)
    else:
        st.info("No hay información geográfica disponible.")

with tab3:
    st.subheader("📋 Búsqueda y Detalle de Contratos")
    df_all = pd.read_sql_query("""
        SELECT 
            referencia_del_contrato as Referencia,
            nombre_entidad as Entidad,
            departamento as Departamento,
            proveedor_adjudicado as Contratista,
            valor_del_contrato as Valor_COP,
            modalidad_de_contratacion as Modalidad,
            tipo_de_contrato as Tipo,
            estado_contrato as Estado,
            objeto_del_contrato as Objeto
        FROM contracts
        ORDER BY valor_del_contrato DESC
    """, conn)
    
    search_query = st.text_input("Buscar por contratista, entidad o palabra clave:", "")
    if search_query:
        mask = (
            df_all["Entidad"].str.contains(search_query, case=False, na=False) |
            df_all["Contratista"].str.contains(search_query, case=False, na=False) |
            df_all["Objeto"].str.contains(search_query, case=False, na=False)
        )
        filtered_view = df_all[mask]
    else:
        filtered_view = df_all

    formatted_table = filtered_view.copy()
    formatted_table["Valor_COP"] = formatted_table["Valor_COP"].apply(format_cop)
    st.dataframe(formatted_table, use_container_width=True, height=450)

with tab4:
    st.subheader("🛠️ Arquitectura Técnica del Proyecto")
    st.markdown("""
    Este proyecto fue diseñado siguiendo buenas prácticas de ingeniería de software y análisis de datos:
    1. **Extracción (ETL):** Conexión HTTP vía `requests` al endpoint SODA (Socrata Open Data API) de Datos Abiertos Colombia con ordenamiento y paginación controlada.
    2. **Transformación:** Normalización de tipos de datos, limpieza de valores nulos y parseo de fechas en `pandas`.
    3. **Carga y Persistencia:** Creación y actualización de tablas estructuradas en base de datos relacional `SQLite`.
    4. **Consultas SQL avanzadas:** Uso de **CTEs** (*Common Table Expressions*) y **Window Functions** (`DENSE_RANK() OVER`) para calcular rankings dinámicos en base de datos en lugar de procesarlo en memoria.
    5. **Visualización y Despliegue:** Dashboard reactivo en `Streamlit` y gráficos interactivos con `Plotly`, preparado para despliegue en la nube en **Streamlit Cloud**.
    """)
    
    st.code("""
-- Ejemplo de la consulta SQL ejecutada en el módulo database.py:
WITH ContratistasTotal AS (
    SELECT 
        proveedor_adjudicado,
        documento_proveedor,
        COUNT(*) as numero_adjudicaciones,
        SUM(valor_del_contrato) as total_adjudicado_cop
    FROM contracts
    WHERE proveedor_adjudicado IS NOT NULL
    GROUP BY proveedor_adjudicado, documento_proveedor
)
SELECT 
    DENSE_RANK() OVER (ORDER BY total_adjudicado_cop DESC) as ranking,
    proveedor_adjudicado,
    numero_adjudicaciones,
    total_adjudicado_cop
FROM ContratistasTotal
ORDER BY total_adjudicado_cop DESC
LIMIT 10;
    """, language="sql")

st.markdown("---")
st.caption("Desarrollado por **Andrés Felipe Calderón Cantillo** | Estudiante de Ingeniería de Sistemas - Universidad Libre")
