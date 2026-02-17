# tests/test_e2e.py

import os
import re
import time

import pytest
from playwright.sync_api import Page, expect

BASE_URL = os.getenv("APP_URL", "http://localhost:8501")
TIMEOUT = 20_000  # ms

pytestmark = pytest.mark.tryfirst

TEST_PASSWORD = "TestPassword2026!"
TEST_WRONG_PASSWORD = "WrongPassword!"
TEST_NAME = "E2E Testeur"


def _register_user(page: Page, email: str, password: str):
    """Helper function to register a new user, and then log out."""
    page.goto(f"{BASE_URL}/Authentification")

    register_form = page.locator('[data-testid="stForm"]').filter(has_text="S'inscrire")
    register_form.get_by_label("Nom complet").fill(TEST_NAME)
    register_form.get_by_label("Email").fill(email)
    register_form.get_by_label("Mot de passe").fill(password)
    register_form.get_by_text("Male", exact=True).click()
    register_form.get_by_label("Année de naissance").fill("1990")
    register_form.get_by_text("RX", exact=True).click()

    register_form.get_by_role("button", name="S'inscrire").click()

    # Streamlit utilise WebSocket pour les reruns, networkidle ne suffit pas.
    # On attend un élément présent sur Home pour confirmer la redirection.
    expect(page.get_by_role("heading", name="2026 CrossFit Games Open")).to_be_visible(timeout=TIMEOUT)

    # Se déconnecter pour préparer la phase de connexion du test
    sidebar = page.locator('[data-testid="stSidebar"]')
    sidebar.get_by_role("button", name="Se déconnecter").click()
    # FIX: attendre le rerun Streamlit après déconnexion
    page.wait_for_load_state("networkidle")
    expect(page).to_have_url(re.compile(r".*/Authentification$"), timeout=TIMEOUT)


# --- Fixture d'Authentification ---
@pytest.fixture(scope="function")
def authenticated_page(page: Page):
    """
    Fixture qui INSCRIT puis CONNECTE un utilisateur unique et retourne la page.
    """
    email = f"fixture_{time.time_ns()}@crossfit-test.fr"

    _register_user(page, email=email, password=TEST_PASSWORD)

    login_form = page.locator('[data-testid="stForm"]').filter(has_text="Se connecter")
    login_form.get_by_label("Email").fill(email)
    login_form.get_by_label("Mot de passe").fill(TEST_PASSWORD)
    login_form.get_by_role("button", name="Se connecter").click()

    # Même logique : attendre un élément de Home plutôt que l'URL
    expect(page.get_by_role("heading", name="2026 CrossFit Games Open")).to_be_visible(timeout=TIMEOUT)
    return page


# --- Tests ---


class TestAuthFlow:
    def test_auth_page_loads(self, page: Page):
        """Vérifie que la page d'authentification se charge."""
        page.goto(f"{BASE_URL}/Authentification")
        expect(page.get_by_role("heading", name="S'inscrire")).to_be_visible()
        expect(page.get_by_role("heading", name="Ou se connecter")).to_be_visible()

    def test_login_flow_redirects_to_home(self, page: Page):
        """Vérifie que le login réussit et redirige vers la page d'accueil."""
        email = f"test_login_{time.time_ns()}@crossfit-test.fr"
        _register_user(page, email=email, password=TEST_PASSWORD)

        login_form = page.locator('[data-testid="stForm"]').filter(has_text="Se connecter")
        login_form.get_by_label("Email").fill(email)
        login_form.get_by_label("Mot de passe").fill(TEST_PASSWORD)
        login_form.get_by_role("button", name="Se connecter").click()

        # Attendre un élément de Home pour confirmer la redirection
        expect(page.get_by_role("heading", name="2026 CrossFit Games Open")).to_be_visible(timeout=TIMEOUT)
        sidebar = page.locator('[data-testid="stSidebar"]')
        expect(sidebar.get_by_text("Connecté en tant que")).to_be_visible()

    def test_wrong_password_shows_error(self, page: Page):
        """Vérifie qu'un mauvais mot de passe affiche une erreur."""
        email = f"test_wrong_pass_{time.time_ns()}@crossfit-test.fr"
        _register_user(page, email=email, password=TEST_PASSWORD)

        login_form = page.locator('[data-testid="stForm"]').filter(has_text="Se connecter")
        login_form.get_by_label("Email").fill(email)
        login_form.get_by_label("Mot de passe").fill(TEST_WRONG_PASSWORD)
        login_form.get_by_role("button", name="Se connecter").click()

        page.wait_for_load_state("networkidle")
        expect(page.get_by_text("Email ou mot de passe incorrect.")).to_be_visible()
        expect(page).to_have_url(re.compile(r".*/Authentification$"))

    def test_logout_flow_redirects_to_auth_page(self, authenticated_page: Page):
        """Vérifie le cycle de déconnexion depuis une page authentifiée."""
        page = authenticated_page
        sidebar = page.locator('[data-testid="stSidebar"]')
        logout_btn = sidebar.get_by_role("button", name="Se déconnecter")
        expect(logout_btn).to_be_visible()
        logout_btn.click()
        # FIX: attendre le rerun Streamlit après déconnexion
        page.wait_for_load_state("networkidle")
        expect(page).to_have_url(re.compile(r".*/Authentification$"), timeout=TIMEOUT)
        expect(page.get_by_text("Ou se connecter")).to_be_visible()


class TestPageProtection:
    def test_home_page_is_public(self, page: Page):
        """Vérifie que la page d'accueil est accessible sans connexion."""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        expect(
            page.get_by_text("Veuillez vous connecter pour accéder à cette page.")
        ).not_to_be_visible()
        expect(page.get_by_role("heading", name="2026 CrossFit Games Open")).to_be_visible()

    def test_saisie_scores_page_requires_auth(self, page: Page):
        """Vérifie qu'une autre page protégée (ex: Saisie_scores) l'est aussi."""
        page.goto(f"{BASE_URL}/Saisie_scores")
        page.wait_for_load_state("networkidle")
        expect(
            page.get_by_text("Veuillez vous connecter pour accéder à cette page.")
        ).to_be_visible()

    def test_can_access_protected_page_when_logged_in(self, authenticated_page: Page):
        """Vérifie qu'un utilisateur connecté peut voir le contenu de Saisie_scores."""
        page = authenticated_page
        page.goto(f"{BASE_URL}/Saisie_scores")
        page.wait_for_load_state("networkidle")
        expect(page.get_by_text("Veuillez vous connecter")).not_to_be_visible()
        expect(page.get_by_text("Saisie des Scores")).to_be_visible()
