from string import Template

import streamlit as st

from backend.themes import DEFAULT_THEME, THEME_PRESETS
from backend.user_db import get_user_theme


def apply_app_styles(username=None):
    theme_id = get_user_theme(username) if username else DEFAULT_THEME
    theme = THEME_PRESETS[theme_id]
    st.html(Template("""
    <style>
    :root {
        --eco-accent: $accent;
        --eco-accent-deep: $accent_deep;
        --eco-glass: $glass;
        --eco-glass-strong: $glass_strong;
        --eco-glass-border: $glass_border;
        --eco-glow: $glow;
    }

    .stApp {
        background:
            radial-gradient(ellipse at 50% 4%, $glow, transparent 42%),
            radial-gradient(ellipse at 4% 65%, $glow_secondary, transparent 34%),
            linear-gradient(150deg, $background_start 0%, $background_mid 54%, $background_start 100%);
    }

    .stApp h1,
    .stApp h2,
    .stApp h3 {
        letter-spacing: -0.035em;
    }

    .stApp [data-testid="stIconMaterial"],
    .stApp .material-symbols-rounded,
    .stApp .material-symbols-outlined,
    .eco-login-mark,
    .eco-login-workspace__spark {
        animation: eco-icon-float 4.2s ease-in-out infinite;
        display: inline-block;
    }

    .stApp [data-testid="stVerticalBlockBorderWrapper"] {
        background: linear-gradient(145deg, var(--eco-glass-strong), var(--eco-glass));
        border: 1px solid var(--eco-glass-border);
        border-radius: 20px;
        box-shadow: 0 20px 70px rgba(0, 0, 0, 0.22);
        backdrop-filter: blur(20px);
    }

    .stApp [data-testid="stMetric"] {
        background: linear-gradient(145deg, var(--eco-glass-strong), var(--eco-glass));
        border: 1px solid var(--eco-glass-border);
        border-radius: 18px;
        padding: 0.85rem;
        backdrop-filter: blur(18px);
    }

    .stApp .stButton > button {
        background: var(--eco-glass);
        border: 1px solid var(--eco-glass-border);
        border-radius: 999px;
        backdrop-filter: blur(12px);
        transition: border-color 160ms ease, transform 160ms ease, box-shadow 160ms ease;
    }

    .stApp .stButton > button:hover {
        border-color: var(--eco-accent);
        box-shadow: 0 0 22px var(--eco-glow);
        transform: translateY(-1px);
    }

    .stApp .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--eco-accent-deep), var(--eco-accent));
        border-color: transparent;
        color: #FFFFFF;
    }

    .stApp input,
    .stApp textarea {
        background-color: var(--eco-glass) !important;
        border-color: var(--eco-glass-border) !important;
        border-radius: 14px !important;
    }

    section[data-testid="stSidebar"] {
        background:
            linear-gradient(180deg, $background_mid 0%, $background_start 100%);
        border-right: 1px solid var(--eco-glass-border);
        backdrop-filter: blur(22px);
    }

    .st-key-eco-login-stage,
    .st-key-eco-home-stage,
    .st-key-eco-assistant-stage {
        max-width: 68rem;
        margin: 0 auto;
    }

    .st-key-eco-login-stage {
        max-width: 76rem;
        padding: 0.5rem 0 1.5rem;
    }

    .st-key-eco-home-stage {
        max-width: 80rem;
        padding: 0.25rem 0 1.5rem;
    }

    .st-key-eco-login-story {
        background:
            radial-gradient(ellipse at 82% 8%, var(--eco-glow), transparent 42%),
            linear-gradient(145deg, var(--eco-glass-strong), var(--eco-glass));
        border: 1px solid var(--eco-glass-border);
        border-radius: 28px;
        box-shadow: 0 28px 90px rgba(0, 0, 0, 0.30);
        backdrop-filter: blur(26px);
        padding: 2.1rem;
    }

    .eco-login-brand {
        align-items: center;
        display: flex;
        gap: 0.85rem;
        margin-bottom: 1.25rem;
    }

    .eco-login-brand strong,
    .eco-login-brand small {
        display: block;
    }

    .eco-login-brand small {
        color: #B6AABD;
        margin-top: 0.15rem;
    }

    .eco-login-mark {
        align-items: center;
        background: linear-gradient(135deg, var(--eco-accent-deep), var(--eco-accent));
        border: 1px solid rgba(255, 255, 255, 0.28);
        border-radius: 16px;
        box-shadow: 0 10px 32px var(--eco-glow);
        color: #FFFFFF;
        display: inline-flex;
        font-size: 1.4rem;
        font-weight: 800;
        height: 3rem;
        justify-content: center;
        width: 3rem;
    }

    .eco-login-eyebrow {
        color: var(--eco-accent);
        font-size: 0.7rem;
        font-weight: 750;
        letter-spacing: 0.17em;
        margin: 0 0 0.8rem;
        text-transform: uppercase;
    }

    .eco-login-heading {
        color: #FBF8FF;
        font-size: clamp(2.2rem, 4vw, 3.5rem);
        font-weight: 700;
        letter-spacing: -0.06em;
        line-height: 1.05;
        margin: 0 0 1rem;
        max-width: 34rem;
    }

    .eco-login-copy {
        color: #C0B7CA;
        font-size: 1.02rem;
        line-height: 1.7;
        margin-bottom: 0.7rem;
        max-width: 34rem;
    }

    .eco-login-workspace {
        height: 16rem;
        isolation: isolate;
        margin: 0.6rem -0.5rem 1.25rem;
        perspective: 1000px;
        position: relative;
        transform-style: preserve-3d;
    }

    .eco-login-workspace__glow {
        background: radial-gradient(ellipse, var(--eco-glow), transparent 68%);
        filter: blur(12px);
        height: 17rem;
        left: 20%;
        position: absolute;
        top: 0;
        transform: translateZ(-50px);
        width: 65%;
        z-index: -2;
    }

    .eco-login-workspace__orbit {
        border: 1px solid var(--eco-glass-border);
        border-radius: 50%;
        height: 15rem;
        left: 15%;
        opacity: 0.75;
        position: absolute;
        top: 0.5rem;
        transform: rotateX(68deg) rotateZ(-18deg) translateZ(12px);
        width: 70%;
    }

    .eco-login-workspace__floor {
        background:
            linear-gradient(rgba(255, 255, 255, 0.055) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255, 255, 255, 0.055) 1px, transparent 1px),
            linear-gradient(145deg, var(--eco-glass-strong), var(--eco-glass));
        background-size: 22px 22px, 22px 22px, auto;
        border: 1px solid var(--eco-glass-border);
        border-radius: 26px;
        bottom: 0.8rem;
        box-shadow: 0 35px 60px rgba(0, 0, 0, 0.4), 0 0 32px var(--eco-glow);
        height: 8.5rem;
        left: 8%;
        opacity: 0.9;
        position: absolute;
        transform: rotateX(62deg) rotateZ(-15deg) translateZ(-38px);
        width: 83%;
    }

    .eco-login-workspace__desk {
        background:
            linear-gradient(155deg, rgba(255, 255, 255, 0.13), transparent 38%),
            linear-gradient(135deg, var(--eco-glass-strong), var(--eco-glass));
        border: 1px solid var(--eco-glass-border);
        border-radius: 20px;
        bottom: 1.7rem;
        box-shadow: 0 22px 34px rgba(0, 0, 0, 0.34), inset 0 1px rgba(255, 255, 255, 0.13);
        height: 6rem;
        left: 17%;
        position: absolute;
        transform: rotateX(58deg) rotateZ(-15deg) translateZ(-4px);
        width: 68%;
    }

    .eco-login-workspace__document {
        animation: eco-float 6s ease-in-out infinite;
        background: linear-gradient(150deg, rgba(255, 255, 255, 0.16), var(--eco-glass-strong) 38%);
        border: 1px solid rgba(255, 255, 255, 0.28);
        border-radius: 16px;
        box-shadow: 0 28px 55px rgba(0, 0, 0, 0.38), inset 0 1px rgba(255, 255, 255, 0.2);
        height: 12.6rem;
        left: 28%;
        padding: 0.85rem 1rem;
        position: absolute;
        top: 0.45rem;
        transform: rotateY(-17deg) rotateZ(-7deg) translateZ(65px);
        width: 43%;
    }

    .eco-login-workspace__document-head {
        display: flex;
        gap: 0.25rem;
        margin-bottom: 0.7rem;
    }

    .eco-login-workspace__document-head span {
        background: var(--eco-accent);
        border-radius: 50%;
        height: 0.35rem;
        opacity: 0.8;
        width: 0.35rem;
    }

    .eco-login-workspace__document small,
    .eco-login-workspace__tutor small {
        color: var(--eco-accent);
        display: block;
        font-size: 0.54rem;
        font-weight: 750;
        letter-spacing: 0.13em;
        margin-bottom: 0.35rem;
    }

    .eco-login-workspace__document strong {
        color: #FBF8FF;
        display: block;
        font-size: 0.95rem;
        line-height: 1.18;
        margin-bottom: 0.55rem;
    }

    .eco-login-workspace__document i {
        background: rgba(235, 226, 255, 0.38);
        border-radius: 99px;
        display: block;
        height: 0.18rem;
        margin: 0.27rem 0;
        width: 88%;
    }

    .eco-login-workspace__document i:nth-of-type(2) {
        width: 72%;
    }

    .eco-login-workspace__document i:nth-of-type(3) {
        width: 80%;
    }

    .eco-login-workspace__chart {
        align-items: flex-end;
        display: flex;
        gap: 0.28rem;
        height: 1.7rem;
        margin-top: 0.55rem;
    }

    .eco-login-workspace__chart span {
        background: linear-gradient(180deg, var(--eco-accent), var(--eco-accent-deep));
        border-radius: 0.2rem 0.2rem 0 0;
        box-shadow: 0 0 12px var(--eco-glow);
        flex: 1;
    }

    .eco-login-workspace__chart span:nth-child(1) { height: 42%; }
    .eco-login-workspace__chart span:nth-child(2) { height: 68%; }
    .eco-login-workspace__chart span:nth-child(3) { height: 54%; }
    .eco-login-workspace__chart span:nth-child(4) { height: 92%; }

    .eco-login-workspace__tutor {
        animation: eco-float 7s ease-in-out infinite reverse;
        background: linear-gradient(145deg, var(--eco-glass-strong), var(--eco-glass));
        border: 1px solid var(--eco-glass-border);
        border-radius: 15px;
        box-shadow: 0 22px 42px rgba(0, 0, 0, 0.35), 0 0 24px var(--eco-glow);
        padding: 0.75rem 0.85rem;
        position: absolute;
        right: 3%;
        top: 5.3rem;
        transform: rotateY(-16deg) rotateZ(7deg) translateZ(105px);
        width: 36%;
    }

    .eco-login-workspace__tutor strong {
        color: #F7F1FF;
        display: block;
        font-size: 0.67rem;
        white-space: nowrap;
    }

    .eco-login-workspace__spark {
        align-items: center;
        background: linear-gradient(135deg, var(--eco-accent-deep), var(--eco-accent));
        border-radius: 0.55rem;
        box-shadow: 0 0 16px var(--eco-glow);
        color: #FFFFFF;
        display: flex;
        font-size: 0.8rem;
        height: 1.55rem;
        justify-content: center;
        margin-bottom: 0.55rem;
        width: 1.55rem;
    }

    .eco-login-workspace__dots {
        display: flex;
        gap: 0.24rem;
        margin-top: 0.62rem;
    }

    .eco-login-workspace__dots span {
        background: var(--eco-accent);
        border-radius: 50%;
        box-shadow: 0 0 9px var(--eco-glow);
        height: 0.28rem;
        width: 0.28rem;
    }

    .eco-login-workspace__orb {
        animation: eco-float 5s ease-in-out infinite;
        background: radial-gradient(circle at 32% 28%, #FFFFFF, var(--eco-accent) 18%, var(--eco-accent-deep) 72%);
        border: 1px solid rgba(255, 255, 255, 0.45);
        border-radius: 50%;
        box-shadow: 0 12px 30px var(--eco-glow), inset -8px -9px 16px rgba(0, 0, 0, 0.28);
        height: 3.2rem;
        left: 9%;
        position: absolute;
        top: 4.1rem;
        transform: translateZ(120px);
        width: 3.2rem;
    }

    .eco-login-workspace__tag {
        background: var(--eco-glass-strong);
        border: 1px solid var(--eco-glass-border);
        border-radius: 999px;
        box-shadow: 0 10px 24px rgba(0, 0, 0, 0.25);
        color: var(--eco-accent);
        font-size: 0.54rem;
        font-weight: 750;
        letter-spacing: 0.12em;
        padding: 0.5rem 0.7rem;
        position: absolute;
        right: 8%;
        top: 1.7rem;
        transform: rotateZ(5deg) translateZ(80px);
    }

    @keyframes eco-float {
        0%, 100% { translate: 0 0; }
        50% { translate: 0 -7px; }
    }

    @keyframes eco-icon-float {
        0%, 100% { translate: 0 0; }
        50% { translate: 0 -3px; }
    }

    .st-key-eco-login-panel [role="tablist"] {
        border-bottom: 1px solid var(--eco-glass-border);
        margin-bottom: 1.3rem;
    }

    .st-key-eco-login-panel,
    .st-key-eco-home-panel {
        background: linear-gradient(145deg, var(--eco-glass-strong), var(--eco-glass));
        border: 1px solid var(--eco-glass-border);
        border-radius: 22px;
        box-shadow: 0 24px 80px rgba(0, 0, 0, 0.24);
        backdrop-filter: blur(24px);
        padding: 1.25rem;
    }

    .st-key-eco-login-panel {
        border-radius: 28px;
        padding: 1.5rem;
    }

    .st-key-eco-home-panel {
        background:
            radial-gradient(ellipse at 12% 0%, var(--eco-glow), transparent 48%),
            linear-gradient(145deg, var(--eco-glass-strong), var(--eco-glass));
        border-radius: 24px;
        margin: 0.35rem 0 0.8rem;
        padding: 0.95rem;
    }

    .eco-home-profile {
        align-items: center;
        display: flex;
        gap: 0.7rem;
        justify-content: flex-end;
        padding: 0.35rem 0;
    }

    .eco-home-profile strong,
    .eco-home-profile small {
        display: block;
        white-space: nowrap;
    }

    .eco-home-profile strong {
        color: #F7F1FF;
        font-size: 0.9rem;
    }

    .eco-home-profile small {
        color: #A7B4CF;
        font-size: 0.65rem;
        letter-spacing: 0.12em;
        margin-top: 0.12rem;
    }

    .eco-home-avatar {
        align-items: center;
        background: linear-gradient(135deg, var(--eco-accent-deep), #287BFF);
        border: 1px solid rgba(255, 255, 255, 0.25);
        border-radius: 50%;
        box-shadow: 0 0 22px var(--eco-glow);
        color: #FFFFFF;
        display: inline-flex;
        font-weight: 750;
        height: 2.4rem;
        justify-content: center;
        width: 2.4rem;
    }

    .eco-home-kicker {
        color: #9BAED3;
        font-size: 0.72rem;
        font-weight: 750;
        letter-spacing: 0.2em;
        margin: 0 0 0.7rem;
    }

    .eco-home-title {
        color: #F8FAFF;
        font-size: clamp(1.6rem, 2.1vw, 1.8rem);
        font-weight: 730;
        letter-spacing: -0.055em;
        line-height: 1.08;
        margin: 0 0 0.65rem;
        max-width: 46rem;
    }

    .eco-home-title span {
        background: linear-gradient(100deg, #B463FF, #428DFF);
        background-clip: text;
        color: transparent;
    }

    .eco-home-copy {
        color: #AAB8D2;
        font-size: 0.92rem;
        line-height: 1.65;
        margin: 0;
        max-width: 44rem;
    }

    .eco-brain-art {
        align-items: center;
        display: flex;
        height: 8rem;
        justify-content: center;
        margin: -0.4rem 0 0;
        perspective: 700px;
        position: relative;
    }

    .eco-brain-art__glow {
        background: radial-gradient(circle, rgba(48, 113, 255, 0.48), transparent 68%);
        border-radius: 50%;
        height: 12rem;
        position: absolute;
        width: 12rem;
    }

    .eco-brain-art__orbit {
        border: 1px solid rgba(72, 143, 255, 0.55);
        border-radius: 50%;
        height: 6rem;
        position: absolute;
        transform: rotate(-24deg) scaleX(1.55);
        width: 6rem;
    }

    .eco-brain-art__core {
        align-items: center;
        background:
            radial-gradient(circle at 30% 22%, rgba(116, 172, 255, 0.38), transparent 36%),
            linear-gradient(145deg, rgba(58, 93, 214, 0.44), rgba(8, 24, 67, 0.72));
        border: 1px solid rgba(117, 165, 255, 0.48);
        border-radius: 50%;
        box-shadow: 0 0 35px rgba(48, 113, 255, 0.42), inset 0 0 28px rgba(91, 128, 255, 0.16);
        color: #85B8FF;
        display: flex;
        height: 6rem;
        justify-content: center;
        position: relative;
        transform: translateZ(32px);
        width: 6rem;
    }

    .eco-brain-art__emoji {
        filter: drop-shadow(0 0 18px rgba(92, 151, 255, 0.9));
        font-size: 4.2rem;
        line-height: 1;
    }

    .eco-brain-art__spark {
        animation: eco-icon-float 3.2s ease-in-out infinite;
        background: #74A8FF;
        border-radius: 50%;
        box-shadow: 0 0 14px #4A8BFF;
        height: 0.45rem;
        position: absolute;
        width: 0.45rem;
    }

    .eco-brain-art__spark--one {
        left: 10%;
        top: 28%;
    }

    .eco-brain-art__spark--two {
        animation-delay: -1.6s;
        right: 12%;
        top: 20%;
    }

    .eco-home-benefits {
        align-items: center;
        color: #AAB8D2;
        display: flex;
        flex-wrap: wrap;
        font-size: 0.78rem;
        gap: 0.7rem 1.45rem;
        margin-top: 1.15rem;
    }

    .eco-home-benefits > span {
        align-items: center;
        display: inline-flex;
        gap: 0.42rem;
    }

    .eco-benefit-symbol {
        color: #A8B9FF;
        font-size: 1rem;
        font-weight: 700;
    }

    .eco-tools-heading {
        border-left: 3px solid var(--eco-accent-deep);
        color: #F2F5FF;
        font-size: 1.15rem;
        font-weight: 700;
        margin: 0.25rem 0 0.55rem;
        padding-left: 0.65rem;
    }

    .st-key-eco-home-tools [data-testid="stVerticalBlock"] {
        gap: 0.55rem;
    }

    .eco-tool-icon {
        align-items: center;
        background: linear-gradient(135deg, var(--tool-color), rgba(49, 108, 255, 0.92));
        border: 1px solid rgba(255, 255, 255, 0.22);
        border-radius: 0.75rem;
        box-shadow: 0 8px 24px rgba(50, 89, 190, 0.3);
        color: #FFFFFF;
        display: inline-flex;
        height: 2.35rem;
        justify-content: center;
        margin-bottom: 0.75rem;
        width: 2.35rem;
    }

    .eco-tool-icon span {
        font-size: 1.45rem;
        line-height: 1;
    }

    .eco-tool-title {
        color: #F3F6FF;
        display: block;
        font-size: 0.98rem;
    }

    .eco-tool-description {
        color: #AAB8D2;
        font-size: 0.7rem;
        line-height: 1.45;
        min-height: 2rem;
        margin: 0.35rem 0 0.65rem;
    }

    .eco-home-footer {
        align-items: center;
        color: #8C83BC;
        display: flex;
        font-size: 0.85rem;
        justify-content: space-between;
        margin-top: 2rem;
        padding: 0 0.3rem;
    }

    .st-key-eco-settings-theme-panel,
    .st-key-eco-settings-account-panel,
    .st-key-eco-settings-data-panel {
        background: linear-gradient(145deg, var(--eco-glass-strong), var(--eco-glass));
        border: 1px solid var(--eco-glass-border);
        border-radius: 22px;
        box-shadow: 0 24px 80px rgba(0, 0, 0, 0.24);
        backdrop-filter: blur(24px);
        padding: 1.25rem;
    }

    .st-key-eco-assistant-stage {
        max-width: 58rem;
    }

    .st-key-eco-assistant-panel {
        background: linear-gradient(145deg, var(--eco-glass-strong), var(--eco-glass));
        border: 1px solid var(--eco-glass-border);
        border-radius: 24px;
        box-shadow: 0 24px 90px rgba(0, 0, 0, 0.34);
        backdrop-filter: blur(26px);
        padding: 1.25rem 1.5rem;
    }

    .st-key-eco-chat-transcript {
        border-top: 1px solid var(--eco-glass-border);
        margin-top: 1rem;
        padding-top: 0.5rem;
    }

    .eco-theme-preview {
        align-items: center;
        background:
            radial-gradient(ellipse at 85% 20%, var(--eco-glow), transparent 45%),
            linear-gradient(135deg, var(--eco-glass-strong), var(--eco-glass));
        border: 1px solid var(--eco-glass-border);
        border-radius: 20px;
        box-shadow: 0 18px 55px rgba(0, 0, 0, 0.22);
        color: #F4EFFA;
        display: flex;
        justify-content: space-between;
        gap: 1rem;
        margin: 1rem 0;
        padding: 1.15rem 1.3rem;
        backdrop-filter: blur(22px);
    }

    .eco-theme-preview p {
        color: #B6AABD;
        margin: 0.3rem 0 0;
    }

    .eco-theme-preview__label {
        color: var(--eco-accent);
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.16em;
        text-transform: uppercase;
    }

    .eco-theme-preview__swatches {
        align-items: center;
        display: flex;
        gap: 0.45rem;
        flex: 0 0 auto;
    }

    .eco-theme-preview__swatches span {
        border: 1px solid rgba(255, 255, 255, 0.28);
        border-radius: 50%;
        height: 1rem;
        width: 1rem;
    }

    @media (max-width: 640px) {
        .st-key-eco-login-panel,
        .st-key-eco-login-story,
        .st-key-eco-home-panel,
        .st-key-eco-assistant-panel,
        .st-key-eco-settings-theme-panel,
        .st-key-eco-settings-account-panel,
        .st-key-eco-settings-data-panel {
            padding: 0.9rem;
        }

        .st-key-eco-login-stage {
            padding: 1rem 0 2rem;
        }

        .eco-login-brand {
            margin-bottom: 2rem;
        }

        .eco-login-workspace {
            height: 15rem;
            margin-left: -0.25rem;
            margin-right: -0.25rem;
        }

        .eco-login-workspace__document {
            left: 25%;
            width: 47%;
        }

        .eco-login-workspace__tutor {
            right: 0;
            width: 39%;
        }

        .st-key-eco-home-stage {
            padding-bottom: 1rem;
        }

        .st-key-eco-home-panel {
            padding: 0.9rem;
        }

        .eco-home-title {
            font-size: clamp(1.6rem, 7vw, 1.9rem);
        }

        .eco-brain-art {
            height: 7.5rem;
        }

        .eco-brain-art__core {
            height: 5rem;
            width: 5rem;
        }

        .eco-brain-art__emoji {
            font-size: 3.5rem;
        }

        .eco-home-footer {
            align-items: flex-start;
            flex-direction: column;
            gap: 0.35rem;
        }

        .eco-theme-preview {
            align-items: flex-start;
            flex-direction: column;
        }
    }

    @media (prefers-reduced-motion: reduce) {
        .stApp [data-testid="stIconMaterial"],
        .stApp .material-symbols-rounded,
        .stApp .material-symbols-outlined,
        .eco-login-mark,
        .eco-login-workspace__spark,
        .eco-brain-art__spark,
        .eco-login-workspace__document,
        .eco-login-workspace__tutor,
        .eco-login-workspace__orb {
            animation: none;
        }
    }
    </style>
    """).substitute(theme))
