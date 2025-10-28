import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd

# ---------- CONFIG DB ----------
USER = "postgres.vbeuhmiiygpljvqwqiyo"
PASSWORD = "alfre943553109"
HOST = "aws-1-us-east-2.pooler.supabase.com"
PORT = "5432"
DBNAME = "postgres"

# ---------- Conexión ----------
def get_connection():
    return psycopg2.connect(
        user=USER,
        password=PASSWORD,
        host=HOST,
        port=PORT,
        dbname=DBNAME
    )

# ---------- Crear tabla ----------
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS tienda_computo_inventario (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(50) UNIQUE NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    marca VARCHAR(100),
    modelo VARCHAR(100),
    tipo_parte VARCHAR(100),
    compatibilidad VARCHAR(150),
    categoria VARCHAR(100),
    stock INTEGER DEFAULT 0,
    stock_minimo INTEGER DEFAULT 0,
    precio_compra NUMERIC(12,2),
    precio_venta NUMERIC(12,2),
    ubicacion VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

def create_table():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(CREATE_TABLE_SQL)
    conn.commit()
    cur.close()
    conn.close()

# ---------- CRUD ----------
def insert_item(item):
    sql = """
    INSERT INTO tienda_computo_inventario
    (codigo, nombre, marca, modelo, tipo_parte, compatibilidad, categoria,
     stock, stock_minimo, precio_compra, precio_venta, ubicacion)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    RETURNING id;
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(sql, (
        item['codigo'], item['nombre'], item['marca'], item['modelo'],
        item['tipo_parte'], item['compatibilidad'], item['categoria'],
        item['stock'], item['stock_minimo'], item['precio_compra'],
        item['precio_venta'], item['ubicacion']
    ))
    new_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return new_id

def get_items(search=None, limit=200, offset=0):
    base = "SELECT * FROM tienda_computo_inventario"
    params = []
    if search:
        base += " WHERE codigo ILIKE %s OR nombre ILIKE %s OR marca ILIKE %s OR categoria ILIKE %s"
        q = f"%{search}%"
        params = [q, q, q, q]
    base += " ORDER BY id DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(base, tuple(params))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def get_item_by_id(item_id):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM tienda_computo_inventario WHERE id = %s", (item_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row

def update_item(item_id, data):
    sql = """
    UPDATE tienda_computo_inventario SET
      codigo=%s, nombre=%s, marca=%s, modelo=%s, tipo_parte=%s, compatibilidad=%s,
      categoria=%s, stock=%s, stock_minimo=%s, precio_compra=%s, precio_venta=%s,
      ubicacion=%s
    WHERE id=%s
    """
    params = (
        data['codigo'], data['nombre'], data['marca'], data['modelo'],
        data['tipo_parte'], data['compatibilidad'], data['categoria'],
        data['stock'], data['stock_minimo'], data['precio_compra'],
        data['precio_venta'], data['ubicacion'], item_id
    )
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(sql, params)
    conn.commit()
    cur.close()
    conn.close()

def delete_item(item_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM tienda_computo_inventario WHERE id = %s", (item_id,))
    conn.commit()
    cur.close()
    conn.close()

# ---------- UI ----------
st.set_page_config(page_title="Inventario Tienda de Cómputo", layout="wide")
st.title("💻 Inventario - Tienda de Computadoras y Laptops")

create_table()

menu = st.sidebar.selectbox("Menú", ["Registrar parte", "Ver inventario", "Editar / Eliminar", "Exportar CSV", "Acerca"])

if menu == "Registrar parte":
    st.header("Registrar nueva parte o componente")
    with st.form("form_nuevo"):
        codigo = st.text_input("Código de producto", max_chars=50)
        nombre = st.text_input("Nombre del componente")
        marca = st.text_input("Marca")
        modelo = st.text_input("Modelo")
        tipo_parte = st.text_input("Tipo de parte (Ej. SSD, Placa madre, Mouse, Laptop)")
        compatibilidad = st.text_input("Compatibilidad (Ej. Intel, AMD, DDR4)")
        categoria = st.text_input("Categoría")
        col1, col2, col3 = st.columns(3)
        with col1:
            stock = st.number_input("Stock actual", min_value=0, value=0)
            stock_minimo = st.number_input("Stock mínimo", min_value=0, value=5)
        with col2:
            precio_compra = st.number_input("Precio de compra (S/.)", min_value=0.0, value=0.0, format="%.2f")
            precio_venta = st.number_input("Precio de venta (S/.)", min_value=0.0, value=0.0, format="%.2f")
        with col3:
            ubicacion = st.text_input("Ubicación en tienda (Ej. Estante A3)")
        submitted = st.form_submit_button("Registrar")

    if submitted:
        if not codigo or not nombre:
            st.error("Complete al menos Código y Nombre.")
        else:
            item = {
                'codigo': codigo.strip(),
                'nombre': nombre.strip(),
                'marca': marca.strip(),
                'modelo': modelo.strip(),
                'tipo_parte': tipo_parte.strip(),
                'compatibilidad': compatibilidad.strip(),
                'categoria': categoria.strip(),
                'stock': int(stock),
                'stock_minimo': int(stock_minimo),
                'precio_compra': float(precio_compra),
                'precio_venta': float(precio_venta),
                'ubicacion': ubicacion.strip()
            }
            try:
                new_id = insert_item(item)
                st.success(f"Parte registrada correctamente (ID={new_id})")
            except Exception as e:
                st.error(f"Error al registrar: {e}")

elif menu == "Ver inventario":
    st.header("Inventario de componentes")
    q = st.text_input("Buscar por código/nombre/marca/categoría")
    per_page = st.selectbox("Mostrar", [10, 25, 50, 100], index=1)
    page = st.session_state.get("page", 0)
    if st.button("Buscar") or q != "":
        st.session_state.page = 0
        page = 0
    offset = page * per_page

    try:
        rows = get_items(search=q if q else None, limit=per_page, offset=offset)
        df = pd.DataFrame(rows)
        if df.empty:
            st.info("No hay registros.")
        else:
            st.dataframe(df.drop(columns=['created_at']), height=400)
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("<< Anterior") and page > 0:
                    st.session_state.page = page - 1
                    st.experimental_rerun()
            with c2:
                st.write(f"Página: {page + 1}")
            with c3:
                if st.button("Siguiente >>") and len(df) == per_page:
                    st.session_state.page = page + 1
                    st.experimental_rerun()
    except Exception as e:
        st.error(f"Error obteniendo inventario: {e}")

elif menu == "Editar / Eliminar":
    st.header("Editar o eliminar parte")
    id_to_edit = st.number_input("ID del producto", min_value=1, step=1)
    if st.button("Cargar parte"):
        item = get_item_by_id(id_to_edit)
        if not item:
            st.error("Parte no encontrada.")
        else:
            st.session_state.edit_item = item

    if "edit_item" in st.session_state:
        it = st.session_state.edit_item
        with st.form("form_edit"):
            codigo = st.text_input("Código", value=it['codigo'])
            nombre = st.text_input("Nombre", value=it['nombre'])
            marca = st.text_input("Marca", value=it['marca'])
            modelo = st.text_input("Modelo", value=it['modelo'])
            tipo_parte = st.text_input("Tipo de parte", value=it['tipo_parte'])
            compatibilidad = st.text_input("Compatibilidad", value=it['compatibilidad'])
            categoria = st.text_input("Categoría", value=it['categoria'])
            col1, col2, col3 = st.columns(3)
            with col1:
                stock = st.number_input("Stock actual", min_value=0, value=it['stock'])
                stock_minimo = st.number_input("Stock mínimo", min_value=0, value=it['stock_minimo'])
            with col2:
                precio_compra = st.number_input("Precio compra (S/.)", min_value=0.0, value=float(it['precio_compra']), format="%.2f")
                precio_venta = st.number_input("Precio venta (S/.)", min_value=0.0, value=float(it['precio_venta']), format="%.2f")
            with col3:
                ubicacion = st.text_input("Ubicación", value=it['ubicacion'])
            btn_update = st.form_submit_button("Actualizar")
            btn_delete = st.form_submit_button("Eliminar")

        if btn_update:
            try:
                data = {
                    'codigo': codigo.strip(),
                    'nombre': nombre.strip(),
                    'marca': marca.strip(),
                    'modelo': modelo.strip(),
                    'tipo_parte': tipo_parte.strip(),
                    'compatibilidad': compatibilidad.strip(),
                    'categoria': categoria.strip(),
                    'stock': int(stock),
                    'stock_minimo': int(stock_minimo),
                    'precio_compra': float(precio_compra),
                    'precio_venta': float(precio_venta),
                    'ubicacion': ubicacion.strip()
                }
                update_item(it['id'], data)
                st.success("Parte actualizada correctamente.")
                del st.session_state['edit_item']
            except Exception as e:
                st.error(f"Error actualizando: {e}")

        if btn_delete:
            try:
                delete_item(it['id'])
                st.success("Parte eliminada.")
                del st.session_state['edit_item']
            except Exception as e:
                st.error(f"Error eliminando: {e}")

elif menu == "Exportar CSV":
    st.header("Exportar inventario a CSV")
    try:
        rows = get_items(limit=10000, offset=0)
        df = pd.DataFrame(rows)
        if df.empty:
            st.info("No hay registros para exportar.")
        else:
            st.dataframe(df.drop(columns=['created_at']), height=300)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Descargar CSV", data=csv, file_name="inventario_tienda_computo.csv", mime="text/csv")
    except Exception as e:
        st.error(f"Error exportando: {e}")

else:
    st.header("Acerca")
    st.write("""
    Aplicativo CRUD para inventario de partes y componentes de computadoras.
    - Registrar, buscar, editar y eliminar componentes.
    - Exportar inventario a CSV.
    """)
