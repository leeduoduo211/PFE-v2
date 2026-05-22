"""Small helpers for Streamlit navigation workarounds."""


def tab_switch_script(tab_index: int, minimum_tabs: int) -> str:
    """Return JS that clicks a Streamlit tab after rerun, retrying briefly."""
    return f"""
    <script>
    const clickTargetTab = () => {{
        const tabs = window.parent.document.querySelectorAll('button[data-baseweb="tab"]');
        if (tabs.length >= {minimum_tabs}) {{
            tabs[{tab_index}].click();
            return true;
        }}
        return false;
    }};
    if (!clickTargetTab()) {{
        let tries = 0;
        const timer = window.setInterval(() => {{
            tries += 1;
            if (clickTargetTab() || tries >= 20) {{
                window.clearInterval(timer);
            }}
        }}, 50);
    }}
    </script>
    """
