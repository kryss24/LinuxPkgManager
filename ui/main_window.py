import sys
import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QScrollArea, QFrame, QDialog, QPushButton, 
    QGraphicsOpacityEffect, QComboBox, QGridLayout, QStackedWidget
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QRect, QEasingCurve, QSize, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QFont, QPalette, QColor, QDragEnterEvent, QDropEvent

from ui.package_card import PackageCard, SkeletonCard
from ui.components.sidebar import Sidebar
from ui.components.search_bar import SearchBar
from ui.components.dialogs import ConfirmDialog
from ui.components.maintenance import MaintenanceView
from ui.components.updates import UpdatesView
from ui.components.history import HistoryView
from ui.components.discover import DiscoverView
from ui.components.stats import StatsView
from ui.components.ppa_manager import PPAManagerView

from core.apt_backend import PackageWorker, UninstallWorker, AptBackend, InstallWorker
from core.snap_backend import SnapWorker
from core.flatpak_backend import FlatpakBackend
from core.appimage_backend import AppImageBackend
from core.config import config

class MultiWorker(QThread):
    finished = pyqtSignal(list)
    def run(self):
        pkgs = []
        # Apt
        manual = AptBackend.get_manual_list()
        pkgs.extend(AptBackend.get_package_details(manual))
        # Snap
        from core.snap_backend import SnapBackend
        pkgs.extend(SnapBackend.get_snaps())
        # Flatpak
        if FlatpakBackend.is_available():
            pkgs.extend(FlatpakBackend.get_installed())
        # AppImage
        pkgs.extend(AppImageBackend.get_appimages())
        self.finished.emit(pkgs)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setObjectName("mainWindow")
        self.setWindowTitle("Linux Package Manager")
        self.setMinimumSize(1100, 750)
        self.setAcceptDrops(True) # Feature 9

        self.packages = []
        self.active_tab = "All"
        self.search_term = ""
        self.view_mode = config.get("view_mode")

        self.init_ui()
        self.load_styles()
        self.load_packages()
        QTimer.singleShot(2000, self.updates_view.check_updates)

    def load_styles(self):
        theme = config.get("theme")
        qss_file = "styles.qss" if theme == "dark" else "styles_light.qss"
        qss_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ui", qss_file)
        if os.path.exists(qss_path):
            with open(qss_path, "r") as f:
                self.setStyleSheet(f.read())

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QHBoxLayout(central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.sidebar = Sidebar(self)
        self.sidebar.tabChanged.connect(self.on_tab_changed)
        self.main_layout.addWidget(self.sidebar)

        self.stacked_widget = QStackedWidget()
        self.main_layout.addWidget(self.stacked_widget, stretch=1)

        # Browse View
        self.browse_page = QWidget()
        self.browse_layout = QVBoxLayout(self.browse_page)
        self.browse_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        self.top_bar = QWidget()
        self.top_bar.setObjectName("topBar")
        top_layout = QHBoxLayout(self.top_bar)
        top_layout.setContentsMargins(30, 0, 30, 0)
        
        title_container = QVBoxLayout()
        self.view_title = QLabel("All Packages")
        self.view_title.setObjectName("appTitle")
        self.pkg_counter = QLabel("Scanning system...")
        self.pkg_counter.setObjectName("packageCounter")
        title_container.addWidget(self.view_title)
        title_container.addWidget(self.pkg_counter)
        top_layout.addLayout(title_container)
        top_layout.addStretch()

        self.search_bar = SearchBar()
        self.search_bar.searchChanged.connect(self.on_search_changed)
        top_layout.addWidget(self.search_bar)

        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Name A-Z", "Type", "Install Date"])
        self.sort_combo.setCurrentText(config.get("sort_by"))
        self.sort_combo.currentIndexChanged.connect(self.on_sort_changed)
        top_layout.addWidget(self.sort_combo)

        self.view_toggle = QPushButton("🔲" if self.view_mode == "list" else "☰")
        self.view_toggle.setFixedSize(36, 36)
        self.view_toggle.clicked.connect(self.toggle_view_mode)
        top_layout.addWidget(self.view_toggle)

        self.theme_toggle = QPushButton("☀️" if config.get("theme") == "dark" else "🌙")
        self.theme_toggle.setFixedSize(36, 36)
        self.theme_toggle.clicked.connect(self.toggle_theme)
        top_layout.addWidget(self.theme_toggle)

        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setFixedSize(36, 36)
        self.refresh_btn.clicked.connect(self.load_packages)
        top_layout.addWidget(self.refresh_btn)

        self.browse_layout.addWidget(self.top_bar)

        # Scroll Area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setObjectName("mainScroll")
        self.scroll_container = QWidget()
        self.scroll_container.setObjectName("scrollContainer")
        self.packages_layout = QVBoxLayout(self.scroll_container) if self.view_mode == "list" else QGridLayout(self.scroll_container)
        self.packages_layout.setSpacing(12 if self.view_mode == "list" else 20)
        self.packages_layout.setContentsMargins(30, 20, 30, 40)
        self.packages_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.scroll_container)
        self.browse_layout.addWidget(self.scroll)

        self.stacked_widget.addWidget(self.browse_page)

        # Specialized Views
        self.discover_view = DiscoverView()
        self.stacked_widget.addWidget(self.discover_view)
        
        self.updates_view = UpdatesView()
        self.updates_view.updatesFound.connect(self.sidebar.set_updates_count)
        self.stacked_widget.addWidget(self.updates_view)
        
        self.history_view = HistoryView()
        self.stacked_widget.addWidget(self.history_view)
        
        self.stats_view = StatsView()
        self.stacked_widget.addWidget(self.stats_view)
        
        self.ppa_view = PPAManagerView()
        self.stacked_widget.addWidget(self.ppa_view)
        
        self.maintenance_view = MaintenanceView()
        self.stacked_widget.addWidget(self.maintenance_view)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith(".deb"):
                    event.accept()
                    return
        event.ignore()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path.lower().endswith(".deb"):
                self.handle_deb_drop(path)
                break

    def handle_deb_drop(self, path):
        info = AptBackend.get_deb_info(path)
        if info:
            msg = f"Install {info.get('package', 'Unknown')} v{info.get('version', '?')}?\n\n{info.get('description', '')[:200]}..."
            diag = ConfirmDialog("Install .deb", msg, danger_text="Install Now", parent=self)
            if diag.exec():
                self.start_deb_install(path)

    def start_deb_install(self, path):
        worker = InstallWorker(path, "APT", action="local")
        worker.finished.connect(lambda s, m: Toast(m, is_error=not s, parent=self))
        worker.finished.connect(self.load_packages)
        worker.start()

    def load_packages(self):
        self.packages = []
        self.clear_packages()
        self.pkg_counter.setText("Refreshing database...")
        self.worker = MultiWorker()
        self.worker.finished.connect(self.on_packages_loaded)
        self.worker.start()

    def on_packages_loaded(self, pkgs):
        self.packages = pkgs
        self.stats_view.update_stats(pkgs)
        self.filter_packages()

    def on_tab_changed(self, tab_name):
        self.active_tab = tab_name
        self.view_title.setText(tab_name if tab_name != "All" else "All Packages")
        
        if tab_name == "Discover": self.stacked_widget.setCurrentWidget(self.discover_view)
        elif tab_name == "Updates": self.stacked_widget.setCurrentWidget(self.updates_view)
        elif tab_name == "History": self.stacked_widget.setCurrentWidget(self.history_view); self.history_view.load_history()
        elif tab_name == "Stats": self.stacked_widget.setCurrentWidget(self.stats_view)
        elif tab_name == "PPAs": self.stacked_widget.setCurrentWidget(self.ppa_view); self.ppa_view.load_ppas()
        elif tab_name == "Maintenance": self.stacked_widget.setCurrentWidget(self.maintenance_view)
        else: self.stacked_widget.setCurrentWidget(self.browse_page); self.filter_packages()

    def filter_packages(self):
        self.clear_packages()
        filtered = [
            p for p in self.packages
            if (self.active_tab == "All" or p["type"] == self.active_tab)
            and (not self.search_term or self.search_term in p["name"].lower() or self.search_term in p.get("description", "").lower())
        ]
        
        sort_type = self.sort_combo.currentText()
        if sort_type == "Name A-Z": filtered.sort(key=lambda x: x["name"].lower())
        elif sort_type == "Type": filtered.sort(key=lambda x: x["type"])
        elif sort_type == "Install Date": filtered.sort(key=lambda x: str(x.get("install_date", "")), reverse=True)
            
        self.pkg_counter.setText(f"{len(filtered)} packages found")
        
        if self.view_mode == "list":
            for pkg in filtered:
                self.packages_layout.addWidget(PackageCard(pkg, self.confirm_uninstall, view_mode="list"))
        else:
            cols = max(1, (self.width() - 240) // 250)
            for i, pkg in enumerate(filtered):
                self.packages_layout.addWidget(PackageCard(pkg, self.confirm_uninstall, view_mode="grid"), i // cols, i % cols)

    def clear_packages(self):
        while self.packages_layout.count():
            item = self.packages_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

    def toggle_view_mode(self):
        self.view_mode = "grid" if self.view_mode == "list" else "list"
        config.set("view_mode", self.view_mode)
        self.view_toggle.setText("🔲" if self.view_mode == "list" else "☰")
        
        old_layout = self.scroll_container.layout()
        if old_layout:
            self.clear_packages()
            from PyQt6 import sip
            sip.delete(old_layout)
            
        self.packages_layout = QVBoxLayout(self.scroll_container) if self.view_mode == "list" else QGridLayout(self.scroll_container)
        self.packages_layout.setSpacing(12 if self.view_mode == "list" else 20)
        self.packages_layout.setContentsMargins(30, 20, 30, 40)
        self.packages_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.filter_packages()

    def toggle_theme(self):
        new_theme = "light" if config.get("theme") == "dark" else "dark"
        config.set("theme", new_theme)
        self.load_styles()

    def on_sort_changed(self):
        config.set("sort_by", self.sort_combo.currentText())
        self.filter_packages()

    def on_search_changed(self, text):
        self.search_term = text.lower()
        self.filter_packages()

    def confirm_uninstall(self, pkg):
        diag = ConfirmDialog("Uninstall", f"Remove {pkg['name']}?", parent=self)
        if diag.exec():
            worker = UninstallWorker(pkg.get("path") or pkg.get("id") or pkg["name"], pkg["type"])
            worker.finished.connect(lambda s, m: (Toast(m, is_error=not s, parent=self), self.load_packages()))
            worker.start()

class Toast(QFrame):
    def __init__(self, message, is_error=False, parent=None):
        super().__init__(parent)
        self.setObjectName("toastError" if is_error else "toastSuccess")
        self.setFixedSize(320, 56)
        layout = QHBoxLayout(self)
        layout.addWidget(QLabel("❌" if is_error else "✅"))
        l = QLabel(message); l.setObjectName("toastMessage"); l.setWordWrap(True)
        layout.addWidget(l, 1)
        self.show()
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

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
