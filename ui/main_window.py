import sys
import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QScrollArea, QGridLayout,
    QFrame, QDialog, QPushButton
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QRect, QEasingCurve
from ui.package_card import PackageCard, SkeletonCard
from core.apt_backend import PackageWorker, UninstallWorker
from core.snap_backend import SnapWorker


def get_base_path():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS  # PyInstaller
    # Mode dev : remonter d'un niveau depuis ui/ vers la racine
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

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

        self.raise_()
        self.show()

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


class LoadingOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background-color: rgba(13, 15, 20, 210);")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.spinner_label = QLabel("⏳")
        self.spinner_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spinner_label.setStyleSheet("font-size: 52px; background: transparent;")

        self.status_label = QLabel("Loading packages...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet(
            "color: #4F9EFF; font-size: 16px; font-weight: bold; background: transparent;"
        )

        self.sub_label = QLabel("Scanning APT & Snap")
        self.sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sub_label.setStyleSheet(
            "color: #5A6380; font-size: 13px; background: transparent;"
        )

        layout.addWidget(self.spinner_label)
        layout.addSpacing(12)
        layout.addWidget(self.status_label)
        layout.addWidget(self.sub_label)

        self._dots = 0
        self._dot_timer = QTimer(self)
        self._dot_timer.timeout.connect(self._animate_dots)
        self._dot_timer.start(500)

        self._spinners = ["⏳", "⌛"]
        self._spin_idx = 0
        self._spin_timer = QTimer(self)
        self._spin_timer.timeout.connect(self._animate_spinner)
        self._spin_timer.start(700)

    def _animate_dots(self):
        self._dots = (self._dots + 1) % 4
        self.sub_label.setText("Scanning APT & Snap" + "." * self._dots)

    def _animate_spinner(self):
        self._spin_idx = (self._spin_idx + 1) % len(self._spinners)
        self.spinner_label.setText(self._spinners[self._spin_idx])

    def stop(self):
        self._dot_timer.stop()
        self._spin_timer.stop()
        self.hide()


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
        self._workers_done = 0

        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.filter_packages)

        self.init_ui()
        self.load_styles()
        self.load_packages()

    def load_styles(self):
        base = get_base_path()
        qss_path = os.path.join(base, "ui", "styles.qss")
        if os.path.exists(qss_path):
            with open(qss_path, "r") as f:
                self.setStyleSheet(f.read())
        else:
            print(f"[WARN] styles.qss not found at: {qss_path}")

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

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

        tab_bar = QWidget()
        tab_bar.setObjectName("customTabBar")
        tab_layout = QHBoxLayout(tab_bar)
        tab_layout.setContentsMargins(20, 0, 0, 0)
        tab_layout.setSpacing(0)

        self.tab_buttons = []
        for i, name in enumerate(["All", "APT", "Snap"]):
            btn = QPushButton(f"{name} (0)")
            btn.setObjectName("tabBtn")
            btn.setCheckable(True)
            btn.clicked.connect(lambda _, idx=i: self.on_tab_changed(idx))
            tab_layout.addWidget(btn)
            self.tab_buttons.append(btn)

        tab_layout.addStretch()
        self.tab_buttons[0].setChecked(True)

        main_layout.addWidget(tab_bar)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setObjectName("mainScroll")

        self.grid_container = QWidget()
        self.grid_container.setObjectName("gridContainer")
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(20)
        self.grid_layout.setContentsMargins(20, 20, 20, 20)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        self.scroll.setWidget(self.grid_container)
        main_layout.addWidget(self.scroll)

        self.loading_overlay = LoadingOverlay(self)
        self.loading_overlay.setGeometry(self.rect())
        self.loading_overlay.show()
        self.loading_overlay.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'loading_overlay'):
            self.loading_overlay.setGeometry(self.rect())
        if hasattr(self, 'grid_layout'):
            self.filter_packages()

    def load_packages(self):
        self._workers_done = 0
        self.packages = []
        self.clear_grid()

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
        self.update_tab_counts()
        self.filter_packages()

    def update_tab_counts(self):
        apt_count = sum(1 for p in self.packages if p["type"] == "APT")
        snap_count = sum(1 for p in self.packages if p["type"] == "Snap")
        counts = [len(self.packages), apt_count, snap_count]
        names = ["All", "APT", "Snap"]
        for i, btn in enumerate(self.tab_buttons):
            btn.setText(f"{names[i]} ({counts[i]})")

    def on_search_changed(self, text):
        self.search_term = text.lower()
        self.search_timer.start(150)

    def on_tab_changed(self, index):
        tabs = ["All", "APT", "Snap"]
        self.active_tab = tabs[index]
        for i, btn in enumerate(self.tab_buttons):
            btn.setChecked(i == index)
        self.filter_packages()

    def filter_packages(self):
        if not hasattr(self, 'grid_layout'):
            return
        self.clear_grid()

        filtered = [
            p for p in self.packages
            if (self.active_tab == "All" or p["type"] == self.active_tab)
            and (not self.search_term
                 or self.search_term in p["name"].lower()
                 or self.search_term in p["description"].lower())
        ]

        if not filtered:
            self.show_empty_state()
            return

        cols = max(2, self.width() // 350)
        for i, pkg in enumerate(filtered):
            card = PackageCard(pkg, self.confirm_uninstall)
            self.grid_layout.addWidget(card, i // cols, i % cols)

    def clear_grid(self):
        if not hasattr(self, 'grid_layout'):
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
        self._active_uninstall = worker

    def on_uninstall_finished(self, success, message, pkg):
        Toast(message, is_error=not success, parent=self)
        if success:
            self.packages = [p for p in self.packages if p["name"] != pkg["name"]]
            self.update_tab_counts()
            self.filter_packages()
