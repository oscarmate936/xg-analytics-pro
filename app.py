import streamlit as st
from scipy.optimize import minimize
from scipy.stats import poisson
import urllib.parse
from datetime import datetime

# Configuración de página - mínimo necesario
st.set_page_config(
    page_title="xG Analytics Pro",
    page_icon="⚽",
    layout="wide"
)

# Título simple
st.title("⚽ xG Analytics Pro")
st.markdown("---")

# Sidebar simple
with st.sidebar:
    st.header("ℹ️ Información")
    st.info("""
    **¿Cómo funciona?**
    
    1. Extrae probabilidades de las cuotas
    2. Elimina el margen de la casa
    3. Optimiza con Poisson para encontrar xG
    4. Calcula goles esperados
    
    **Asunciones:**
    - Goles siguen distribución Poisson
    - Independencia entre equipos
    """)
    
    st.markdown("---")
    st.caption(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    st.caption("🔬 Modelo Poisson v2.1.4")

# Función matemática (sin cambios)
@st.cache_data
def calcular_xg(cuota_local, cuota_empate, cuota_visitante):
    """Calcula xG implícitos desde cuotas 1X2"""
    try:
        # Quitar margen
        p_l = 1 / cuota_local
        p_e = 1 / cuota_empate
        p_v = 1 / cuota_visitante
        margen = p_l + p_e + p_v
        
        if margen == 0:
            return None, None
        
        prob_objetivo = [p_l/margen, p_e/margen, p_v/margen]

        # Probabilidades Poisson
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

        # Error a minimizar
        def error(xg):
            pl, pe, pv = probs_poisson(xg)
            return (pl-prob_objetivo[0])**2 + (pe-prob_objetivo[1])**2 + (pv-prob_objetivo[2])**2

        # Optimización
        resultado = minimize(error, [1.2, 1.2], 
                           bounds=[(0.05, 5.0), (0.05, 5.0)], 
                           method='L-BFGS-B')
        
        xg_l, xg_v = resultado.x
        return round(xg_l, 3), round(xg_v, 3)
    
    except Exception as e:
        return None, None

# Interfaz principal - SIN HTML CUSTOM
st.header("📊 Configuración del Partido")
st.write("Introduce las cuotas del mercado 1X2:")

# Inputs en columnas
col1, col2, col3 = st.columns(3)

with col1:
    cuota_local = st.number_input(
        "Cuota Local (1)",
        min_value=1.01,
        max_value=100.0,
        value=2.10,
        step=0.01,
        help="Cuota para victoria del equipo local"
    )

with col2:
    cuota_empate = st.number_input(
        "Cuota Empate (X)",
        min_value=1.01,
        max_value=100.0,
        value=3.40,
        step=0.01,
        help="Cuota para el empate"
    )

with col3:
    cuota_visitante = st.number_input(
        "Cuota Visitante (2)",
        min_value=1.01,
        max_value=100.0,
        value=3.60,
        step=0.01,
        help="Cuota para victoria del equipo visitante"
    )

# Mostrar probabilidades implícitas
col_p1, col_p2, col_p3 = st.columns(3)
with col_p1:
    st.caption(f"Prob. Local: {round((1/cuota_local)*100, 1)}%")
with col_p2:
    st.caption(f"Prob. Empate: {round((1/cuota_empate)*100, 1)}%")
with col_p3:
    st.caption(f"Prob. Visitante: {round((1/cuota_visitante)*100, 1)}%")

st.markdown("---")

# Botón de calcular con manejo de estado
if 'calcular_presionado' not in st.session_state:
    st.session_state.calcular_presionado = False

if st.button("🔍 Calcular xG", type="primary", use_container_width=True):
    st.session_state.calcular_presionado = True

# Mostrar resultados si se ha calculado
if st.session_state.calcular_presionado:
    with st.spinner("Calculando..."):
        xg_l, xg_v = calcular_xg(cuota_local, cuota_empate, cuota_visitante)
        
        if xg_l is not None and xg_v is not None:
            st.success("✅ Análisis completado")
            
            st.markdown("---")
            st.header("🏆 Resultados xG")
            
            # Métricas principales
            met_col1, met_col2, met_col3 = st.columns(3)
            
            with met_col1:
                st.metric(
                    label="xG Local",
                    value=xg_l,
                    delta=None
                )
            
            with met_col2:
                st.metric(
                    label="Total xG",
                    value=f"{xg_l + xg_v:.3f}"
                )
            
            with met_col3:
                st.metric(
                    label="xG Visitante",
                    value=xg_v,
                    delta=None
                )
            
            # Información adicional en columnas
            info_col1, info_col2 = st.columns(2)
            
            with info_col1:
                st.write("**Detalles del análisis:**")
                st.write(f"- Diferencia xG: {abs(xg_l - xg_v):.3f}")
                if xg_l > xg_v:
                    st.write("- Favorito: 🏠 Local")
                elif xg_v > xg_l:
                    st.write("- Favorito: 🚀 Visitante")
                else:
                    st.write("- Partido: ⚖️ Equilibrado")
            
            with info_col2:
                st.write("**Cuotas analizadas:**")
                st.write(f"- Local: {cuota_local}")
                st.write(f"- Empate: {cuota_empate}")
                st.write(f"- Visitante: {cuota_visitante}")
            
            st.markdown("---")
            
            # Sección compartir
            st.subheader("📤 Compartir Resultados")
            
            mensaje = (
                f"⚽ Análisis xG Pro\n\n"
                f"🏠 Local: {xg_l} xG\n"
                f"🚀 Visitante: {xg_v} xG\n"
                f"📊 Total: {xg_l + xg_v:.3f} xG\n\n"
                f"Cuotas: {cuota_local} | {cuota_empate} | {cuota_visitante}\n\n"
                f"#futbol #xg #analytics"
            )
            
            texto_url = urllib.parse.quote(mensaje)
            
            share_col1, share_col2 = st.columns(2)
            
            with share_col1:
                st.link_button(
                    "🟢 Compartir por WhatsApp",
                    f"https://api.whatsapp.com/send?text={texto_url}",
                    use_container_width=True
                )
            
            with share_col2:
                st.link_button(
                    "🐦 Compartir en X",
                    f"https://twitter.com/intent/tweet?text={texto_url}",
                    use_container_width=True
                )
            
            # Área de texto para copiar
            st.text_area(
                "Mensaje para copiar:",
                value=mensaje,
                height=150
            )
            
            # Análisis adicional en expander
            with st.expander("📊 Ver análisis probabilístico detallado"):
                st.write("**Probabilidades 1X2 según Poisson:**")
                
                prob_l = prob_e = prob_v = 0
                for gl in range(8):
                    for gv in range(8):
                        prob = poisson.pmf(gl, xg_l) * poisson.pmf(gv, xg_v)
                        if gl > gv: prob_l += prob
                        elif gl == gv: prob_e += prob
                        else: prob_v += prob
                
                prob_col1, prob_col2, prob_col3 = st.columns(3)
                with prob_col1:
                    st.metric("Victoria Local", f"{prob_l*100:.1f}%")
                with prob_col2:
                    st.metric("Empate", f"{prob_e*100:.1f}%")
                with prob_col3:
                    st.metric("Victoria Visit.", f"{prob_v*100:.1f}%")
                
                st.write("**Probabilidades Over/Under:**")
                
                prob_o15 = prob_o25 = prob_o35 = 0
                for gl in range(8):
                    for gv in range(8):
                        prob = poisson.pmf(gl, xg_l) * poisson.pmf(gv, xg_v)
                        total = gl + gv
                        if total > 1.5: prob_o15 += prob
                        if total > 2.5: prob_o25 += prob
                        if total > 3.5: prob_o35 += prob
                
                ou_col1, ou_col2, ou_col3 = st.columns(3)
                with ou_col1:
                    st.metric("Over 1.5", f"{prob_o15*100:.1f}%")
                with ou_col2:
                    st.metric("Over 2.5", f"{prob_o25*100:.1f}%")
                with ou_col3:
                    st.metric("Over 3.5", f"{prob_o35*100:.1f}%")
        
        else:
            st.error("❌ Error al calcular. Verifica los valores ingresados.")

# Footer simple
st.markdown("---")
st.caption("⚽ xG Analytics Pro | Modelo Poisson + Optimización | v2.1.4")