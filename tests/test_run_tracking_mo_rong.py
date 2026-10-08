"""Unit test cho module run_tracking_mo_rong.

Kiểm tra các hàm thuần: parse_override_value, parse_override, và parse_overrides.
Không dùng GPU, ảnh lab hay mạng.
"""

from __future__ import annotations

import pytest

from run_tracking_mo_rong import (
    parse_override,
    parse_override_value,
    parse_overrides,
)


def test_parse_override_value_types() -> None:
    """Kiểm tra ép kiểu các chuỗi số nguyên, số thực, boolean và xâu ký tự."""
    assert parse_override_value("3") == 3
    assert isinstance(parse_override_value("3"), int)

    assert parse_override_value("0.75") == pytest.approx(0.75)
    assert isinstance(parse_override_value("0.75"), float)

    assert parse_override_value("true") is True
    assert parse_override_value("True") is True
    assert parse_override_value("false") is False

    assert parse_override_value("custom_text") == "custom_text"


def test_parse_override_valid() -> None:
    """Tách đúng cặp key=value hợp lệ."""
    key, val = parse_override("min_hits=3")
    assert key == "min_hits"
    assert val == 3

    key, val = parse_override("n_init=2")
    assert key == "n_init"
    assert val == 2

    key, val = parse_override("ema_alpha=0.9")
    assert key == "ema_alpha"
    assert val == pytest.approx(0.9)


def test_parse_override_invalid_format() -> None:
    """Báo lỗi ValueError khi định dạng chuỗi sai."""
    with pytest.raises(ValueError, match="Định dạng override phải là key=value"):
        parse_override("min_hits_without_equal")

    with pytest.raises(ValueError, match="Khóa trong override không được để trống"):
        parse_override("=3")


def test_parse_overrides_list() -> None:
    """Chuyển đổi danh sách các chuỗi override thành dictionary hoàn chỉnh."""
    overrides = parse_overrides(["min_hits=2", "max_age=30", "use_byte=false"])
    assert overrides == {
        "min_hits": 2,
        "max_age": 30,
        "use_byte": False,
    }

    assert parse_overrides([]) == {}
    assert parse_overrides(None) == {}
