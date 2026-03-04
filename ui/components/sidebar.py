from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon

class SidebarButton(QPushButton):
    def __init__(self, text, icon_name=None, parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(40)
        self.setObjectName("sidebarBtn")
        
        self.h_layout = QHBoxLayout(self)
        self.h_layout.setContentsMargins(12, 0, 12, 0)
        self.h_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        self.label = QLabel(text)
        self.label.setStyleSheet("background: transparent; border: none;")
        self.h_layout.addWidget(self.label)
        self.h_layout.addStretch()
        
        self.badge = QLabel("0")
        self.badge.setFixedSize(20, 20)
        self.badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.badge.setStyleSheet("background-color: #ef4444; color: white; border-radius: 10px; font-size: 10px; font-weight: bold; border: none;")
        self.badge.hide()
        self.h_layout.addWidget(self.badge)
        self.setText("") 

    def update_badge(self, count):
        if count > 0:
            self.badge.setText(str(count))
            self.badge.show()
        else:
            self.badge.hide()

class Sidebar(QFrame):
    tabChanged = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(240)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(12, 20, 12, 20)
        self.layout.setSpacing(4)
        
        # App Branding
        brand_layout = QHBoxLayout()
        brand_layout.setContentsMargins(8, 0, 8, 20)
        self.logo = QLabel("📦")
        self.logo.setStyleSheet("font-size: 24px; margin-right: 8px;")
        self.title = QLabel("Package Manager")
        self.title.setObjectName("sidebarTitle")
        brand_layout.addWidget(self.logo)
        brand_layout.addWidget(self.title)
        brand_layout.addStretch()
        self.layout.addLayout(brand_layout)
        
        # Navigation
        self.add_section_header("BROWSE")
        self.btn_discover = SidebarButton("Discover")
        self.btn_discover.clicked.connect(lambda: self.on_tab_click("Discover"))
        self.layout.addWidget(self.btn_discover)
        
        self.btn_all = SidebarButton("Installed Apps")
        self.btn_all.setChecked(True)
        self.btn_all.clicked.connect(lambda: self.on_tab_click("All"))
        self.layout.addWidget(self.btn_all)
        
        self.add_section_header("ECOSYSTEMS")
        self.btn_apt = SidebarButton("APT Repos")
        self.btn_apt.clicked.connect(lambda: self.on_tab_click("APT"))
        self.layout.addWidget(self.btn_apt)
        
        self.btn_snap = SidebarButton("Snap Store")
        self.btn_snap.clicked.connect(lambda: self.on_tab_click("Snap"))
        self.layout.addWidget(self.btn_snap)
        
        self.btn_flatpak = SidebarButton("Flatpak")
        self.btn_flatpak.clicked.connect(lambda: self.on_tab_click("Flatpak"))
        self.layout.addWidget(self.btn_flatpak)
        
        self.btn_appimage = SidebarButton("AppImage")
        self.btn_appimage.clicked.connect(lambda: self.on_tab_click("AppImage"))
        self.layout.addWidget(self.btn_appimage)
        
        self.add_section_header("SYSTEM")
        self.btn_updates = SidebarButton("Updates")
        self.btn_updates.clicked.connect(lambda: self.on_tab_click("Updates"))
        self.layout.addWidget(self.btn_updates)
        
        self.btn_history = SidebarButton("History")
        self.btn_history.clicked.connect(lambda: self.on_tab_click("History"))
        self.layout.addWidget(self.btn_history)
        
        self.btn_ppas = SidebarButton("PPAs")
        self.btn_ppas.clicked.connect(lambda: self.on_tab_click("PPAs"))
        self.layout.addWidget(self.btn_ppas)
        
        self.btn_stats = SidebarButton("Stats")
        self.btn_stats.clicked.connect(lambda: self.on_tab_click("Stats"))
        self.layout.addWidget(self.btn_stats)
        
        self.btn_maintenance = SidebarButton("Maintenance")
        self.btn_maintenance.clicked.connect(lambda: self.on_tab_click("Maintenance"))
        self.layout.addWidget(self.btn_maintenance)
        
        self.layout.addStretch()
        
        # Bottom section
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setObjectName("sidebarSeparator")
        self.layout.addWidget(line)
        
        self.btn_settings = SidebarButton("Settings")
        self.btn_settings.clicked.connect(lambda: self.on_tab_click("Settings"))
        self.layout.addWidget(self.btn_settings)
        
        self.buttons = {
            "Discover": self.btn_discover,
            "All": self.btn_all,
            "APT": self.btn_apt,
            "Snap": self.btn_snap,
            "Flatpak": self.btn_flatpak,
            "AppImage": self.btn_appimage,
            "Updates": self.btn_updates,
            "History": self.btn_history,
            "PPAs": self.btn_ppas,
            "Stats": self.btn_stats,
            "Maintenance": self.btn_maintenance,
            "Settings": self.btn_settings
        }

    def add_section_header(self, text):
        header = QLabel(text)
        header.setObjectName("sidebarHeader")
        header.setStyleSheet("margin-top: 15px; margin-bottom: 5px; margin-left: 10px;")
        self.layout.addWidget(header)

    def on_tab_click(self, tab_name):
        for name, btn in self.buttons.items():
            btn.setChecked(name == tab_name)
        self.tabChanged.emit(tab_name)

    def set_updates_count(self, count):
        self.btn_updates.update_badge(count)
