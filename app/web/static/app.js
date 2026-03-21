/* DeviceProbe Web UI - JavaScript */

let selectedDeviceId = null;
let testPollingInterval = null;

// ── API Helper ──

async function api(url, options = {}) {
    try {
        const resp = await fetch(url, {
            headers: { "Content-Type": "application/json" },
            ...options,
        });
        return await resp.json();
    } catch (err) {
        console.error("API hatası:", err);
        setStatus("Bağlantı hatası");
        return null;
    }
}

function setStatus(msg) {
    document.getElementById("statusText").textContent = msg;
    document.getElementById("footerStatus").textContent = msg;
}

// ── Tabs ──

function switchTab(tabName) {
    document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
    document.querySelectorAll(".tab-content").forEach(t => t.classList.remove("active"));
    document.querySelector(`[data-tab="${tabName}"]`).classList.add("active");
    document.getElementById(`tab-${tabName}`).classList.add("active");

    // Load data for tabs when switched
    if (selectedDeviceId) {
        if (tabName === "pins") loadPinMatrix();
        if (tabName === "report") loadReport();
    }
}

// ── Device Discovery ──

async function scanDevices() {
    setStatus("Taranıyor...");
    document.getElementById("infoLabel").textContent = "Taranıyor...";

    const sshHost = document.getElementById("sshHost").value.trim();
    const sshHosts = sshHost ? [sshHost] : [];

    const devices = await api("/api/scan", {
        method: "POST",
        body: JSON.stringify({ ssh_hosts: sshHosts }),
    });

    if (devices) {
        populateDeviceTable(devices);
        document.getElementById("infoLabel").textContent = `${devices.length} cihaz bulundu`;
        setStatus(`${devices.length} cihaz bulundu`);
    }
}

async function addSSHDevice() {
    const host = document.getElementById("sshHost").value.trim();
    if (!host) {
        document.getElementById("infoLabel").textContent = "Önce bir IP veya hostname girin";
        return;
    }
    const user = document.getElementById("sshUser").value.trim() || "pi";
    const pass = document.getElementById("sshPass").value;

    const devices = await api("/api/devices/ssh", {
        method: "POST",
        body: JSON.stringify({ host, username: user, password: pass }),
    });

    if (devices) {
        populateDeviceTable(devices);
        setStatus(`SSH hedefi eklendi: ${host}`);
    }
}

function populateDeviceTable(devices) {
    const tbody = document.getElementById("deviceTableBody");
    tbody.innerHTML = "";

    devices.forEach(dev => {
        const tr = document.createElement("tr");
        tr.dataset.deviceId = dev.id;
        tr.onclick = () => selectDevice(dev.id);
        if (dev.id === selectedDeviceId) tr.classList.add("selected");

        tr.innerHTML = `
            <td>${esc(dev.board_model)}</td>
            <td>${esc(dev.family)}</td>
            <td>${esc(dev.address)}</td>
            <td style="text-align:center">${Math.round(dev.confidence * 100)}%</td>
        `;
        tbody.appendChild(tr);
    });

    document.getElementById("connectBtn").disabled = devices.length === 0;
}

// ── Device Selection ──

async function selectDevice(deviceId) {
    selectedDeviceId = deviceId;

    // Highlight row
    document.querySelectorAll("#deviceTableBody tr").forEach(tr => {
        tr.classList.toggle("selected", tr.dataset.deviceId === deviceId);
    });
    document.getElementById("connectBtn").disabled = false;

    const detail = await api(`/api/devices/${deviceId}/select`, { method: "POST" });
    if (detail) {
        updateDeviceDetail(detail);
        setStatus(`Seçildi: ${detail.board_model}`);
    }
}

function updateDeviceDetail(d) {
    document.getElementById("infoModel").textContent = d.board_model;
    document.getElementById("infoFamily").textContent = d.family;
    document.getElementById("infoMCU").textContent = d.mcu || "Bilinmiyor";
    document.getElementById("infoPort").textContent = d.port;
    document.getElementById("infoConn").textContent = d.connection_type;
    document.getElementById("infoConf").textContent = Math.round(d.confidence * 100) + "%";
    document.getElementById("infoVidPid").textContent = `${d.vid} / ${d.pid}`;
    document.getElementById("infoMfr").textContent = d.manufacturer;
    document.getElementById("infoSerial").textContent = d.serial_number;
    document.getElementById("infoFlash").textContent = d.flash || "Yok";
    document.getElementById("infoRAM").textContent = d.ram || "Yok";
    document.getElementById("infoFeatures").textContent = d.features?.length ? d.features.join(", ") : "Yok";

    // Capabilities
    const tests = d.supported_tests?.length ? d.supported_tests.join(", ") : "Yok";
    document.getElementById("capText").innerHTML =
        `<strong>Desteklenen testler:</strong> ${esc(tests)}<br><br>` +
        `<strong>Notlar:</strong> ${esc(d.notes || "")}`;

    // Test center
    const connected = d.is_connected;
    document.getElementById("testDeviceLabel").textContent =
        `Cihaz: ${d.board_model} | ${connected ? "Bağlı" : "Bağlı değil"}`;
    document.getElementById("quickTestBtn").disabled = !connected;
    document.getElementById("fullTestBtn").disabled = !connected;

    // Pin matrix
    document.getElementById("pinDeviceLabel").textContent =
        `${d.board_model} - ${d.pin_count || 0} pin tanımlı`;
}

// ── Connection ──

async function connectDevice() {
    if (!selectedDeviceId) return;
    setStatus("Bağlanıyor...");

    const result = await api(`/api/devices/${selectedDeviceId}/connect`, { method: "POST" });
    if (result) {
        setStatus(result.message);
        // Refresh detail
        const detail = await api(`/api/devices/${selectedDeviceId}`);
        if (detail) updateDeviceDetail(detail);
        // Refresh device list
        const devices = await api("/api/devices");
        if (devices) populateDeviceTable(devices);
    }
}

// ── Pin Matrix ──

async function loadPinMatrix() {
    if (!selectedDeviceId) return;
    const pins = await api(`/api/devices/${selectedDeviceId}/pins`);
    if (!pins) return;

    const tbody = document.getElementById("pinTableBody");
    tbody.innerHTML = "";

    pins.forEach(pin => {
        const tr = document.createElement("tr");
        tr.onclick = () => showPinDetail(pin);

        const statusClass = `status-${pin.status}`;
        tr.innerHTML = `
            <td>${pin.number}</td>
            <td>${esc(pin.name)}</td>
            <td>${pin.gpio !== null ? pin.gpio : "-"}</td>
            <td>${esc(pin.functions.join(", "))}</td>
            <td>${pin.voltage}V</td>
            <td><span class="${statusClass}" style="padding:2px 6px;border-radius:3px;font-weight:bold;font-size:11px">${pin.status}</span></td>
            <td>${esc(pin.notes)}</td>
        `;
        tbody.appendChild(tr);
    });
}

function showPinDetail(pin) {
    document.getElementById("pinDetail").innerHTML = `
        <strong>Pin:</strong> ${esc(pin.name)}<br>
        <strong>İşlevler:</strong> ${esc(pin.functions.join(", ") || "-")}<br>
        <strong>Voltaj:</strong> ${pin.voltage}V<br>
        <strong>Durum:</strong> ${pin.status}<br>
        <strong>Notlar:</strong> ${esc(pin.notes || "-")}
    `;
}

// ── Test Execution ──

async function runTest(mode) {
    if (!selectedDeviceId) return;

    document.getElementById("quickTestBtn").disabled = true;
    document.getElementById("fullTestBtn").disabled = true;
    document.getElementById("stopTestBtn").disabled = false;
    document.getElementById("progressBar").style.width = "0%";
    document.getElementById("resultsText").textContent = "";

    await api(`/api/devices/${selectedDeviceId}/test`, {
        method: "POST",
        body: JSON.stringify({ mode }),
    });

    // Start polling for progress
    startTestPolling();
}

function startTestPolling() {
    if (testPollingInterval) clearInterval(testPollingInterval);
    testPollingInterval = setInterval(async () => {
        const progress = await api("/api/test/progress");
        if (!progress) return;

        document.getElementById("progressBar").style.width = progress.pct + "%";

        if (progress.running) {
            document.getElementById("progressLabel").textContent =
                `Çalışıyor: ${progress.test_id} (${progress.current}/${progress.total})`;
        } else {
            clearInterval(testPollingInterval);
            testPollingInterval = null;
            document.getElementById("progressBar").style.width = "100%";
            document.getElementById("progressLabel").textContent = "Tamamlandı";
            document.getElementById("quickTestBtn").disabled = false;
            document.getElementById("fullTestBtn").disabled = false;
            document.getElementById("stopTestBtn").disabled = true;
            document.getElementById("exportBtn").disabled = false;

            // Load report
            const report = await api("/api/report?format=text");
            if (report) {
                document.getElementById("resultsText").textContent = report.content;
            }
            setStatus("Tamamlandı");
        }
    }, 500);
}

async function stopTest() {
    await api("/api/test/stop", { method: "POST" });
    document.getElementById("stopTestBtn").disabled = true;
    document.getElementById("progressLabel").textContent = "Durduruluyor...";
    setStatus("Durduruldu");
}

// ── Reports ──

async function loadReport() {
    const fmt = document.getElementById("reportFormat").value;
    const report = await api(`/api/report?format=${fmt}`);

    if (report && !report.error) {
        document.getElementById("reportText").textContent = report.content;
        const s = report.summary;
        document.getElementById("reportSummary").textContent =
            `Cihaz: ${s.board_model} | Toplam: ${s.total} | ` +
            `Başarılı: ${s.passed} | Başarısız: ${s.failed} | ` +
            `Uyarı: ${s.warnings} | Atlanan: ${s.skipped}`;
        document.getElementById("exportBtn").disabled = false;
    } else {
        document.getElementById("reportText").textContent = "";
        document.getElementById("reportSummary").textContent = "Rapor yok. Önce testleri çalıştırın.";
    }
}

function exportReport() {
    const fmt = document.getElementById("reportFormat").value;
    const content = document.getElementById("reportText").textContent;
    if (!content) return;

    const extMap = { text: "txt", json: "json", csv: "csv" };
    const ext = extMap[fmt] || "txt";
    const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `rapor.${ext}`;
    a.click();
    URL.revokeObjectURL(url);
}

// ── Utilities ──

function esc(str) {
    if (!str) return "";
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}

// ── Status Polling ──

setInterval(async () => {
    const data = await api("/api/status");
    if (data) {
        setStatus(data.status);
    }
}, 3000);
