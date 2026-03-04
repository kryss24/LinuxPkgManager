from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QScrollArea, QLineEdit, QComboBox, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from core.apt_backend import AptBackend
from core.snap_backend import SnapBackend

class HistoryView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("historyView")
        self.history = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 20, 40, 40)
        layout.setSpacing(20)

        # Title
        title = QLabel("Installation History")
        title.setObjectName("appTitle")
        layout.addWidget(title)

        # Filter Bar
        h_filters = QHBoxLayout()
        h_filters.setSpacing(10)
        
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Filter history (package name)...")
        self.search_bar.setObjectName("searchBar")
        self.search_bar.textChanged.connect(self.filter_history)
        h_filters.addWidget(self.search_bar)
        
        self.action_combo = QComboBox()
        self.action_combo.addItems(["All Actions", "Install", "Upgrade", "Remove"])
        self.action_combo.setObjectName("sortCombo")
        self.action_combo.currentIndexChanged.connect(self.filter_history)
        h_filters.addWidget(self.action_combo)
        
        self.btn_refresh = QPushButton("🔄")
        self.btn_refresh.setFixedSize(36, 36)
        self.btn_refresh.clicked.connect(self.load_history)
        h_filters.addWidget(self.btn_refresh)
        
        layout.addLayout(h_filters)

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

    def load_history(self):
        self.worker = HistoryWorker()
        self.worker.finished.connect(self.on_history_loaded)
        self.worker.start()

    def on_history_loaded(self, history):
        self.history = history
        self.filter_history()

    def filter_history(self):
        self.clear_list()
        search_text = self.search_bar.text().lower()
        action_filter = self.action_combo.currentText()
        
        for h in self.history:
            if search_text and search_text not in h["package"].lower(): continue
            if action_filter != "All Actions" and action_filter.lower() not in h["action"].lower(): continue
            self.add_history_row(h)

    def add_history_row(self, h):
        row = QFrame()
        row.setObjectName("packageCard")
        row.setStyleSheet("background-color: transparent; border-bottom: 1px solid #3d3d3d; border-radius: 0px;")
        row.setFixedHeight(60)
        r_layout = QHBoxLayout(row)
        
        date = QLabel(h["date"])
        date.setStyleSheet("color: #888a85; font-size: 11px;")
        date.setFixedWidth(140)
        r_layout.addWidget(date)
        
        action = QLabel(h["action"])
        action_color = "#3584e4" if h["action"] == "Install" else "#ef4444" if h["action"] == "Remove" else "#10b981"
        action.setStyleSheet(f"color: {action_color}; font-weight: bold; font-size: 13px;")
        action.setFixedWidth(80)
        r_layout.addWidget(action)
        
        pkg = QLabel(h["package"])
        pkg.setStyleSheet("font-weight: bold; font-size: 14px;")
        r_layout.addWidget(pkg)
        
        ver = QLabel(h["version"])
        ver.setStyleSheet("color: #a0a0a0; font-size: 12px;")
        r_layout.addWidget(ver)
        
        r_layout.addStretch()
        
        type_badge = QLabel(h["type"])
        type_badge.setStyleSheet("color: #a0a0a0; font-size: 10px; border: 1px solid #3d3d3d; border-radius: 4px; padding: 2px 6px;")
        r_layout.addWidget(type_badge)
        
        self.list_layout.addWidget(row)

    def clear_list(self):
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

class HistoryWorker(QThread):
    finished = pyqtSignal(list)
    def run(self):
        history = []
        history.extend(AptBackend.get_history())
        history.extend(SnapBackend.get_history())
        # Sort by date
        history.sort(key=lambda x: x["date"], reverse=True)
        self.finished.emit(history)
