"""ESP32-S3 two-axis turret: desktop TCP control UI (motion placeholders)."""
from __future__ import annotations

import queue
import select
import socket
import sys
import time
from datetime import datetime

from PySide6.QtCore import QObject, QThread, Qt, Signal, Slot
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication, QDoubleSpinBox, QFrame, QGridLayout, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox,
    QPushButton, QSpinBox, QTextEdit, QVBoxLayout, QWidget
)


class TcpWorker(QObject):
    connected = Signal()
    disconnected = Signal(str)
    received = Signal(str)
    error = Signal(str)
    finished = Signal()

    def __init__(self, host: str, port: int):
        super().__init__()
        self.host, self.port = host, port
        self.outgoing: queue.Queue[str] = queue.Queue()
        self.running = True

    def send(self, command: str):
        if self.running:
            self.outgoing.put(command + "\n")

    def request_stop(self):
        self.running = False

    @Slot()
    def run(self):
        reason = "Disconnected"
        sock = None
        try:
            sock = socket.create_connection((self.host, self.port), timeout=4)
            sock.setblocking(False)
            self.connected.emit()
            receive_buffer = bytearray()
            next_status = time.monotonic() + 1.0
            last_received = time.monotonic()
            while self.running:
                now = time.monotonic()
                if now >= next_status:
                    self.outgoing.put("STATUS\n")
                    next_status = now + 2.0
                try:
                    while True:
                        packet = self.outgoing.get_nowait()
                        sock.sendall(packet.encode("utf-8"))
                except queue.Empty:
                    pass

                readable, _, exceptional = select.select([sock], [], [sock], 0.10)
                if exceptional:
                    raise ConnectionError("Socket error")
                if readable:
                    data = sock.recv(4096)
                    if not data:
                        raise ConnectionError("ESP32 closed the connection")
                    last_received = time.monotonic()
                    receive_buffer.extend(data)
                    if len(receive_buffer) > 8192:
                        raise ConnectionError("Response exceeded buffer limit")
                    while b"\n" in receive_buffer:
                        line, _, remainder = receive_buffer.partition(b"\n")
                        receive_buffer = bytearray(remainder)
                        line_text = line.decode("utf-8", errors="replace").strip()
                        if line_text:
                            self.received.emit(line_text)
                if time.monotonic() - last_received > 10:
                    raise TimeoutError("No response from ESP32 for 10 seconds")
        except (OSError, TimeoutError, ConnectionError) as ex:
            reason = str(ex)
            if self.running:
                self.error.emit(reason)
        finally:
            if sock is not None:
                try:
                    sock.close()
                except OSError:
                    pass
            self.running = False
            self.disconnected.emit(reason)
            self.finished.emit()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ESP32-S3 Turret Controller")
        self.setMinimumSize(740, 690)
        self.worker: TcpWorker | None = None
        self.thread: QThread | None = None
        self.connected_now = False
        self.motor_state = "UNKNOWN"
        self._build_ui()
        self._set_connection_ui(False)
        self.log("Ready. Connect to ESP32-S3 TCP server.")

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(22, 22, 22, 20)
        layout.setSpacing(14)

        header = QLabel("Turret Controller")
        header.setObjectName("header")
        layout.addWidget(header)
        tagline = QLabel("ESP32-S3-LCD-2  •  Dual A4988  •  TCP/IP")
        tagline.setObjectName("muted")
        layout.addWidget(tagline)

        network = QGroupBox("Connection")
        nr = QHBoxLayout(network)
        nr.addWidget(QLabel("ESP32 IP"))
        self.host = QLineEdit("192.168.0.118")
        self.host.setPlaceholderText("ESP32 IP address")
        nr.addWidget(self.host, 2)
        nr.addWidget(QLabel("Port"))
        self.port = QSpinBox()
        self.port.setRange(1, 65535)
        self.port.setValue(5000)
        nr.addWidget(self.port)
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.toggle_connection)
        nr.addWidget(self.connect_button)
        layout.addWidget(network)

        summary = QGroupBox("Controller status")
        sg = QGridLayout(summary)
        self.connection_label = QLabel("Disconnected")
        self.wifi_label = QLabel("—")
        self.motors_label = QLabel("Unknown")
        self.pan_label = QLabel("Not implemented")
        self.tilt_label = QLabel("Not implemented")
        for row, (name, value) in enumerate([
            ("TCP connection", self.connection_label), ("ESP32 Wi-Fi", self.wifi_label),
            ("Motor drivers", self.motors_label), ("Pan state", self.pan_label),
            ("Tilt state", self.tilt_label),
        ]):
            sg.addWidget(QLabel(name), row, 0)
            sg.addWidget(value, row, 1)
        self.refresh_button = QPushButton("Refresh status")
        self.refresh_button.clicked.connect(lambda: self.send_command("STATUS"))
        sg.addWidget(self.refresh_button, 5, 0, 1, 2)
        layout.addWidget(summary)

        driver_box = QGroupBox("Driver control")
        dr = QHBoxLayout(driver_box)
        self.enable_button = QPushButton("Enable drivers")
        self.enable_button.clicked.connect(lambda: self.send_command("ENABLE"))
        self.disable_button = QPushButton("Disable drivers")
        self.disable_button.setObjectName("warningButton")
        self.disable_button.clicked.connect(lambda: self.send_command("DISABLE"))
        dr.addWidget(self.enable_button)
        dr.addWidget(self.disable_button)
        layout.addWidget(driver_box)

        movement = QGroupBox("Future pan / tilt commands  —  firmware placeholders")
        mg = QGridLayout(movement)
        mg.addWidget(QLabel("Pan target (degrees)"), 0, 0)
        self.pan_target = QDoubleSpinBox()
        self.pan_target.setRange(-360.0, 360.0)
        self.pan_target.setDecimals(1)
        self.pan_target.setSingleStep(5)
        self.pan_target.setSuffix(" °")
        mg.addWidget(self.pan_target, 0, 1)
        self.pan_button = QPushButton("Send PAN")
        self.pan_button.clicked.connect(lambda: self.send_command(f"PAN {self.pan_target.value():g}"))
        mg.addWidget(self.pan_button, 0, 2)

        mg.addWidget(QLabel("Tilt target (degrees)"), 1, 0)
        self.tilt_target = QDoubleSpinBox()
        self.tilt_target.setRange(-360.0, 360.0)
        self.tilt_target.setDecimals(1)
        self.tilt_target.setSingleStep(5)
        self.tilt_target.setSuffix(" °")
        mg.addWidget(self.tilt_target, 1, 1)
        self.tilt_button = QPushButton("Send TILT")
        self.tilt_button.clicked.connect(lambda: self.send_command(f"TILT {self.tilt_target.value():g}"))
        mg.addWidget(self.tilt_button, 1, 2)
        self.move_button = QPushButton("Send MOVE (both)")
        self.move_button.clicked.connect(lambda: self.send_command(
            f"MOVE {self.pan_target.value():g} {self.tilt_target.value():g}"))
        mg.addWidget(self.move_button, 2, 0, 1, 3)
        note = QLabel("Motion is NOT implemented in the ESP32 firmware yet. Commands currently return NOT_IMPLEMENTED.")
        note.setWordWrap(True)
        note.setObjectName("muted")
        mg.addWidget(note, 3, 0, 1, 3)
        layout.addWidget(movement)

        stop_row = QHBoxLayout()
        self.stop_button = QPushButton("Send STOP (placeholder only)")
        self.stop_button.setObjectName("warningButton")
        self.stop_button.clicked.connect(self.send_stop)
        stop_row.addWidget(self.stop_button)
        layout.addLayout(stop_row)
        danger_note = QLabel("STOP is NOT a functional emergency stop. Disconnecting does not necessarily disable A4988 outputs.")
        danger_note.setWordWrap(True)
        danger_note.setObjectName("warning")
        layout.addWidget(danger_note)

        layout.addWidget(QLabel("Communication log"))
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setMinimumHeight(115)
        layout.addWidget(self.log_box, 1)
        self.setStyleSheet("""
            QMainWindow, QWidget { background: #141b27; color: #e8edf6; font-family: 'Segoe UI'; font-size: 12px; }
            QLabel#header { font-size: 27px; font-weight: 700; }
            QLabel#muted { color: #9eacc1; }
            QLabel#warning { color: #ffc991; font-size: 11px; }
            QGroupBox { border: 1px solid #354157; border-radius: 9px; margin-top: 12px; padding: 13px 10px 10px; font-weight: 600; }
            QGroupBox::title { subcontrol-origin: margin; left: 13px; padding: 0 6px; }
            QLineEdit, QSpinBox, QDoubleSpinBox, QTextEdit { background: #202b3c; color: #f1f5fa; border: 1px solid #41516a; border-radius: 6px; padding: 7px; }
            QPushButton { background: #3577cb; color: #ffffff; border: 0px; border-radius: 6px; padding: 9px 13px; font-weight: 600; }
            QPushButton:hover { background: #4588de; }
            QPushButton:disabled { background: #394457; color: #8590a3; }
            QPushButton#warningButton { background: #755445; }
            QPushButton#warningButton:hover { background: #90624a; }
        """)

    def log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_box.append(f"[{timestamp}] {message}")

    def _set_connection_ui(self, connected: bool):
        self.connected_now = connected
        self.connection_label.setText("Connected" if connected else "Disconnected")
        self.connect_button.setText("Disconnect" if connected else "Connect")
        self.host.setEnabled(not connected)
        self.port.setEnabled(not connected)
        for widget in [self.refresh_button, self.enable_button, self.disable_button,
                       self.pan_button, self.tilt_button, self.move_button, self.stop_button]:
            widget.setEnabled(connected)
        if not connected:
            self.wifi_label.setText("—")
            self.motors_label.setText("Unknown")
            self.motor_state = "UNKNOWN"

    def toggle_connection(self):
        if self.connected_now or self.thread is not None:
            self.disconnect_now()
        else:
            self.connect_now()

    def connect_now(self):
        host = self.host.text().strip()
        if not host:
            QMessageBox.warning(self, "Missing IP", "Enter the ESP32 IP address.")
            return
        self.worker = TcpWorker(host, self.port.value())
        self.thread = QThread(self)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.connected.connect(self.on_connected)
        self.worker.received.connect(self.on_received)
        self.worker.error.connect(self.on_error)
        self.worker.disconnected.connect(self.on_disconnected)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(self.thread_finished)
        self.connect_button.setEnabled(False)
        self.log(f"Connecting to {host}:{self.port.value()}...")
        self.thread.start()

    @Slot()
    def thread_finished(self):
        self.thread = None
        self.worker = None
        self.connect_button.setEnabled(True)

    def disconnect_now(self):
        if self.worker:
            self.worker.request_stop()
            self.log("Disconnect requested...")
        self.connect_button.setEnabled(False)

    @Slot()
    def on_connected(self):
        self._set_connection_ui(True)
        self.log("TCP connection established")

    @Slot(str)
    def on_error(self, message: str):
        self.log(f"ERROR: {message}")

    @Slot(str)
    def on_disconnected(self, reason: str):
        self._set_connection_ui(False)
        self.log(f"TCP disconnected ({reason})")
        if self.thread is not None:
            self.connect_button.setEnabled(False)

    @Slot(str)
    def on_received(self, line: str):
        self.log("ESP32 ← " + line)
        if line.startswith("WIFI="):
            self.wifi_label.setText(line.split("=", 1)[1])
        elif line.startswith("MOTORS="):
            self.motor_state = line.split("=", 1)[1]
            self.motors_label.setText(self.motor_state)
        elif line.startswith("PAN="):
            self.pan_label.setText(line.split("=", 1)[1])
        elif line.startswith("TILT="):
            self.tilt_label.setText(line.split("=", 1)[1])
        elif line == "OK ENABLED":
            self.motors_label.setText("ENABLED")
        elif line == "OK DISABLED":
            self.motors_label.setText("DISABLED")

    def send_command(self, command: str):
        if self.worker and self.connected_now:
            self.worker.send(command)
            self.log("PC → " + command)

    def send_stop(self):
        self.send_command("STOP")
        self.log("WARNING: ESP32 STOP function is NOT_IMPLEMENTED.")

    def closeEvent(self, event):
        if self.worker:
            self.worker.request_stop()
        if self.thread is not None:
            # Allow the network thread to exit before destroying the window.
            if not self.thread.wait(5500):
                event.ignore()
                self.log("Network thread did not exit; please retry closing.")
                return
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
