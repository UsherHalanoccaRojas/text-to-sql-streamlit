"""
app.py
Text-to-SQL Query Generator
----------------------------
Aplicacion Streamlit que traduce preguntas en lenguaje natural a
consultas SQL usando un modelo de Hugging Face (text-to-SQL), y las
ejecuta contra una base de datos SQLite de ejemplo.

Autor: Usher Halanocca Rojas
Curso: Research Team Work N 01 - SQL AI Database Solutions
"""

import os
import sqlite3
import pandas as pd
import streamlit as st
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

DB_PATH = os.path.join("data", "store.db")
MODEL_NAME = "juierror/text-to-sql-with-table-schema"  # modelo público en HF Hub


# ---------------------------------------------------------------------
# Utilidades de base de datos
# ---------------------------------------------------------------------
def get_schema(db_path: str) -> str:
    """Extrae el esquema de la base de datos como texto plano."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]

    schema_parts = []
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [col[1] for col in cursor.fetchall()]
        schema_parts.append(f"{table} ({', '.join(columns)})")

    conn.close()
    return " | ".join(schema_parts)


def run_query(db_path: str, query: str) -> pd.DataFrame:
    """Ejecuta una consulta SQL de solo lectura y devuelve un DataFrame."""
    forbidden = ["insert", "update", "delete", "drop", "alter"]
    if any(word in query.lower() for word in forbidden):
        raise ValueError("Por seguridad, solo se permiten consultas SELECT.")

    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


# ---------------------------------------------------------------------
# Carga del modelo (cacheada para no recargarlo en cada interaccion)
# ---------------------------------------------------------------------
@st.cache_resource
def load_model():
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
    return tokenizer, model


def generate_sql(question: str, schema: str, tokenizer, model) -> str:
    """Genera SQL a partir de una pregunta en lenguaje natural + esquema."""
    prompt = f"tables: {schema}\nquestion: {question}"
    inputs = tokenizer(prompt, return_tensors="pt", padding=True, truncation=True)
    outputs = model.generate(**inputs, max_length=256)
    sql = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return sql


# ---------------------------------------------------------------------
# Interfaz Streamlit
# ---------------------------------------------------------------------
def main():
    st.set_page_config(page_title="Text-to-SQL con IA", page_icon="🗄️")
    st.title("🗄️ Text-to-SQL Query Generator")
    st.caption("Streamlit + Hugging Face — pregunta en lenguaje natural, obtén SQL")

    if not os.path.exists(DB_PATH):
        st.error("No se encontró la base de datos. Ejecuta primero `python create_db.py`.")
        return

    schema = get_schema(DB_PATH)
    with st.expander("📋 Ver esquema de la base de datos"):
        st.code(schema)

    tokenizer, model = load_model()

    question = st.text_input(
        "Escribe tu pregunta en lenguaje natural",
        placeholder="Ej: ¿Cuántos clientes son de Peru?",
    )

    if st.button("Generar y ejecutar consulta") and question:
        with st.spinner("Generando SQL con el modelo..."):
            sql_query = generate_sql(question, schema, tokenizer, model)

        st.subheader("🧠 SQL generado")
        st.code(sql_query, language="sql")

        try:
            result_df = run_query(DB_PATH, sql_query)
            st.subheader("📊 Resultado")
            st.dataframe(result_df, use_container_width=True)
        except Exception as e:
            st.error(f"No se pudo ejecutar la consulta: {e}")

    st.divider()
    st.caption(
        "Proyecto educativo — valida siempre el SQL generado antes de usarlo en producción."
    )


if __name__ == "__main__":
    main()
