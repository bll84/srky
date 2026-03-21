"""Flask routes for DeviceProbe web interface."""

from __future__ import annotations

import logging

from flask import Blueprint, Flask, jsonify, render_template, request

from app.web.web_controller import WebController

logger = logging.getLogger(__name__)

controller = WebController()

api = Blueprint("api", __name__, url_prefix="/api")


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )
    app.register_blueprint(api)

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.teardown_appcontext
    def shutdown(exception=None):
        pass

    return app


# ── API Routes ──

@api.route("/status")
def get_status():
    return jsonify({
        "status": controller.get_status(),
        "test_progress": controller.get_test_progress(),
    })


@api.route("/devices")
def get_devices():
    return jsonify(controller.get_devices())


@api.route("/scan", methods=["POST"])
def scan_devices():
    data = request.get_json(silent=True) or {}
    ssh_hosts = data.get("ssh_hosts", [])
    devices = controller.scan_devices(ssh_hosts=ssh_hosts if ssh_hosts else None)
    return jsonify(devices)


@api.route("/devices/ssh", methods=["POST"])
def add_ssh_device():
    data = request.get_json()
    if not data or not data.get("host"):
        return jsonify({"error": "Host gerekli"}), 400
    devices = controller.add_ssh_device(
        host=data["host"],
        username=data.get("username", "pi"),
        password=data.get("password", ""),
    )
    return jsonify(devices)


@api.route("/devices/<device_id>")
def get_device_detail(device_id: str):
    detail = controller.get_device_detail(device_id)
    if not detail:
        return jsonify({"error": "Cihaz bulunamadı"}), 404
    return jsonify(detail)


@api.route("/devices/<device_id>/select", methods=["POST"])
def select_device(device_id: str):
    detail = controller.select_device(device_id)
    if not detail:
        return jsonify({"error": "Cihaz bulunamadı"}), 404
    return jsonify(detail)


@api.route("/devices/<device_id>/connect", methods=["POST"])
def connect_device(device_id: str):
    result = controller.connect_device(device_id)
    return jsonify(result)


@api.route("/devices/<device_id>/pins")
def get_pin_matrix(device_id: str):
    pins = controller.get_pin_matrix(device_id)
    return jsonify(pins)


@api.route("/devices/<device_id>/test", methods=["POST"])
def run_test(device_id: str):
    data = request.get_json(silent=True) or {}
    mode = data.get("mode", "quick")
    controller.run_tests(device_id, mode)
    return jsonify({"message": f"{'Hızlı' if mode == 'quick' else 'Tam'} test başlatıldı"})


@api.route("/test/stop", methods=["POST"])
def stop_test():
    controller.stop_tests()
    return jsonify({"message": "Testler durduruluyor"})


@api.route("/test/progress")
def test_progress():
    return jsonify(controller.get_test_progress())


@api.route("/report")
def get_report():
    fmt = request.args.get("format", "text")
    report = controller.get_report(fmt)
    if not report:
        return jsonify({"error": "Rapor yok. Önce testleri çalıştırın."}), 404
    return jsonify(report)
