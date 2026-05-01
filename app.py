import streamlit as st
import math
from scipy.optimize import minimize
from scipy.stats import poisson
import urllib.parse
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA (DEBE SER LA PRIMERA LLAMADA) ---
st.set_page_config(
    page_title="xG Analytics Pro | Fútbol Avanzado",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILOS CSS - VERSIÓN CORREGIDA SIN ANIMACIONES PROBLEMÁTICAS ---
st.markdown("""
<style>
    /* Estilos base - Sin animaciones que causen conflictos con el DOM */
    .main-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    
    .xg-card {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 15px 40px rgba(0,0,0,0.1);
        margin: 1rem 0;
        border: 2px solid #e0e0e0;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        border: 1px solid #d0d0d0;
    }
    
    .share-section {
        background: #f8f9fa;
        padding: 2rem;
        border-radius: 15px;
        border: 2px solid #e0e0e0;
        margin-top: 1rem;
    }
    
    .result-container {
        margin: 20px 0;
        padding: 20px;
        background: white;
        border-radius: 10px;
        border: 1px solid #ddd;
    }
    
    /* Estilos seguros para botones */
    .stButton > button {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        border: none;
        padding: 15px 30px;
        border-radius: 10px;
        font-weight: bold;
        transition: background 0.3s ease;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #2a5298 0%, #1e3c72 100%);
        box-shadow: 0 10px 20px rgba(0,0,0,0.2);
    }
    
    /* Estilos para el sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    /* Estilos para pestañas */
    .stTabs [data-baseweb="tab"] {
        font-weight: bold;
        padding: 10px 20px;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 20px;
        color: #666;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# --- INICIALIZACIÓN DE ESTADO DE SESIÓN (CRUCIAL PARA EVITAR ERRORES DOM) ---
if 'resultados_calculados' not in st.session_state:
    st.session_state.resultados_calculados = False
    st.session_state.xg_local = 0
    st.session_state.xg_visitante = 0
    st.session_state.cuota_local_guardada = 2.10
    st.session_state.cuota_empate_guardada = 3.40
    st.session_state.cuota_visitante_guardada = 3.60

# --- LÓGICA MATEMÁTICA (SIN CAMBIOS) ---
def xg_desde_cuotas(cuota_local, cuota_empate, cuota_visitante):
    """
    Calcula los xG implícitos a partir de las cuotas 1X2
    """
    # Paso 1: Quitar margen de la casa
    p_l = 1 / cuota_local
    p_e = 1 / cuota_empate
    p_v = 1 / cuota_visitante
    margen = p_l + p_e + p_v
    
    # Evitar división por cero
    if margen == 0:
        return 0, 0
    
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

    try:
        resultado = minimize(error, [1.2, 1.2], bounds=[(0.05, 5.0), (0.05, 5.0)], method='L-BFGS-B')
        xg_l, xg_v = resultado.x
        return round(xg_l, 3), round(xg_v, 3)
    except:
        return 0, 0

# --- FUNCIÓN PARA FORMATEAR MENSAJE ---
def formatear_mensaje_share(xg_l, xg_v, c_l, c_e, c_v):
    return (
        f"⚽ *Análisis xG Pro - {datetime.now().strftime('%d/%m/%Y %H:%M')}*\n\n"
        f"🏠 Local: {xg_l} xG\n"
        f"🚀 Visitante: {xg_v} xG\n"
        f"📊 Total: {xg_l + xg_v:.3f} xG\n\n"
        f"📈 Basado en cuotas:\n"
        f"1 → {c_l} | X → {c_e} | 2 → {c_v}\n\n"
        f"🔬 Modelo: Poisson + Optimización\n"
        f"#futbol #xg #analytics #apuestas"
    )

# --- HEADER PRINCIPAL ---
st.markdown("""
<div class="main-header">
    <h1 style="margin: 0; font-size: 2.5rem;">⚽ xG Analytics Pro</h1>
    <p style="font-size: 1.1rem; margin-top: 1rem; opacity: 0.9;">
        Ingeniería inversa de cuotas para revelar Goles Esperados (xG)
    </p>
</div>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### 🎯 Metodología")
    
    with st.expander("📚 ¿Cómo funciona?", expanded=True):
        st.markdown("""
        1. 📊 Extracción de probabilidades implícitas
        2. 🧮 Eliminación del margen de la casa
        3. 📈 Optimización con distribución de Poisson
        4. 🎯 Cálculo de xG por equipo
        
        **Asunciones:**
        - Goles siguen distribución de Poisson
        - Independencia entre equipos
        - Cuotas basadas en probabilidades reales
        """)
    
    st.markdown("---")
    
    st.markdown("### ⚡ Información")
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.metric("Hora", datetime.now().strftime("%H:%M"))
    with col_s2:
        st.metric("Fecha", datetime.now().strftime("%d/%m/%Y"))
    
    st.markdown("---")
    
    st.markdown("### 📊 Modelo")
    st.code("Poisson v2.1.3", language="bash")
    
    st.markdown("### 🔗 Enlaces Útiles")
    st.markdown("[📖 Documentación Streamlit](https://docs.streamlit.io)")
    st.markdown("[🎓 Teoría de xG](https://es.wikipedia.org/wiki/Goles_esperados)")
    st.markdown("[📈 Estadísticas](https://fbref.com)")

# --- CONTENIDO PRINCIPAL ---
tab1, tab2 = st.tabs(["⚙️ Calculadora", "📊 Análisis Detallado"])

with tab1:
    st.markdown("## Configuración del Partido")
    st.markdown("Introduce las cuotas del mercado 1X2")
    
    # Inputs en columns (versión simplificada para evitar conflictos)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### 🏠 Local")
        cuota_local = st.number_input(
            "Cuota victoria local",
            min_value=1.01,
            max_value=100.0,
            value=st.session_state.cuota_local_guardada,
            step=0.01,
            key="input_local"
        )
        
    with col2:
        st.markdown("#### 🤝 Empate")
        cuota_empate = st.number_input(
            "Cuota empate",
            min_value=1.01,
            max_value=100.0,
            value=st.session_state.cuota_empate_guardada,
            step=0.01,
            key="input_empate"
        )
        
    with col3:
        st.markdown("#### 🚀 Visitante")
        cuota_visitante = st.number_input(
            "Cuota victoria visitante",
            min_value=1.01,
            max_value=100.0,
            value=st.session_state.cuota_visitante_guardada,
            step=0.01,
            key="input_visitante"
        )
    
    # Mostrar probabilidades implícitas
    prob_l = (1/cuota_local)*100
    prob_e = (1/cuota_empate)*100
    prob_v = (1/cuota_visitante)*100
    
    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        st.caption(f"Probabilidad bruta: {prob_l:.1f}%")
    with col_p2:
        st.caption(f"Probabilidad bruta: {prob_e:.1f}%")
    with col_p3:
        st.caption(f"Probabilidad bruta: {prob_v:.1f}%")
    
    st.markdown("---")
    
    # Botón de cálculo
    if st.button("🔍 CALCULAR xG IMPLÍCITO", use_container_width=True, type="primary"):
        with st.spinner("🔄 Optimizando modelo de Poisson..."):
            try:
                # Guardar valores en session_state
                st.session_state.cuota_local_guardada = cuota_local
                st.session_state.cuota_empate_guardada = cuota_empate
                st.session_state.cuota_visitante_guardada = cuota_visitante
                
                # Calcular xG
                xg_l, xg_v = xg_desde_cuotas(cuota_local, cuota_empate, cuota_visitante)
                
                # Guardar resultados
                st.session_state.resultados_calculados = True
                st.session_state.xg_local = xg_l
                st.session_state.xg_visitante = xg_v
                
                st.success("✅ ¡Análisis completado exitosamente!")
                
            except Exception as e:
                st.error(f"❌ Error en el cálculo: {str(e)}")
                st.info("💡 Verifica que las cuotas sean válidas")
    
    # Mostrar resultados si existen
    if st.session_state.resultados_calculados:
        st.markdown("---")
        st.markdown("## 🏆 Resultados de xG")
        
        xg_l = st.session_state.xg_local
        xg_v = st.session_state.xg_visitante
        
        # Resultados en formato simple (evitando HTML complejo)
        res_col1, res_col2, res_col3 = st.columns([2, 1, 2])
        
        with res_col1:
            st.markdown("""
            <div class="metric-card">
                <div style="font-size: 0.9rem; color: #666;">GOLES ESPERADOS LOCAL</div>
                <div style="font-size: 2.5rem; font-weight: bold; color: #1e3c72;">{}</div>
                <div style="font-size: 0.8rem; color: #999;">xG - Expected Goals</div>
            </div>
            """.format(xg_l), unsafe_allow_html=True)
        
        with res_col2:
            st.markdown("""
            <div style="text-align: center; padding-top: 1.5rem;">
                <div style="font-size: 1.5rem;">⚡ vs ⚡</div>
            </div>
            """, unsafe_allow_html=True)
        
        with res_col3:
            st.markdown("""
            <div class="metric-card">
                <div style="font-size: 0.9rem; color: #666;">GOLES ESPERADOS VISITANTE</div>
                <div style="font-size: 2.5rem; font-weight: bold; color: #2a5298;">{}</div>
                <div style="font-size: 0.8rem; color: #999;">xG - Expected Goals</div>
            </div>
            """.format(xg_v), unsafe_allow_html=True)
        
        # Métricas adicionales
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.metric("Total xG Partido", f"{xg_l + xg_v:.3f}")
        with col_m2:
            st.metric("Diferencia xG", f"{abs(xg_l - xg_v):.3f}")
        with col_m3:
            if xg_l > xg_v:
                favorito = "Local"
            elif xg_v > xg_l:
                favorito = "Visitante"
            else:
                favorito = "Equilibrado"
            st.metric("Favorito", favorito)
        
        st.markdown("---")
        
        # Sección de compartir (versión corregida)
        st.markdown("## 📤 Compartir Análisis")
        
        mensaje_share = formatear_mensaje_share(
            xg_l, xg_v,
            st.session_state.cuota_local_guardada,
            st.session_state.cuota_empate_guardada,
            st.session_state.cuota_visitante_guardada
        )
        
        texto_url = urllib.parse.quote(mensaje_share)
        url_wa = f"https://api.whatsapp.com/send?text={texto_url}"
        url_tw = f"https://twitter.com/intent/tweet?text={texto_url}"
        
        share_col1, share_col2 = st.columns(2)
        
        with share_col1:
            st.link_button(
                "🟢 WhatsApp",
                url_wa,
                use_container_width=True
            )
        
        with share_col2:
            st.link_button(
                "🐦 X (Twitter)",
                url_tw,
                use_container_width=True
            )
        
        # Área de texto simple
        st.text_area(
            "📋 Mensaje para compartir:",
            value=mensaje_share,
            height=150,
            key="mensaje_share"
        )

with tab2:
    st.markdown("## 📊 Análisis Probabilístico")
    
    if st.session_state.resultados_calculados:
        xg_l = st.session_state.xg_local
        xg_v = st.session_state.xg_visitante
        
        st.markdown("### 📈 Probabilidades de Resultado")
        
        # Calcular probabilidades 1X2
        prob_local = 0
        prob_empate = 0
        prob_visitante = 0
        
        for gl in range(8):
            for gv in range(8):
                prob = poisson.pmf(gl, xg_l) * poisson.pmf(gv, xg_v)
                if gl > gv:
                    prob_local += prob
                elif gl == gv:
                    prob_empate += prob
                else:
                    prob_visitante += prob
        
        col_r1, col_r2, col_r3 = st.columns(3)
        with col_r1:
            st.metric("Victoria Local", f"{prob_local*100:.1f}%")
        with col_r2:
            st.metric("Empate", f"{prob_empate*100:.1f}%")
        with col_r3:
            st.metric("Victoria Visitante", f"{prob_visitante*100:.1f}%")
        
        st.markdown("### 🎯 Mercado Over/Under")
        
        # Calcular probabilidades Over/Under
        prob_over_15 = 0
        prob_over_25 = 0
        prob_over_35 = 0
        
        for gl in range(8):
            for gv in range(8):
                prob = poisson.pmf(gl, xg_l) * poisson.pmf(gv, xg_v)
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
        
    else:
        st.info("👈 Calcula primero los xG en la pestaña 'Calculadora'")

# --- FOOTER ---
st.markdown("---")
st.markdown("""
<div class="footer">
    <p>⚽ xG Analytics Pro v2.1.3 | Powered by Streamlit & SciPy</p>
    <p>Modelo: Distribución de Poisson · Optimización L-BFGS-B</p>
</div>
""", unsafe_allow_html=True)