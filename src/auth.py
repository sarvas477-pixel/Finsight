"""FinSight demo authentication.

Credentials can be overridden with:
- FINSIGHT_LOGIN_EMAIL
- FINSIGHT_LOGIN_PASSWORD_HASH

Only the SHA-256 password hash is stored in source.
"""
from __future__ import annotations

import hashlib
import hmac
import os

import streamlit as st

DEFAULT_EMAIL = "sarvas477@gmail.com"
DEFAULT_PASSWORD_HASH = "30e0f3e1d6923fe4a66a143f9eb0fc845ae454485d24cdf5e27535ca828739fd"


def _secret_or_env(name: str, default: str) -> str:
    value = os.getenv(name)
    if value:
        return value
    try:
        value = st.secrets.get(name)
        if value:
            return str(value)
    except Exception:
        pass
    return default


def _password_hash(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def authenticate(email: str, password: str) -> bool:
    configured_email = _secret_or_env("FINSIGHT_LOGIN_EMAIL", DEFAULT_EMAIL).strip().lower()
    configured_hash = _secret_or_env(
        "FINSIGHT_LOGIN_PASSWORD_HASH", DEFAULT_PASSWORD_HASH
    ).strip().lower()
    return (
        hmac.compare_digest(email.strip().lower(), configured_email)
        and hmac.compare_digest(_password_hash(password), configured_hash)
    )


def render_login() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
        [data-testid="stAppViewContainer"]{
            background:
              radial-gradient(circle at 50% 35%,rgba(0,217,255,.075),transparent 30%),
              radial-gradient(circle at 85% 85%,rgba(77,142,255,.08),transparent 28%),
              #081325 !important;
        }
        [data-testid="stHeader"]{background:transparent!important}
        [data-testid="stSidebar"]{display:none!important}
        .block-container{
            min-height:100vh;display:flex;align-items:center;justify-content:center;
            padding:24px 16px!important;max-width:100%!important;
        }
        .login-wrap{width:min(490px,100%);position:relative}
        .login-glow{
            position:absolute;width:560px;height:560px;left:50%;top:45%;
            transform:translate(-50%,-50%);border-radius:50%;
            background:rgba(0,217,255,.10);filter:blur(140px);pointer-events:none;
        }
        .login-card{
            position:relative;z-index:1;padding:32px;border-radius:12px;
            background:rgba(4,14,32,.88);border:1px solid rgba(60,73,77,.55);
            box-shadow:0 28px 80px rgba(0,4,15,.65),0 0 45px rgba(0,217,255,.045);
            backdrop-filter:blur(22px);
        }
        .login-brand{display:flex;align-items:center;justify-content:space-between}
        .login-brand-left{display:flex;align-items:center;gap:12px}
        .login-orb{
            width:40px;height:40px;border-radius:9px;display:grid;place-items:center;
            background:#152032;border:1px solid rgba(0,217,255,.16);
            box-shadow:inset 0 0 18px rgba(0,217,255,.05);
            color:#00d9ff!important;font:700 20px 'Space Grotesk';
        }
        .login-name{font:700 18px 'Space Grotesk';color:#d8e3fc!important;line-height:1}
        .login-kicker{font:700 10px 'Space Grotesk';letter-spacing:.14em;color:#00d9ff!important;margin-top:4px}
        .login-status{
            display:flex;align-items:center;gap:6px;padding:5px 9px;border-radius:999px;
            background:rgba(0,217,255,.08);color:#00d9ff!important;
            font:700 10px 'Space Grotesk';letter-spacing:.08em;
        }
        .login-dot{width:6px;height:6px;border-radius:50%;background:#00d9ff}
        .login-title{font:700 32px 'Space Grotesk';letter-spacing:-.04em;color:#d8e3fc!important;margin:28px 0 5px}
        .login-sub{font:400 15px 'Inter';color:#bbc9ce!important;margin-bottom:24px}
        .login-label{
            color:#bbc9ce!important;font:700 11px 'Space Grotesk';letter-spacing:.12em;
            text-transform:uppercase;margin:10px 0 7px;
        }
        .login-card .stTextInput input{
            height:44px;background:#111c2e!important;color:#d8e3fc!important;
            border:1px solid #3c494d!important;border-radius:8px!important;
        }
        .login-card .stTextInput input:focus{
            border-color:#00d9ff!important;box-shadow:0 0 0 1px rgba(0,217,255,.18)!important;
        }
        .login-card .stFormSubmitButton button{
            height:48px;border-radius:10px!important;border:0!important;
            background:linear-gradient(90deg,#00d9ff,#4d8eff)!important;
            color:#003641!important;font:700 15px 'Space Grotesk'!important;
            box-shadow:0 8px 25px rgba(0,217,255,.18)!important;
        }
        .login-security{
            display:flex;justify-content:center;align-items:center;gap:7px;
            color:#859398!important;font:700 10px 'Space Grotesk';letter-spacing:.10em;
            text-transform:uppercase;margin-top:18px;text-align:center;
        }
        .login-meta{
            display:flex;justify-content:space-between;margin-top:12px;padding:9px 11px;
            border-radius:7px;background:#111c2e;color:#859398!important;
            font:700 9px 'Space Grotesk';letter-spacing:.09em;text-transform:uppercase;
        }
        .login-meta b{color:#00d9ff!important}
        .login-footer{
            text-align:center;color:#65738b!important;font:700 10px 'Space Grotesk';
            letter-spacing:.12em;text-transform:uppercase;margin-top:22px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="login-wrap">
          <div class="login-glow"></div>
          <div class="login-card">
            <div class="login-brand">
              <div class="login-brand-left">
                <div class="login-orb">F</div>
                <div>
                  <div class="login-name">FinSight AI</div>
                  <div class="login-kicker">AP CONTROL TERMINAL</div>
                </div>
              </div>
              <div class="login-status"><span class="login-dot"></span>V2.4 AI AUDIT</div>
            </div>
            <div class="login-title">Welcome back</div>
            <div class="login-sub">Sign in to your invoice intelligence workspace.</div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("finsight_login", clear_on_submit=False):
        st.markdown('<div class="login-label">◉ &nbsp; WORK EMAIL</div>', unsafe_allow_html=True)
        email = st.text_input(
            "Email",
            label_visibility="collapsed",
            placeholder="analyst@enterprise.ai",
            autocomplete="username",
        )
        st.markdown('<div class="login-label">◆ &nbsp; PASSWORD</div>', unsafe_allow_html=True)
        password = st.text_input(
            "Password",
            type="password",
            label_visibility="collapsed",
            placeholder="••••••••••••",
            autocomplete="current-password",
        )
        submitted = st.form_submit_button("🔒  Sign in", type="primary", width="stretch")
        if submitted:
            if authenticate(email, password):
                st.session_state.authenticated = True
                st.session_state.login_error = ""
                st.rerun()
            else:
                st.session_state.login_error = "Invalid email or password."

    if st.session_state.get("login_error"):
        st.error(st.session_state.login_error)

    st.markdown(
        """
            <div class="login-security">✓ &nbsp; 256-BIT ENCRYPTED SESSION · AI VALIDATION MODEL ACTIVE</div>
            <div class="login-meta"><span>● AWS-AP-NE-1</span><span>LATENCY: 14MS</span><b>ENGINE READY</b></div>
          </div>
          <div class="login-footer">SYSTEM ID: FS-NODE-8910 &nbsp; • &nbsp; ISOLATED TENANT &nbsp; • &nbsp; REV 24.2.0</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def require_login() -> bool:
    st.session_state.setdefault("authenticated", False)
    st.session_state.setdefault("login_error", "")
    if st.session_state.authenticated:
        return True
    render_login()
    return False
