"""
Small compatibility layer so the app works on both older and newer Streamlit
versions. Newer releases replaced `use_container_width=True` with
`width="stretch"`; this helper picks whichever the installed version supports.
"""

import streamlit as st


def _version():
    try:
        parts = st.__version__.split(".")
        return int(parts[0]), int(parts[1])
    except Exception:
        return 1, 0


_NEW_WIDTH_API = _version() >= (1, 50)


def show_chart(fig):
    """Render a Plotly figure at full container width."""
    try:
        if _NEW_WIDTH_API:
            st.plotly_chart(fig, width="stretch")
        else:
            st.plotly_chart(fig, use_container_width=True)
    except Exception:
        st.plotly_chart(fig)


def show_table(df, height=None):
    """Render a DataFrame at full container width without the index column."""
    kwargs = {"hide_index": True}
    if height:
        kwargs["height"] = height
    try:
        if _NEW_WIDTH_API:
            st.dataframe(df, width="stretch", **kwargs)
        else:
            st.dataframe(df, use_container_width=True, **kwargs)
    except Exception:
        st.dataframe(df)
