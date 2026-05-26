import streamlit as st
from auth import authenticate, create_account
import jobseeker_portal
import hr_portal

st.set_page_config(
    page_title="AI Resume Screener",
    page_icon="🤖",
    layout="centered"
)

st.markdown("""
<style>
    body, .main { background-color: #0f0f0f; color: white; }
</style>
""", unsafe_allow_html=True)

# ── SESSION STATE ──
for key, val in {
    "logged_in": False,
    "role": None,
    "icon": None,
    "show_signup": False
}.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ── LOGGED IN → ROUTE TO PORTAL ──
if st.session_state.logged_in:
    with st.sidebar:
        st.markdown(f"### {st.session_state.icon} {st.session_state.role}")
        st.caption(f"Logged in as: **{st.session_state.username}**")
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            for key in ["logged_in", "role", "icon", "username"]:
                st.session_state[key] = None
            st.session_state.logged_in = False
            st.rerun()

    if st.session_state.role == "Job Seeker":
        jobseeker_portal.render()
    elif st.session_state.role == "HR Recruiter":
        hr_portal.render()

# ── NOT LOGGED IN ──
else:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style='background:#1a1a2e;border:2px solid #9b59b6;border-radius:16px;
                padding:36px;text-align:center;margin-bottom:24px'>
        <h1 style='color:white'>🤖 AI Resume Screener</h1>
        <p style='color:#aaa;font-size:15px'>Powered by BERT Semantic Matching + Claude AI</p>
    </div>
    """, unsafe_allow_html=True)

    # Toggle between Login and Sign Up
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Create Account"])

    # ── LOGIN TAB ──
    with tab1:
        st.markdown("### Welcome back!")
        username = st.text_input("Username", key="login_user", placeholder="Enter your username")
        password = st.text_input("Password", type="password", key="login_pass", placeholder="••••••••")

        if st.button("Login →", use_container_width=True, type="primary", key="login_btn"):
            if not username.strip() or not password.strip():
                st.error("❌ Please fill in both fields.")
            else:
                success, role, icon = authenticate(username, password)
                if success:
                    st.session_state.logged_in = True
                    st.session_state.role = role
                    st.session_state.icon = icon
                    st.session_state.username = username
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password.")

    # ── SIGN UP TAB ──
    with tab2:
        st.markdown("### Create your account")
        new_user = st.text_input("Choose a Username", key="signup_user", placeholder="e.g. newshika")
        new_pass = st.text_input("Choose a Password", type="password", key="signup_pass", placeholder="Min 6 characters")
        confirm_pass = st.text_input("Confirm Password", type="password", key="signup_confirm", placeholder="Re-enter password")
        new_role = st.selectbox("I am a...", ["Job Seeker", "HR Recruiter"], key="signup_role")

        st.caption("👤 Job Seeker — analyze & improve your own resume\n\n🏢 HR Recruiter — screen & rank multiple candidates")

        if st.button("Create Account →", use_container_width=True, type="primary", key="signup_btn"):
            if not new_user.strip() or not new_pass.strip():
                st.error("❌ Please fill in all fields.")
            elif len(new_pass) < 6:
                st.error("❌ Password must be at least 6 characters.")
            elif new_pass != confirm_pass:
                st.error("❌ Passwords do not match.")
            else:
                success, message = create_account(new_user, new_pass, new_role)
                if success:
                    st.success(message)
                    st.info("👆 Go to the Login tab to sign in.")
                else:
                    st.error(message)