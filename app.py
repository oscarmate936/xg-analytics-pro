import streamlit as st
import math
from scipy.optimize import minimize
from scipy.stats import poisson
import urllib.parse

# --- LÓGICA MATEMÁTICA ---
def xg_desde_cuotas(cuota_local, cuota_empate, cuota_visitante):
    # Paso 1: Quitar margen de la casa
    p_l = 1 / cuota_local
    p_e = 1 / cuota_empate
    p_v = 1 / cuota_visitante
    margen = p_l + p_e + p_v
    prob_objetivo = [p_l/margen, p_e/margen, p_v/margen]

    # Paso 2: Función que calcula 1X2 dado un xG
    def probs_poisson(xg):
        xg_l, xg_v = xg
        pl = pe = pv = 0
        for gl in range(8):
            for gv in range(8):
                prob = poisson.pmf(gl, xg_l) * poisson.pmf(gv, xg_v)
                if gl > gv: pl += prob
                elif gl == gv: pe += prob
                else: pv += prob
        return pl, pe, pv

    # Paso 3: Buscar xG que minimice error vs probs reales
    def error(xg):
        pl, pe, pv = probs_poisson(xg)
        return (pl-prob_objetivo[0])**2 + (pe-prob_objetivo[1])**2 + (pv-prob_objetivo[2])**2

    resultado = minimize(error, [1.2, 1.2], bounds=[(0.05, 5.0), (0.05, 5.0)], method='L-BFGS-B')
    xg_l, xg_v = resultado.x
    return round(xg_l, 3), round(xg_v, 3)

# --- INTERFAZ DE USUARIO (STREAMLIT) ---
st.set_page_config(page_title="xG Analytics Pro", page_icon="⚽", layout="centered")

st.title("⚽ xG Analytics Pro")
st.markdown("""
Esta herramienta utiliza un modelo basado en la **distribución de Poisson** para realizar una ingeniería inversa de las cuotas de las casas de apuestas y determinar los **Goles Esperados (xG)** implícitos.
""")

st.divider()

# Configuración de entrada de datos
st.subheader("Configuración del Encuentro")
col1, col2, col3 = st.columns(3)

with col1:
    cuota_local = st.number_input("Cuota Local (1)", min_value=1.01, value=2.10, step=0.01, help="Cuota ofrecida para la victoria local.")
with col2:
    cuota_empate = st.number_input("Cuota Empate (X)", min_value=1.01, value=3.40, step=0.01, help="Cuota ofrecida para el empate.")
with col3:
    cuota_visitante = st.number_input("Cuota Visitante (2)", min_value=1.01, value=3.60, step=0.01, help="Cuota ofrecida para la victoria visitante.")

# Botón principal de ejecución
if st.button("📊 Calcular xG Implícito", use_container_width=True, type="primary"):
    with st.spinner("Optimizando modelo de Poisson..."):
        try:
            xg_l, xg_v = xg_desde_cuotas(cuota_local, cuota_empate, cuota_visitante)
            
            st.success("Análisis realizado correctamente")
            
            # Visualización de resultados principales
            res_col1, res_col2 = st.columns(2)
            with res_col1:
                st.metric("xG Local", f"{xg_l}")
            with res_col2:
                st.metric("xG Visitante", f"{xg_v}")
            
            st.divider()
            
            # Sección para compartir
            st.subheader("📤 Compartir Análisis")
            
            # Formateo del mensaje para redes sociales
            mensaje_share = (
                f"⚽ *Análisis de xG Pro*\n\n"
                f"🏠 Local: {xg_l} xG\n"
                f"🚀 Visitante: {xg_v} xG\n\n"
                f"Basado en cuotas: {cuota_local} | {cuota_empate} | {cuota_visitante}"
            )
            
            texto_url = urllib.parse.quote(mensaje_share)
            url_wa = f"https://api.whatsapp.com/send?text={texto_url}"
            url_tw = f"https://twitter.com/intent/tweet?text={texto_url}"
            
            # Botones de compartir (uso de componentes nativos para evitar errores de DOM)
            share_col1, share_col2 = st.columns(2)
            with share_col1:
                st.link_button("🟢 WhatsApp", url_wa, use_container_width=True)
            with share_col2:
                st.link_button("🐦 X (Twitter)", url_tw, use_container_width=True)
            
            # Área de texto para copiar manualmente
            st.text_area("Texto para copiar:", value=mensaje_share, height=100)
            
        except Exception as e:
            st.error(f"Hubo un problema con el cálculo: {e}")

st.sidebar.info("Este modelo asume independencia entre los goles marcados por cada equipo siguiendo una distribución de Poisson.")
