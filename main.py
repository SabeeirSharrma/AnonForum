import sys
import json
import subprocess
import requests
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QPushButton, QTextEdit, QLabel, QLineEdit, QSpinBox, QMessageBox
)
from PyQt5.QtCore import QTimer
import time

CONFIG_PATH = "config.json"

class ForumServerUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Forum Server Control")
        self.resize(800, 600)

        # Load config
        with open(CONFIG_PATH, "r") as f:
            self.config = json.load(f)

        # Server process
        self.server_proc = None

        # Layouts
        main_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()

        # Thread list
        self.thread_list = QListWidget()
        left_layout.addWidget(QLabel("Threads"))
        left_layout.addWidget(self.thread_list)

        # Buttons
        self.btn_delete_thread = QPushButton("Delete Selected Forum")
        self.btn_wipe_all = QPushButton("Wipe All Forums")
        left_layout.addWidget(self.btn_delete_thread)
        left_layout.addWidget(self.btn_wipe_all)

        # Server log
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        right_layout.addWidget(QLabel("Server Log"))
        right_layout.addWidget(self.log_text)

        # Config controls
        self.host_input = QLineEdit(self.config.get("HOST", "0.0.0.0"))
        self.port_input = QSpinBox()
        self.port_input.setMaximum(65535)
        self.port_input.setValue(self.config.get("PORT", 5000))
        self.username_limit = QSpinBox()
        self.username_limit.setMaximum(1000)
        self.username_limit.setValue(self.config.get("LIMITS", {}).get("USERNAME", 50))
        self.thread_title_limit = QSpinBox()
        self.thread_title_limit.setMaximum(1000)
        self.thread_title_limit.setValue(self.config.get("LIMITS", {}).get("THREAD_TITLE", 200))
        self.post_content_limit = QSpinBox()
        self.post_content_limit.setMaximum(10000)
        self.post_content_limit.setValue(self.config.get("LIMITS", {}).get("POST_CONTENT", 1000))

        right_layout.addWidget(QLabel("Host:"))
        right_layout.addWidget(self.host_input)
        right_layout.addWidget(QLabel("Port:"))
        right_layout.addWidget(self.port_input)
        right_layout.addWidget(QLabel("Max Username Length:"))
        right_layout.addWidget(self.username_limit)
        right_layout.addWidget(QLabel("Max Thread Title Length:"))
        right_layout.addWidget(self.thread_title_limit)
        right_layout.addWidget(QLabel("Max Post Content Length:"))
        right_layout.addWidget(self.post_content_limit)

        # Server control buttons
        self.btn_stop = QPushButton("Stop Server")
        self.btn_restart = QPushButton("Restart Server")
        right_layout.addWidget(self.btn_stop)
        right_layout.addWidget(self.btn_restart)

        # Set layouts
        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 2)
        self.setLayout(main_layout)

        # Connect buttons
        self.btn_delete_thread.clicked.connect(self.delete_selected_thread)
        self.btn_wipe_all.clicked.connect(self.wipe_all_threads)
        self.btn_stop.clicked.connect(self.stop_server)
        self.btn_restart.clicked.connect(self.restart_server)

        # Timer for auto-refreshing threads
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.update_thread_list)
        self.refresh_timer.start(5000)  # every 5 seconds

        # Start server on launch
        self.start_server()
        self.update_thread_list()

    def append_log(self, msg):
        self.log_text.append(msg)

    def start_server(self):
        self.save_config()
        if self.server_proc:
            self.append_log("Server already running.")
            return
        try:
            self.server_proc = subprocess.Popen([sys.executable, "server.py"])
            self.append_log("Server started.")
        except Exception as e:
            self.append_log(f"Failed to start server: {e}")

    def stop_server(self):
        if self.server_proc:
            self.server_proc.terminate()
            self.server_proc.wait()
            self.server_proc = None
            self.append_log("Server stopped.")
        else:
            self.append_log("Server is not running.")

    def restart_server(self):
        self.stop_server()
        self.append_log("Restarting server...")
        time.sleep(3)
        self.start_server()

    def save_config(self):
        self.config["HOST"] = self.host_input.text()
        self.config["PORT"] = self.port_input.value()
        self.config["LIMITS"]["USERNAME"] = self.username_limit.value()
        self.config["LIMITS"]["THREAD_TITLE"] = self.thread_title_limit.value()
        self.config["LIMITS"]["POST_CONTENT"] = self.post_content_limit.value()
        with open(CONFIG_PATH, "w") as f:
            json.dump(self.config, f, indent=2)
        self.append_log("Config saved.")

    def update_thread_list(self):
        try:
            resp = requests.get(f"http://{self.config['HOST']}:{self.config['PORT']}/api/threads")
            threads = resp.json()
            self.thread_list.clear()
            for t in threads:
                item_text = f"{t['title']} [{t['id']}]"
                self.thread_list.addItem(item_text)
        except Exception as e:
            self.append_log(f"Error fetching threads: {e}")

    def delete_selected_thread(self):
        selected = self.thread_list.currentItem()
        if not selected:
            QMessageBox.warning(self, "No selection", "Please select a thread to delete.")
            return
        text = selected.text()
        thread_id = text.split('[')[-1].replace(']', '').strip()
        try:
            resp = requests.delete(f"http://{self.config['HOST']}:{self.config['PORT']}/api/threads/{thread_id}")
            if resp.status_code == 200:
                self.append_log(f"Thread {thread_id} deleted.")
                self.update_thread_list()
            else:
                self.append_log(f"Failed to delete thread {thread_id}: {resp.text}")
        except Exception as e:
            self.append_log(f"Error deleting thread: {e}")

    def wipe_all_threads(self):
        reply = QMessageBox.question(self, "Confirm Wipe",
                                     "Are you sure you want to wipe ALL forums? This cannot be undone.",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                resp = requests.delete(f"http://{self.config['HOST']}:{self.config['PORT']}/api/threads/wipe")
                if resp.status_code == 200:
                    self.append_log("All threads wiped.")
                    self.update_thread_list()
                else:
                    self.append_log(f"Failed to wipe threads: {resp.text}")
            except Exception as e:
                self.append_log(f"Error wiping threads: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = ForumServerUI()
    ui.show()
    sys.exit(app.exec_())
