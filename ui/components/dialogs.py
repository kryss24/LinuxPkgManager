from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QColor, QPalette, QBrush

class ConfirmDialog(QDialog):
    def __init__(self, title, message, danger_text="Uninstall", cancel_text="Cancel", parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(400, 200)
        
        self.init_ui(title, message, danger_text, cancel_text)

    def init_ui(self, title, message, danger_text, cancel_text):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        container = QFrame()
        container.setObjectName("dialogContainer")
        container.setStyleSheet("""
            QFrame#dialogContainer {
                background-color: #2D2D2D;
                border: 1px solid #3d3d3d;
                border-radius: 12px;
            }
        """)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #ffffff; font-size: 18px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Message
        msg_label = QLabel(message)
        msg_label.setStyleSheet("color: #a0a0a0; font-size: 14px;")
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        cancel_btn = QPushButton(cancel_text)
        cancel_btn.setObjectName("dialogCancelBtn")
        cancel_btn.setFixedHeight(36)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        
        danger_btn = QPushButton(danger_text)
        danger_btn.setObjectName("dialogDangerBtn")
        danger_btn.setFixedHeight(36)
        danger_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        danger_btn.clicked.connect(self.accept)
        
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(danger_btn)
        
        layout.addLayout(btn_layout)
        main_layout.addWidget(container)
