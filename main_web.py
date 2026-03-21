"""DeviceProbe - Web Interface Entry Point.

Kullanım:
    python main_web.py

Tarayıcıda http://localhost:5000 adresini açın.
"""

import logging
import sys
import webbrowser
from threading import Timer

from app.web.routes import create_app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("deviceprobe.log", mode="a"),
    ],
)
logger = logging.getLogger("DeviceProbe")


def open_browser():
    webbrowser.open("http://localhost:5000")


def main() -> int:
    logger.info("DeviceProbe Web arayüzü başlatılıyor")

    app = create_app()

    # Tarayıcıyı otomatik aç
    Timer(1.5, open_browser).start()

    print("\n  DeviceProbe Web Arayüzü")
    print("  ──────────────────────")
    print("  http://localhost:5000")
    print("  Durdurmak için Ctrl+C\n")

    app.run(host="0.0.0.0", port=5000, debug=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
