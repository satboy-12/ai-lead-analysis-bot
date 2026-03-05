"""Generate synthetic lead data for analysis.

This module creates realistic and varied lead data with 50,000 records
including valid/invalid phone numbers and emails, call attempts, and lead scores.
"""

import random
import csv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Configuration
DOMAINS = ["gmail.com", "yahoo.com", "outlook.com", "protonmail.com"]
NAMES = ["rahul", "anita", "rohit", "priya", "deepak", "kiran", "vijay", "sneha", "arjun", "meera"]
NUM_RECORDS = 50000
OUTPUT_FILE = "leads.csv"


def generate_valid_phone() -> str:
    """Generate a valid Indian phone number format.
    
    Returns:
        str: Valid 10-digit phone number starting with 6-9
    """
    first_digit = random.choice(["6", "7", "8", "9"])
    return first_digit + ''.join(str(random.randint(0, 9)) for _ in range(9))


def generate_invalid_phone() -> str:
    """Generate an invalid phone number.
    
    Returns:
        str: Invalid phone number in various formats
    """
    invalid_choices = [
        ''.join(str(random.randint(0, 9)) for _ in range(8)),  # Too short
        ''.join(str(random.randint(0, 9)) for _ in range(12)),  # Too long
        "1234567890",  # Starts with invalid digit
        "98A76B321C",  # Contains letters
        "99999"  # Too short
    ]
    return random.choice(invalid_choices)


def generate_valid_email() -> str:
    """Generate a valid email address.
    
    Returns:
        str: Valid email address
    """
    name = random.choice(NAMES)
    number = random.randint(1, 9999)
    domain = random.choice(DOMAINS)
    return f"{name}{number}@{domain}"


def generate_invalid_email() -> str:
    """Generate an invalid email address.
    
    Returns:
        str: Invalid email address in various formats
    """
    invalid_choices = [
        "usergmail.com",  # Missing @
        "test@",  # Missing domain
        "@gmail.com",  # Missing username
        "hello@domain",  # Missing TLD
        "abc@abc"  # Invalid TLD
    ]
    return random.choice(invalid_choices)


def get_valid_lead() -> tuple[str, str]:
    """Generate a valid lead record.
    
    Returns:
        Tuple of (phone, email)
    """
    return generate_valid_phone(), generate_valid_email()


def generate_leads(num_records: int = NUM_RECORDS) -> list[list]:  # type: ignore
    """Generate synthetic lead records with varied data quality.
    
    Distribution:
        - 60% valid leads (valid phone and email)
        - 20% invalid phone numbers
        - 10% invalid email addresses
        - 10% duplicate records
    
    Args:
        num_records: Number of lead records to generate
        
    Returns:
        List of lead records [phone, email, call_attempt, lead_score]
    """
    rows: list[list] = []  # type: ignore
    logger.info(f"Generating {num_records} synthetic leads...")
    
    for _ in range(num_records):
        probability = random.random()
        call_attempt = random.randint(0, 5)
        lead_score = random.randint(0, 100)
        
        # 60% valid leads
        if probability < 0.6:
            phone, email = get_valid_lead()
        # 20% invalid phone
        elif probability < 0.8:
            phone = generate_invalid_phone()
            email = generate_valid_email()
        # 10% invalid email
        elif probability < 0.9:
            phone = generate_valid_phone()
            email = generate_invalid_email()
        # 10% duplicates
        else:
            if rows:
                phone, email, _, _ = random.choice(rows)  # type: ignore
            else:
                phone, email = get_valid_lead()
        
        rows.append([phone, email, call_attempt, lead_score])  # type: ignore
    
    return rows  # type: ignore


def save_leads(rows: list[list], filename: str = OUTPUT_FILE) -> None:  # type: ignore
    """Save lead records to CSV file.
    
    Args:
        rows: List of lead records
        filename: Output CSV filename
        
    Raises:
        IOError: If file write fails
    """
    try:
        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["phone", "email", "call_attempt", "lead_score"])
            writer.writerows(rows)  # type: ignore
        logger.info(f"Saved {len(rows)} leads to {filename}")  # type: ignore
    except IOError as e:
        logger.error(f"Failed to save leads to {filename}: {e}")
        raise


def main() -> None:
    """Main function to generate and save synthetic leads."""
    try:
        leads = generate_leads(NUM_RECORDS)  # type: ignore
        save_leads(leads)
        print(f"\n[OK] Successfully generated and saved {NUM_RECORDS:,} synthetic leads!")
        print(f"     Output file: {OUTPUT_FILE}")
    except Exception as e:
        logger.error(f"Failed to generate leads: {e}")
        raise


if __name__ == "__main__":
    main()