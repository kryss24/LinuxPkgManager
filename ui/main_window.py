import sys
import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QScrollArea, QFrame, QDialog, QPushButton, QGraphicsOpacityEffect
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QRect, QEasingCurve, QSize
from PyQt6.QtGui import QIcon, QFont, QPalette, QColor

from ui.package_card import PackageCard, SkeletonCard
from ui.components.sidebar import Sidebar
from ui.components.search_bar import SearchBar
from ui.components.dialogs import ConfirmDialog
from core.apt_backend import PackageWorker, UninstallWorker
from core.snap_backend import SnapWorker

def get_base_path():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Toast(QFrame):
    def __init__(self, message, is_error=False, parent=None):
        super().__init__(parent)
        self.setObjectName("toastError" if is_error else "toastSuccess")
        self.setFixedSize(320, 56)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        
        icon_label = QLabel("❌" if is_error else "✅")
        icon_label.setStyleSheet("font-size: 18px;")
        
        label = QLabel(message)
        label.setObjectName("toastMessage")
        label.setWordWrap(True)
        
        layout.addWidget(icon_label)
        layout.addWidget(label, 1)

        self.show()
        
        # Position animation
        self.anim = QPropertyAnimation(self, b"geometry")
        self.anim.setDuration(400)
        start_x = parent.width() // 2 - 160
        self.anim.setStartValue(QRect(start_x, -60, 320, 56))
        self.anim.setEndValue(QRect(start_x, 20, 320, 56))
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.anim.start()

        QTimer.singleShot(4000, self.close_toast)

    def close_toast(self):
        self.anim.setDirection(QPropertyAnimation.Direction.Backward)
        self.anim.finished.connect(self.deleteLater)
        self.anim.start()


class LoadingOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background-color: rgba(30, 30, 30, 200);")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.spinner_label = QLabel("⚙️")
        self.spinner_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spinner_label.setStyleSheet("font-size: 64px; background: transparent;")

        self.status_label = QLabel("Loading Packages")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet(
            "color: #ffffff; font-size: 20px; font-weight: 800; background: transparent; margin-top: 15px;"
        )

        layout.addWidget(self.spinner_label)
        layout.addWidget(self.status_label)

        self._spin_timer = QTimer(self)
        self._spin_timer.timeout.connect(self._animate_spinner)
        self._spin_timer.start(50)
        self.angle = 0

    def _animate_spinner(self):
        self.angle = (self.angle + 30) % 360
        # Rotate the spinner label using a transform or just change characters
        # For simplicity and to avoid QPainter complexity in this overlay, 
        # let's cycle through characters that look like a spinner
        chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.spinner_label.setText(chars[self.angle // 30 % len(chars)])

    def stop(self):
        self._spin_timer.stop()
        self.hide()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setObjectName("mainWindow")
        self.setWindowTitle("Linux Package Manager")
        self.setMinimumSize(1100, 750)

        self.packages = []
        self.active_tab = "All"
        self.search_term = ""
        self._workers_done = 0

        self.init_ui()
        self.load_styles()
        self.load_packages()
        
        # Fade-in animation
        self.setWindowOpacity(0)
        self.fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self.fade_anim.setDuration(600)
        self.fade_anim.setStartValue(0)
        self.fade_anim.setEndValue(1)
        self.fade_anim.start()

    def load_styles(self):
        base = get_base_path()
        qss_path = os.path.join(base, "ui", "styles.qss")
        if os.path.exists(qss_path):
            with open(qss_path, "r") as f:
                self.setStyleSheet(f.read())

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Sidebar
        self.sidebar = Sidebar(self)
        self.sidebar.tabChanged.connect(self.on_tab_changed)
        main_layout.addWidget(self.sidebar)

        # 2. Main Content
        content_area = QWidget()
        content_area.setObjectName("mainContent")
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        main_layout.addWidget(content_area, stretch=1)

        # Header
        top_bar = QWidget()
        top_bar.setObjectName("topBar")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(30, 0, 30, 0)

        title_container = QVBoxLayout()
        title_container.setSpacing(2)
        
        self.view_title = QLabel("All Packages")
        self.view_title.setObjectName("appTitle")
        title_container.addWidget(self.view_title)
        
        self.pkg_counter = QLabel("Scanning system...")
        self.pkg_counter.setObjectName("packageCounter")
        title_container.addWidget(self.pkg_counter)
        
        top_layout.addLayout(title_container)
        top_layout.addStretch()

        self.search_bar = SearchBar()
        self.search_bar.searchChanged.connect(self.on_search_changed)
        top_layout.addWidget(self.search_bar)
        
        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setFixedSize(36, 36)
        self.refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_btn.setStyleSheet("font-size: 16px; border: none; background: transparent; color: #a0a0a0;")
        self.refresh_btn.clicked.connect(self.load_packages)
        top_layout.addWidget(self.refresh_btn)

        content_layout.addWidget(top_bar)

        # Scroll Area for Packages
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setObjectName("mainScroll")

        self.list_container = QWidget()
        self.list_container.setObjectName("scrollContainer")
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setSpacing(8)
        self.list_layout.setContentsMargins(30, 20, 30, 40)
        self.list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.scroll.setWidget(self.list_container)
        content_layout.addWidget(self.scroll)

        # Loading Overlay
        self.loading_overlay = LoadingOverlay(self)
        self.loading_overlay.setGeometry(self.rect())
        self.loading_overlay.show()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'loading_overlay'):
            self.loading_overlay.setGeometry(self.rect())

    def load_packages(self):
        self._workers_done = 0
        self.packages = []
        self.clear_list()
        self.loading_overlay.show()
        self.loading_overlay.raise_()
        self.pkg_counter.setText("Refreshing database...")

        self.apt_worker = PackageWorker()
        self.apt_worker.finished.connect(self.on_packages_loaded)
        self.apt_worker.start()

        self.snap_worker = SnapWorker()
        self.snap_worker.finished.connect(self.on_packages_loaded)
        self.snap_worker.start()

    def on_packages_loaded(self, pkgs):
        self.packages.extend(pkgs)
        self._workers_done += 1
        if self._workers_done >= 2:
            self.loading_overlay.stop()
            self.filter_packages()

    def on_tab_changed(self, tab_name):
        self.active_tab = tab_name
        self.view_title.setText(f"{tab_name} Packages" if tab_name != "All" else "All Packages")
        self.filter_packages()

    def on_search_changed(self, text):
        self.search_term = text.lower()
        self.filter_packages()

    def filter_packages(self):
        if not hasattr(self, 'list_layout'): return
        self.clear_list()

        filtered = [
            p for p in self.packages
            if (self.active_tab == "All" or p["type"] == self.active_tab)
            and (not self.search_term
                 or self.search_term in p["name"].lower()
                 or self.search_term in p["description"].lower())
        ]

        self.pkg_counter.setText(f"{len(filtered)} packages found")

        if not filtered:
            self.show_empty_state()
            return

        for pkg in filtered:
            card = PackageCard(pkg, self.confirm_uninstall)
            self.list_layout.addWidget(card)

    def clear_list(self):
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def show_empty_state(self):
        label = QLabel("No packages found.")
        label.setStyleSheet("color: #666666; font-size: 16px; margin-top: 100px;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.list_layout.addWidget(label)

    def confirm_uninstall(self, pkg):
        diag = ConfirmDialog(
            "Confirm Uninstall",
            f"Are you sure you want to remove {pkg['name']}? This action cannot be undone.",
            danger_text="Uninstall",
            parent=self
        )

        if diag.exec():
            self.start_uninstall(pkg)

    def start_uninstall(self, pkg):
        self.pkg_counter.setText(f"Uninstalling {pkg['name']}...")
        worker = UninstallWorker(pkg["name"], pkg["type"])
        worker.finished.connect(lambda s, m: self.on_uninstall_finished(s, m, pkg))
        worker.start()

    def on_uninstall_finished(self, success, message, pkg):
        Toast(message, is_error=not success, parent=self)
        if success:
            self.packages = [p for p in self.packages if p["name"] != pkg["name"]]
            self.filter_packages()
        else:
            self.pkg_counter.setText(f"{len(self.packages)} packages found")
