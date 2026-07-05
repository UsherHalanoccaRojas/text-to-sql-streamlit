# 🗄️ Text-to-SQL Query Generator — Streamlit + Hugging Face

Aplicación web que traduce preguntas en **lenguaje natural** a **consultas SQL**
usando un modelo de Hugging Face, y las ejecuta en tiempo real contra una base
de datos SQLite de ejemplo (tienda online: clientes, productos y órdenes).

Proyecto desarrollado para el **Research Team Work N° 01: SQL AI Database Solutions**.

## 🚀 Demo

![demo](docs/demo.png)

Preguntas de ejemplo que puedes probar:
- "¿Cuántos clientes son de Peru?"
- "¿Cuál es el producto más caro?"
- "Muéstrame el total de órdenes por cliente"

## 🧱 Arquitectura

```
Usuario (pregunta en lenguaje natural)
        │
        ▼
Streamlit UI ──► Esquema de la BD (extraído dinámicamente)
        │
        ▼
Modelo Hugging Face (text-to-SQL)
        │
        ▼
Consulta SQL generada
        │
        ▼
SQLite (ejecución solo-lectura) ──► Resultado en tabla (pandas)
```

## 📦 Instalación

```bash
git clone https://github.com/UsherHalanoccaRojas/text-to-sql-streamlit.git
cd text-to-sql-streamlit
python -m venv venv
# Activar el entorno virtual
# Windows
venv\\Scripts\\activate
# Linux / macOS
source venv/bin/activate
pip install -r requirements.txt
```

## 🗃️ Crear la base de datos de ejemplo

```bash
python create_db.py
```

## ▶️ Ejecutar la aplicación

```bash
streamlit run app.py
```

Abre tu navegador en `http://localhost:8501`.

## 🔍 Cómo funciona

1. Se extrae automáticamente el **esquema** de la base de datos SQLite (tablas y columnas).
2. La pregunta del usuario + el esquema se envían al modelo
   [`juierror/text-to-sql-with-table-schema`](https://huggingface.co/juierror/text-to-sql-with-table-schema),
   un modelo seq2seq entrenado específicamente para generar SQL a partir de esquemas de tablas.
3. El SQL generado se muestra en pantalla para que el usuario lo revise.
4. Se ejecuta contra SQLite (bloqueando por seguridad cualquier sentencia que no sea `SELECT`).
5. El resultado se muestra como tabla interactiva con `pandas` + `st.dataframe`.

## ⚠️ Limitaciones y consideraciones de seguridad

- Los modelos text-to-SQL pueden **alucinar** columnas o tablas que no existen; siempre se debe
  validar el SQL antes de ejecutarlo en un entorno productivo.
- Esta demo bloquea palabras clave destructivas (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`)
  como medida mínima de seguridad, pero en producción se recomienda usar un **usuario de base
  de datos de solo lectura** además de validación adicional.
- El rendimiento del modelo depende del esquema: mientras más claros sean los nombres de tablas
  y columnas, mejores resultados se obtienen.

## 🛠️ Stack

- [Streamlit](https://streamlit.io/) — interfaz web
- [Hugging Face Transformers](https://huggingface.co/docs/transformers) — modelo text-to-SQL
- [SQLite](https://www.sqlite.org/) — base de datos de ejemplo
- [pandas](https://pandas.pydata.org/) — manejo y visualización de resultados

## 📄 Licencia

MIT — uso libre con fines educativos.

## ✍️ Autor

<TU NOMBRE> — Research Team Work N° 01, SQL AI Database Solutions
