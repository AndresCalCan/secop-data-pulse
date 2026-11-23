# 🇨🇴 SECOP II Data Pulse: Monitor Analítico de Contratación Pública en Colombia

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40%2B-FF4B4B.svg)](https://streamlit.io/)
[![SQLite](https://img.shields.io/badge/Database-SQLite-003B57.svg)](https://www.sqlite.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> Pipeline automatizado de extracción (ETL), procesamiento y visualización analítica de contratos del Estado colombiano en tiempo real, consumiendo la API abierta del **SECOP II** de [Datos Abiertos Colombia](https://www.datos.gov.co/).

---

## 📌 Contexto del Problema
La contratación pública en Colombia a través de SECOP II genera millones de registros anuales con presupuestos multimillonarios. Analizar de forma ágil qué entidades gastan más, cuáles son los contratistas con mayor concentración de recursos y qué modalidades predominan representa un reto fundamental tanto para la auditoría, la transparencia y la inteligencia de negocios en el sector público y privado.

Este proyecto implementa una solución completa de ingeniería de datos y desarrollo backend:
1. Conexión y consulta a la **SODA REST API** de Datos Abiertos.
2. Limpieza, transformación y estructuración mediante **Pandas**.
3. Almacenamiento y consultas analíticas de alto rendimiento mediante **SQL relacional (SQLite)** con soporte para **CTEs y Window Functions**.
4. Interfaz web reactiva y gráficos interactivos con **Streamlit y Plotly**.

---

## 🏗️ Arquitectura de la Solución

```mermaid
flowchart LR
    A["API SECOP II (datos.gov.co)"] -->|Extracción REST / JSON| B["ETL Pipeline (src/etl.py)"]
    B -->|Limpieza y normalización| C["Base de Datos SQLite (data/secop.db)"]
    C -->|Consultas SQL avanzadas (CTEs & Window Functions)| D["Módulo Analítico (src/database.py)"]
    D -->|DataFrames procesados| E["Dashboard Web (Streamlit & Plotly)"]
```

---

## 🛠️ Stack Tecnológico
* **Lenguaje:** Python 3.14
* **Extracción y ETL:** `requests`, `pandas`
* **Base de Datos & SQL:** `sqlite3` (Consultas con `WITH`, `DENSE_RANK() OVER`, `GROUP BY`)
* **Visualización:** `streamlit`, `plotly`
* **Control de Versiones:** Git & GitHub

---

## 🚀 Instalación y Ejecución Local

### 1. Clonar el repositorio
```bash
git clone https://github.com/AndresCalCan/secop-data-pulse.git
cd secop-data-pulse
```

### 2. Crear entorno virtual e instalar dependencias
```bash
python -m venv venv
# En Windows:
venv\Scripts\activate
# En Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Ejecutar la aplicación
```bash
streamlit run app.py
```
La aplicación se abrirá automáticamente en tu navegador en `http://localhost:8501`.

---

## 🧠 Consultas SQL Implementadas (Destacadas)

Para evitar sobrecargar la memoria en el cliente web, los análisis de concentración de contratos se realizan directamente en el motor relacional utilizando **Window Functions**:

```sql
WITH ContratistasTotal AS (
    SELECT 
        proveedor_adjudicado,
        documento_proveedor,
        COUNT(*) AS numero_adjudicaciones,
        SUM(valor_del_contrato) AS total_adjudicado_cop
    FROM contracts
    WHERE proveedor_adjudicado IS NOT NULL
    GROUP BY proveedor_adjudicado, documento_proveedor
)
SELECT 
    DENSE_RANK() OVER (ORDER BY total_adjudicado_cop DESC) AS ranking,
    proveedor_adjudicado,
    documento_proveedor,
    numero_adjudicaciones,
    total_adjudicado_cop
FROM ContratistasTotal
ORDER BY total_adjudicado_cop DESC
LIMIT 10;
```

---

## 👨‍💻 Autor
**Andrés Felipe Calderón Cantillo**  
*Estudiante de Ingeniería de Sistemas — Universidad Libre (Bogotá, Colombia)*  
* Enfoque: Backend, Ingeniería de Datos y Analítica.  
* GitHub: [@AndresCalCan](https://github.com/AndresCalCan)
