/* Srky Alarm - Mobil PWA Alarm Uygulaması */
(function () {
  'use strict';

  // -----------------------------
  // Yardımcılar
  // -----------------------------
  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => document.querySelectorAll(sel);
  const STORAGE_KEY = 'srky.alarms.v1';
  const THEME_KEY = 'srky.theme';
  const DAY_NAMES = ['Paz', 'Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt'];

  const pad = (n) => String(n).padStart(2, '0');
  const uid = () => Math.random().toString(36).slice(2, 10);

  // -----------------------------
  // Durum
  // -----------------------------
  let alarms = loadAlarms();
  let selectedDays = new Set();
  let ringing = null; // { alarm, audioStop }
  let audioCtx = null;
  let audioUnlocked = false;
  let snoozeTimeoutId = null;

  function loadAlarms() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return [];
      const arr = JSON.parse(raw);
      return Array.isArray(arr) ? arr : [];
    } catch (e) {
      console.warn('Alarmlar yüklenemedi', e);
      return [];
    }
  }

  function saveAlarms() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(alarms));
  }

  // -----------------------------
  // Ses üretimi (Web Audio API)
  // -----------------------------
  function ensureAudio() {
    if (!audioCtx) {
      const Ctx = window.AudioContext || window.webkitAudioContext;
      if (!Ctx) return null;
      audioCtx = new Ctx();
    }
    return audioCtx;
  }

  function unlockAudio() {
    const ctx = ensureAudio();
    if (!ctx) return;
    if (ctx.state === 'suspended') ctx.resume();
    // Çok kısa sessiz bir ton çalarak tarayıcı kilidini aç
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    gain.gain.value = 0.0001;
    osc.connect(gain).connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + 0.05);
    audioUnlocked = true;
    $('#unlockBanner').classList.add('hidden');
  }

  // Farklı alarm tonları: notaları repeat eden bir döngü
  function playTone(type) {
    const ctx = ensureAudio();
    if (!ctx) return () => {};
    if (ctx.state === 'suspended') ctx.resume();

    const master = ctx.createGain();
    master.gain.value = 0.0;
    master.connect(ctx.destination);

    // Volume envelope
    const now = ctx.currentTime;
    master.gain.linearRampToValueAtTime(0.35, now + 0.05);

    const patterns = {
      beep: { notes: [880, 0, 880, 0, 880, 0, 0, 0], step: 0.18, wave: 'square' },
      chime: { notes: [523.25, 659.25, 783.99, 1046.5, 0, 0], step: 0.22, wave: 'sine' },
      digital: { notes: [1200, 0, 1200, 0, 900, 0, 1200, 0], step: 0.12, wave: 'triangle' },
      wave: { notes: [440, 494, 523, 587, 659, 587, 523, 494], step: 0.2, wave: 'sine' },
    };
    const p = patterns[type] || patterns.beep;

    let step = 0;
    let stopped = false;
    const nodes = [];

    function schedule() {
      if (stopped) return;
      const t = ctx.currentTime;
      const freq = p.notes[step % p.notes.length];
      if (freq > 0) {
        const osc = ctx.createOscillator();
        const g = ctx.createGain();
        osc.type = p.wave;
        osc.frequency.value = freq;
        g.gain.value = 0;
        g.gain.linearRampToValueAtTime(0.9, t + 0.01);
        g.gain.linearRampToValueAtTime(0, t + p.step * 0.9);
        osc.connect(g).connect(master);
        osc.start(t);
        osc.stop(t + p.step);
        nodes.push(osc);
      }
      step++;
      setTimeout(schedule, p.step * 1000);
    }
    schedule();

    return function stop() {
      stopped = true;
      try {
        master.gain.cancelScheduledValues(ctx.currentTime);
        master.gain.linearRampToValueAtTime(0, ctx.currentTime + 0.05);
      } catch (e) { /* ignore */ }
      nodes.forEach((n) => { try { n.stop(); } catch (e) {} });
    };
  }

  // Titreşim (destekleyen cihazlarda)
  function startVibration() {
    if (!('vibrate' in navigator)) return;
    const pattern = [400, 200, 400, 200, 600, 400];
    navigator.vibrate(pattern);
    // Periyodik titreşim
    ringing && (ringing.vibrateId = setInterval(() => navigator.vibrate(pattern), 2200));
  }
  function stopVibration() {
    if ('vibrate' in navigator) navigator.vibrate(0);
    if (ringing && ringing.vibrateId) clearInterval(ringing.vibrateId);
  }

  // -----------------------------
  // Saat
  // -----------------------------
  function updateClock() {
    const now = new Date();
    $('#currentTime').textContent = `${pad(now.getHours())}:${pad(now.getMinutes())}`;
    const opts = { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' };
    try {
      $('#currentDate').textContent = now.toLocaleDateString('tr-TR', opts);
    } catch (e) {
      $('#currentDate').textContent = now.toDateString();
    }
  }

  // -----------------------------
  // Alarm oluşturma
  // -----------------------------
  function addAlarm() {
    const time = $('#alarmTime').value;
    if (!time) return;
    const [h, m] = time.split(':').map(Number);
    const label = $('#alarmLabel').value.trim();
    const sound = $('#alarmSound').value;
    const days = Array.from(selectedDays).sort();

    const alarm = {
      id: uid(),
      hour: h,
      minute: m,
      label,
      sound,
      days, // boş => tek seferlik
      enabled: true,
      // Tek seferlik alarmlar için hedef timestamp (bir sonraki oluşum) hesaplanır
    };
    alarms.push(alarm);
    saveAlarms();
    renderAlarms();

    // Formu sıfırla
    $('#alarmLabel').value = '';
    selectedDays.clear();
    $$('.day').forEach((d) => d.classList.remove('active'));

    // Sesi etkinleştirmeye çalış (kullanıcı etkileşimi var)
    if (!audioUnlocked) unlockAudio();
  }

  function removeAlarm(id) {
    alarms = alarms.filter((a) => a.id !== id);
    saveAlarms();
    renderAlarms();
  }

  function toggleAlarm(id, enabled) {
    const a = alarms.find((x) => x.id === id);
    if (!a) return;
    a.enabled = enabled;
    // Eğer etkinleştiriliyorsa ertelemeyi de temizle
    delete a.snoozedUntil;
    saveAlarms();
    renderAlarms();
  }

  // -----------------------------
  // Tetikleme
  // -----------------------------
  let lastCheckKey = '';
  function checkAlarms() {
    if (ringing) return;
    const now = new Date();
    // Her dakikada bir tetikle (aynı dakika içinde tekrar tetiklenmesin)
    const key = `${now.getFullYear()}-${now.getMonth()}-${now.getDate()}-${now.getHours()}-${now.getMinutes()}`;
    if (key === lastCheckKey) return;

    const hr = now.getHours();
    const mn = now.getMinutes();
    const dow = now.getDay();
    const ts = now.getTime();

    for (const a of alarms) {
      if (!a.enabled) continue;

      // Erteleme kontrolü
      if (a.snoozedUntil && ts >= a.snoozedUntil && ts < a.snoozedUntil + 60000) {
        delete a.snoozedUntil;
        saveAlarms();
        triggerAlarm(a);
        lastCheckKey = key;
        return;
      }
      if (a.snoozedUntil && ts < a.snoozedUntil) continue;

      if (a.hour === hr && a.minute === mn) {
        const repeats = a.days && a.days.length > 0;
        if (repeats) {
          if (a.days.includes(dow)) {
            triggerAlarm(a);
            lastCheckKey = key;
            return;
          }
        } else {
          // Tek seferlik: tetikle ve devre dışı bırak
          triggerAlarm(a);
          a.enabled = false;
          saveAlarms();
          renderAlarms();
          lastCheckKey = key;
          return;
        }
      }
    }
    lastCheckKey = key;
  }

  function triggerAlarm(alarm) {
    const stopAudio = playTone(alarm.sound || 'beep');
    ringing = { alarm, stopAudio };
    startVibration();

    // Modalı aç
    $('#ringLabel').textContent = alarm.label
      ? alarm.label
      : `${pad(alarm.hour)}:${pad(alarm.minute)}`;
    $('#ringOverlay').classList.remove('hidden');

    // Ekranı uyanık tutmaya çalış
    requestWakeLock();

    // Sistem bildirimi (izin varsa)
    try {
      if ('Notification' in window && Notification.permission === 'granted') {
        new Notification('⏰ Alarm', {
          body: alarm.label || `${pad(alarm.hour)}:${pad(alarm.minute)}`,
          icon: 'icon.svg',
          tag: 'srky-alarm',
          renotify: true,
        });
      }
    } catch (e) { /* ignore */ }
  }

  function stopRinging() {
    if (!ringing) return;
    try { ringing.stopAudio && ringing.stopAudio(); } catch (e) {}
    stopVibration();
    ringing = null;
    $('#ringOverlay').classList.add('hidden');
    releaseWakeLock();
  }

  function snoozeRinging() {
    if (!ringing) return;
    const a = ringing.alarm;
    // 5 dk sonraya ertele
    const target = Date.now() + 5 * 60 * 1000;
    const stored = alarms.find((x) => x.id === a.id);
    if (stored) {
      stored.snoozedUntil = target;
      stored.enabled = true;
      saveAlarms();
    }
    stopRinging();
    renderAlarms();
  }

  // -----------------------------
  // Wake Lock (destekleyen cihazlarda)
  // -----------------------------
  let wakeLock = null;
  async function requestWakeLock() {
    try {
      if ('wakeLock' in navigator) {
        wakeLock = await navigator.wakeLock.request('screen');
      }
    } catch (e) { /* ignore */ }
  }
  function releaseWakeLock() {
    try { wakeLock && wakeLock.release(); } catch (e) {}
    wakeLock = null;
  }

  // -----------------------------
  // Render
  // -----------------------------
  function formatDays(days) {
    if (!days || days.length === 0) return 'Bir kez';
    if (days.length === 7) return 'Her gün';
    // Hafta içi / hafta sonu kısaltmaları
    const wd = [1, 2, 3, 4, 5];
    const we = [0, 6];
    const sorted = [...days].sort();
    if (JSON.stringify(sorted) === JSON.stringify(wd)) return 'Hafta içi';
    if (JSON.stringify(sorted) === JSON.stringify(we)) return 'Hafta sonu';
    return sorted.map((d) => DAY_NAMES[d]).join(' · ');
  }

  function renderAlarms() {
    const list = $('#alarmList');
    list.innerHTML = '';
    // Saate göre sırala
    const sorted = [...alarms].sort((a, b) => (a.hour * 60 + a.minute) - (b.hour * 60 + b.minute));

    for (const a of sorted) {
      const li = document.createElement('li');
      li.className = 'alarm-item' + (a.enabled ? '' : ' disabled');

      const main = document.createElement('div');
      main.className = 'alarm-main';

      const time = document.createElement('div');
      time.className = 'alarm-time';
      time.textContent = `${pad(a.hour)}:${pad(a.minute)}`;

      const label = document.createElement('div');
      label.className = 'alarm-label';
      label.textContent = a.label || 'Alarm';

      const days = document.createElement('div');
      days.className = 'alarm-days';
      let daysText = formatDays(a.days);
      if (a.snoozedUntil && a.snoozedUntil > Date.now()) {
        const dt = new Date(a.snoozedUntil);
        daysText += ` · Ertelendi → ${pad(dt.getHours())}:${pad(dt.getMinutes())}`;
      }
      days.textContent = daysText;

      main.appendChild(time);
      main.appendChild(label);
      main.appendChild(days);

      const ctrl = document.createElement('div');
      ctrl.className = 'alarm-ctrl';

      const sw = document.createElement('label');
      sw.className = 'switch';
      const input = document.createElement('input');
      input.type = 'checkbox';
      input.checked = !!a.enabled;
      input.addEventListener('change', () => toggleAlarm(a.id, input.checked));
      const slider = document.createElement('span');
      slider.className = 'slider';
      sw.appendChild(input);
      sw.appendChild(slider);

      const del = document.createElement('button');
      del.className = 'del-btn';
      del.textContent = 'Sil';
      del.addEventListener('click', () => {
        if (confirm('Alarmı silmek istediğinize emin misiniz?')) removeAlarm(a.id);
      });

      ctrl.appendChild(sw);
      ctrl.appendChild(del);

      li.appendChild(main);
      li.appendChild(ctrl);
      list.appendChild(li);
    }

    $('#alarmCount').textContent = alarms.length;
    $('#emptyState').style.display = alarms.length ? 'none' : 'block';
  }

  // -----------------------------
  // Tema
  // -----------------------------
  function applyTheme(theme) {
    if (theme === 'light') document.documentElement.classList.add('light');
    else document.documentElement.classList.remove('light');
    localStorage.setItem(THEME_KEY, theme);
  }
  function toggleTheme() {
    const cur = localStorage.getItem(THEME_KEY) || 'dark';
    applyTheme(cur === 'dark' ? 'light' : 'dark');
  }

  // -----------------------------
  // Olaylar
  // -----------------------------
  function bindEvents() {
    $('#addAlarmBtn').addEventListener('click', addAlarm);
    $('#stopBtn').addEventListener('click', stopRinging);
    $('#snoozeBtn').addEventListener('click', snoozeRinging);
    $('#themeBtn').addEventListener('click', toggleTheme);
    $('#unlockBtn').addEventListener('click', () => {
      unlockAudio();
      requestNotificationPermission();
    });

    $$('.day').forEach((btn) => {
      btn.addEventListener('click', () => {
        const d = Number(btn.dataset.day);
        if (selectedDays.has(d)) {
          selectedDays.delete(d);
          btn.classList.remove('active');
        } else {
          selectedDays.add(d);
          btn.classList.add('active');
        }
      });
    });

    // Sekmeye geri dönünce saati/alarmı tazele
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden) {
        updateClock();
        checkAlarms();
      }
    });

    // Ses için ilk kullanıcı etkileşiminde kilidi kaldır
    const unlockOnce = () => {
      if (!audioUnlocked) unlockAudio();
      document.removeEventListener('touchstart', unlockOnce);
      document.removeEventListener('click', unlockOnce);
    };
    document.addEventListener('touchstart', unlockOnce, { passive: true });
    document.addEventListener('click', unlockOnce);
  }

  function requestNotificationPermission() {
    if ('Notification' in window && Notification.permission === 'default') {
      try { Notification.requestPermission(); } catch (e) {}
    }
  }

  // -----------------------------
  // Başlat
  // -----------------------------
  function init() {
    applyTheme(localStorage.getItem(THEME_KEY) || 'dark');
    bindEvents();
    renderAlarms();
    updateClock();
    setInterval(() => {
      updateClock();
      checkAlarms();
    }, 1000);

    // Ses izni banner'ı göster (sadece bir kez)
    if (!audioUnlocked) {
      setTimeout(() => {
        if (!audioUnlocked) $('#unlockBanner').classList.remove('hidden');
      }, 500);
    }

    // Service worker
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('sw.js').catch(() => {});
    }
  }

  document.addEventListener('DOMContentLoaded', init);
})();
