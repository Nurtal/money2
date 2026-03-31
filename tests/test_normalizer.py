from datetime import date

import pytest

from utils.normalizer import normalize_amount, normalize_date


class TestNormalizeAmount:
    def test_plain_amount(self):
        assert normalize_amount("2 000 000 €") == (2000000.0, 2000000.0)

    def test_max_only(self):
        _, mx = normalize_amount("jusqu'à 2M€")
        assert mx == 2_000_000.0

    def test_range(self):
        mn, mx = normalize_amount("200 000 € à 500 000 €")
        assert mn == 200_000.0
        assert mx == 500_000.0

    def test_k_suffix(self):
        assert normalize_amount("300K€") == (300_000.0, 300_000.0)

    def test_none_input(self):
        assert normalize_amount(None) == (None, None)

    def test_empty(self):
        assert normalize_amount("") == (None, None)


class TestNormalizeDate:
    def test_slash_format(self):
        assert normalize_date("30/06/2025") == date(2025, 6, 30)

    def test_iso_format(self):
        assert normalize_date("2025-06-30") == date(2025, 6, 30)

    def test_french_full(self):
        assert normalize_date("30 juin 2025") == date(2025, 6, 30)

    def test_french_month_year(self):
        assert normalize_date("juin 2025") == date(2025, 6, 1)

    def test_none_input(self):
        assert normalize_date(None) is None
