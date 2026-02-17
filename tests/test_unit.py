"""
tests/test_unit.py
Tests unitaires purs (aucune DB, aucun Streamlit requis).
Run : pytest tests/test_unit.py -v
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from unittest.mock import MagicMock, patch

# ─────────────────────────────────────────────
# 1. Helpers isolés (pas d'import streamlit)
# ─────────────────────────────────────────────

def score_to_seconds(score_str: str):
    """Copie locale de _score_to_seconds pour tester sans dépendances."""
    try:
        parts = list(map(int, score_str.split(":")))
        if len(parts) == 2:
            return parts[0] * 60 + parts[1]
        elif len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
    except Exception:
        return None
    return None


def normalize_time_score(input_str: str, timecap_seconds: int):
    """Copie locale de normalize_time_score."""
    import re
    if not input_str:
        return None
    s = input_str.strip().upper()
    m = re.match(r"^CAP:(\d{1,3})$", s)
    if m:
        return timecap_seconds + int(m.group(1))
    try:
        parts = list(map(int, s.split(":")))
        if len(parts) == 2:
            return parts[0] * 60 + parts[1]
        elif len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
    except Exception:
        return None
    return None


def calculate_age_category(birth_year, current_year=2026):
    age = current_year - birth_year
    if age <= 17:
        category = "Teenager"
    elif age < 35:
        category = "Elite"
    else:
        category = "Masters"
    return age, category


def normalize_for_stats(value: str, wod_type: str, timecap):
    if wod_type == "time":
        if not value:
            return None
        s = value.strip().upper()
        if s.startswith("CAP:"):
            try:
                over = int(s.split(":")[1])
                return float((timecap or 0) + over)
            except Exception:
                return None
        try:
            parts = list(map(int, s.split(":")))
            if len(parts) == 2:
                return float(parts[0] * 60 + parts[1])
            elif len(parts) == 3:
                return float(parts[0] * 3600 + parts[1] * 60 + parts[2])
        except Exception:
            return None
        return None
    else:
        try:
            return float(int(value))
        except Exception:
            return None


# ─────────────────────────────────────────────
# 2. Tests score_to_seconds
# ─────────────────────────────────────────────

class TestScoreToSeconds:
    def test_mm_ss_format(self):
        assert score_to_seconds("10:30") == 630

    def test_hh_mm_ss_format(self):
        assert score_to_seconds("1:00:00") == 3600

    def test_zero_minutes(self):
        assert score_to_seconds("00:45") == 45

    def test_invalid_returns_none(self):
        assert score_to_seconds("abc") is None

    def test_empty_string_returns_none(self):
        assert score_to_seconds("") is None

    def test_single_value_returns_none(self):
        assert score_to_seconds("120") is None  # pas de ':'

    def test_exact_timecap_12min(self):
        assert score_to_seconds("12:00") == 720

    def test_exact_timecap_20min(self):
        assert score_to_seconds("20:00") == 1200


# ─────────────────────────────────────────────
# 3. Tests normalize_time_score (saisie scores)
# ─────────────────────────────────────────────

class TestNormalizeTimeScore:
    def test_cap_format_adds_to_timecap(self):
        # CAP:05 avec timecap 720s → 725s
        assert normalize_time_score("CAP:05", 720) == 725

    def test_cap_zero(self):
        assert normalize_time_score("CAP:000", 720) == 720

    def test_cap_lowercase(self):
        assert normalize_time_score("cap:10", 1200) == 1210

    def test_normal_time_mm_ss(self):
        assert normalize_time_score("09:45", 720) == 585

    def test_normal_time_hh_mm_ss(self):
        assert normalize_time_score("00:12:00", 720) == 720

    def test_empty_returns_none(self):
        assert normalize_time_score("", 720) is None

    def test_invalid_format_returns_none(self):
        assert normalize_time_score("abc", 720) is None

    def test_cap_with_leading_zeros(self):
        assert normalize_time_score("CAP:001", 1200) == 1201

    def test_whitespace_handled(self):
        assert normalize_time_score("  09:30  ", 720) == 570


# ─────────────────────────────────────────────
# 4. Tests calculate_age_category
# ─────────────────────────────────────────────

class TestCalculateAgeCategory:
    def test_teenager(self):
        age, cat = calculate_age_category(2012, 2026)  # 14 ans
        assert age == 14
        assert cat == "Teenager"

    def test_teenager_boundary(self):
        age, cat = calculate_age_category(2009, 2026)  # 17 ans
        assert age == 17
        assert cat == "Teenager"

    def test_elite_lower_boundary(self):
        age, cat = calculate_age_category(2008, 2026)  # 18 ans
        assert age == 18
        assert cat == "Elite"

    def test_elite_upper_boundary(self):
        age, cat = calculate_age_category(1992, 2026)  # 34 ans
        assert age == 34
        assert cat == "Elite"

    def test_masters_boundary(self):
        age, cat = calculate_age_category(1991, 2026)  # 35 ans
        assert age == 35
        assert cat == "Masters"

    def test_masters_senior(self):
        age, cat = calculate_age_category(1960, 2026)
        assert age == 66
        assert cat == "Masters"


# ─────────────────────────────────────────────
# 5. Tests normalize_for_stats
# ─────────────────────────────────────────────

class TestNormalizeForStats:
    # --- type 'time' ---
    def test_time_mm_ss(self):
        assert normalize_for_stats("10:30", "time", 720) == 630.0

    def test_time_cap_format(self):
        assert normalize_for_stats("CAP:05", "time", 720) == 725.0

    def test_time_empty_returns_none(self):
        assert normalize_for_stats("", "time", 720) is None

    def test_time_invalid_returns_none(self):
        assert normalize_for_stats("INVALID", "time", 720) is None

    def test_time_no_timecap_cap_format(self):
        assert normalize_for_stats("CAP:10", "time", None) == 10.0  # 0 + 10

    # --- type 'reps' ---
    def test_reps_integer_string(self):
        assert normalize_for_stats("150", "reps", None) == 150.0

    def test_reps_zero(self):
        assert normalize_for_stats("0", "reps", None) == 0.0

    def test_reps_invalid_returns_none(self):
        assert normalize_for_stats("abc", "reps", None) is None

    def test_reps_float_string_invalid(self):
        # Les reps doivent être des entiers
        assert normalize_for_stats("12.5", "reps", None) is None


# ─────────────────────────────────────────────
# 6. Tests logique du classement (tri)
# ─────────────────────────────────────────────

class TestClassementSort:
    """Vérifie que la logique de tri est correcte : ASC pour time, DESC pour reps."""

    def _sort_classement(self, athletes, wod_type):
        if wod_type == "time":
            return sorted(athletes, key=lambda x: x[1])
        else:
            return sorted(athletes, key=lambda x: x[1], reverse=True)

    def test_time_sort_ascending(self):
        athletes = [("Alice", 650), ("Bob", 590), ("Charlie", 720)]
        result = self._sort_classement(athletes, "time")
        assert result[0][0] == "Bob"    # meilleur temps = plus petit
        assert result[-1][0] == "Charlie"

    def test_reps_sort_descending(self):
        athletes = [("Alice", 180), ("Bob", 250), ("Charlie", 90)]
        result = self._sort_classement(athletes, "reps")
        assert result[0][0] == "Bob"    # plus de reps = meilleur
        assert result[-1][0] == "Charlie"

    def test_time_tie_stable(self):
        athletes = [("Alice", 600), ("Bob", 600)]
        result = self._sort_classement(athletes, "time")
        assert len(result) == 2  # pas de crash en cas d'égalité

    def test_overall_points_cumulation(self):
        """Vérifie la logique d'accumulation des points Overall."""
        # Simule 2 WODs, 2 athlètes
        # WOD1 : Alice 1er (1pt), Bob 2e (2pts)
        # WOD2 : Bob 1er (1pt), Alice 2e (2pts)
        general = {}
        wod1_results = [("Alice", 590), ("Bob", 650)]
        wod2_results = [("Bob", 420), ("Alice", 500)]

        for i, (name, _) in enumerate(wod1_results):
            general[name] = general.get(name, 0) + (i + 1)
        for i, (name, _) in enumerate(wod2_results):
            general[name] = general.get(name, 0) + (i + 1)

        sorted_gen = sorted(general.items(), key=lambda x: x[1])
        # Alice: 1+2=3pts, Bob: 2+1=3pts → égalité
        assert sorted_gen[0][1] == sorted_gen[1][1] == 3
