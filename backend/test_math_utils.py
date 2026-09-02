import pytest
import math

from math_utils import calculate_square_root


def test_perfect_square():
    """Test square root of a perfect square."""
    assert calculate_square_root(4.0) == 2.0
    assert calculate_square_root(9.0) == 3.0
    assert calculate_square_root(16.0) == 4.0
    assert calculate_square_root(25.0) == 5.0


def test_non_perfect_square():
    """Test square root of a non-perfect square."""
    result = calculate_square_root(2.0)
    assert abs(result - math.sqrt(2.0)) < 1e-10

    result = calculate_square_root(3.0)
    assert abs(result - math.sqrt(3.0)) < 1e-10


def test_zero():
    """Test square root of zero."""
    assert calculate_square_root(0.0) == 0.0


def test_one():
    """Test square root of one."""
    assert calculate_square_root(1.0) == 1.0


def test_decimal_numbers():
    """Test square root of decimal numbers."""
    result = calculate_square_root(0.25)
    assert abs(result - 0.5) < 1e-10

    result = calculate_square_root(2.5)
    assert abs(result - math.sqrt(2.5)) < 1e-10


def test_large_number():
    """Test square root of a large number."""
    result = calculate_square_root(1000000.0)
    assert abs(result - 1000.0) < 1e-10


def test_negative_number_raises_error():
    """Test that negative numbers raise ValueError."""
    with pytest.raises(ValueError):
        calculate_square_root(-1.0)

    with pytest.raises(ValueError):
        calculate_square_root(-0.5)
