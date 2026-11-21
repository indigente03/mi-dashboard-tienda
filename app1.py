import os
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# ============================================================
# RUTAS BLINDADAS (funciona en Spyder, VSCode o terminal)
# ============================================================
try:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    BASE_DIR = os.getcwd()

DATA_DIR = os.path.join(BASE_DIR, "data")
ASSETS_DIR = os.path.join(BASE_DIR, "assets", "imagenes")

# ============================================================
# CONFIGURACIÓN DE PÁGINA
# ============================================================
st.set_page_config(
    page_title="Dashboard Tienda de Barrio",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🏪 Dashboard — Tienda de Barrio Colombiana")
st.markdown("**Datos 2026 · Streamlit + Plotly**")

# ============================================================
# CARGA DE DATOS
# ============================================================
@st.cache_data
def cargar_datos():
    def leer_csv_robusto(ruta):
        with open(ruta, "r", encoding="utf-8-sig") as f:
            lineas = f.readlines()
        
        lineas = [line.replace('"', '').strip() for line in lineas if line.strip()]
        if not lineas:
            return pd.DataFrame()
            
        primera_linea = lineas[0]
        separador = ';' if ';' in primera_linea else ','
        
        datos = [line.split(separador) for line in lineas]
        df = pd.DataFrame(datos[1:], columns=datos[0])
        df.columns = df.columns.str.strip().str.lower()
        return df

    # 1. Leer los archivos
    productos = leer_csv_robusto(os.path.join(DATA_DIR, "productos.csv"))
    inventario = leer_csv_robusto(os.path.join(DATA_DIR, "inventario.csv"))
    ventas = leer_csv_robusto(os.path.join(DATA_DIR, "ventas_cabecera.csv"))
    detalle = leer_csv_robusto(os.path.join(DATA_DIR, "ventas_detalle.csv"))

    # 2. Convertir a numéricos
    for df in [productos, inventario, ventas, detalle]:
        cols_numericas = ['producto_id', 'precio_compra', 'precio_venta', 'stock_actual', 
                          'stock_minimo', 'venta_id', 'anio', 'mes', 'cliente_id', 
                          'total', 'detalle_id', 'cantidad', 'precio_unitario', 'subtotal']
        for col in cols_numericas:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

    # 3. ARREGLO DE FECHAS
    if "fecha" in ventas.columns:
        ventas["fecha"] = pd.to_datetime(ventas["fecha"], format="%d/%m/%Y %H:%M", errors='coerce')
        if ventas["fecha"].isna().all():
            ventas["fecha"] = pd.to_datetime(ventas["fecha"], dayfirst=True, errors='coerce')

    if "ultima_actualizacion" in inventario.columns:
        inventario["ultima_actualizacion"] = pd.to_datetime(inventario["ultima_actualizacion"], errors='coerce')

    return productos, inventario, ventas, detalle

try:
    productos, inventario, ventas, detalle = cargar_datos()
except FileNotFoundError as e:
    st.error(f"❌ No se encontraron los datos. Verifica la carpeta `data/`.\n\nDetalle: {e}")
    st.stop()

# ============================================================
# MENÚ LATERAL
# ============================================================
st.sidebar.header("🧭 Navegación")
opcion = st.sidebar.radio(
    "Selecciona una sección",
    ["💰 Ventas", "📦 Inventario"]
)
st.sidebar.markdown("---")

# ============================================================
# SECCIÓN: VENTAS
# ============================================================
if opcion == "💰 Ventas":

    st.sidebar.subheader("🔎 Filtros de Ventas")
    
    categorias = ["Todas"] + sorted(productos["categoria"].unique().tolist())
    cat_sel = st.sidebar.selectbox("Categoría", categorias)


    
  # -- SELECTOR DE MESES CON SEGMENTED CONTROL --
    st.markdown("### 📅 Selección de Meses")
    
    # 1. Inicializamos el estado del selector si no existe
    if "selector_meses" not in st.session_state:
        st.session_state.selector_meses = list(range(1, 13))
        
    # 2. Función que se ejecuta al presionar el botón
    def seleccionar_todos():
        st.session_state.selector_meses = list(range(1, 13))

    # 3. El botón usa el callback para actualizar el estado ANTES de que se dibuje el widget
    st.button("🔄 Seleccionar todos los meses", on_click=seleccionar_todos)
    
    meses = {
        1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr",
        5: "May", 6: "Jun", 7: "Jul", 8: "Ago",
        9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"
    }
    
    # 4. El Segmented Control se dibuja leyendo el session_state
    mes_sel = st.segmented_control(
        "Selecciona los meses",
        options=list(meses.keys()),
        format_func=lambda x: meses[x],
        selection_mode="multi",
        key="selector_meses" # Aquí Streamlit se enlaza automáticamente al session_state
    )
    
    # 5. Protección si el usuario desmarca todos
    if not mes_sel:
        st.warning("⚠️ Por favor selecciona al menos un mes.")
        mes_sel = [1]
    
    # Si el usuario da clic en el botón, forzamos el estado
    if mes_sel == []:
        st.warning("⚠️ Por favor selecciona al menos un mes.")
        mes_sel = [1] # Evita que el dashboard se rompa si no hay meses

    # Filtros de datos
    ventas_f = ventas[ventas["mes"].isin(mes_sel)].copy()
    detalle_f = detalle.merge(
        ventas_f[["venta_id", "fecha", "mes"]], on="venta_id", how="inner"
    )
    detalle_f = detalle_f.merge(
        productos[["producto_id", "nombre", "categoria"]],
        on="producto_id", how="left"
    )
    if cat_sel != "Todas":
        detalle_f = detalle_f[detalle_f["categoria"] == cat_sel]
        ventas_f = ventas_f[ventas_f["venta_id"].isin(detalle_f["venta_id"].unique())]

    # KPIs
    st.markdown("## 📊 Indicadores de desempeño")
    total_ventas = ventas_f["total"].sum()
    num_transacciones = ventas_f["venta_id"].nunique()
    ticket_promedio = total_ventas / num_transacciones if num_transacciones > 0 else 0

    if len(mes_sel) > 0:
        mes_actual = max(mes_sel)
        mes_anterior = mes_actual - 1 if mes_actual > 1 else 12
        v_act = ventas[ventas["mes"] == mes_actual]["total"].sum()
        v_ant = ventas[ventas["mes"] == mes_anterior]["total"].sum()
        cambio_mes = ((v_act - v_ant) / v_ant * 100) if v_ant > 0 else 0
    else:
        cambio_mes = 0

    ventas_por_dia = (
        ventas_f.groupby(ventas_f["fecha"].dt.date)["total"]
        .sum().sort_index()
    )
    if len(ventas_por_dia) >= 2:
        v_ult = ventas_por_dia.iloc[-1]
        v_pen = ventas_por_dia.iloc[-2]
        cambio_dia = ((v_ult - v_pen) / v_pen * 100) if v_pen > 0 else 0
    else:
        v_ult = ventas_por_dia.iloc[-1] if len(ventas_por_dia) > 0 else 0
        cambio_dia = 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 Total Ventas", f"${total_ventas:,.0f}", f"{cambio_mes:+.1f}% vs mes ant.")
    c2.metric("🧾 Transacciones", f"{num_transacciones:,}")
    c3.metric("🎯 Ticket Promedio", f"${ticket_promedio:,.0f}")
    c4.metric("📅 Último día", f"${v_ult:,.0f}", f"{cambio_dia:+.1f}% vs día ant.")

    # Ventas por mes
    st.markdown("## 📈 Ventas por Mes")
    ventas_mes = ventas_f.groupby("mes")["total"].sum().reset_index()
    ventas_mes["mes_nombre"] = ventas_mes["mes"].map(meses)
    fig_mes = px.bar(
        ventas_mes, x="mes_nombre", y="total", text="total",
        color="total", color_continuous_scale="Blues",
        labels={"mes_nombre": "Mes", "total": "Ventas (COP)"}
    )
    fig_mes.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
    fig_mes.update_layout(showlegend=False, coloraxis_showscale=False)
    st.plotly_chart(fig_mes, use_container_width=True)

    # Top productos
    st.markdown("## 🏆 Top Productos")
    top = (
        detalle_f.groupby("nombre")["subtotal"]
        .sum().sort_values(ascending=False).head(10).reset_index()
    )
    fig_top = px.bar(
        top, x="subtotal", y="nombre", orientation="h", text="subtotal",
        color="subtotal", color_continuous_scale="Greens",
        labels={"subtotal": "Ingresos (COP)", "nombre": "Producto"}
    )
    fig_top.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
    fig_top.update_layout(
        yaxis=dict(autorange="reversed"),
        showlegend=False, coloraxis_showscale=False
    )
    st.plotly_chart(fig_top, use_container_width=True)

    # Acumulado
    st.markdown("## 📉 Acumulado de Ventas")
    acum = ventas_por_dia.cumsum().reset_index()
    acum.columns = ["fecha", "acumulado"]
    fig_acum = px.area(
        acum, x="fecha", y="acumulado",
        labels={"fecha": "Fecha", "acumulado": "Ventas Acumuladas (COP)"}
    )
    fig_acum.update_traces(line_color="#2E86C1", fillcolor="rgba(46,134,193,0.3)")
    st.plotly_chart(fig_acum, use_container_width=True)

    # Día de la semana
    st.markdown("## 📅 ¿Qué día se vende más?")
    ventas_f["dia_semana"] = ventas_f["fecha"].dt.day_name()
    dias_es = {
        "Monday": "Lunes", "Tuesday": "Martes", "Wednesday": "Miércoles",
        "Thursday": "Jueves", "Friday": "Viernes",
        "Saturday": "Sábado", "Sunday": "Domingo"
    }
    ventas_f["dia_semana_es"] = ventas_f["dia_semana"].map(dias_es)
    orden = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    ventas_dia_sem = (
        ventas_f.groupby("dia_semana_es")["total"]
        .sum().reindex(orden).reset_index()
    )
    fig_dia = px.bar(
        ventas_dia_sem, x="dia_semana_es", y="total", text="total",
        color="total", color_continuous_scale="Purples",
        labels={"dia_semana_es": "Día", "total": "Ventas (COP)"}
    )
    fig_dia.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
    fig_dia.update_layout(showlegend=False, coloraxis_showscale=False)
    st.plotly_chart(fig_dia, use_container_width=True)

    with st.expander("🔍 Ver detalle de ventas"):
        st.dataframe(
            ventas_f.sort_values("fecha", ascending=False)[
                ["venta_id", "fecha", "mes", "cliente_id", "total"]
            ],
            use_container_width=True, hide_index=True
        )

# ============================================================
# SECCIÓN: INVENTARIO
# ============================================================
elif opcion == "📦 Inventario":

    st.sidebar.subheader("🔎 Filtros de Inventario")

    categorias = ["Todas"] + sorted(productos["categoria"].unique().tolist())
    cat_inv = st.sidebar.selectbox("Categoría", categorias, key="cat_inv")

    estado_sel = st.sidebar.multiselect(
        "Estado de stock",
        ["🔴 Crítico", "🟡 Bajo", "🟢 OK"],
        default=["🔴 Crítico", "🟡 Bajo", "🟢 OK"]
    )

    # Merge inventario con productos
    inv = inventario.merge(
        productos[["producto_id", "nombre", "categoria", "precio_compra", "precio_venta"]],
        on="producto_id"
    )
    inv["estado"] = inv.apply(
        lambda r: "🔴 Crítico" if r["stock_actual"] <= r["stock_minimo"]
        else ("🟡 Bajo" if r["stock_actual"] <= r["stock_minimo"] * 1.5 else "🟢 OK"),
        axis=1
    )
    inv["valor_inventario"] = inv["stock_actual"] * inv["precio_compra"]

    if cat_inv != "Todas":
        inv = inv[inv["categoria"] == cat_inv]
    inv = inv[inv["estado"].isin(estado_sel)]

    # KPIs inventario
    st.markdown("## 📊 Indicadores de Inventario")
    total_productos = len(inv)
    total_unidades = inv["stock_actual"].sum()
    valor_total = inv["valor_inventario"].sum()
    criticos = len(inv[inv["estado"] == "🔴 Crítico"])
    bajos = len(inv[inv["estado"] == "🟡 Bajo"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📦 Productos", f"{total_productos}")
    c2.metric("🔢 Unidades en stock", f"{total_unidades:,}")
    c3.metric("💵 Valor inventario", f"${valor_total:,.0f}")
    c4.metric("⚠️ Alertas", f"{criticos} críticos / {bajos} bajos")

    # Alertas de stock
    st.markdown("## ⚠️ Alertas de Stock")
    alertas = inv[inv["estado"] != "🟢 OK"].sort_values("stock_actual")
    if len(alertas) > 0:
        st.dataframe(
            alertas[[
                "nombre", "categoria", "stock_actual",
                "stock_minimo", "estado", "ultima_actualizacion"
            ]],
            use_container_width=True, hide_index=True
        )
    else:
        st.success("✅ Todos los productos tienen stock suficiente.")

    # Stock por producto
    st.markdown("## 📊 Stock Actual vs Mínimo")
    fig_stock = px.bar(
        inv.sort_values("stock_actual"),
        x="stock_actual", y="nombre", orientation="h",
        color="estado", text="stock_actual",
        labels={"stock_actual": "Unidades", "nombre": "Producto", "estado": "Estado"},
        color_discrete_map={
            "🔴 Crítico": "#E74C3C",
            "🟡 Bajo": "#F39C12",
            "🟢 OK": "#27AE60"
        }
    )
    fig_stock.update_traces(textposition="outside")
    fig_stock.update_layout(yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig_stock, use_container_width=True)

    # Valor de inventario por categoría
    st.markdown("## 💰 Valor de Inventario por Categoría")
    val_cat = (
        inv.groupby("categoria")["valor_inventario"]
        .sum().reset_index().sort_values("valor_inventario", ascending=False)
    )
    fig_val = px.pie(
        val_cat, names="categoria", values="valor_inventario", hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    fig_val.update_traces(textinfo="percent+label")
    st.plotly_chart(fig_val, use_container_width=True)

    # Rotación de inventario
    st.markdown("## 🔄 Rotación de Inventario")
    rot = detalle.groupby("producto_id")["cantidad"].sum().reset_index()
    rot = rot.merge(inventario[["producto_id", "stock_actual"]], on="producto_id")
    rot = rot.merge(productos[["producto_id", "nombre", "categoria"]], on="producto_id")
    rot["rotacion"] = rot.apply(
        lambda r: r["cantidad"] / r["stock_actual"] if r["stock_actual"] > 0 else 0,
        axis=1
    )
    if cat_inv != "Todas":
        rot = rot[rot["categoria"] == cat_inv]
    rot = rot.sort_values("rotacion", ascending=False).head(15)

    fig_rot = px.bar(
        rot, x="rotacion", y="nombre", orientation="h", text="rotacion",
        color="rotacion", color_continuous_scale="Oranges",
        labels={"rotacion": "Índice de Rotación", "nombre": "Producto"}
    )
    fig_rot.update_traces(texttemplate="%{text:.1f}", textposition="outside")
    fig_rot.update_layout(
        yaxis=dict(autorange="reversed"),
        showlegend=False, coloraxis_showscale=False
    )
    st.plotly_chart(fig_rot, use_container_width=True)

    with st.expander("🔍 Ver tabla completa de inventario"):
        st.dataframe(
            inv[[
                "nombre", "categoria", "stock_actual", "stock_minimo",
                "precio_compra", "precio_venta", "valor_inventario",
                "estado", "ultima_actualizacion"
            ]],
            use_container_width=True, hide_index=True
        )

# ============================================================
# PIE DE PÁGINA
# ============================================================
st.markdown("---")
st.caption("Dashboard Streamlit + Plotly | Datos simulados 2026 | Tienda de barrio colombiana")