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
        # In a real app we'd load icons from a resource file or theme
        # self.setIcon(QIcon.fromTheme(icon_name))

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
        
        # Placeholder for Logo
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
        self.btn_all = SidebarButton("All Packages")
        self.btn_all.setChecked(True)
        self.btn_all.clicked.connect(lambda: self.on_tab_click("All"))
        
        self.add_section_header("INSTALLED")
        self.btn_apt = SidebarButton("APT Packages")
        self.btn_apt.clicked.connect(lambda: self.on_tab_click("APT"))
        
        self.btn_snap = SidebarButton("Snap Packages")
        self.btn_snap.clicked.connect(lambda: self.on_tab_click("Snap"))
        
        self.layout.addWidget(self.btn_all)
        self.layout.addWidget(self.btn_apt)
        self.layout.addWidget(self.btn_snap)
        
        self.layout.addStretch()
        
        # Bottom section
        self.layout.addWidget(self.create_separator())
        self.btn_settings = SidebarButton("Settings")
        self.btn_settings.clicked.connect(lambda: self.on_tab_click("Settings"))
        self.layout.addWidget(self.btn_settings)
        
        self.buttons = [self.btn_all, self.btn_apt, self.btn_snap, self.btn_settings]

    def add_section_header(self, text):
        header = QLabel(text)
        header.setObjectName("sidebarHeader")
        header.setStyleSheet("margin-top: 15px; margin-bottom: 5px; margin-left: 10px;")
        self.layout.addWidget(header)

    def create_separator(self):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Plain)
        line.setObjectName("sidebarSeparator")
        return line

    def on_tab_click(self, tab_name):
        for btn in self.buttons:
            btn.setChecked(False)
            if btn.text().startswith(tab_name) or (tab_name == "All" and btn.text() == "All Packages"):
                btn.setChecked(True)
        
        self.tabChanged.emit(tab_name)
