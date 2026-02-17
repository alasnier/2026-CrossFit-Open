# tests/conftest.py
"""
Configuration pytest partagée.
"""
import os
import sys

# Assure que la racine du projet est dans le path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock streamlit pour les imports qui l'utilisent au module level
import unittest.mock as mock

# Streamlit ne doit pas se lancer dans les tests
streamlit_mock = mock.MagicMock()
streamlit_mock.secrets = {"database": {}}
sys.modules.setdefault("streamlit", streamlit_mock)
