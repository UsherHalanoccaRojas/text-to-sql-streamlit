# Cómo construí un traductor de lenguaje natural a SQL con Streamlit y Hugging Face

## Introducción

No todos en un equipo saben escribir SQL, pero casi todos saben hacer preguntas
en lenguaje natural como *"¿cuántos clientes tenemos en Perú?"* o *"¿cuál es
nuestro producto más vendido?"*. Esa brecha es exactamente lo que resuelven las
soluciones **Text-to-SQL**: sistemas de IA que traducen preguntas humanas en
consultas SQL ejecutables contra una base de datos real.

En este artículo muestro cómo construí, con código real, una aplicación web
usando **Streamlit** + un modelo de **Hugging Face** especializado en generar
SQL a partir de un esquema de base de datos. El código completo está disponible
en mi repositorio público (link al final).

## ¿Por qué Text-to-SQL importa?

Las bases de datos empresariales suelen tener decenas de tablas con nombres
técnicos. Pedirle a un analista de negocio que aprenda SQL para cada pregunta
es poco práctico. Un modelo de lenguaje entrenado para SQL puede:

- Reducir la dependencia de un equipo de datos para consultas simples.
- Acelerar la exploración de datos ("self-service analytics").
- Servir como capa conversacional sobre dashboards existentes.

## Arquitectura de la solución

```
Pregunta en lenguaje natural
        │
        ▼
Esquema de la base de datos (extraído dinámicamente con SQLite PRAGMA)
        │
        ▼
Modelo Hugging Face (text-to-SQL con esquema)
        │
        ▼
SQL generado → validado → ejecutado en SQLite
        │
        ▼
Resultado mostrado como tabla en Streamlit
```

La clave de este enfoque es que el modelo recibe **tanto la pregunta como el
esquema de las tablas**, lo que mejora sustancialmente la precisión frente a
pedirle SQL "a ciegas".

## Código real

### 1. Base de datos de ejemplo

Genero una base SQLite con tres tablas (`customers`, `products`, `orders`)
que simulan una tienda online:

```python
cursor.execute("""
    CREATE TABLE customers (
        customer_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        country TEXT NOT NULL,
        signup_date TEXT NOT NULL
    )
""")
```

### 2. Extracción dinámica del esquema

Para que el modelo entienda la estructura de la base, extraigo el esquema
en tiempo de ejecución con `PRAGMA table_info`:

```python
def get_schema(db_path: str) -> str:
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
```

### 3. Generación de SQL con Hugging Face

Uso el modelo público `juierror/text-to-sql-with-table-schema`, un modelo
seq2seq entrenado específicamente para recibir un esquema y una pregunta,
y devolver SQL:

```python
@st.cache_resource
def load_model():
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
    return tokenizer, model

def generate_sql(question, schema, tokenizer, model):
    prompt = f"tables: {schema}\nquestion: {question}"
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True)
    outputs = model.generate(**inputs, max_length=256)
    return tokenizer.decode(outputs[0], skip_special_tokens=True)
```

### 4. Ejecución segura de la consulta

Antes de ejecutar cualquier SQL generado por el modelo, filtro sentencias
destructivas como medida mínima de seguridad:

```python
def run_query(db_path: str, query: str) -> pd.DataFrame:
    forbidden = ["insert", "update", "delete", "drop", "alter"]
    if any(word in query.lower() for word in forbidden):
        raise ValueError("Por seguridad, solo se permiten consultas SELECT.")

    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df
```

### 5. Interfaz con Streamlit

Todo se conecta en una interfaz simple donde el usuario escribe su pregunta,
ve el SQL generado y el resultado en una tabla interactiva:

```python
question = st.text_input("Escribe tu pregunta en lenguaje natural")

if st.button("Generar y ejecutar consulta") and question:
    sql_query = generate_sql(question, schema, tokenizer, model)
    st.code(sql_query, language="sql")
    result_df = run_query(DB_PATH, sql_query)
    st.dataframe(result_df)
```

## Resultado

Con preguntas como *"¿cuántos clientes son de Peru?"*, la aplicación genera
automáticamente el SQL equivalente (`SELECT COUNT(*) FROM customers WHERE
country = 'Peru'`) y muestra el resultado en una tabla, sin que el usuario
escriba una sola línea de SQL.

## Limitaciones importantes

- **Alucinaciones**: el modelo puede inventar columnas o tablas si el esquema
  es ambiguo o muy grande. Siempre hay que mostrar el SQL generado para que
  el usuario lo valide antes de confiar en el resultado.
- **Seguridad**: bloquear palabras clave no es suficiente en producción; se
  recomienda usar un usuario de base de datos de solo lectura.
- **Escalabilidad del esquema**: con decenas de tablas, conviene enviar solo
  el subconjunto de esquema relevante a la pregunta (técnica de *schema
  linking*) en lugar del esquema completo.

## Conclusión

Text-to-SQL es un ejemplo claro de cómo la IA generativa puede reducir
fricciones reales en el trabajo con datos. Con herramientas gratuitas y
públicas —Streamlit para la interfaz y un modelo abierto de Hugging Face para
la generación— es posible construir un prototipo funcional en menos de una
hora, como se muestra en el repositorio de este proyecto.

## Repositorio

🔗 Código completo: `https://github.com/<tu-usuario>/text-to-sql-streamlit`

## Referencias

- Kuhelidey, "Building a Text-to-SQL Query Generator with Streamlit and Hugging Face", Medium.
- Hugging Face, "Text-to-SQL", smolagents docs.
- freeCodeCamp, "How to Talk to Any Database Using AI".
