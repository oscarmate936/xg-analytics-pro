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
st.markdown("Convierte las cuotas 1X2 de las casas de apuestas en **Goles Esperados (xG)** utilizando la distribución de Poisson para encontrar valor en tus análisis.")

st.divider()

# Inputs en columnas
col1, col2, col3 = st.columns(3)

with col1:
    cuota_local = st.number_input("Cuota Local (1)", min_value=1.01, value=2.00, step=0.05)
with col2:
    cuota_empate = st.number_input("Cuota Empate (X)", min_value=1.01, value=3.20, step=0.05)
with col3:
    cuota_visitante = st.number_input("Cuota Visitante (2)", min_value=1.01, value=3.50, step=0.05)

if st.button("📊 Calcular xG", use_container_width=True, type="primary"):
    with st.spinner("Calculando modelo de Poisson..."):
        xg_l, xg_v = xg_desde_cuotas(cuota_local, cuota_empate, cuota_visitante)
        
        st.success("¡Cálculo completado!")
        
        # Mostrar resultados en grande
        res_col1, res_col2 = st.columns(2)
        res_col1.metric("xG Equipo Local", f"{xg_l}")
        res_col2.metric("xG Equipo Visitante", f"{xg_v}")
        
        st.divider()
        st.subheader("🔗 Compartir Resultados")
        
        # Texto formateado para compartir
        texto_compartir = f"⚽ Análisis de Cuotas a xG:\nLocal ({cuota_local}) ➡️ {xg_l} xG\nEmpate ({cuota_empate})\nVisitante ({cuota_visitante}) ➡️ {xg_v} xG\n\nCalculado con xG Analytics Pro."
        
        # Generar URLs para los botones
        texto_codificado = urllib.parse.quote(texto_compartir)
        url_whatsapp = f"https://api.whatsapp.com/send?text={texto_codificado}"
        url_twitter = f"https://twitter.com/intent/tweet?text={texto_codificado}"
        
        # Botones de compartir usando HTML/Markdown
        st.markdown(
            f"""
            <a href="{url_whatsapp}" target="_blank">
                <button style="background-color:#25D366; color:white; border:none; padding:8px 16px; border-radius:4px; cursor:pointer;">
                    Compartir en WhatsApp
                </button>
            </a>
            <a href="{url_twitter}" target="_blank">
                <button style="background-color:#1DA1F2; color:white; border:none; padding:8px 16px; border-radius:4px; cursor:pointer; margin-left:10px;">
                    Compartir en X (Twitter)
                </button>
            </a>
            """,
            unsafe_allow_html=True
        )
        
        # Opción para copiar manualmente
        st.text_area("Copiar texto manualmente:", value=texto_compartir, height=120)
