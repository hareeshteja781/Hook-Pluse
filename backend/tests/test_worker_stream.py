import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT))

from worker.stream import GROUP_NAME, STREAM_NAME

def test_stream_contract():
    assert STREAM_NAME == "hookpluse:webhook_events"
    assert GROUP_NAME == "hookpluse-delivery"
