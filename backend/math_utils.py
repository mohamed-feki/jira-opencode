import math


def calculate_square_root(number: float) -> float:
    """
    Calculate and return the square root of a real number.

    Args:
        number: A non-negative real number.

    Returns:
        The square root of the input number.

    Raises:
        ValueError: If the input number is negative.
    """
    if number < 0:
        raise ValueError(
            f"Cannot calculate square root of negative number: {number}"
        )

    return math.sqrt(number)


def extract_integer_part(number: float) -> int:
    """
    Extract and return the integer part of a given real number.

    Truncates the fractional part, rounding toward zero.

    Args:
        number: A real (floating-point) number.

    Returns:
        The integer part of the input number as an int.
    """
    return int(number)
