from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QTabWidget, QScrollArea, QGridLayout, 
    QFrame, QGraphicsOpacityEffect, QDialog, QPushButton,
    QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, QSize, QPropertyAnimation, QRect, QEasingCurve
from PyQt6.QtGui import QIcon, QFontDatabase, QColor
from ui.package_card import PackageCard, SkeletonCard
from core.apt_backend import PackageWorker, UninstallWorker
from core.snap_backend import SnapWorker
import os

class Toast(QFrame):
    def __init__(self, message, is_error=False, parent=None):
        super().__init__(parent)
        self.setObjectName("toastError" if is_error else "toastSuccess")
        self.setFixedSize(300, 50)
        
        layout = QHBoxLayout(self)
        label = QLabel(message)
        label.setObjectName("toastMessage")
        label.setWordWrap(True)
        layout.addWidget(label)
        
        self.show()
        # Slide in animation
        self.anim = QPropertyAnimation(self, b"geometry")
        self.anim.setDuration(300)
        self.anim.setStartValue(QRect(parent.width(), parent.height() - 70, 300, 50))
        self.anim.setEndValue(QRect(parent.width() - 320, parent.height() - 70, 300, 50))
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.anim.start()
        
        QTimer.singleShot(3000, self.close_toast)

    def close_toast(self):
        self.anim.setDirection(QPropertyAnimation.Direction.Backward)
        self.anim.finished.connect(self.deleteLater)
        self.anim.start()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setObjectName("mainWindow")
        self.setWindowTitle("Package Manager GUI")
        self.setMinimumSize(1000, 700)
        
        self.packages = []
        self.filtered_packages = []
        self.active_tab = "All"
        self.search_term = ""
        
        # Debounce timer for search
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.filter_packages)
        
        self.init_ui()
        self.load_styles()
        self.load_packages()

    def load_styles(self):
        qss_path = os.path.join(os.path.dirname(__file__), "styles.qss")
        if os.path.exists(qss_path):
            with open(qss_path, "r") as f:
                self.setStyleSheet(f.read())

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Top Bar
        top_bar = QWidget()
        top_bar.setObjectName("topBar")
        top_layout = QHBoxLayout(top_bar)
        
        title = QLabel("Package Manager")
        title.setObjectName("appTitle")
        top_layout.addWidget(title)
        
        top_layout.addStretch()
        
        self.search_bar = QLineEdit()
        self.search_bar.setObjectName("searchBar")
        self.search_bar.setPlaceholderText("Search packages...")
        self.search_bar.textChanged.connect(self.on_search_changed)
        top_layout.addWidget(self.search_bar)
        
        main_layout.addWidget(top_bar)
        
        # Tabs
        self.tabs = QTabWidget()
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
        self.tab_all = QWidget()
        self.tab_apt = QWidget()
        self.tab_snap = QWidget()
        
        self.tabs.addTab(self.tab_all, "All (0)")
        self.tabs.addTab(self.tab_apt, "APT (0)")
        self.tabs.addTab(self.tab_snap, "Snap (0)")
        
        main_layout.addWidget(self.tabs)
        
        # Grid Area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(20)
        self.grid_layout.setContentsMargins(20, 20, 20, 20)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        self.scroll.setWidget(self.grid_container)
        main_layout.addWidget(self.scroll)

    def load_packages(self):
        # Show skeletons
        self.clear_grid()
        for i in range(8):
            skel = SkeletonCard()
            self.grid_layout.addWidget(skel, i // 3, i % 3)
            
        self.apt_worker = PackageWorker()
        self.apt_worker.finished.connect(self.on_packages_loaded)
        self.apt_worker.start()
        
        self.snap_worker = SnapWorker()
        self.snap_worker.finished.connect(self.on_packages_loaded)
        self.snap_worker.start()

    def on_packages_loaded(self, pkgs):
        self.packages.extend(pkgs)
        self.update_tab_counts()
        self.filter_packages()

    def update_tab_counts(self):
        apt_count = len([p for p in self.packages if p["type"] == "APT"])
        snap_count = len([p for p in self.packages if p["type"] == "Snap"])
        self.tabs.setTabText(0, f"All ({len(self.packages)})")
        self.tabs.setTabText(1, f"APT ({apt_count})")
        self.tabs.setTabText(2, f"Snap ({snap_count})")

    def on_search_changed(self, text):
        self.search_term = text.lower()
        self.search_timer.start(150)

    def on_tab_changed(self, index):
        tabs = ["All", "APT", "Snap"]
        self.active_tab = tabs[index]
        self.filter_packages()

    def filter_packages(self):
        if not hasattr(self, 'grid_layout'):  # ← ajoute cette ligne
            return
    
        self.clear_grid()
        
        filtered = []
        for p in self.packages:
            if self.active_tab != "All" and p["type"] != self.active_tab:
                continue
            if self.search_term and self.search_term not in p["name"].lower() and self.search_term not in p["description"].lower():
                continue
            filtered.append(p)
            
        if not filtered:
            self.show_empty_state()
            return
            
        # Add to grid (2 columns min)
        cols = max(2, self.width() // 350)
        for i, pkg in enumerate(filtered):
            card = PackageCard(pkg, self.confirm_uninstall)
            self.grid_layout.addWidget(card, i // cols, i % cols)

    def clear_grid(self):
        if not hasattr(self, 'grid_layout'):  # ← ajoute cette ligne
            return
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def show_empty_state(self):
        label = QLabel("No packages found.")
        label.setStyleSheet("color: #5A6380; font-size: 18px; margin-top: 100px;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.grid_layout.addWidget(label, 0, 0, 1, 3)

    def confirm_uninstall(self, pkg):
        msg = f"Are you sure you want to uninstall {pkg['name']}?"
        # Simple confirmation dialog
        diag = QDialog(self)
        diag.setWindowTitle("Confirm Uninstall")
        diag.setFixedSize(350, 150)
        diag.setStyleSheet("background-color: #161922; color: #E2E8F8; border-radius: 10px;")
        
        l = QVBoxLayout(diag)
        l.addWidget(QLabel(msg))
        
        btn_box = QHBoxLayout()
        yes = QPushButton("Yes, Uninstall")
        yes.setStyleSheet("background-color: #FF6B6B; padding: 8px; border-radius: 5px; font-weight: bold;")
        no = QPushButton("Cancel")
        no.setStyleSheet("background-color: #2A2F42; padding: 8px; border-radius: 5px;")
        
        btn_box.addWidget(no)
        btn_box.addWidget(yes)
        l.addLayout(btn_box)
        
        yes.clicked.connect(diag.accept)
        no.clicked.connect(diag.reject)
        
        if diag.exec():
            self.start_uninstall(pkg)

    def start_uninstall(self, pkg):
        worker = UninstallWorker(pkg["name"], pkg["type"])
        worker.finished.connect(lambda s, m: self.on_uninstall_finished(s, m, pkg))
        worker.start()
        # Keep reference to prevent GC
        self._active_uninstall = worker

    def on_uninstall_finished(self, success, message, pkg):
        Toast(message, is_error=not success, parent=self)
        if success:
            self.packages = [p for p in self.packages if p["name"] != pkg["name"]]
            self.update_tab_counts()
            self.filter_packages()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.filter_packages()
