import os
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from supabase import create_client

st.set_page_config(page_title="Control de Proyecto", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

# ---------- Config ----------
def secret(name, default=None):
    try:
        return st.secrets[name]
    except Exception:
        return os.getenv(name, default)

SUPABASE_URL = secret("SUPABASE_URL")
SUPABASE_SERVICE_KEY = secret("SUPABASE_SERVICE_KEY")
APP_PASSWORD = secret("APP_PASSWORD")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    st.error("La aplicación está instalada, pero todavía no tiene configuradas las credenciales de Supabase.")
    st.code('SUPABASE_URL = "https://TU-PROYECTO.supabase.co"\nSUPABASE_SERVICE_KEY = "TU_SERVICE_ROLE_KEY"\nAPP_PASSWORD = "TU_CLAVE"')
    st.info("En el paquete encontrarás SUPABASE_SETUP.md con el procedimiento exacto para conectarla.")
    st.stop()

@st.cache_resource
def get_client():
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

sb = get_client()

# ---------- Simple app gate ----------
if APP_PASSWORD:
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if not st.session_state.authenticated:
        st.title("🔐 Control de Proyecto")
        st.caption("Acceso privado")
        pwd = st.text_input("Contraseña", type="password")
        if st.button("Entrar", type="primary"):
            if pwd == APP_PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta.")
        st.stop()

# ---------- DB helpers ----------
def select_table(table, columns="*", order="fecha.asc", limit=5000):
    res = sb.table(table).select(columns).order(order.split('.')[0], desc=order.endswith('.desc')).limit(limit).execute()
    return pd.DataFrame(res.data or [])

def daily_df():
    df = select_table("registros_diarios")
    if not df.empty:
        df["fecha"] = pd.to_datetime(df["fecha"])
    return df

def activities_df():
    df = select_table("actividades", order="fecha.asc")
    if not df.empty:
        df["fecha"] = pd.to_datetime(df["fecha"])
    return df

def upsert_daily(payload):
    sb.table("registros_diarios").upsert(payload, on_conflict="fecha").execute()

def add_activity(payload):
    sb.table("actividades").insert(payload).execute()

def delete_day(d):
    sb.table("actividades").delete().eq("fecha", d).execute()
    sb.table("registros_diarios").delete().eq("fecha", d).execute()

def money(v):
    return f"${float(v or 0):,.2f}"

# ---------- Style ----------
st.markdown("""
<style>
.block-container {padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1450px;}
[data-testid="stMetricValue"] {font-size: 1.7rem;}
.small-muted {color:#6b7280;font-size:.9rem;}
.card {padding:1rem;border:1px solid #e5e7eb;border-radius:12px;background:#fff;}
</style>
""", unsafe_allow_html=True)

# ---------- Sidebar ----------
st.sidebar.title("📊 Control de Proyecto")
st.sidebar.caption("Captura rápida · cálculos · cronograma · dashboard")
page = st.sidebar.radio("Ir a", ["Inicio", "⚡ Captura rápida", "🗓️ Cronograma", "📈 Dashboard", "🖼️ Mi pizarra", "🧾 Datos"], label_visibility="collapsed")
if APP_PASSWORD and st.sidebar.button("Cerrar sesión"):
    st.session_state.authenticated = False
    st.rerun()

D = daily_df()
A = activities_df()

# ---------- Inicio ----------
if page == "Inicio":
    st.title("Control de Proyecto")
    st.write("Una sola captura diaria alimenta automáticamente costos, indicadores, cronograma y riesgos.")
    if D.empty:
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Días registrados", 0)
        c2.metric("Actividades", 0)
        c3.metric("Costo acumulado", "$0.00")
        c4.metric("Avance", "0%")
        st.info("Empieza en **⚡ Captura rápida**. El sistema calculará todo automáticamente.")
    else:
        last = D.iloc[-1]
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Último registro", last["fecha"].strftime("%d/%m/%Y"))
        c2.metric("Días registrados", len(D))
        c3.metric("Costo acumulado", money(A[["mano_obra","insumos","viaticos","depreciacion","gastos_admin"]].sum().sum()) if not A.empty else "$0.00")
        c4.metric("Riesgos altos", int(last.get("riesgo_alto",0)))
        st.subheader("Resumen del último día")
        cols = st.columns(6)
        cols[0].metric("Retrasos", f"{float(last.retrasos_horas):.1f} h")
        cols[1].metric("Depreciación", money(last.depreciacion))
        cols[2].metric("Sueldo promedio", money(last.sueldo_promedio))
        cols[3].metric("Altas", int(last.altas))
        cols[4].metric("Bajas", int(last.bajas))
        cols[5].metric("Cambios", f"{float(last.cambios):.1f}")
    st.divider()
    st.markdown("### Flujo de trabajo")
    st.markdown("**1. Captura** → **2. Guardar** → **3. Cálculo automático** → **4. Dashboard** → **5. Histórico en la nube**")
    st.caption("La información queda en Supabase; tu laptop no necesita permanecer encendida.")

# ---------- Captura rápida ----------
elif page == "⚡ Captura rápida":
    st.title("⚡ Captura rápida")
    st.caption("Una pantalla para registrar el día. Si la fecha ya existe, se actualiza.")
    selected = st.date_input("Fecha", date.today())
    existing = D[D["fecha"].dt.date == selected] if not D.empty else pd.DataFrame()
    row = existing.iloc[0] if not existing.empty else None
    if row is not None:
        st.warning("Ya existe información para esta fecha. Guardar reemplazará los indicadores de ese día.")

    with st.form("quick_capture"):
        st.markdown("### Indicadores")
        c = st.columns(6)
        retrasos = c[0].number_input("Retrasos (h)", min_value=0.0, value=float(row.retrasos_horas) if row is not None else 0.0, step=0.5)
        depreciacion = c[1].number_input("Depreciación ($)", min_value=0.0, value=float(row.depreciacion) if row is not None else 0.0, step=50.0)
        sueldo = c[2].number_input("Sueldo promedio ($)", min_value=0.0, value=float(row.sueldo_promedio) if row is not None else 0.0, step=100.0)
        altas = c[3].number_input("Altas", min_value=0, value=int(row.altas) if row is not None else 0)
        bajas = c[4].number_input("Bajas", min_value=0, value=int(row.bajas) if row is not None else 0)
        cambios = c[5].number_input("Cambios", value=float(row.cambios) if row is not None else 0.0, step=1.0)
        st.markdown("### Matriz de riesgos")
        r = st.columns(3)
        rb = r[0].number_input("🟢 Riesgos bajos", min_value=0, value=int(row.riesgo_bajo) if row is not None else 0)
        rm = r[1].number_input("🟡 Riesgos medios", min_value=0, value=int(row.riesgo_medio) if row is not None else 0)
        ra = r[2].number_input("🔴 Riesgos altos", min_value=0, value=int(row.riesgo_alto) if row is not None else 0)
        obs = st.text_area("Observaciones", value=str(row.observaciones) if row is not None else "")
        st.markdown("### Actividad del día (opcional)")
        a = st.columns(4)
        codigo = a[0].text_input("Código", placeholder="A")
        desc = a[1].text_input("Descripción", placeholder="Entrevista de usuario")
        resp = a[2].text_input("Responsable", placeholder="JP")
        estado = a[3].selectbox("Estado", ["Planeado","En curso","Completado","Retrasado","Cancelado"])
        b = st.columns(5)
        dias = b[0].number_input("Días", min_value=0.0, step=0.5)
        horas = b[1].number_input("Horas", min_value=0.0, step=0.5)
        mo = b[2].number_input("Mano de obra ($)", min_value=0.0, step=100.0)
        ins = b[3].number_input("Insumos ($)", min_value=0.0, step=100.0)
        via = b[4].number_input("Viáticos ($)", min_value=0.0, step=100.0)
        c2 = st.columns(4)
        dep = c2[0].number_input("Dep. actividad ($)", min_value=0.0, step=50.0)
        adm = c2[1].number_input("Gastos admin ($)", min_value=0.0, step=50.0)
        ent = c2[2].text_input("Entregable")
        av = c2[3].slider("Avance (%)", 0, 100, 0, 5)
        actobs = st.text_input("Observación de actividad")
        save = st.form_submit_button("💾 Guardar todo", type="primary", use_container_width=True)

    if save:
        try:
            upsert_daily({
                "fecha": selected.isoformat(), "retrasos_horas": retrasos, "depreciacion": depreciacion,
                "sueldo_promedio": sueldo, "altas": altas, "bajas": bajas, "cambios": cambios,
                "riesgo_bajo": rb, "riesgo_medio": rm, "riesgo_alto": ra, "observaciones": obs
            })
            if any([codigo.strip(), desc.strip(), resp.strip(), mo, ins, via, dep, adm, ent.strip()]):
                total = mo + ins + via + dep + adm
                add_activity({
                    "fecha": selected.isoformat(), "codigo": codigo, "descripcion": desc, "responsable": resp,
                    "participante": "", "dias": dias, "horas": horas, "mano_obra": mo, "insumos": ins,
                    "viaticos": via, "depreciacion": dep, "gastos_admin": adm, "entregable": ent,
                    "observaciones": actobs, "estado": estado, "avance": av, "costo_total": total
                })
            st.success("✓ Guardado. Todos los cálculos y vistas se actualizaron.")
            st.rerun()
        except Exception as e:
            st.error(f"No se pudo guardar: {e}")

# ---------- Cronograma ----------
elif page == "🗓️ Cronograma":
    st.title("🗓️ Cronograma visual")
    if A.empty:
        st.info("Registra actividades para construir el cronograma.")
    else:
        work = A.copy()
        work["inicio"] = work["fecha"].dt.date
        work["duracion"] = work["dias"].clip(lower=0.1)
        work["fin"] = work.apply(lambda x: x["inicio"] + timedelta(days=max(int(x["duracion"])-1,0)), axis=1)
        work["label"] = work["codigo"].fillna("") + " · " + work["descripcion"].fillna("")
        fig = px.timeline(work, x_start="inicio", x_end="fin", y="label", color="estado", hover_data=["responsable","horas","avance","costo_total"])
        fig.update_yaxes(autorange="reversed")
        fig.update_layout(height=max(420, 55*len(work)), margin=dict(l=20,r=20,t=30,b=20), xaxis_title="Fecha", yaxis_title="Actividad")
        st.plotly_chart(fig, use_container_width=True)
        st.subheader("Tabla de actividades")
        show = work[["fecha","codigo","descripcion","responsable","dias","horas","avance","costo_total","estado","entregable"]].copy()
        show["fecha"] = show["fecha"].dt.strftime("%Y-%m-%d")
        show["avance"] = show["avance"].map(lambda x: f"{x:.0f}%")
        show["costo_total"] = show["costo_total"].map(money)
        st.dataframe(show, use_container_width=True, hide_index=True)

# ---------- Dashboard ----------
elif page == "📈 Dashboard":
    st.title("📈 Dashboard ejecutivo")
    if D.empty:
        st.info("Todavía no hay datos.")
    else:
        last = D.iloc[-1]
        prev = D.iloc[-2] if len(D)>1 else None
        c=st.columns(6)
        c[0].metric("Retrasos", f"{float(last.retrasos_horas):.1f} h", None if prev is None else f"{float(last.retrasos_horas-prev.retrasos_horas):+.1f}")
        c[1].metric("Depreciación", money(last.depreciacion))
        c[2].metric("Sueldo promedio", money(last.sueldo_promedio))
        c[3].metric("Altas / bajas", f"{int(last.altas)} / {int(last.bajas)}")
        c[4].metric("Riesgo alto", int(last.riesgo_alto))
        avg = float(A.avance.mean()) if not A.empty and "avance" in A else 0
        c[5].metric("Avance promedio", f"{avg:.0f}%")
        st.divider()
        l,r = st.columns(2)
        with l:
            st.subheader("Personal")
            fig=go.Figure()
            fig.add_bar(x=D.fecha,y=D.altas,name="Altas")
            fig.add_bar(x=D.fecha,y=D.bajas,name="Bajas")
            fig.add_scatter(x=D.fecha,y=D.cambios,name="Cambios",mode="lines+markers",yaxis="y2")
            fig.update_layout(barmode="group",height=350,yaxis_title="Personas",yaxis2=dict(title="Cambios",overlaying="y",side="right"),legend=dict(orientation="h"))
            st.plotly_chart(fig,use_container_width=True)
        with r:
            st.subheader("Matriz de riesgos")
            risk=pd.DataFrame({"Nivel":["Bajo","Medio","Alto"],"Cantidad":[last.riesgo_bajo,last.riesgo_medio,last.riesgo_alto]})
            fig=px.bar(risk,x="Nivel",y="Cantidad",text="Cantidad",height=350)
            fig.update_traces(textposition="outside")
            st.plotly_chart(fig,use_container_width=True)
        st.subheader("Evolución")
        vars_sel=st.multiselect("Indicadores",["retrasos_horas","depreciacion","sueldo_promedio","cambios"],default=["retrasos_horas","depreciacion"])
        labels={"retrasos_horas":"Retrasos (h)","depreciacion":"Depreciación ($)","sueldo_promedio":"Sueldo promedio ($)","cambios":"Cambios"}
        if vars_sel:
            long=D[["fecha"]+vars_sel].melt("fecha",var_name="variable",value_name="valor")
            long["variable"]=long["variable"].map(labels)
            fig=px.line(long,x="fecha",y="valor",color="variable",markers=True,height=400)
            st.plotly_chart(fig,use_container_width=True)
        if not A.empty:
            total=A[["mano_obra","insumos","viaticos","depreciacion","gastos_admin"]].sum().sum()
            st.metric("💰 Costo total acumulado",money(total))

# ---------- Pizarra ----------
elif page == "🖼️ Mi pizarra":
    st.title("🖼️ Mi pizarra original")
    st.caption("Conservamos tu referencia para que el sistema digital mantenga la lógica de trabajo de tu pizarra.")
    img=Path(__file__).parent/"referencia"/"pizarra_referencia.jpg"
    if img.exists(): st.image(str(img), caption="Pizarra proporcionada como referencia", use_container_width=True)
    st.divider()
    st.subheader("Cómo se traduce al sistema")
    st.markdown("**Tabla de actividades** → Cronograma · **Costos** → Costo acumulado · **Retrasos** → Indicadores · **Riesgos** → Matriz · **Semanas** → Evolución diaria")

# ---------- Datos ----------
else:
    st.title("🧾 Datos e histórico")
    D=daily_df(); A=activities_df()
    if not D.empty:
        st.subheader("Indicadores diarios")
        st.dataframe(D,use_container_width=True,hide_index=True)
        st.download_button("⬇️ Descargar indicadores CSV",D.to_csv(index=False).encode("utf-8-sig"),"indicadores_diarios.csv","text/csv")
    if not A.empty:
        st.subheader("Actividades")
        st.dataframe(A,use_container_width=True,hide_index=True)
        st.download_button("⬇️ Descargar actividades CSV",A.to_csv(index=False).encode("utf-8-sig"),"actividades.csv","text/csv")
    st.divider()
    st.subheader("Administración")
    d=st.date_input("Eliminar un día",date.today())
    if st.button("🗑️ Eliminar día",type="secondary"):
        if not D.empty and not D[D.fecha.dt.date.eq(d)].empty:
            delete_day(d.isoformat()); st.success("Día eliminado."); st.rerun()
        else: st.warning("No existe información para esa fecha.")
