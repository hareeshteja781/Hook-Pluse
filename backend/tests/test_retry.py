import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from app.core.config import settings
from worker.delivery import determine_delivery_status, retry_delay_seconds

def test_retry_delay_is_exponential():
    base = settings.retry_base_seconds
    assert retry_delay_seconds(1) == base
    assert retry_delay_seconds(2) == base * 2
    assert retry_delay_seconds(3) == base * 4
    assert retry_delay_seconds(4) == base * 8

def test_success_is_delivered():
    assert determine_delivery_status(1, True) == "DELIVERED"

def test_failure_retries_until_max_attempts():
    assert determine_delivery_status(1, False) == "RETRY_SCHEDULED"
    assert determine_delivery_status(settings.max_delivery_attempts - 1, False) == "RETRY_SCHEDULED"

def test_final_failure_goes_to_dlq():
    assert determine_delivery_status(settings.max_delivery_attempts, False) == "DLQ"
