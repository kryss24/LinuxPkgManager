from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QScrollArea, QDialog, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from core.maintenance_worker import MaintenanceWorker

class OrphanDetailsDialog(QDialog):
    def __init__(self, orphans, size, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Orphaned Packages Details")
        self.setFixedSize(500, 400)
        self.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title = QLabel(f"The following {len(orphans)} packages will be removed:")
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(title)
        
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setText("\n".join(orphans))
        self.text_area.setStyleSheet("background-color: #2d2d2d; border: 1px solid #3d3d3d; border-radius: 6px; padding: 10px; color: #cccccc;")
        layout.addWidget(self.text_area)
        
        size_label = QLabel(f"Estimated space to be freed: {size}")
        size_label.setStyleSheet("color: #3584e4; font-weight: bold;")
        layout.addWidget(size_label)
        
        close_btn = QPushButton("Close")
        close_btn.setObjectName("actionBtn")
        close_btn.setStyleSheet("height: 36px; background-color: #3d3d3d; border-radius: 6px; font-weight: bold;")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

class MaintenanceView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("maintenanceView")
        self.orphans = []
        self.orphan_size = "0 KB"
        self.init_ui()
        self.refresh_cache_info()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 20, 40, 40)
        layout.setSpacing(24)

        # Title
        title = QLabel("System Maintenance")
        title.setObjectName("appTitle")
        layout.addWidget(title)

        desc = QLabel("Optimize your system by removing unused packages and cleaning cache.")
        desc.setObjectName("pkgMeta")
        layout.addWidget(desc)

        # 1. Orphans Card
        self.orphan_card = QFrame()
        self.orphan_card.setObjectName("maintenanceCard")
        orphan_layout = QVBoxLayout(self.orphan_card)
        orphan_layout.setContentsMargins(20, 20, 20, 20)

        h_layout = QHBoxLayout()
        v_info = QVBoxLayout()
        self.orphan_title = QLabel("Orphaned Packages")
        self.orphan_title.setObjectName("cardTitle")
        self.orphan_status = QLabel("Scan your system to find unused dependencies.")
        self.orphan_status.setObjectName("cardDesc")
        v_info.addWidget(self.orphan_title)
        v_info.addWidget(self.orphan_status)
        h_layout.addLayout(v_info)
        h_layout.addStretch()

        self.btn_details = QPushButton("View Details")
        self.btn_details.setObjectName("sidebarBtn")
        self.btn_details.setFixedWidth(120)
        self.btn_details.hide()
        self.btn_details.clicked.connect(self.show_orphan_details)
        h_layout.addWidget(self.btn_details)

        self.btn_scan_orphans = QPushButton("Scan Now")
        self.btn_scan_orphans.setObjectName("actionBtn")
        self.btn_scan_orphans.setFixedWidth(140)
        self.btn_scan_orphans.clicked.connect(self.scan_orphans)
        h_layout.addWidget(self.btn_scan_orphans)
        
        orphan_layout.addLayout(h_layout)
        layout.addWidget(self.orphan_card)

        # 2. APT Cache Card
        self.cache_card = QFrame()
        self.cache_card.setObjectName("maintenanceCard")
        cache_layout = QVBoxLayout(self.cache_card)
        cache_layout.setContentsMargins(20, 20, 20, 20)

        h_cache = QHBoxLayout()
        v_cache_info = QVBoxLayout()
        self.cache_title = QLabel("APT Cache")
        self.cache_title.setObjectName("cardTitle")
        self.cache_status = QLabel("Calculating cache size...")
        self.cache_status.setObjectName("cardDesc")
        v_cache_info.addWidget(self.cache_title)
        v_cache_info.addWidget(self.cache_status)
        h_cache.addLayout(v_cache_info)
        h_cache.addStretch()

        self.btn_clean_cache = QPushButton("Clean Cache")
        self.btn_clean_cache.setObjectName("dangerBtn")
        self.btn_clean_cache.setFixedWidth(140)
        self.btn_clean_cache.clicked.connect(self.clean_cache)
        h_cache.addWidget(self.btn_clean_cache)
        
        cache_layout.addLayout(h_cache)
        layout.addWidget(self.cache_card)

        layout.addStretch()

    def refresh_cache_info(self):
        self.worker_cache = MaintenanceWorker("scan_cache")
        self.worker_cache.finished.connect(self.on_cache_scanned)
        self.worker_cache.start()

    def on_cache_scanned(self, type, success, message, data):
        if success:
            self.cache_status.setText(f"Local repository archives: {data} can be freed.")
        else:
            self.cache_status.setText("Could not determine cache size.")

    def scan_orphans(self):
        self.btn_scan_orphans.setEnabled(False)
        self.orphan_status.setText("Scanning system... please wait.")
        self.btn_details.hide()
        self.worker = MaintenanceWorker("scan_orphans")
        self.worker.finished.connect(self.on_orphans_scanned)
        self.worker.start()

    def on_orphans_scanned(self, type, success, message, data):
        self.btn_scan_orphans.setEnabled(True)
        if success:
            self.orphans, self.orphan_size = data
            if self.orphans:
                self.orphan_status.setText(f"Found {len(self.orphans)} orphans ({self.orphan_size} can be freed).")
                self.btn_scan_orphans.setText("Clean Orphans")
                self.btn_scan_orphans.clicked.disconnect()
                self.btn_scan_orphans.clicked.connect(self.clean_orphans)
                self.btn_details.show()
            else:
                self.orphan_status.setText("Your system is clean! No orphans found.")
        else:
            self.orphan_status.setText(f"Error: {message}")

    def show_orphan_details(self):
        if self.orphans:
            diag = OrphanDetailsDialog(self.orphans, self.orphan_size, self)
            diag.exec()

    def clean_orphans(self):
        self.btn_scan_orphans.setEnabled(False)
        self.btn_details.setEnabled(False)
        self.orphan_status.setText("Cleaning system (requires password)...")
        self.worker = MaintenanceWorker("clean_orphans")
        self.worker.finished.connect(self.on_cleaned)
        self.worker.start()

    def clean_cache(self):
        self.btn_clean_cache.setEnabled(False)
        self.cache_status.setText("Cleaning cache (requires password)...")
        self.worker = MaintenanceWorker("clean_cache")
        self.worker.finished.connect(self.on_cleaned)
        self.worker.start()

    def on_cleaned(self, type, success, message, data):
        self.btn_scan_orphans.setEnabled(True)
        self.btn_clean_cache.setEnabled(True)
        self.btn_details.setEnabled(True)
        if success:
            if type == "clean_orphans":
                self.btn_scan_orphans.setText("Scan Now")
                self.btn_scan_orphans.clicked.disconnect()
                self.btn_scan_orphans.clicked.connect(self.scan_orphans)
                self.orphan_status.setText("Cleaning complete.")
                self.btn_details.hide()
                self.orphans = []
            else:
                self.cache_status.setText("Cache cleared.")
                self.refresh_cache_info()
        else:
            if type == "clean_orphans":
                self.orphan_status.setText(f"Failed: {message}")
            else:
                self.cache_status.setText(f"Failed: {message}")
