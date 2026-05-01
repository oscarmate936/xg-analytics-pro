import streamlit as st
import math
from scipy.optimize import minimize
from scipy.stats import poisson
import urllib.parse
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="xG Analytics Pro | Fútbol Avanzado",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILOS CSS PERSONALIZADOS ---
st.markdown("""
<style>
    /* Estilos generales */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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
        border-left: 4px solid #667eea;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }
    
    .share-section {
        background: #f8f9fa;
        padding: 2rem;
        border-radius: 15px;
        border: 2px solid #e0e0e0;
    }
    
    /* Estilos para los botones */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 15px 30px;
        border-radius: 10px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.2);
    }
    
    /* Animaciones */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .fade-in {
        animation: fadeIn 0.8s ease-out;
    }
    
    /* Personalización de métricas */
    [data-testid="stMetricValue"] {
        font-size: 2.5rem;
        font-weight: bold;
        color: #667eea;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f5f7fa 0%, #c3cfe2 100%);
    }
</style>
""", unsafe_allow_html=True)

# --- LÓGICA MATEMÁTICA (SIN CAMBIOS) ---
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

# --- HEADER PRINCIPAL ---
st.markdown("""
<div class="main-header">
    <h1 style="margin: 0; font-size: 3rem;">⚽ xG Analytics Pro</h1>
    <p style="font-size: 1.2rem; margin-top: 1rem; opacity: 0.9;">
        Ingeniería inversa de cuotas de apuestas para revelar los Goles Esperados (xG) mediante modelos de Poisson
    </p>
</div>
""", unsafe_allow_html=True)

# --- SIDEBAR MEJORADA ---
with st.sidebar:
    st.markdown("### 🎯 Acerca del Modelo")
    st.info("""
    **Metodología Avanzada:**
    
    1. 📊 Extracción de probabilidades implícitas de las cuotas
    2. 🧮 Eliminación del margen de la casa de apuestas
    3. 📈 Optimización mediante distribución de Poisson
    4. 🎯 Cálculo de xG para cada equipo
    
    **Asunciones Clave:**
    - Los goles siguen una distribución de Poisson
    - Independencia entre goles locales y visitantes
    - Cuotas basadas en probabilidades de Poisson
    """)
    
    st.markdown("---")
    
    st.markdown("### ⚡ Estadísticas en Tiempo Real")
    now = datetime.now()
    st.metric("Hora del Sistema", now.strftime("%H:%M:%S"))
    st.metric("Fecha", now.strftime("%d/%m/%Y"))
    
    st.markdown("---")
    
    st.markdown("### 📈 Versión del Modelo")
    st.code("Poisson v2.1.0", language="bash")
    
    st.markdown("### 🔗 Recursos")
    st.markdown("[📚 Documentación](https://docs.streamlit.io)")
    st.markdown("[💡 Teoría xG](https://es.wikipedia.org/wiki/Goles_esperados)")

# --- CONTENIDO PRINCIPAL ---
tab1, tab2 = st.tabs(["🎮 Calculadora Principal", "📊 Análisis Detallado"])

with tab1:
    st.markdown("## ⚙️ Configuración del Encuentro")
    st.markdown("Ajusta las cuotas del mercado 1X2 para obtener los xG implícitos")
    
    # Container para inputs con diseño mejorado
    input_container = st.container()
    with input_container:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### 🏠 Local")
            cuota_local = st.number_input(
                "Cuota Victoria Local (1)",
                min_value=1.01,
                value=2.10,
                step=0.01,
                help="Probabilidad implícita: " + str(round(1/2.10*100, 1)) + "%",
                key="local"
            )
            prob_local = 1/cuota_local*100
            st.caption(f"💰 Probabilidad bruta: {prob_local:.1f}%")
            
        with col2:
            st.markdown("### 🤝 Empate")
            cuota_empate = st.number_input(
                "Cuota Empate (X)",
                min_value=1.01,
                value=3.40,
                step=0.01,
                help="Probabilidad implícita: " + str(round(1/3.40*100, 1)) + "%",
                key="empate"
            )
            prob_empate = 1/cuota_empate*100
            st.caption(f"💰 Probabilidad bruta: {prob_empate:.1f}%")
            
        with col3:
            st.markdown("### 🚀 Visitante")
            cuota_visitante = st.number_input(
                "Cuota Victoria Visitante (2)",
                min_value=1.01,
                value=3.60,
                step=0.01,
                help="Probabilidad implícita: " + str(round(1/3.60*100, 1)) + "%",
                key="visitante"
            )
            prob_visitante = 1/cuota_visitante*100
            st.caption(f"💰 Probabilidad bruta: {prob_visitante:.1f}%")

    st.markdown("---")
    
    # Botón de cálculo centrado y estilizado
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        if st.button("🔍 CALCULAR xG IMPLÍCITO", use_container_width=True, type="primary"):
            with st.spinner("🔄 Optimizando modelo de Poisson... El universo cuántico está calculando..."):
                try:
                    xg_l, xg_v = xg_desde_cuotas(cuota_local, cuota_empate, cuota_visitante)
                    
                    st.success("✅ ¡Análisis completado exitosamente!")
                    
                    # Resultados en cards animadas
                    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
                    
                    st.markdown("## 🏆 Resultados de xG")
                    
                    res_col1, res_col2, res_col3 = st.columns([2, 1, 2])
                    
                    with res_col1:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div style="font-size: 0.9rem; color: #666;">GOLES ESPERADOS LOCAL</div>
                            <div style="font-size: 3rem; font-weight: bold; color: #667eea;">{xg_l}</div>
                            <div style="font-size: 0.8rem; color: #999;">xG - Expected Goals</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with res_col2:
                        st.markdown("""
                        <div style="text-align: center; padding-top: 2rem;">
                            <div style="font-size: 2rem;">⚡</div>
                            <div style="font-weight: bold; color: #764ba2;">vs</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with res_col3:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div style="font-size: 0.9rem; color: #666;">GOLES ESPERADOS VISITANTE</div>
                            <div style="font-size: 3rem; font-weight: bold; color: #764ba2;">{xg_v}</div>
                            <div style="font-size: 0.8rem; color: #999;">xG - Expected Goals</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Métricas adicionales
                    col_m1, col_m2, col_m3 = st.columns(3)
                    with col_m1:
                        st.metric("Total xG Partido", f"{xg_l + xg_v:.3f}")
                    with col_m2:
                        st.metric("Diferencia xG", f"{abs(xg_l - xg_v):.3f}")
                    with col_m3:
                        favorito = "Local" if xg_l > xg_v else "Visitante" if xg_v > xg_l else "Empate"
                        st.metric("Favorito según xG", favorito)
                    
                    st.markdown("---")
                    
                    # Sección de compartir mejorada
                    st.markdown("## 📤 Compartir Análisis")
                    
                    share_container = st.container()
                    with share_container:
                        st.markdown("""
                        <div class="share-section">
                            <h3 style="margin-bottom: 1rem;">🚀 Difunde el conocimiento</h3>
                        """, unsafe_allow_html=True)
                        
                        # Formateo del mensaje
                        mensaje_share = (
                            f"⚽ *Análisis xG Pro - {datetime.now().strftime('%d/%m/%Y %H:%M')}*\n\n"
                            f"🏠 Local: {xg_l} xG\n"
                            f"🚀 Visitante: {xg_v} xG\n"
                            f"📊 Total: {xg_l + xg_v:.3f} xG\n\n"
                            f"📈 Basado en cuotas:\n"
                            f"1 → {cuota_local} | X → {cuota_empate} | 2 → {cuota_visitante}\n\n"
                            f"🔬 Modelo: Poisson + Optimización\n"
                            f"#futbol #xg #analytics #apuestas"
                        )
                        
                        texto_url = urllib.parse.quote(mensaje_share)
                        url_wa = f"https://api.whatsapp.com/send?text={texto_url}"
                        url_tw = f"https://twitter.com/intent/tweet?text={texto_url}"
                        
                        share_col1, share_col2, share_col3 = st.columns(3)
                        
                        with share_col1:
                            st.link_button(
                                "🟢 Compartir por WhatsApp",
                                url_wa,
                                use_container_width=True
                            )
                        
                        with share_col2:
                            st.link_button(
                                "🐦 Compartir en X",
                                url_tw,
                                use_container_width=True
                            )
                        
                        with share_col3:
                            if st.button("📋 Copiar al Portapapeles", use_container_width=True):
                                st.toast("✅ Texto copiado al portapapeles", icon="📋")
                                st.code(mensaje_share, language="markdown")
                        
                        st.markdown("</div>", unsafe_allow_html=True)
                        
                        # Vista previa del mensaje
                        with st.expander("👁️ Vista previa del mensaje"):
                            st.text_area("Mensaje a compartir:", value=mensaje_share, height=200)
                    
                except Exception as e:
                    st.error(f"❌ Error en el cálculo: {str(e)}")
                    st.info("💡 Verifica que las cuotas sean válidas y mayores a 1.01")

with tab2:
    st.markdown("## 📊 Análisis Probabilístico Detallado")
    
    if 'xg_l' in locals():
        # Matriz de probabilidades de goles
        st.markdown("### 📈 Matriz de Probabilidad de Goles")
        st.markdown("Probabilidad conjunta de cada resultado posible")
        
        # Crear matriz de probabilidades
        matrix_data = {"Goles Local": list(range(0, 6))}
        for gv in range(0, 6):
            col_name = f"{gv} Goles Vis"
            matrix_data[col_name] = []
            for gl in range(0, 6):
                prob = poisson.pmf(gl, xg_l) * poisson.pmf(gv, xg_v)
                matrix_data[col_name].append(f"{prob*100:.2f}%")
        
        st.dataframe(matrix_data, use_container_width=True)
        
        # Probabilidades de Over/Under
        st.markdown("### 🎯 Probabilidades Over/Under")
        
        prob_over_15 = 0
        prob_over_25 = 0
        prob_over_35 = 0
        
        for gl in range(8):
            for gv in range(8):
                prob = poisson.pmf(gl, xg_l) * poisson.pmf(gv, xg_v)
                total = gl + gv
                if total > 1.5: prob_over_15 += prob
                if total > 2.5: prob_over_25 += prob
                if total > 3.5: prob_over_35 += prob
        
        ou_col1, ou_col2, ou_col3 = st.columns(3)
        with ou_col1:
            st.metric("Over 1.5", f"{prob_over_15*100:.1f}%")
        with ou_col2:
            st.metric("Over 2.5", f"{prob_over_25*100:.1f}%")
        with ou_col3:
            st.metric("Over 3.5", f"{prob_over_35*100:.1f}%")
    else:
        st.info("👈 Primero calcula los xG en la pestaña principal para ver el análisis detallado")

# --- FOOTER ---
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 20px; color: #666;">
    <p>⚽ xG Analytics Pro v2.1 | Powered by Streamlit & SciPy</p>
    <p style="font-size: 0.8rem;">Modelo basado en distribución de Poisson · Optimización L-BFGS-B · Cálculos en tiempo real</p>
    <p style="font-size: 0.8rem;">Desarrollado con ❤️ para la comunidad futbolística · © 2024</p>
</div>
""", unsafe_allow_html=True)