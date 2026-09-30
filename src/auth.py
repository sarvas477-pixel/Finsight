"""FinSight demo authentication.

Credentials can be overridden with:
- FINSIGHT_LOGIN_EMAIL
- FINSIGHT_LOGIN_PASSWORD_HASH

The repository contains only a SHA-256 password hash, not the plaintext password.
For production use, configure the values in Streamlit Secrets/environment variables.
"""
from __future__ import annotations

import hashlib
import hmac
import os

import streamlit as st


DEFAULT_EMAIL = "sarvas477@gmail.com"
# SHA-256 hash of the requested demo password. Plaintext is intentionally not stored.
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
        [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(circle at 18% 20%, rgba(0, 217, 255, .10), transparent 28%),
                radial-gradient(circle at 82% 78%, rgba(113, 92, 255, .10), transparent 30%),
                #050914 !important;
        }
        [data-testid="stHeader"] { background: transparent !important; }
        [data-testid="stSidebar"] { display: none !important; }
        .block-container {
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 32px 18px !important;
            max-width: 100% !important;
        }
        .login-shell {
            width: min(460px, 100%);
            padding: 38px;
            border: 1px solid rgba(0, 217, 255, .18);
            border-radius: 28px;
            background: linear-gradient(145deg, rgba(11, 22, 40, .96), rgba(5, 9, 20, .98));
            box-shadow:
                0 0 70px rgba(0, 198, 255, .08),
                0 28px 90px rgba(0, 0, 0, .45);
            backdrop-filter: blur(22px);
        }
        .login-logo {
            display: inline-flex;
            align-items: center;
            gap: 10px;
            color: #f4f8ff !important;
            font: 700 1.55rem 'Space Grotesk', sans-serif;
            letter-spacing: -.04em;
        }
        .login-orb {
            width: 38px;
            height: 38px;
            border-radius: 12px;
            display: grid;
            place-items: center;
            background: linear-gradient(135deg, #00d9ff, #147bff);
            box-shadow: 0 0 30px rgba(0, 217, 255, .28);
            color: #06101d !important;
            font-weight: 900;
        }
        .login-title {
            color: #f6f8ff !important;
            font: 700 2.2rem 'Space Grotesk', sans-serif;
            letter-spacing: -.05em;
            margin: 30px 0 8px;
        }
        .login-subtitle {
            color: #8996ad !important;
            line-height: 1.6;
            margin-bottom: 25px;
        }
        .login-label {
            color: #b7c3d8 !important;
            font-size: .78rem;
            font-weight: 700;
            letter-spacing: .08em;
            text-transform: uppercase;
            margin: 14px 0 7px;
        }
        .stTextInput input {
            background: rgba(7, 17, 31, .92) !important;
            color: #f3f7ff !important;
            border: 1px solid rgba(137, 154, 184, .22) !important;
            border-radius: 12px !important;
        }
        .stTextInput input:focus {
            border-color: #00d9ff !important;
            box-shadow: 0 0 0 1px rgba(0, 217, 255, .25), 0 0 25px rgba(0, 217, 255, .08) !important;
        }
        .login-foot {
            color: #65738b !important;
            text-align: center;
            font-size: .72rem;
            margin-top: 22px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="login-shell">
            <div class="login-logo">
                <div class="login-orb">F</div>
                FINSIGHT
            </div>
            <div class="login-title">Welcome back.</div>
            <div class="login-subtitle">
                Sign in to access your invoice intelligence workspace.
            </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("finsight_login", clear_on_submit=False):
        st.markdown('<div class="login-label">Email</div>', unsafe_allow_html=True)
        email = st.text_input(
            "Email",
            label_visibility="collapsed",
            placeholder="you@example.com",
            autocomplete="username",
        )
        st.markdown('<div class="login-label">Password</div>', unsafe_allow_html=True)
        password = st.text_input(
            "Password",
            type="password",
            label_visibility="collapsed",
            placeholder="Enter your password",
            autocomplete="current-password",
        )
        submitted = st.form_submit_button("Sign in to FinSight", type="primary", width="stretch")

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
        <div class="login-foot">
            FINsight · AP intelligence · Secure workspace
        </div>
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
