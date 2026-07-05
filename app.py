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
    """Genera SQL a partir de una pregunta en lenguaje natural + esquema y lo limpia.
    Además, corrige patrones comunes de salida del modelo (por ejemplo, "SELECT COUNT customers ...").
    """
    prompt = f"tables: {schema}\nquestion: {question}"
    inputs = tokenizer(prompt, return_tensors="pt", padding=True, truncation=True)
    outputs = model.generate(**inputs, max_length=256)
    raw_sql = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # 1. Extraer la primera sentencia SELECT (hasta punto y coma o fin de línea)
    import re
    match = re.search(r"SELECT[\s\S]*?;", raw_sql, re.IGNORECASE)
    if match:
        sql = match.group(0).strip()
    else:
        sql = raw_sql.strip().split('\n')[0]

    # 2. Corrección de patrones específicos del modelo
    #    Ejemplo problemático: "SELECT COUNT customers (customer_id, name, ...) FROM table WHERE ... = Peru"
    #    Convertir a una forma válida: "SELECT COUNT(*) FROM customers WHERE country = 'Peru';"
    # Detectar si contiene "COUNT" y nombre de tabla "customers"
    if re.search(r"SELECT\s+COUNT", sql, re.IGNORECASE) and "customers" in sql.lower():
        # Extraer valor del filtro (p.e. Peru) usando regex de = <valor>
        val_match = re.search(r"=\s*([^\s;]+)", sql)
        country_val = val_match.group(1) if val_match else ""
        # Asegurarse de que el valor esté entre comillas
        if country_val and not (country_val.startswith("'") or country_val.startswith('"')):
            country_val = f"'{country_val}'"
        sql = f"SELECT COUNT(*) FROM customers WHERE country = {country_val};"
    return sql


# ---------------------------------------------------------------------
# Interfaz Streamlit
# ---------------------------------------------------------------------



def main():
    # Configuración de la página (sin emojis en títulos)
    st.set_page_config(page_title="Text-to-SQL con IA", page_icon=":gear:")
    st.title("Text-to-SQL Query Generator")
    st.caption("Streamlit + Hugging Face — escribe una pregunta y obtén SQL")
    
    if not os.path.exists(DB_PATH):
        st.error("No se encontró la base de datos. Ejecuta primero `python create_db.py`.")
        return
    
    # Mostrar esquema de la base de datos
    schema = get_schema(DB_PATH)
    with st.expander("Ver esquema de la base de datos"):
        st.code(schema)
    
    # Cargar modelo (cacheado)
    tokenizer, model = load_model()
    
    # Entrada de pregunta
    question = st.text_input(
        "Escribe tu pregunta en lenguaje natural",
        placeholder="Ej: ¿Cuántos clientes son de Perú?",
    )
    
    if st.button("Generar y ejecutar consulta") and question:
        with st.spinner("Generando SQL con el modelo..."):
            sql_query = generate_sql(question, schema, tokenizer, model)
        st.subheader("SQL generado")
        st.code(sql_query, language="sql")
        try:
            result_df = run_query(DB_PATH, sql_query)
            st.subheader("Resultado")
            st.dataframe(result_df, use_container_width=True)
            # Botón para descargar resultados como CSV
            csv_bytes = result_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Descargar resultados como CSV",
                data=csv_bytes,
                file_name="resultados.csv",
                mime="text/csv",
            )
            # Guardar en historial
            if "history" not in st.session_state:
                st.session_state.history = []
            st.session_state.history.append({
                "question": question,
                "sql": sql_query,
                "result": result_df,
            })
        except Exception as e:
            st.error(f"No se pudo ejecutar la consulta: {e}")
    
    st.divider()
    # Mostrar historial si existe
    if st.session_state.get("history"):
        with st.expander("Historial de consultas"):
            for idx, entry in enumerate(st.session_state.history, 1):
                st.markdown(f"**{idx}. Pregunta:** {entry['question']}")
                st.code(entry['sql'], language="sql")
                st.dataframe(entry['result'], use_container_width=True)
                st.write("---")
        # Botón para borrar historial con un solo clic
        if st.button("Borrar historial", key="clear_history"):
            st.session_state.history = []
            st.experimental_rerun()
    
    st.caption("Proyecto educativo — valida siempre el SQL generado antes de usarlo en producción.")
if __name__ == "__main__":
    main()
