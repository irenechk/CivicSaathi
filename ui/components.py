"""
Reusable UI components and custom CSS styling for Civicsaathi.
Visual Theme:
- Deep Navy: #0A192F
- Indigo: #1E3A8A
- Saffron Accent: #FF9933
- Teal: #0D9488
- Warm Off-White / Cream: #F8FAFC
- Clean accessible typography and cards
- Supports Day and Night mode toggling
"""

import streamlit as st
from typing import Dict, Any, List


def get_theme_css(is_dark_mode: bool = False) -> str:
    if is_dark_mode:
        bg_main = "#0B132B"
        bg_card = "#1C2541"
        text_primary = "#F8FAFC"
        text_secondary = "#94A3B8"
        border_color = "#3A506B"
        badge_bg = "#1E293B"
    else:
        bg_main = "#F8FAFC"
        bg_card = "#FFFFFF"
        text_primary = "#0F172A"
        text_secondary = "#475569"
        border_color = "#E2E8F0"
        badge_bg = "#F1F5F9"

    return f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Plus Jakarta Sans', sans-serif;
    }}

    .stApp {{
        background-color: {bg_main};
        color: {text_primary};
    }}

    /* Hero Header */
    .hero-banner {{
        background: linear-gradient(135deg, #0A192F 0%, #1E3A8A 50%, #0D9488 100%);
        border-radius: 16px;
        padding: 2.2rem 2.5rem;
        margin-bottom: 2rem;
        color: #FFFFFF;
        box-shadow: 0 10px 25px -5px rgba(10, 25, 47, 0.2);
    }}
    .hero-title {{
        font-size: 2.4rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.02em;
    }}
    .hero-tagline {{
        font-size: 1.15rem;
        color: #FFB74D;
        font-weight: 600;
        margin-top: 0.5rem;
    }}
    .hero-desc {{
        font-size: 0.95rem;
        color: #CBD5E1;
        margin-top: 0.5rem;
        max-width: 800px;
    }}

    /* Cards */
    .scheme-card {{
        background-color: {bg_card};
        border: 1px solid {border_color};
        border-radius: 12px;
        padding: 1.4rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }}
    .scheme-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }}

    /* Badges */
    .badge {{
        display: inline-block;
        padding: 0.25rem 0.65rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 700;
        margin-right: 0.4rem;
        margin-bottom: 0.4rem;
    }}
    .badge-verified {{
        background-color: #DCFCE7;
        color: #166534;
        border: 1px solid #86EFAC;
    }}
    .badge-partial {{
        background-color: #FEF9C3;
        color: #854D0E;
        border: 1px solid #FDE047;
    }}
    .badge-unverified {{
        background-color: #FEE2E2;
        color: #991B1B;
        border: 1px solid #FCA5A5;
    }}
    .badge-level {{
        background-color: #DBEAFE;
        color: #1E40AF;
        border: 1px solid #93C5FD;
    }}
    .badge-saffron {{
        background-color: #FFEDD5;
        color: #C2410C;
        border: 1px solid #FDBA74;
    }}

    /* Metrics */
    .metric-box {{
        background-color: {bg_card};
        border: 1px solid {border_color};
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);
    }}
    .metric-number {{
        font-size: 2rem;
        font-weight: 800;
        color: #FF9933;
    }}
    .metric-label {{
        font-size: 0.85rem;
        color: {text_secondary};
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}

    /* Citations */
    .citation-box {{
        background-color: {badge_bg};
        border-left: 4px solid #0D9488;
        padding: 0.8rem 1rem;
        border-radius: 0 8px 8px 0;
        font-size: 0.85rem;
        margin-top: 0.8rem;
    }}
    </style>
    """


def render_header(language: str = "en"):
    taglines = {
        "en": "From Citizen's Problem to Government Solution — One Guided Journey",
        "hi": "नागरिक की समस्या से सरकारी समाधान तक — एक सशक्त डिजिटल यात्रा",
        "mr": "नागरिकांच्या समस्येपासून शासकीय उपायांपर्यंत — एक सुलभ डिजिटल प्रवास",
    }
    desc = {
        "en": "Independent AI-powered Indian welfare scheme discovery and eligibility intelligence platform. 100% locally hosted with zero paid API dependencies.",
        "hi": "भारत सरकार की कल्याणकारी योजनाओं की सटीक जानकारी और पात्रता जाँचने का स्वतंत्र व सुरक्षित मंच। पूर्णतः स्थानीय व निःशुल्क।",
        "mr": "शासकीय कल्याणकारी योजना शोधणे आणि पात्रता तपासण्यासाठी स्वतंत्र व सुरक्षित डिजिटल माध्यम. संपूर्ण स्थानिक व विश्वासार्ह.",
    }

    st.markdown(
        f"""
        <div class="hero-banner">
            <div class="hero-title">Civicsaathi 🇮🇳 नागरिक साथी</div>
            <div class="hero-tagline">{taglines.get(language, taglines['en'])}</div>
            <div class="hero-desc">{desc.get(language, desc['en'])}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_scheme_card(scheme: Dict[str, Any], language: str = "en"):
    v_status = scheme.get("verification_status", "unverified")
    if v_status == "verified":
        v_class = "badge-verified"
        v_label = "✅ Verified"
    elif v_status == "partially_verified":
        v_class = "badge-partial"
        v_label = "⚠️ Partially Verified"
    else:
        v_class = "badge-unverified"
        v_label = "❓ Unverified"

    app_status = scheme.get("application_status", "ACTIVE_CONFIRMED")
    s_level = scheme.get("scheme_level", "central").upper()
    ministry = scheme.get("ministry") or "Central Government of India"
    benefit_amount = scheme.get("benefit_amount") or "See scheme details for benefit terms."
    official_url = scheme.get("official_scheme_url") or scheme.get("official_application_url") or "https://www.myscheme.gov.in"

    card_html = f"""
    <div class="scheme-card">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.5rem;">
            <div>
                <span class="badge badge-level">{s_level}</span>
                <span class="badge {v_class}">{v_label}</span>
                <span class="badge badge-saffron">{app_status}</span>
            </div>
            <small style="color: #64748B; font-weight: 600;">{scheme.get('scheme_id')}</small>
        </div>
        <h3 style="margin: 0.2rem 0 0.5rem 0; font-size: 1.25rem; font-weight: 700;">{scheme.get('scheme_name')}</h3>
        <p style="color: #0D9488; font-size: 0.85rem; font-weight: 600; margin-bottom: 0.6rem;">🏛️ {ministry}</p>
        <p style="font-size: 0.9rem; margin-bottom: 0.8rem; line-height: 1.45;">{scheme.get('description')}</p>
        <div style="background-color: rgba(255, 153, 51, 0.08); padding: 0.6rem 0.8rem; border-radius: 8px; border-left: 3px solid #FF9933; margin-bottom: 0.8rem;">
            <strong style="color: #C2410C; font-size: 0.85rem;">💰 Benefit:</strong> <span style="font-size: 0.85rem;">{benefit_amount}</span>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.8rem; color: #64748B;">
            <span>Verified: {scheme.get('research_verified_date', '2026-11-21')}</span>
            <a href="{official_url}" target="_blank" style="color: #1E3A8A; font-weight: 700; text-decoration: none;">Official Portal ↗</a>
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)
