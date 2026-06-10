"""REST API service for the pfev2 engine.

Phase 1 of the Streamlit-to-SPA migration: a FastAPI layer that exposes the
instrument/modifier registry, T0 MtM previews, and asynchronous PFE runs over
HTTP. Requires the ``api`` extra (``pip3 install -e ".[api]"``).

Launch with:

    python3 -m uvicorn api.app:app --reload
"""
