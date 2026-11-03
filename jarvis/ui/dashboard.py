from __future__ import annotations

import math
import logging
from typing import Optional, Dict, Any, Set
from PySide6.QtCore import Qt, QTimer, Signal, QObject, QRunnable, QThreadPool, QRectF, QPointF
from PySide6.QtGui import QColor, QPainter, QFont, QPen, QRadialGradient, QPolygonF
from PySide6.QtWidgets import (
    QWidget, QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QLineEdit, QPushButton, QFrame, QSplitter, QProgressBar, QGridLayout
)
from jarvis.core.models import ToolResult

class WorkerSignals(QObject):
    finished = Signal(object)

class Worker(QRunnable):
    def __init__(self, fn):
        super().__init__()
        self.fn = fn
        self.signals = WorkerSignals()

    def run(self):
        try:
            res = self.fn()
            try:
                self.signals.finished.emit(res)
            except RuntimeError:
                pass
        except Exception as exc:
            logging.exception("Background task failed")
            try:
                self.signals.finished.emit(ToolResult(False, f"Task error: {exc}"))
            except RuntimeError:
                pass

class VoiceWorker(QRunnable):
    def __init__(self):
        super().__init__()
        self.signals = WorkerSignals()

    def run(self):
        try:
            from jarvis.voice.command import VoiceCommand
            text = VoiceCommand().listen_once()
            try:
                self.signals.finished.emit((True, text))
            except RuntimeError:
                pass
        except Exception as exc:
            logging.warning("Voice recognition failed: %s", exc)
            try:
                self.signals.finished.emit((False, str(exc)))
            except RuntimeError:
                pass

class SpeechWorker(QRunnable):
    def __init__(self, text: str):
        super().__init__()
        self.text = text
        self.signals = WorkerSignals()

    def run(self):
        try:
            from jarvis.voice.output import VoiceOutput
            VoiceOutput().speak(self.text)
            try:
                self.signals.finished.emit(True)
            except RuntimeError:
                pass
        except Exception as exc:
            logging.error("TTS worker failed: %s", exc)
            try:
                self.signals.finished.emit(False)
            except RuntimeError:
                pass

class HudRoot(QWidget):
    """Animated, low-opacity command-grid backdrop for the entire interface."""
    def __init__(self):
        super().__init__()
        self.phase = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(70)

    def tick(self):
        self.phase = (self.phase + 1) % 240
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor("#02070c"))
        p.setPen(QPen(QColor(21, 90, 115, 36), 1))
        for x in range(-20, self.width()+20, 42):
            p.drawLine(x, 0, x, self.height())
        for y in range(-20, self.height()+20, 42):
            p.drawLine(0, y, self.width(), y)
        scan = (self.phase / 240) * self.height()
        glow = QRadialGradient(QPointF(self.width() * 0.5, scan), self.width() * 0.6)
        glow.setColorAt(0, QColor(25, 215, 255, 24))
        glow.setColorAt(1, QColor(25, 215, 255, 0))
        p.setBrush(glow)
        p.setPen(Qt.NoPen)
        p.drawRect(self.rect())
        p.setPen(QPen(QColor(105, 238, 255, 70), 1))
        p.drawLine(0, scan, self.width(), scan)
        for index in range(18):
            x = (index * 173 + self.phase * (index % 3 + 1) * 2) % max(self.width(), 1)
            y = (index * 97 + self.phase * (index % 2 + 1)) % max(self.height(), 1)
            p.setBrush(QColor(135, 242, 255, 80))
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(x, y), 1.5, 1.5)

class ReactorCore(QWidget):
    """Lightweight Arc Reactor central visual with dynamic states."""
    def __init__(self):
        super().__init__()
        self.phase, self.state = 0, "IDLE"
        self.setMinimumSize(380, 380)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(33)

    def _tick(self):
        delta = 6 if self.state in {"THINKING", "EXECUTING", "SPEAKING"} else 2
        self.phase = (self.phase + delta) % 360
        self.update()

    def _palette(self):
        if self.state == "ERROR":
            return QColor("#ff4b55"), QColor("#ffccd0")
        if self.state == "THINKING":
            return QColor("#167cff"), QColor("#8deeff")
        if self.state == "EXECUTING":
            return QColor("#00ffcc"), QColor("#d9fff7")
        if self.state == "SPEAKING":
            return QColor("#1d9fff"), QColor("#ffffff")
        return QColor("#22d9ff"), QColor("#a9f5ff")

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        center = QPointF(self.width() / 2, self.height() / 2)
        size = min(self.width(), self.height())
        primary, secondary = self._palette()
        breath = math.sin(math.radians(self.phase * 2)) * 4

        glow = QRadialGradient(center, size * 0.47)
        glow.setColorAt(0, QColor(primary.red(), primary.green(), primary.blue(), 105))
        glow.setColorAt(0.38, QColor(primary.red(), primary.green(), primary.blue(), 32))
        glow.setColorAt(1, QColor(primary.red(), primary.green(), primary.blue(), 0))
        p.setPen(Qt.NoPen)
        p.setBrush(glow)
        p.drawEllipse(center, size * 0.47, size * 0.47)

        for ratio, width, alpha in ((0.46, 2, 35), (0.41, 1, 75), (0.34, 3, 175), (0.27, 1, 95), (0.20, 2, 225)):
            p.setBrush(Qt.NoBrush)
            p.setPen(QPen(QColor(primary.red(), primary.green(), primary.blue(), alpha), width))
            p.drawEllipse(center, size * ratio, size * ratio)

        outer = QRectF(center.x() - size*0.41, center.y() - size*0.41, size*0.82, size*0.82)
        middle = QRectF(center.x() - size*0.34, center.y() - size*0.34, size*0.68, size*0.68)
        p.setPen(QPen(secondary, 3))
        p.drawArc(outer, -self.phase * 16, 68 * 16)
        p.drawArc(outer, (155 - self.phase) * 16, 45 * 16)
        p.setPen(QPen(primary, 2))
        p.drawArc(middle, self.phase * 16, 105 * 16)
        p.drawArc(middle, (220 + self.phase) * 16, 42 * 16)

        for offset in (0, 120, 240):
            angle = math.radians(offset - 90)
            points = []
            for radius, spread in ((size*0.16, -13), (size*0.36, -20), (size*0.36, 20), (size*0.16, 13)):
                a = angle + math.radians(spread)
                points.append(QPointF(center.x() + math.cos(a)*radius, center.y() + math.sin(a)*radius))
            p.setBrush(QColor(9, 31, 42, 230))
            p.setPen(QPen(QColor(40, 138, 160, 170), 2))
            p.drawPolygon(QPolygonF(points))
            p.setPen(QPen(secondary, 3))
            p.drawLine(
                center.x() + math.cos(angle - math.radians(4))*size*0.19,
                center.y() + math.sin(angle - math.radians(4))*size*0.19,
                center.x() + math.cos(angle + math.radians(4))*size*0.34,
                center.y() + math.sin(angle + math.radians(4))*size*0.34
            )

        radius = size * 0.155 + breath
        core = QRadialGradient(center, radius)
        core.setColorAt(0, QColor("#ffffff"))
        core.setColorAt(0.16, QColor("#d9fbff"))
        core.setColorAt(0.42, secondary)
        core.setColorAt(0.73, primary)
        core.setColorAt(1, QColor(primary.red(), primary.green(), primary.blue(), 80))
        p.setBrush(core)
        p.setPen(QPen(QColor("#e5fcff"), 1))
        p.drawEllipse(center, radius, radius)

        p.setPen(QColor("#06121a"))
        p.setFont(QFont("Segoe UI", 10, QFont.Black))
        p.drawText(QRectF(0, center.y() - 18, self.width(), 36), Qt.AlignCenter, "ARC CORE\n" + self.state)

class SignalWave(QWidget):
    def __init__(self):
        super().__init__()
        self.phase = 0
        self.setMinimumHeight(48)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(55)

    def _tick(self):
        self.phase = (self.phase + 1) % 120
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        p.fillRect(rect, QColor("#04111d"))
        p.setPen(QPen(QColor("#15384a"), 1))
        for x in range(0, rect.width(), 20):
            p.drawLine(x, 0, x, rect.height())
        baseline = rect.height() / 2
        for i, x in enumerate(range(10, rect.width()-8, 12)):
            level = abs(math.sin((self.phase + i * 11) * 0.11)) * 0.8 + abs(math.sin((self.phase + i * 5) * 0.045)) * 0.25
            height = 5 + level * (rect.height() * 0.38)
            color = QColor("#25dcff") if i % 4 else QColor("#8ef8ff")
            p.setPen(QPen(color, 2))
            p.drawLine(x, baseline - height, x, baseline + height)

class TelemetryStream(QWidget):
    def __init__(self):
        super().__init__()
        self.phase = 0
        self.setMinimumHeight(56)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(60)

    def tick(self):
        self.phase = (self.phase + 2) % 360
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = self.rect()
        p.fillRect(r, QColor("#06131d"))
        p.setPen(QPen(QColor(33, 111, 138, 80), 1))
        for y in range(8, r.height(), 14):
            p.drawLine(0, y, r.width(), y)
        for channel, base in enumerate((14, 28, 42)):
            p.setPen(QPen((QColor("#33dfff"), QColor("#89f5ff"), QColor("#278fc2"))[channel], 1.5))
            points = []
            for x in range(0, r.width()+1, 7):
                val = math.sin((x + self.phase*(channel+1))*0.045) * (5 + channel*2) + math.sin((x+self.phase)*0.12)*2
                points.append(QPointF(x, base + val))
            for a, b in zip(points, points[1:]):
                p.drawLine(a, b)
        p.setPen(QColor("#c8f8ff"))
        p.setFont(QFont("Segoe UI", 7, QFont.Bold))
        p.drawText(8, 11, "LIVE DATA BUS // NOMINAL")

class DiagnosticMatrix(QWidget):
    def __init__(self):
        super().__init__()
        self.phase = 0
        self.setMinimumHeight(76)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(85)

    def tick(self):
        self.phase = (self.phase + 1) % 100
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = self.rect()
        p.fillRect(r, QColor("#07131c"))
        labels = ("AI CORE", "DESKTOP OPS", "VOICE I/O", "SECURITY", "GPU BUS", "AUDIT LOG", "VISION", "AUTOMATION")
        columns, rows = 4, 2
        cell_w, cell_h = r.width()/columns, r.height()/rows
        for index, label in enumerate(labels):
            x, y = (index % columns)*cell_w, (index // columns)*cell_h
            active = ((self.phase + index*13) % 35) < 29
            color = QColor("#35e1ff") if active else QColor("#23516a")
            p.setPen(QPen(QColor(38, 118, 145, 120), 1))
            p.setBrush(QColor(5, 19, 28, 200))
            p.drawRoundedRect(QRectF(x+4, y+4, cell_w-8, cell_h-8), 4, 4)
            p.setBrush(color)
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(x+15, y+15), 3, 3)
            p.setPen(QColor("#bfeefa"))
            p.setFont(QFont("Segoe UI", 7, QFont.Bold))
            p.drawText(QRectF(x+24, y+8, cell_w-30, 15), Qt.AlignLeft, label)

class MetricCard(QFrame):
    def __init__(self, label: str, accent: str = "#20d8ff"):
        super().__init__()
        self.setObjectName("metricCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(3)
        self.label = QLabel(label.upper())
        self.label.setObjectName("metricLabel")
        self.value = QLabel("--")
        self.value.setObjectName("metricValue")
        self.bar = QProgressBar()
        self.bar.setTextVisible(False)
        self.bar.setRange(0, 100)
        self.bar.setValue(0)
        self.bar.setStyleSheet(f"QProgressBar::chunk{{background:{accent};border-radius:2px;}}")
        layout.addWidget(self.label)
        layout.addWidget(self.value)
        layout.addWidget(self.bar)

    def update_metric(self, value: str, percent: float):
        self.value.setText(value)
        self.bar.setValue(max(0, min(100, round(percent))))

class Dashboard(QMainWindow):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.pool = QThreadPool.globalInstance()
        self._active_workers: Set[QRunnable] = set()
        self.pending_action: Optional[Dict[str, Any]] = None
        self.monitor_busy = False

        self.setWindowTitle("J.A.R.V.I.S. // WINDOWS AI DESKTOP ASSISTANT")
        self.resize(1440, 920)
        self.setMinimumSize(1160, 780)
        self.setStyleSheet(self._stylesheet())

        root = HudRoot()
        root.setObjectName("root")
        self.setCentralWidget(root)

        page = QVBoxLayout(root)
        page.setContentsMargins(18, 16, 18, 16)
        page.setSpacing(10)

        page.addLayout(self._header())

        splitter = QSplitter()
        splitter.setHandleWidth(2)
        splitter.setStyleSheet("QSplitter::handle{background:#163b52;}")
        splitter.addWidget(self._left_panel())
        splitter.addWidget(self._right_panel())
        splitter.setSizes([560, 880])
        page.addWidget(splitter, 1)

        # Hardware telemetry refresh timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_telemetry)
        self.timer.start(2000)
        self.refresh_telemetry()

    def _start_worker(self, worker: QRunnable) -> None:
        """Safely tracks worker to prevent garbage collection before completion."""
        self._active_workers.add(worker)
        if hasattr(worker, "signals") and hasattr(worker.signals, "finished"):
            worker.signals.finished.connect(lambda *_: self._active_workers.discard(worker))
        self.pool.start(worker)

    def _header(self) -> QHBoxLayout:
        row = QHBoxLayout()
        brand = QLabel("J.A.R.V.I.S. <span style='color:#22dcff'>//</span> DESKTOP INTELLIGENCE")
        brand.setObjectName("brand")
        sub = QLabel("WINDOWS AI ASSISTANT  •  SANDBOXED & AUDITED")
        sub.setObjectName("subtitle")
        self.status_chip = QLabel("● SYSTEM ONLINE")
        self.status_chip.setObjectName("statusChip")
        row.addWidget(brand)
        row.addWidget(sub)
        row.addStretch()
        row.addWidget(self.status_chip)
        return row

    def _panel_title(self, title: str, detail: str) -> QFrame:
        frame = QFrame()
        frame.setObjectName("titleRail")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(10, 6, 10, 6)
        a = QLabel(title)
        a.setObjectName("panelTitle")
        b = QLabel(detail)
        b.setObjectName("panelDetail")
        layout.addWidget(a)
        layout.addStretch()
        layout.addWidget(b)
        return frame

    def _left_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        layout.addWidget(self._panel_title("ARC REACTOR CORE", "TELEMETRY ACTIVE"))

        self.orb = ReactorCore()
        layout.addWidget(self.orb, alignment=Qt.AlignCenter)

        readout = QLabel(
            "CORE PROTOCOL // ONLINE <span style='color:#eafaff'>•</span> CONTAINMENT // ENFORCED\n"
            "<span style='color:#6996aa'>LOCAL OLLAMA + WINDOWS AUTOMATION BUS</span>"
        )
        readout.setObjectName("coreReadout")
        readout.setAlignment(Qt.AlignCenter)
        layout.addWidget(readout)

        row1 = QHBoxLayout()
        self.cpu = MetricCard("CPU", "#35d9ff")
        self.ram = MetricCard("RAM", "#47cfff")
        row1.addWidget(self.cpu)
        row1.addWidget(self.ram)
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        self.gpu = MetricCard("GPU", "#00b9ff")
        self.power = MetricCard("POWER", "#d9fbff")
        row2.addWidget(self.gpu)
        row2.addWidget(self.power)
        layout.addLayout(row2)

        self.hardware_detail = QLabel()
        self.hardware_detail.setObjectName("hardwareDetail")
        self.hardware_detail.setWordWrap(True)
        layout.addWidget(self.hardware_detail)

        layout.addWidget(self._panel_title("VOICE STREAM BUS", "INPUT VISUALIZER"))
        self.wave = SignalWave()
        layout.addWidget(self.wave)

        self.voice_status = QLabel("● VOICE LINK // STANDBY     ▣ MIC OPT-IN")
        self.voice_status.setObjectName("voiceStatus")
        layout.addWidget(self.voice_status)

        return panel

    def _right_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        layout.addWidget(self._panel_title("COMMAND CONSOLE // ACTIVITY AUDIT", "SYSTEM LOG"))

        self.chat = QTextEdit()
        self.chat.setReadOnly(True)
        self.chat.setObjectName("chat")
        self.chat.setHtml(
            "<p><span style='color:#22dcff;font-weight:700'>J.A.R.V.I.S. READY // LOCAL INTELLIGENCE ACTIVE</span><br>"
            "<span style='color:#dceffc'>Ready for natural desktop commands, file management, and system tasks.</span></p>"
            "<p><span style='color:#6d90a6;font-size:10px'>"
            "EXAMPLES: 'open Chrome' • 'organize my desktop' • 'find my python files' • 'what applications are running'"
            "</span></p>"
        )
        layout.addWidget(self.chat, 1)

        # Interactive Confirmation Banner (Hidden by default)
        self.confirm_frame = QFrame()
        self.confirm_frame.setObjectName("confirmFrame")
        self.confirm_frame.hide()
        confirm_layout = QVBoxLayout(self.confirm_frame)
        confirm_layout.setContentsMargins(10, 8, 10, 8)
        confirm_layout.setSpacing(6)

        self.confirm_label = QLabel("APPROVAL REQUIRED")
        self.confirm_label.setObjectName("confirmTitle")
        self.confirm_detail = QLabel("")
        self.confirm_detail.setObjectName("confirmDetail")
        self.confirm_detail.setWordWrap(True)

        btn_row = QHBoxLayout()
        self.btn_approve = QPushButton("✔  APPROVE & EXECUTE")
        self.btn_approve.setObjectName("approveButton")
        self.btn_approve.clicked.connect(self.approve_pending_action)
        self.btn_cancel = QPushButton("✖  CANCEL")
        self.btn_cancel.setObjectName("cancelButton")
        self.btn_cancel.clicked.connect(self.cancel_pending_action)

        btn_row.addWidget(self.btn_approve)
        btn_row.addWidget(self.btn_cancel)
        confirm_layout.addWidget(self.confirm_label)
        confirm_layout.addWidget(self.confirm_detail)
        confirm_layout.addLayout(btn_row)
        layout.addWidget(self.confirm_frame)

        self.stream = TelemetryStream()
        layout.addWidget(self.stream)
        self.matrix = DiagnosticMatrix()
        layout.addWidget(self.matrix)

        layout.addWidget(self._panel_title("DIRECTIVE CONTROLS", "QUICK ACTIONS"))

        quick = QGridLayout()
        quick.setHorizontalSpacing(6)
        quick.setVerticalSpacing(6)

        quick_actions = [
            ("SYSTEM TELEMETRY", "system status"),
            ("RUNNING APPS", "what applications are currently running"),
            ("ORGANIZE DESKTOP", "organize my desktop"),
            ("FIND PYTHON FILES", "find my python files"),
            ("OPEN CHROME", "open Chrome"),
            ("CLEAR CONSOLE", "!CLEAR"),
        ]
        for i, (name, cmd) in enumerate(quick_actions):
            btn = QPushButton("◈  " + name)
            btn.setObjectName("quickButton")
            if cmd == "!CLEAR":
                btn.clicked.connect(self.clear_console)
            else:
                btn.clicked.connect(lambda _, c=cmd: self.run_quick(c))
            quick.addWidget(btn, i // 3, i % 3)
        layout.addLayout(quick)

        self.notice = QLabel("READY  •  Safety boundary active")
        self.notice.setObjectName("notice")
        layout.addWidget(self.notice)

        input_row = QHBoxLayout()
        self.input = QLineEdit()
        self.input.setObjectName("input")
        self.input.setPlaceholderText("Enter natural language command or request...")
        self.input.returnPressed.connect(self.send)

        execute_btn = QPushButton("EXECUTE")
        execute_btn.setObjectName("executeButton")
        execute_btn.clicked.connect(self.send)

        self.voice_btn = QPushButton("MIC PUSH-TO-TALK")
        self.voice_btn.setObjectName("voiceButton")
        self.voice_btn.clicked.connect(self.listen)

        input_row.addWidget(self.input, 1)
        input_row.addWidget(execute_btn)
        input_row.addWidget(self.voice_btn)
        layout.addLayout(input_row)

        return panel

    def refresh_telemetry(self) -> None:
        if self.monitor_busy:
            return
        self.monitor_busy = True
        worker = Worker(self.app.monitor.snapshot)
        worker.signals.finished.connect(self.apply_hardware_snapshot)
        self._start_worker(worker)

    def apply_hardware_snapshot(self, h) -> None:
        self.monitor_busy = False
        if not hasattr(h, "cpu"):
            return
        self.cpu.update_metric(f"{h.cpu:.0f}%", h.cpu)
        self.ram.update_metric(f"{h.ram_used_gb:.1f} / {h.ram_total_gb:.1f} GB", h.ram_percent)
        gpu_pct = h.gpu_percent or 0
        self.gpu.update_metric(f"{gpu_pct:.0f}%" if h.gpu_percent is not None else "STANDBY", gpu_pct)
        battery = h.battery if h.battery is not None else 100
        self.power.update_metric(f"{battery:.0f}%" if h.battery is not None else "AC POWER", battery)

        vram = f"VRAM {h.vram_used_gb:.1f} / {h.vram_total_gb:.1f} GB" if h.vram_total_gb else "VRAM: Standard"
        temp = f" • {h.temperature:.0f}°C" if h.temperature is not None else ""
        self.hardware_detail.setText(
            f"{h.gpu_name}\n{vram}{temp}\nCUDA: {'READY' if h.cuda else 'CPU FALLBACK'} • DISK (C:): {h.disk_percent:.0f}%"
        )
        self.status_chip.setText("● PRIVATE MODE" if self.app.settings.privacy_mode else f"● ONLINE // {self.app.settings.performance_mode.upper()}")

    def send(self) -> None:
        text = self.input.text().strip()
        if not text:
            return
        self.input.clear()
        self.chat.append(f"<p><span style='color:#6e9db3;font-weight:700'>USER DIRECTIVE:</span><br>{text}</p>")
        self.orb.state = "THINKING"
        self.notice.setText("ANALYZING DIRECTIVE • Processing safely outside UI thread...")
        worker = Worker(lambda: self.app.router.handle(text))
        worker.signals.finished.connect(self.reply)
        self._start_worker(worker)

    def run_quick(self, command: str) -> None:
        self.input.setText(command)
        self.send()

    def clear_console(self) -> None:
        self.chat.clear()
        self.chat.append("<p><span style='color:#22dcff;font-weight:700'>CONSOLE CLEARED</span></p>")

    def listen(self) -> None:
        if not self.app.settings.voice_enabled:
            self.notice.setText("Voice interaction is disabled in configuration.")
            return
        self.voice_btn.setEnabled(False)
        self.orb.state = "THINKING"
        self.voice_status.setText("● VOICE LINK // LISTENING...     ▣ MIC ACTIVE")
        self.notice.setText("LISTENING • Speak your command clearly...")
        worker = VoiceWorker()
        worker.signals.finished.connect(self.voice_result)
        self._start_worker(worker)

    def voice_result(self, result) -> None:
        ok, message = result
        self.voice_btn.setEnabled(True)
        if not ok:
            self.orb.state = "ERROR"
            self.voice_status.setText("● VOICE LINK // OFFLINE     ▣ CHECK MIC")
            self.notice.setText("Voice recognition error: " + message)
            return
        self.voice_status.setText("● VOICE LINK // TRANSCRIBED     ▣ 100% SIGNAL")
        self.input.setText(message)
        self.notice.setText(f"Transcribed: '{message}'")
        self.send()

    def reply(self, result: ToolResult) -> None:
        self.orb.state = "IDLE" if result.ok else "ERROR"
        tint = "#22dcff" if result.ok else "#ff7777"

        # Format and append output
        formatted = result.message.replace("\n", "<br>")
        self.chat.append(f"<p><span style='color:{tint};font-weight:700'>J.A.R.V.I.S. RESPONSE:</span><br>{formatted}</p>")

        # Handle confirmation requirement
        if result.requires_confirmation and result.pending_action:
            self.pending_action = result.pending_action
            self.confirm_detail.setText(
                f"Proposed Operation: {result.pending_action.get('description', result.pending_action.get('tool_name'))}\n"
                f"Risk Level: {result.pending_action.get('risk', 'HIGH').upper()}"
            )
            self.confirm_frame.show()
            self.notice.setText("⚠️ EXPLICIT APPROVAL REQUIRED • Review details above")
        else:
            self.confirm_frame.hide()
            self.notice.setText("READY • Safety protocols active")

        # Spoken audio reply if TTS enabled
        if result.ok and self.app.settings.tts_enabled:
            self.orb.state = "SPEAKING"
            spoken = result.message.split("\n\n")[0][:180]
            self.voice_status.setText("● VOICE LINK // SPEAKING")
            speaker = SpeechWorker(spoken)
            speaker.signals.finished.connect(self.speech_finished)
            self._start_worker(speaker)

    def approve_pending_action(self) -> None:
        if not self.pending_action:
            return
        action = self.pending_action
        self.pending_action = None
        self.confirm_frame.hide()

        self.chat.append("<p><span style='color:#00ffcc;font-weight:700'>AUTHORIZATION GRANTED</span><br>Executing confirmed directive...</p>")
        self.orb.state = "EXECUTING"
        self.notice.setText("EXECUTING AUTHORIZED DIRECTIVE...")
        worker = Worker(lambda: self.app.router.handle("", approved=True, pending_action=action))
        worker.signals.finished.connect(self.reply)
        self._start_worker(worker)

    def cancel_pending_action(self) -> None:
        self.pending_action = None
        self.confirm_frame.hide()
        self.chat.append("<p><span style='color:#ff7777;font-weight:700'>AUTHORIZATION ABORTED</span><br>Operation safely cancelled by user.</p>")
        self.notice.setText("OPERATION CANCELLED • Ready")

    def speech_finished(self, _) -> None:
        self.orb.state = "IDLE"
        self.voice_status.setText("● VOICE LINK // STANDBY     ▣ 100% SIGNAL")

    def _stylesheet(self) -> str:
        return """
        QWidget#root { background-color: #03080e; }
        QFrame#panel { background-color: rgba(6, 19, 29, 215); border: 1px solid #16465c; border-radius: 8px; }
        QLabel#brand { font-size: 20px; font-weight: 900; color: #eafaff; letter-spacing: 1.5px; }
        QLabel#subtitle { font-size: 10px; font-weight: 700; color: #5d8ea6; letter-spacing: 1px; }
        QLabel#statusChip { background: #062b3a; color: #2bf0ff; border: 1px solid #1fa3c4; border-radius: 10px; padding: 4px 10px; font-size: 10px; font-weight: 800; letter-spacing: 0.8px; }
        QFrame#titleRail { background-color: #061722; border-bottom: 1px solid #1b4f69; border-radius: 4px; }
        QLabel#panelTitle { font-size: 11px; font-weight: 900; color: #dff7ff; letter-spacing: 1px; }
        QLabel#panelDetail { font-size: 9px; font-weight: 700; color: #52869f; letter-spacing: 0.8px; }
        QLabel#coreReadout { font-size: 9px; font-weight: 700; color: #7cb1c9; line-height: 14px; }
        QFrame#metricCard { background-color: #081a26; border: 1px solid #1c5573; border-radius: 6px; }
        QLabel#metricLabel { font-size: 9px; font-weight: 800; color: #72a8c2; letter-spacing: 0.8px; }
        QLabel#metricValue { font-size: 14px; font-weight: 900; color: #eafaff; }
        QLabel#hardwareDetail { background: #071722; border: 1px solid #164057; border-radius: 6px; padding: 8px; font-size: 9px; font-weight: 600; color: #a5d7eb; }
        QLabel#voiceStatus { background: #05141e; border: 1px solid #153c52; border-radius: 5px; padding: 6px 10px; font-size: 9px; font-weight: 700; color: #87c5e0; letter-spacing: 0.8px; }
        QTextEdit#chat { background-color: #040e17; border: 1px solid #163f57; border-radius: 6px; color: #dceef7; font-family: 'Segoe UI', Consolas; font-size: 11px; padding: 10px; }

        QFrame#confirmFrame { background-color: #170d10; border: 2px solid #ff4b55; border-radius: 6px; }
        QLabel#confirmTitle { color: #ff6b75; font-size: 11px; font-weight: 900; letter-spacing: 1px; }
        QLabel#confirmDetail { color: #fce6e8; font-size: 10px; }
        QPushButton#approveButton { background-color: #00ffcc; color: #021a14; border: none; border-radius: 4px; padding: 7px 14px; font-size: 10px; font-weight: 900; }
        QPushButton#approveButton:hover { background-color: #66ffdd; }
        QPushButton#cancelButton { background-color: #2b1115; color: #ff9da4; border: 1px solid #ff4b55; border-radius: 4px; padding: 7px 14px; font-size: 10px; font-weight: 800; }
        QPushButton#cancelButton:hover { background-color: #471b22; }

        QPushButton#quickButton { background: #09202c; border: 1px solid #1b627a; border-radius: 5px; color: #d7f6ff; padding: 7px; font-size: 9px; font-weight: 700; }
        QPushButton#quickButton:hover { background: #164553; border-color: #a9f5ff; }
        QLabel#notice { background: #071118; border: 1px solid #20475a; border-radius: 5px; color: #a4d6e4; padding: 6px 10px; font-size: 9px; }
        QLineEdit#input { background-color: #05141e; border: 1px solid #226787; border-radius: 6px; color: #eafaff; font-size: 11px; padding: 8px 12px; }
        QLineEdit#input:focus { border: 1px solid #24dcff; }
        QPushButton#executeButton { background: #22dcff; color: #02141c; border: none; border-radius: 6px; padding: 8px 16px; font-size: 10px; font-weight: 900; letter-spacing: 0.8px; }
        QPushButton#executeButton:hover { background: #55e4ff; }
        QPushButton#voiceButton { background: #102d3d; color: #dffaff; border: 1px solid #3cccf3; border-radius: 6px; padding: 8px 14px; font-size: 10px; font-weight: 800; }
        QPushButton#voiceButton:hover { background: #15516b; }
        QPushButton#voiceButton:disabled { color: #587987; border-color: #24414f; background: #0b1820; }
        """
