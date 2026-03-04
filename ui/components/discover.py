from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QScrollArea, QLineEdit, QProgressBar, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from core.apt_backend import AptBackend, InstallWorker
from core.snap_backend import SnapBackend
from core.flatpak_backend import FlatpakBackend

class DiscoverView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("discoverView")
        self.results = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 20, 40, 40)
        layout.setSpacing(24)

        # Title
        title = QLabel("Discover Packages")
        title.setObjectName("appTitle")
        layout.addWidget(title)

        # Search Bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search for new apps and packages (APT, Snap, Flatpak)...")
        self.search_bar.setObjectName("searchBar")
        self.search_bar.setFixedHeight(40)
        self.search_bar.textChanged.connect(self.on_search_changed)
        layout.addWidget(self.search_bar)

        self.status_label = QLabel("Enter a query to start searching.")
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
        self.progress_label = QLabel("Install progress will appear here.")
        p_layout.addWidget(self.progress_label)
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(12)
        p_layout.addWidget(self.progress_bar)
        layout.addWidget(self.progress_area)
        self.progress_area.hide()

        # Search timer
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.do_search)

    def on_search_changed(self, text):
        if len(text) >= 2:
            self.search_timer.start(500) # Debounce 500ms for heavy searches

    def do_search(self):
        query = self.search_bar.text()
        self.status_label.setText(f"Searching for '{query}'...")
        self.clear_list()
        
        self.worker = SearchWorker(query)
        self.worker.finished.connect(self.on_results_loaded)
        self.worker.start()

    def on_results_loaded(self, results):
        self.results = results
        self.status_label.setText(f"Found {len(self.results)} results.")
        for res in self.results:
            self.add_result_card(res)

    def add_result_card(self, res):
        card = QFrame()
        card.setObjectName("packageCard")
        card.setStyleSheet("background-color: #2d2d2d; border-radius: 10px; border: 1px solid #3d3d3d;")
        card.setFixedHeight(100)
        c_layout = QHBoxLayout(card)
        
        v_info = QVBoxLayout()
        name_row = QHBoxLayout()
        name = QLabel(res["name"])
        name.setStyleSheet("font-size: 15px; font-weight: bold;")
        badge_color = "#3584e4" if res["type"] == "APT" else "#ec4899" if res["type"] == "Snap" else "#33d17a"
        badge = QLabel(res["type"].upper())
        badge.setStyleSheet(f"background-color: {badge_color}; color: white; border-radius: 4px; padding: 2px 8px; font-size: 10px; font-weight: bold;")
        name_row.addWidget(name)
        name_row.addWidget(badge)
        name_row.addStretch()
        v_info.addLayout(name_row)
        
        desc_text = res["description"].split('\n')[0]
        if len(desc_text) > 100: desc_text = desc_text[:97] + "..."
        desc = QLabel(desc_text)
        desc.setStyleSheet("font-size: 12px; color: #a0a0a0;")
        desc.setWordWrap(True)
        v_info.addWidget(desc)
        c_layout.addLayout(v_info)
        
        c_layout.addStretch()
        
        btn = QPushButton("Install")
        btn.setObjectName("actionBtn")
        btn.setFixedWidth(100)
        btn.clicked.connect(lambda: self.start_install(res))
        c_layout.addWidget(btn)
        
        self.list_layout.addWidget(card)

    def clear_list(self):
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def start_install(self, res):
        self.progress_area.show()
        self.progress_label.setText(f"Installing {res['name']}...")
        self.progress_bar.setRange(0, 0)
        
        self.worker_inst = InstallWorker(res["name"], res["type"], action="install")
        self.worker_inst.progress.connect(lambda m: self.progress_label.setText(m))
        self.worker_inst.finished.connect(self.on_install_finished)
        self.worker_inst.start()

    def on_install_finished(self, success, message):
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(1)
        self.progress_label.setText(message)

class SearchWorker(QThread):
    finished = pyqtSignal(list)
    def __init__(self, query):
        super().__init__()
        self.query = query
    def run(self):
        results = []
        results.extend(AptBackend.search_packages(self.query))
        results.extend(SnapBackend.search_snaps(self.query))
        results.extend(FlatpakBackend.search_flatpaks(self.query))
        self.finished.emit(results)
