import sys
from pathlib import Path

BACKEND_PATH = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_PATH) not in sys.path:
    sys.path.insert(0, str(BACKEND_PATH))

from worker.consumer import consume_loop
from worker.dispatcher import dispatch_loop

def main() -> None:
    import threading
    dispatcher = threading.Thread(target=dispatch_loop, name="dispatcher", daemon=True)
    dispatcher.start()
    consume_loop()

if __name__ == "__main__":
    main()
