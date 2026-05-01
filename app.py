import streamlit as st
import numpy as np
import urllib.parse
from datetime import datetime
import math

# Configuración mínima
st.set_page_config(
    page_title="xG Analytics Pro",
    page_icon="⚽",
    layout="wide"
)

# Título
st.title("⚽ xG Analytics Pro")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("ℹ️ Información")
    st.info("""
    **Metodología:**
    
    1. Extrae probabilidades de cuotas
    2. Elimina margen de la casa
    3. Optimiza con distribución Poisson
    4. Calcula Goles Esperados (xG)
    
    **Asunciones:**
    - Independencia de goles
    - Distribución de Poisson
    - Cuotas basadas en probabilidad real
    """)
    
    st.markdown("---")
    st.caption(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    st.caption("🔬 v2.2.0 | Pure Python")

# Funciones matemáticas PURAS (sin scipy)
def poisson_pmf(k, lam):
    """Calcula la probabilidad de Poisson manualmente"""
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return (lam ** k) * math.exp(-lam) / math.factorial(k)

def prob_poisson_resultado(xg_local, xg_visitante, max_goles=8):
    """
    Calcula probabilidades 1X2 usando distribución de Poisson
    """
    prob_local = 0
    prob_empate = 0
    prob_visitante = 0
    
    for gl in range(max_goles):
        for gv in range(max_goles):
            prob = poisson_pmf(gl, xg_local) * poisson_pmf(gv, xg_visitante)
            if gl > gv:
                prob_local += prob
            elif gl == gv:
                prob_empate += prob
            else:
                prob_visitante += prob
    
    return prob_local, prob_empate, prob_visitante

def optimizar_xg(prob_objetivo, max_iter=1000, paso=0.01):
    """
    Encuentra los xG que mejor se ajustan a las probabilidades objetivo
    usando grid search (alternativa a scipy.optimize)
    """
    mejor_error = float('inf')
    mejor_xg = (1.2, 1.2)
    
    # Grid search en espacio de xG
    for xg_l in np.arange(0.1, 5.0, paso):
        for xg_v in np.arange(0.1, 5.0, paso):
            pl, pe, pv = prob_poisson_resultado(xg_l, xg_v)
            
            # Error cuadrático
            error = ((pl - prob_objetivo[0])**2 + 
                    (pe - prob_objetivo[1])**2 + 
                    (pv - prob_objetivo[2])**2)
            
            if error < mejor_error:
                mejor_error = error
                mejor_xg = (xg_l, xg_v)
    
    return round(mejor_xg[0], 3), round(mejor_xg[1], 3)

def xg_desde_cuotas(cuota_local, cuota_empate, cuota_visitante):
    """
    Calcula xG implícitos desde cuotas 1X2
    """
    try:
        # Quitar margen de la casa
        p_l = 1 / cuota_local
        p_e = 1 / cuota_empate
        p_v = 1 / cuota_visitante
        
        margen = p_l + p_e + p_v
        
        if margen <= 0:
            return 0.0, 0.0
        
        # Probabilidades reales (sin margen)
        prob_real_local = p_l / margen
        prob_real_empate = p_e / margen
        prob_real_visitante = p_v / margen
        
        prob_objetivo = [prob_real_local, prob_real_empate, prob_real_visitante]
        
        # Optimizar para encontrar xG
        xg_l, xg_v = optimizar_xg(prob_objetivo)
        
        return xg_l, xg_v
    
    except Exception as e:
        st.error(f"Error en cálculo: {e}")
        return 0.0, 0.0

# Interfaz principal
st.header("📊 Configuración del Partido")
st.write("Introduce las cuotas del mercado 1X2 para calcular los xG implícitos:")

# Inputs
col1, col2, col3 = st.columns(3)

with col1:
    cuota_local = st.number_input(
        "Cuota Local (1)",
        min_value=1.01,
        max_value=100.0,
        value=2.10,
        step=0.01,
        key="local"
    )

with col2:
    cuota_empate = st.number_input(
        "Cuota Empate (X)",
        min_value=1.01,
        max_value=100.0,
        value=3.40,
        step=0.01,
        key="empate"
    )

with col3:
    cuota_visitante = st.number_input(
        "Cuota Visitante (2)",
        min_value=1.01,
        max_value=100.0,
        value=3.60,
        step=0.01,
        key="visitante"
    )

# Mostrar información de probabilidades
col_p1, col_p2, col_p3 = st.columns(3)
with col_p1:
    st.caption(f"Probabilidad implícita Local: {round((1/cuota_local)*100, 1)}%")
with col_p2:
    st.caption(f"Probabilidad implícita Empate: {round((1/cuota_empate)*100, 1)}%")
with col_p3:
    st.caption(f"Probabilidad implícita Visitante: {round((1/cuota_visitante)*100, 1)}%")

st.markdown("---")

# Botón de calcular
if st.button("🔍 Calcular xG Implícito", type="primary", use_container_width=True):
    with st.spinner("🔄 Optimizando modelo... Esto puede tomar unos segundos..."):
        # Calcular xG
        xg_l, xg_v = xg_desde_cuotas(cuota_local, cuota_empate, cuota_visitante)
        
        if xg_l > 0 or xg_v > 0:
            st.success("✅ Análisis completado exitosamente")
            
            st.markdown("---")
            st.header("🏆 Resultados xG")
            
            # Métricas principales
            met_col1, met_col2, met_col3 = st.columns(3)
            
            with met_col1:
                st.metric(
                    label="xG Local",
                    value=f"{xg_l:.3f}",
                    delta=None
                )
            
            with met_col2:
                st.metric(
                    label="xG Total Partido",
                    value=f"{xg_l + xg_v:.3f}"
                )
            
            with met_col3:
                st.metric(
                    label="xG Visitante",
                    value=f"{xg_v:.3f}",
                    delta=None
                )
            
            # Detalles adicionales
            st.markdown("---")
            
            det_col1, det_col2 = st.columns(2)
            
            with det_col1:
                st.subheader("📈 Análisis del Partido")
                st.write(f"**Diferencia xG:** {abs(xg_l - xg_v):.3f}")
                
                if xg_l > xg_v + 0.3:
                    st.write("**Favorito claro:** 🏠 Local")
                elif xg_v > xg_l + 0.3:
                    st.write("**Favorito claro:** 🚀 Visitante")
                elif xg_l > xg_v:
                    st.write("**Ligero favorito:** 🏠 Local")
                elif xg_v > xg_l:
                    st.write("**Ligero favorito:** 🚀 Visitante")
                else:
                    st.write("**Partido:** ⚖️ Muy equilibrado")
            
            with det_col2:
                st.subheader("🎯 Cuotas Analizadas")
                st.write(f"**Local (1):** {cuota_local}")
                st.write(f"**Empate (X):** {cuota_empate}")
                st.write(f"**Visitante (2):** {cuota_visitante}")
            
            # Probabilidades calculadas
            prob_l, prob_e, prob_v = prob_poisson_resultado(xg_l, xg_v)
            
            st.markdown("---")
            st.subheader("📊 Probabilidades según Poisson")
            
            prob_col1, prob_col2, prob_col3 = st.columns(3)
            with prob_col1:
                st.metric("Victoria Local", f"{prob_l*100:.1f}%")
            with prob_col2:
                st.metric("Empate", f"{prob_e*100:.1f}%")
            with prob_col3:
                st.metric("Victoria Visit.", f"{prob_v*100:.1f}%")
            
            # Over/Under
            st.subheader("🎲 Probabilidades Over/Under")
            
            prob_over_15 = prob_over_25 = prob_over_35 = 0
            
            for gl in range(8):
                for gv in range(8):
                    prob = poisson_pmf(gl, xg_l) * poisson_pmf(gv, xg_v)
                    total = gl + gv
                    if total > 1.5:
                        prob_over_15 += prob
                    if total > 2.5:
                        prob_over_25 += prob
                    if total > 3.5:
                        prob_over_35 += prob
            
            ou_col1, ou_col2, ou_col3 = st.columns(3)
            with ou_col1:
                st.metric("Over 1.5 goles", f"{prob_over_15*100:.1f}%")
            with ou_col2:
                st.metric("Over 2.5 goles", f"{prob_over_25*100:.1f}%")
            with ou_col3:
                st.metric("Over 3.5 goles", f"{prob_over_35*100:.1f}%")
            
            # Compartir
            st.markdown("---")
            st.subheader("📤 Compartir Resultados")
            
            mensaje = (
                f"⚽ Análisis xG Pro\n\n"
                f"🏠 Local: {xg_l:.3f} xG\n"
                f"🚀 Visitante: {xg_v:.3f} xG\n"
                f"📊 Total: {xg_l + xg_v:.3f} xG\n\n"
                f"📈 Cuotas: {cuota_local} | {cuota_empate} | {cuota_visitante}\n"
                f"🔬 #futbol #xg #analytics"
            )
            
            texto_url = urllib.parse.quote(mensaje)
            
            share_col1, share_col2 = st.columns(2)
            with share_col1:
                st.link_button(
                    "🟢 WhatsApp",
                    f"https://api.whatsapp.com/send?text={texto_url}",
                    use_container_width=True
                )
            with share_col2:
                st.link_button(
                    "🐦 X (Twitter)",
                    f"https://twitter.com/intent/tweet?text={texto_url}",
                    use_container_width=True
                )
            
            st.text_area("📋 Copiar mensaje:", value=mensaje, height=150)
        
        else:
            st.error("❌ No se pudieron calcular los xG. Verifica las cuotas ingresadas.")
            st.info("💡 Las cuotas deben ser mayores a 1.01")

st.markdown("---")
st.caption("⚽ xG Analytics Pro | Pure Python + Poisson | v2.2.0 | © 2024")