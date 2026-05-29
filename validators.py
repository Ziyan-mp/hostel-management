"""
Hostel Management System - Input Validators
Provides strict validation functions for all user inputs.
"""
import re


def validate_name(name: str) -> tuple[bool, str]:
    """
    Validate a person's name.
    Rules: Only letters and spaces, minimum 2 characters.
    Returns (is_valid, error_message)
    """
    name = name.strip()
    if len(name) < 2:
        return False, "Name must be at least 2 characters long."
    if not re.match(r'^[A-Za-z\s]+$', name):
        return False, "Name can only contain letters and spaces."
    return True, ""


def validate_phone(phone: str) -> tuple[bool, str]:
    """
    Validate a phone/contact number.
    Rules: Exactly 10 digits.
    Returns (is_valid, error_message)
    """
    phone = phone.strip()
    if not re.match(r'^\d{10}$', phone):
        return False, "Contact must be exactly 10 digits (numbers only)."
    return True, ""


def validate_email(email: str) -> tuple[bool, str]:
    """
    Validate an email address.
    Rules: Must follow standard email format.
    Returns (is_valid, error_message)
    """
    email = email.strip()
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if not re.match(pattern, email):
        return False, "Invalid email format (e.g. user@example.com)."
    return True, ""


def validate_amount(amount: str) -> tuple[bool, str]:
    """
    Validate a payment amount.
    Rules: Must be numeric and positive.
    Returns (is_valid, float_value_or_None, error_message)
    """
    amount = amount.strip()
    try:
        value = float(amount)
        if value <= 0:
            return False, "Amount must be a positive number."
        return True, str(value)
    except ValueError:
        return False, "Amount must be a valid number (e.g. 5000 or 5000.50)."


def validate_room_number(room_no: str) -> tuple[bool, str]:
    """
    Validate a room number.
    Rules: Non-empty, alphanumeric.
    Returns (is_valid, error_message)
    """
    room_no = room_no.strip()
    if not room_no:
        return False, "Room number cannot be empty."
    if not re.match(r'^[A-Za-z0-9\-]+$', room_no):
        return False, "Room number can only contain letters, numbers, and hyphens."
    return True, ""


def validate_reg_no(reg_no: str) -> tuple[bool, str]:
    """
    Validate a registration number.
    Rules: Non-empty, alphanumeric.
    Returns (is_valid, error_message)
    """
    reg_no = reg_no.strip()
    if not reg_no:
        return False, "Registration number cannot be empty."
    if not re.match(r'^[A-Za-z0-9\-/]+$', reg_no):
        return False, "Registration number can only contain letters, numbers, hyphens, and slashes."
    return True, ""


def validate_required(value: str, field_name: str) -> tuple[bool, str]:
    """
    Validate that a required field is not empty.
    Returns (is_valid, error_message)
    """
    if not value or not value.strip():
        return False, f"{field_name} is required."
    return True, ""
