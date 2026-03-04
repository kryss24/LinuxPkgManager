from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QScrollArea, QLineEdit, QDialog, QFormLayout
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from core.apt_backend import AptBackend

class AddPPADialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New PPA")
        self.setFixedSize(400, 180)
        self.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        form = QFormLayout()
        self.ppa_input = QLineEdit()
        self.ppa_input.setPlaceholderText("ppa:user/repo")
        self.ppa_input.setStyleSheet("background-color: #2d2d2d; border: 1px solid #3d3d3d; border-radius: 6px; padding: 8px;")
        form.addRow("PPA Address:", self.ppa_input)
        layout.addLayout(form)
        
        desc = QLabel("Format: ppa:author/name (e.g., ppa:obsproject/obs-studio)")
        desc.setStyleSheet("color: #666666; font-size: 11px;")
        layout.addWidget(desc)
        
        layout.addStretch()
        
        btn_layout = QHBoxLayout()
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        add = QPushButton("Add PPA")
        add.setObjectName("actionBtn")
        add.setStyleSheet("background-color: #3584e4; color: white; border-radius: 6px; padding: 8px 16px; font-weight: bold;")
        add.clicked.connect(self.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(cancel)
        btn_layout.addWidget(add)
        layout.addLayout(btn_layout)

class PPAManagerView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ppaManagerView")
        self.ppas = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 20, 40, 40)
        layout.setSpacing(24)

        # Title
        h_title = QHBoxLayout()
        title = QLabel("Software Sources (PPA)")
        title.setObjectName("appTitle")
        h_title.addWidget(title)
        h_title.addStretch()
        
        self.btn_add = QPushButton("+ Add PPA")
        self.btn_add.setObjectName("actionBtn")
        self.btn_add.setFixedWidth(140)
        self.btn_add.clicked.connect(self.show_add_dialog)
        h_title.addWidget(self.btn_add)
        
        self.btn_refresh = QPushButton("🔄")
        self.btn_refresh.setFixedSize(36, 36)
        self.btn_refresh.clicked.connect(self.load_ppas)
        h_title.addWidget(self.btn_refresh)
        
        layout.addLayout(h_title)

        # Filter
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Filter PPAs...")
        self.search_bar.setObjectName("searchBar")
        self.search_bar.textChanged.connect(self.filter_ppas)
        layout.addWidget(self.search_bar)

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

    def load_ppas(self):
        self.ppas = AptBackend.get_ppas()
        self.filter_ppas()

    def filter_ppas(self):
        self.clear_list()
        query = self.search_bar.text().lower()
        for ppa in self.ppas:
            if not query or query in ppa["name"].lower():
                self.add_ppa_row(ppa)

    def add_ppa_row(self, ppa):
        row = QFrame()
        row.setObjectName("packageCard")
        row.setStyleSheet("background-color: #2d2d2d; border-radius: 10px; border: 1px solid #3d3d3d;")
        row.setFixedHeight(70)
        r_layout = QHBoxLayout(row)
        
        v_info = QVBoxLayout()
        name = QLabel(ppa["name"])
        name.setStyleSheet("font-size: 14px; font-weight: bold;")
        path = QLabel(ppa["path"])
        path.setStyleSheet("font-size: 11px; color: #666666;")
        v_info.addWidget(name)
        v_info.addWidget(path)
        r_layout.addLayout(v_info)
        
        r_layout.addStretch()
        
        toggle_btn = QPushButton("Disable" if ppa["enabled"] else "Enable")
        toggle_btn.setFixedWidth(80)
        toggle_btn.clicked.connect(lambda: self.toggle_ppa(ppa))
        r_layout.addWidget(toggle_btn)
        
        del_btn = QPushButton("🗑️")
        del_btn.setFixedSize(36, 36)
        del_btn.setStyleSheet("background-color: transparent; border: none; font-size: 16px;")
        del_btn.clicked.connect(lambda: self.remove_ppa(ppa))
        r_layout.addWidget(del_btn)
        
        self.list_layout.addWidget(row)

    def clear_list(self):
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

    def show_add_dialog(self):
        diag = AddPPADialog(self)
        if diag.exec():
            ppa_line = diag.ppa_input.text()
            if ppa_line:
                if AptBackend.add_ppa(ppa_line):
                    self.load_ppas()

    def toggle_ppa(self, ppa):
        if AptBackend.toggle_ppa(ppa["file"], not ppa["enabled"]):
            self.load_ppas()

    def remove_ppa(self, ppa):
        from ui.components.dialogs import ConfirmDialog
        diag = ConfirmDialog("Remove PPA", f"Are you sure you want to remove {ppa['name']}?", parent=self)
        if diag.exec():
            if AptBackend.remove_ppa(ppa["name"]):
                self.load_ppas()
