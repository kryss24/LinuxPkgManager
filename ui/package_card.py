from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QPoint, pyqtProperty, QSize, QTimer
from PyQt6.QtGui import QPixmap, QColor, QPainter, QLinearGradient, QBrush, QIcon
import os

class SkeletonCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("skeletonCard")
        self.setFixedSize(300, 160)
        self.setStyleSheet("""
            QFrame#skeletonCard {
                background-color: #161922;
                border: 1px solid #2A2F42;
                border-radius: 12px;
            }
        """)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(30)
        self.offset = 0

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Gradient shimmer
        gradient = QLinearGradient(self.offset - 100, 0, self.offset + 100, 0)
        gradient.setColorAt(0, QColor("#161922"))
        gradient.setColorAt(0.5, QColor("#1F2433"))
        gradient.setColorAt(1, QColor("#161922"))
        
        brush = QBrush(gradient)
        painter.setBrush(brush)
        painter.setPen(Qt.PenStyle.NoPen)
        
        # Icon placeholder
        painter.drawRoundedRect(15, 15, 48, 48, 8, 8)
        
        # Name placeholder
        painter.drawRoundedRect(75, 20, 150, 15, 4, 4)
        
        # Version placeholder
        painter.drawRoundedRect(75, 45, 80, 10, 3, 3)
        
        # Description placeholder
        painter.drawRoundedRect(15, 80, 270, 12, 4, 4)
        painter.drawRoundedRect(15, 100, 200, 12, 4, 4)
        
        # Button placeholder
        painter.drawRoundedRect(200, 125, 85, 25, 12, 12)
        
        self.offset += 5
        if self.offset > self.width() + 100:
            self.offset = -100

class PackageCard(QFrame):
    def __init__(self, pkg, uninstall_callback, parent=None):
        super().__init__(parent)
        self.pkg = pkg
        self.uninstall_callback = uninstall_callback
        self.setObjectName("packageCard")
        self.setFixedSize(320, 160)
        
        self._pos_anim = QPropertyAnimation(self, b"pos")
        self._pos_anim.setDuration(200)
        
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Header (Icon, Name, Version)
        header = QHBoxLayout()
        header.setSpacing(12)
        
        icon_label = QLabel()
        icon_label.setFixedSize(48, 48)
        
        if self.pkg["icon"] and os.path.exists(self.pkg["icon"]):
            pixmap = QPixmap(self.pkg["icon"]).scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            icon_label.setPixmap(pixmap)
        else:
            # Generate colored avatar
            first_letter = self.pkg["name"][0].upper()
            avatar = QPixmap(48, 48)
            avatar.fill(Qt.GlobalColor.transparent)
            painter = QPainter(avatar)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Use hash of name for deterministic color
            color_idx = hash(self.pkg["name"]) % 360
            color = QColor.fromHsv(color_idx, 150, 200)
            
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(0, 0, 48, 48, 12, 12)
            
            painter.setPen(Qt.GlobalColor.white)
            font = painter.font()
            font.setPointSize(18)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(avatar.rect(), Qt.AlignmentFlag.AlignCenter, first_letter)
            painter.end()
            icon_label.setPixmap(avatar)
            
        header.addWidget(icon_label)
        
        info = QVBoxLayout()
        info.setSpacing(2)
        
        name_label = QLabel(self.pkg["name"])
        name_label.setObjectName("pkgName")
        info.addWidget(name_label)
        
        ver_label = QLabel(self.pkg["version"])
        ver_label.setObjectName("pkgVersion")
        info.addWidget(ver_label)
        
        header.addLayout(info)
        header.addStretch()
        
        # Type Badge
        badge = QLabel(self.pkg["type"])
        badge.setStyleSheet(f"""
            background-color: {"#4F9EFF" if self.pkg["type"] == "APT" else "#3DD68C"};
            color: #0D0F14;
            border-radius: 4px;
            padding: 2px 6px;
            font-size: 10px;
            font-weight: bold;
        """)
        header.addWidget(badge, alignment=Qt.AlignmentFlag.AlignTop)
        
        layout.addLayout(header)
        
        # Description
        desc = self.pkg["description"]
        if len(desc) > 80: desc = desc[:77] + "..."
        desc_label = QLabel(desc)
        desc_label.setObjectName("pkgDesc")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Footer (Meta, Action)
        footer = QHBoxLayout()
        
        meta = QLabel(f"Added: {self.pkg['install_date']}")
        meta.setObjectName("pkgMeta")
        footer.addWidget(meta)
        
        footer.addStretch()
        
        self.btn = QPushButton("Uninstall")
        self.btn.setObjectName("uninstallBtn")
        self.btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn.clicked.connect(lambda: self.uninstall_callback(self.pkg))
        footer.addWidget(self.btn)
        
        layout.addLayout(footer)

    def enterEvent(self, event):
        self._pos_anim.stop()
        self._pos_anim.setEndValue(self.pos() + QPoint(0, -3))
        self._pos_anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._pos_anim.stop()
        self._pos_anim.setEndValue(self.pos() + QPoint(0, 3))
        self._pos_anim.start()
        super().leaveEvent(event)
