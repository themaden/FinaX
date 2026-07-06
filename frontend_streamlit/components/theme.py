"""
FinanX — Premium Glassmorphic Tasarım Teması
Uygulamanın genelinde ultra premium, modern ve animasyonlu karanlık tema CSS enjeksiyonu.
"""

import streamlit as st


def apply_custom_theme():
    """Gelişmiş CSS stillerini ve özel temayı sayfaya enjekte eder."""
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

        /* Global Font & Arayüz */
        * {
            font-family: 'Outfit', sans-serif !important;
        }
        
        code, pre, kbd, samp {
            font-family: 'JetBrains Mono', monospace !important;
        }

        .stApp {
            background: radial-gradient(circle at 10% 20%, rgba(13, 20, 44, 1) 0%, rgba(8, 11, 23, 1) 90%);
            color: #e2e8f0;
        }

        /* Cam Küre Efekti (Glassmorphism) Kartlar */
        .glass-card {
            background: rgba(22, 28, 51, 0.45);
            backdrop-filter: blur(16px) saturate(120%);
            -webkit-backdrop-filter: blur(16px) saturate(120%);
            border: 1px solid rgba(255, 255, 255, 0.07);
            border-radius: 16px;
            padding: 24px;
            margin: 12px 0;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.4);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .glass-card:hover {
            transform: translateY(-4px);
            border-color: rgba(78, 144, 255, 0.25);
            box-shadow: 0 15px 50px rgba(78, 144, 255, 0.12);
        }

        /* Küçük İstatistik Kartı */
        .stat-card {
            background: rgba(15, 22, 42, 0.6);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 16px;
            text-align: center;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
            transition: border-color 0.2s;
        }
        
        .stat-card:hover {
            border-color: rgba(0, 212, 170, 0.2);
        }

        /* Pulsating Aktif Dot (Durum Göstergesi) */
        .pulse-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 8px;
            box-shadow: 0 0 0 0 rgba(0, 212, 170, 0.7);
        }
        
        .pulse-dot.online {
            background: #00d4aa;
            animation: pulse-green 2s infinite;
        }

        .pulse-dot.offline {
            background: #ff4b4b;
            animation: pulse-red 2s infinite;
        }

        @keyframes pulse-green {
            0% {
                transform: scale(0.95);
                box-shadow: 0 0 0 0 rgba(0, 212, 170, 0.7);
            }
            70% {
                transform: scale(1);
                box-shadow: 0 0 0 10px rgba(0, 212, 170, 0);
            }
            100% {
                transform: scale(0.95);
                box-shadow: 0 0 0 0 rgba(0, 212, 170, 0);
            }
        }

        @keyframes pulse-red {
            0% {
                transform: scale(0.95);
                box-shadow: 0 0 0 0 rgba(255, 75, 75, 0.7);
            }
            70% {
                transform: scale(1);
                box-shadow: 0 0 0 10px rgba(255, 75, 75, 0);
            }
            100% {
                transform: scale(0.95);
                box-shadow: 0 0 0 0 rgba(255, 75, 75, 0);
            }
        }

        /* Premium Başlık */
        .neon-title {
            font-size: 3.5rem;
            font-weight: 800;
            background: linear-gradient(135deg, #00f2fe 0%, #4facfe 50%, #9b51e0 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 0 4px 30px rgba(78, 144, 255, 0.2);
            letter-spacing: -2px;
            line-height: 1.1;
            margin-bottom: 8px;
            text-align: center;
        }

        /* Premium Butonlar */
        .stButton > button {
            background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%) !important;
            color: #0e1117 !important;
            border: none !important;
            border-radius: 12px !important;
            font-weight: 700 !important;
            font-size: 0.95rem !important;
            letter-spacing: 0.5px !important;
            padding: 10px 24px !important;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
            box-shadow: 0 4px 20px rgba(0, 242, 254, 0.2) !important;
        }

        .stButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 30px rgba(0, 242, 254, 0.45) !important;
            filter: brightness(1.1);
        }

        .stButton > button:active {
            transform: translateY(0px) !important;
        }
        
        /* Secondary butonlar (örneğin temizleme veya yan fonksiyonlar) */
        div[data-testid="stForm"] .stButton > button {
            background: linear-gradient(135deg, #1b2440 0%, #111827 100%) !important;
            color: #4e90ff !important;
            border: 1px solid rgba(78, 144, 255, 0.25) !important;
            box-shadow: none !important;
        }
        
        div[data-testid="stForm"] .stButton > button:hover {
            border-color: #00f2fe !important;
            box-shadow: 0 0 15px rgba(0, 242, 254, 0.15) !important;
        }

        /* Giriş (Input) Alanları */
        .stTextInput > div > div > input,
        .stSelectbox > div > div > select,
        .stTextArea textarea {
            background-color: rgba(13, 17, 33, 0.7) !important;
            border: 1px solid rgba(78, 144, 255, 0.2) !important;
            border-radius: 12px !important;
            color: #e2e8f0 !important;
            padding: 10px 14px !important;
            transition: border-color 0.2s, box-shadow 0.2s !important;
        }

        .stTextInput > div > div > input:focus,
        .stTextArea textarea:focus {
            border-color: #00f2fe !important;
            box-shadow: 0 0 10px rgba(0, 242, 254, 0.25) !important;
        }

        /* Sidebar Geliştirmesi */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #090c15 0%, #0d1222 100%) !important;
            border-right: 1px solid rgba(78, 144, 255, 0.1) !important;
        }
        
        [data-testid="stSidebar"] .finanx-logo {
            text-align: center;
            font-size: 2.2rem;
            font-weight: 800;
            background: linear-gradient(90deg, #00f2fe, #4facfe, #9b51e0);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 20px;
            letter-spacing: -1.5px;
        }

        /* Özel Sekmeler (Tabs) */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background-color: rgba(13, 17, 33, 0.5);
            padding: 6px;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }

        .stTabs [data-baseweb="tab"] {
            background-color: transparent;
            border-radius: 8px;
            color: #94a3b8;
            font-weight: 600;
            padding: 8px 18px;
            border: none !important;
            transition: all 0.2s;
        }

        .stTabs [aria-selected="true"] {
            background-color: rgba(79, 172, 254, 0.15) !important;
            color: #00f2fe !important;
        }

        /* Tablolar (DataFrame/Table) */
        div[data-testid="stTable"] table, 
        .stDataFrame {
            background-color: rgba(15, 22, 42, 0.5) !important;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.05);
            overflow: hidden;
        }

        /* Plotly Grafik Alanları */
        .js-plotly-plot .main-svg {
            border-radius: 16px !important;
        }
        
        /* Hisse Hapları (Badges) */
        .badge-positive {
            background: rgba(0, 212, 170, 0.12);
            color: #00d4aa;
            border: 1px solid rgba(0, 212, 170, 0.3);
            border-radius: 8px;
            padding: 3px 10px;
            font-weight: 700;
            font-size: 0.85rem;
        }
        
        .badge-negative {
            background: rgba(255, 75, 75, 0.12);
            color: #ff4b4b;
            border: 1px solid rgba(255, 75, 75, 0.3);
            border-radius: 8px;
            padding: 3px 10px;
            font-weight: 700;
            font-size: 0.85rem;
        }
    </style>
    """, unsafe_allow_html=True)
