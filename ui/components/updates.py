from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QScrollArea, QProgressBar, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from core.apt_backend import AptBackend, InstallWorker
from core.snap_backend import SnapBackend
from core.flatpak_backend import FlatpakBackend

class UpdatesView(QWidget):
    updatesFound = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("updatesView")
        self.updates = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 20, 40, 40)
        layout.setSpacing(24)

        # Title
        h_title = QHBoxLayout()
        title = QLabel("System Updates")
        title.setObjectName("appTitle")
        h_title.addWidget(title)
        h_title.addStretch()
        
        self.btn_refresh = QPushButton("Refresh List")
        self.btn_refresh.setObjectName("sidebarBtn")
        self.btn_refresh.setFixedWidth(140)
        self.btn_refresh.clicked.connect(self.check_updates)
        h_title.addWidget(self.btn_refresh)
        
        self.btn_update_all = QPushButton("Update All")
        self.btn_update_all.setObjectName("actionBtn")
        self.btn_update_all.setFixedWidth(140)
        self.btn_update_all.clicked.connect(self.update_all)
        self.btn_update_all.hide()
        h_title.addWidget(self.btn_update_all)
        
        layout.addLayout(h_title)

        self.status_label = QLabel("Click refresh to check for available updates.")
        self.status_label.setObjectName("pkgMeta")
        layout.addWidget(self.status_label)

        # List Area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setObjectName("mainScroll")
        self.scroll_content = QWidget()
        self.scroll_content.setObjectName("scrollContainer")
        self.list_layout = QVBoxLayout(self.scroll_content)
        self.list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.scroll_content)
        layout.addWidget(self.scroll)

        # Progress Area
        self.progress_area = QFrame()
        self.progress_area.setObjectName("maintenanceCard")
        p_layout = QVBoxLayout(self.progress_area)
        p_layout.setContentsMargins(16, 16, 16, 16)
        
        self.progress_label = QLabel("Update progress will appear here.")
        self.progress_label.setObjectName("cardDesc")
        p_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(12)
        p_layout.addWidget(self.progress_bar)
        
        layout.addWidget(self.progress_area)
        self.progress_area.hide()

    def check_updates(self):
        self.status_label.setText("Checking for updates... please wait.")
        self.btn_refresh.setEnabled(False)
        self.clear_list()
        
        self.updates = []
        self.worker_apt = UpdateCheckWorker()
        self.worker_apt.finished.connect(self.on_updates_loaded)
        self.worker_apt.start()

    def on_updates_loaded(self, updates):
        self.updates.extend(updates)
        self.status_label.setText(f"Found {len(self.updates)} updates available.")
        self.updatesFound.emit(len(self.updates))
        self.btn_refresh.setEnabled(True)
        
        if self.updates:
            self.btn_update_all.show()
            for up in self.updates:
                self.add_update_card(up)
        else:
            self.btn_update_all.hide()

    def add_update_card(self, up):
        card = QFrame()
        card.setObjectName("packageCard")
        card.setStyleSheet("background-color: #2d2d2d; border-radius: 10px; border: 1px solid #3d3d3d;")
        card.setFixedHeight(80)
        c_layout = QHBoxLayout(card)
        
        v_info = QVBoxLayout()
        name = QLabel(up["name"])
        name.setStyleSheet("font-size: 15px; font-weight: bold;")
        version = QLabel(f"New Version: {up['version']} ({up['type']})")
        version.setStyleSheet("font-size: 12px; color: #a0a0a0;")
        v_info.addWidget(name)
        v_info.addWidget(version)
        c_layout.addLayout(v_info)
        c_layout.addStretch()
        
        btn = QPushButton("Update")
        btn.setObjectName("actionBtn")
        btn.setFixedWidth(100)
        btn.clicked.connect(lambda: self.start_update(up))
        c_layout.addWidget(btn)
        
        self.list_layout.addWidget(card)

    def clear_list(self):
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def start_update(self, up):
        self.progress_area.show()
        self.progress_label.setText(f"Updating {up['name']}...")
        self.progress_bar.setRange(0, 0) # Indeterminate
        
        self.worker = InstallWorker(up["name"], up["type"], action="upgrade")
        self.worker.progress.connect(lambda m: self.progress_label.setText(m))
        self.worker.finished.connect(self.on_update_finished)
        self.worker.start()

    def update_all(self):
        # Implementation for update-all could be sequential or using a bulk command
        if self.updates:
            self.start_update(self.updates[0]) # Start with first for now

    def on_update_finished(self, success, message):
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(1)
        self.progress_label.setText(message)
        if success:
            self.check_updates()

class UpdateCheckWorker(QThread):
    finished = pyqtSignal(list)
    def run(self):
        updates = []
        updates.extend(AptBackend.get_upgradable())
        updates.extend(SnapBackend.get_upgradable())
        updates.extend(FlatpakBackend.get_upgradable())
        self.finished.emit(updates)
