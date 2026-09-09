import streamlit as st
from utils.icons import ICONS
import pandas as pd
import altair as alt
from services import github_service, session_service
from utils import format_number, format_timestamp, get_logger, get_language_color

logger = get_logger(__name__)

def render_dashboard(username: str):
    """Render comprehensive analytics dashboard for the selected GitHub account."""
    with st.spinner(f"Analyzing GitHub profile @{username} via MCP tools..."):
        metrics = github_service.get_dashboard_metrics(username)

    if not metrics:
        st.error(f" Could not retrieve profile data for **@{username}**. Please check if the username exists or if your GitHub token has exceeded rate limits.")
        if st.button("⬅️ Back to Search"):
            session_service.set_username(None)
            st.rerun()
        return

    user = metrics.user
    stats = metrics.stats

    # ==========================================
    # 1. Profile Banner & Metadata
    # ==========================================
    avatar = user.avatar_url or "https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png"
    _bldg = ICONS["building"]
    company = f'<img src="{_bldg}"> {user.company}' if user.company else ""
    _mpin = ICONS["map_pin"]
    location = f'<img src="{_mpin}"> {user.location}' if user.location else ""
    _lnk = ICONS["link"]
    blog = f'<img src="{_lnk}"> <a href="{user.blog}" target="_blank" style="color:#58a6ff;">Website</a>' if user.blog else ""
    
    st.markdown(
        f"""
        <div class="profile-card">
            <img src="{avatar}" class="profile-avatar" alt="Avatar"/>
            <div class="profile-name">{user.display_name}</div>
            <div class="profile-username"><a href="https://github.com/{user.login}" target="_blank" style="color:#58a6ff; text-decoration:none;">@{user.login}</a></div>
            <div class="profile-bio">{user.bio or 'No biographical summary provided.'}</div>
            <div class="profile-meta">
                <span class="meta-item"><img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNCIgaGVpZ2h0PSIxNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiM4Yjk0OWUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48cGF0aCBkPSJNMTYgMjF2LTJhNCA0IDAgMCAwLTQtNEg2YTQgNCAwIDAgMC00IDR2MiIvPjxjaXJjbGUgY3g9IjkiIGN5PSI3IiByPSI0Ii8+PHBhdGggZD0iTTIyIDIxdi0yYTQgNCAwIDAgMC0zLTMuODciLz48cGF0aCBkPSJNMTYgMy4xM2E0IDQgMCAwIDEgMCA3Ljc1Ii8+PC9zdmc+"> <b>{format_number(user.followers)}</b> Followers</span>
                <span class="meta-item"><img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNCIgaGVpZ2h0PSIxNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiM4Yjk0OWUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48cGF0aCBkPSJNMTYgMjF2LTJhNCA0IDAgMCAwLTQtNEg2YTQgNCAwIDAgMC00IDR2MiIvPjxjaXJjbGUgY3g9IjkiIGN5PSI3IiByPSI0Ii8+PHBhdGggZD0iTTIyIDIxdi0yYTQgNCAwIDAgMC0zLTMuODciLz48cGF0aCBkPSJNMTYgMy4xM2E0IDQgMCAwIDEgMCA3Ljc1Ii8+PC9zdmc+"> <b>{format_number(user.following)}</b> Following</span>
                {f'<span class="meta-item">{company}</span>' if company else ''}
                {f'<span class="meta-item">{location}</span>' if location else ''}
                {f'<span class="meta-item">{blog}</span>' if blog else ''}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")

    # ==========================================
    # 2. Key Metrics Grid
    # ==========================================
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    with m_col1:
        st.markdown(f'<div class="metric-box"><div class="metric-value">{stats.total_repos}</div><div class="metric-label">Public Repositories</div></div>', unsafe_allow_html=True)
    with m_col2:
        st.markdown(f'<div class="metric-box"><div class="metric-value"><img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSIjZTNiMzQxIiBzdHJva2U9IiNlM2IzNDEiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48cG9seWdvbiBwb2ludHM9IjEyIDIgMTUuMDkgOC4yNiAyMiA5LjI3IDE3IDE0LjE0IDE4LjE4IDIxLjAyIDEyIDE3Ljc3IDUuODIgMjEuMDIgNyAxNC4xNCAyIDkuMjcgOC45MSA4LjI2IDEyIDIiLz48L3N2Zz4="> {format_number(stats.total_stars)}</div><div class="metric-label">Total Stars</div></div>', unsafe_allow_html=True)
    with m_col3:
        st.markdown(f'<div class="metric-box"><div class="metric-value">⑂ {format_number(stats.total_forks)}</div><div class="metric-label">Total Forks</div></div>', unsafe_allow_html=True)
    with m_col4:
        st.markdown(f'<div class="metric-box"><div class="metric-value">{len(metrics.orgs)}</div><div class="metric-label">Organizations</div></div>', unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    # ==========================================
    # 3. Language Distribution Chart
    # ==========================================
    st.subheader(" Programming Language Breakdown")
    if metrics.language_breakdown:
        df_langs = pd.DataFrame([
            {"Language": l.language, "Repositories": l.count, "Percentage": l.percentage, "Color": l.color}
            for l in metrics.language_breakdown
        ])
        
        # Interactive Altair Bar Chart
        chart = alt.Chart(df_langs).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6).encode(
            x=alt.X('Percentage:Q', title='Percentage of Repositories (%)'),
            y=alt.Y('Language:N', sort='-x', title=None),
            color=alt.Color('Language:N', scale=alt.Scale(domain=df_langs['Language'].tolist(), range=df_langs['Color'].tolist()), legend=None),
            tooltip=['Language', 'Repositories', alt.Tooltip('Percentage:Q', format='.1f')]
        ).properties(height=220).configure_view(strokeWidth=0).configure_axis(
            labelColor="#8b949e", titleColor="#c9d1d9", gridColor="#21262d"
        )
        st.altair_chart(chart, use_container_width=True)

        # Language Badges
        badges_html = " ".join([
            f'<span class="badge-language"><span class="lang-dot" style="background:{l.color};"></span><b>{l.language}</b> ({l.percentage}%)</span>'
            for l in metrics.language_breakdown[:10]
        ])
        st.markdown(f'<div style="margin-top:0.5rem; margin-bottom:1.5rem;">{badges_html}</div>', unsafe_allow_html=True)
    else:
        st.info("No language data detected in public repositories.")

    # ==========================================
    # 4. Top Repositories Grid
    # ==========================================
    st.subheader(" Top Starred Repositories")
    if stats.top_repos:
        repo_cols = st.columns(3)
        for idx, repo in enumerate(stats.top_repos):
            with repo_cols[idx % 3]:
                lang_color = repo.language and get_language_color(repo.language) or "#8a94a6"
                desc = repo.description or "No repository description available."
                desc_short = desc[:90] + "..." if len(desc) > 90 else desc
                
                st.markdown(
                    f"""
                    <div class="repo-card" style="margin-bottom:1rem;">
                        <div>
                            <div class="repo-title">
                                <a href="https://github.com/{repo.full_name}" target="_blank" style="color:#58a6ff; text-decoration:none;"> {repo.name}</a>
                            </div>
                            <div class="repo-desc">{desc_short}</div>
                        </div>
                        <div class="repo-stats">
                            <span><span class="lang-dot" style="background:{lang_color};"></span> {repo.language or 'Unknown'}</span>
                            <span> {format_number(repo.stargazers_count)}</span>
                            <span>⑂ {format_number(repo.forks_count)}</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                # Button to set repository as conversation focus
                is_selected = session_service.selected_repository == repo.name
                btn_label = " Active Focus" if is_selected else f" Focus in Chat"
                btn_type = "primary" if is_selected else "secondary"
                if st.button(btn_label, key=f"focus_btn_{repo.id}", type=btn_type, use_container_width=True):
                    if is_selected:
                        session_service.set_repository(None)
                        st.toast(f"Removed focus from {repo.name}")
                    else:
                        session_service.set_repository(repo.name)
                        st.toast(f"Locked conversation focus to repo: {repo.name}")
                    st.rerun()
    else:
        st.info("No public repositories found for this account.")

    # ==========================================
    # 5. Organizations & Recent Activity Expanders
    # ==========================================
    col_exp1, col_exp2 = st.columns(2)
    with col_exp1:
        with st.expander(" Affiliated Organizations", expanded=False):
            if metrics.orgs:
                for org in metrics.orgs:
                    st.markdown(f"**[{org.login}](https://github.com/{org.login})** — *{org.description or 'No description'}*")
            else:
                st.write("No public organization memberships found.")
                
    with col_exp2:
        with st.expander(" Recent Public Activity", expanded=False):
            if metrics.recent_activity:
                for act in metrics.recent_activity[:6]:
                    repo_name = act.repo.get("name", "unknown")
                    ts = format_timestamp(act.created_at)
                    st.markdown(f"- **{act.type.replace('Event', '')}** on `{repo_name}` *({ts})*")
            else:
                st.write("No recent public activity events found.")
