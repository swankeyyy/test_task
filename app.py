from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QHBoxLayout,
)
from PyQt5.QtCore import QSize, QTimer, Qt

import sqlite3
import psutil
import sys
from datetime import datetime


class App(QWidget):
    """Main app for monitoring system resources"""

    def __init__(self):
        super().__init__()

        # set default values and create db
        self.recording = False
        self._prepare_database()

        # window settings
        self.setWindowTitle("Мониторинг ресурсов")
        self.setFixedSize(QSize(400, 600))

        # data layout
        layout = QVBoxLayout()
        self.title = QLabel("Уровень загруженности:", self)
        self.cpu = QLabel("ЦП: ", self)
        self.ram = QLabel("ОЗУ: ", self)
        self.hdd = QLabel("HDD: ", self)
        layout.addWidget(self.title, alignment=Qt.AlignCenter)
        layout.addWidget(self.cpu)
        layout.addWidget(self.ram)
        layout.addWidget(self.hdd)
        self.setLayout(layout)

        # interval layout
        self.interval_input = QSpinBox(self)
        self.interval_input.setRange(1, 3600)
        self.interval_input.setValue(1)
        self.interval_label = QLabel("Время обновления (секунд): ", self)
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(self.interval_label)
        interval_layout.addWidget(self.interval_input)

        layout.addLayout(interval_layout)
        self.time_elapsed = QLabel("Время записи: ", self)
        layout.addWidget(self.time_elapsed, alignment=Qt.AlignCenter)

        # button
        self.record_button = QPushButton("Начать запись в БД", self)
        self.record_button.clicked.connect(self._button_toggle)
        layout.addWidget(self.record_button)

        # timer of update
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._data_change)
        self.timer.start(1000)

    def _prepare_database(self):
        """Create tables if db not exists"""
        self.conn = sqlite3.connect("monitoring_db.db")
        self.cursor = self.conn.cursor()
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS system_stats (
                time DATETIME DEFAULT CURRENT_TIMESTAMP,
                cpu FLOAT,
                ram FLOAT,
                hdd FLOAT
            )
        """
        )
        self.conn.commit()

    def _data_change(self):
        """function that change data in labels by choosen interval"""

        # stats by psutil
        cpu = psutil.cpu_percent(interval=1)
        ram = round(psutil.virtual_memory().free / (1024**3), 1)
        total_ram = round(psutil.virtual_memory().total / (1024**3), 1)
        hdd = round(psutil.disk_usage("/").free / (1024**3), 2)
        total_hdd = round(psutil.disk_usage("/").total / (1024**3), 2)

        # refresh labels
        self.cpu.setText(f"CPU Usage:    {cpu}%")
        self.ram.setText(f"RAM Usage:    {ram} GB / {total_ram} GB")
        self.hdd.setText(f"Disk Usage:    {hdd}GB / {total_hdd} GB")

        # write data to db
        if self.recording:
            self._write_data_on_db(cpu, ram, hdd)

        # Обновляем таймер с новым интервалом
        self.timer.setInterval(self.interval_input.value() * 1000)

    def _write_data_on_db(self, cpu, ram, hdd):
        """Takes values and insert into table"""
        self.cursor.execute(
            """
            INSERT INTO system_stats (cpu, ram, hdd)
            VALUES (?, ?, ?)
            """,
            (cpu, ram, hdd),
        )
        self.conn.commit()

    def _button_toggle(self):
        """Record button toggle"""
        self.recording = not self.recording
        if not self.recording:
            self.record_button.setText("Начать запись в БД")
            self.timer.timeout.disconnect(self._update_timer)
            self.start_time = None
        else:
            self.record_button.setText("Остановить запись")
            self.start_time = datetime.now()
            self.timer.timeout.connect(self._update_timer)

    def _update_timer(self):
        """timer for label with record time"""
        time = datetime.now() - self.start_time
        self.time_elapsed.setText(f"Время записи: {time.seconds}с")


app = QApplication(sys.argv)
window = App()
window.show()
app.exec()
