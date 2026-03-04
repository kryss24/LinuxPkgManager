from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QGraphicsDropShadowEffect, QGraphicsOpacityEffect
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QPoint, pyqtProperty, QSize, QTimer, QRect, QEasingCurve
from PyQt6.QtGui import QPixmap, QColor, QPainter, QLinearGradient, QBrush, QIcon, QFont, QPalette
import os

class PackageCard(QFrame):
    def __init__(self, pkg, uninstall_callback, parent=None):
        super().__init__(parent)
        self.pkg = pkg
        self.uninstall_callback = uninstall_callback
        self.setObjectName("packageCard")
        self.setFixedHeight(100) # List item height
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(16)
        
        # 1. Icon (64x64)
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(64, 64)
        self.update_icon()
        layout.addWidget(self.icon_label)
        
        # 2. Package Info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        # Name and Badge
        name_row = QHBoxLayout()
        name_row.setSpacing(8)
        
        self.name_label = QLabel(self.pkg["name"])
        self.name_label.setObjectName("pkgName")
        name_row.addWidget(self.name_label)
        
        badge_color = "#6366f1" if self.pkg["type"] == "APT" else "#ec4899"
        self.badge = QLabel(self.pkg["type"].upper())
        self.badge.setObjectName("pkgBadge")
        self.badge.setStyleSheet(f"background-color: {badge_color}; color: white; border-radius: 4px; padding: 2px 8px; font-size: 10px; font-weight: bold;")
        name_row.addWidget(self.badge)
        name_row.addStretch()
        
        info_layout.addLayout(name_row)
        
        # Version and Meta
        meta_row = QHBoxLayout()
        meta_row.setSpacing(12)
        
        self.version_label = QLabel(f"Version: {self.pkg['version']}")
        self.version_label.setObjectName("pkgMeta")
        meta_row.addWidget(self.version_label)
        
        self.date_label = QLabel(f"•  {self.pkg['install_date']}")
        self.date_label.setObjectName("pkgMeta")
        meta_row.addWidget(self.date_label)
        
        meta_row.addStretch()
        info_layout.addLayout(meta_row)
        
        # Description (2 lines)
        desc_text = self.pkg["description"].split('\n')[0]
        if len(desc_text) > 120: desc_text = desc_text[:117] + "..."
        self.desc_label = QLabel(desc_text)
        self.desc_label.setObjectName("pkgDesc")
        self.desc_label.setWordWrap(True)
        info_layout.addWidget(self.desc_label)
        
        layout.addLayout(info_layout, stretch=1)
        
        # 3. Actions (Hidden by default, shown on hover)
        self.action_area = QWidget()
        self.action_area.setFixedWidth(120)
        action_layout = QHBoxLayout(self.action_area)
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.uninstall_btn = QPushButton("Uninstall")
        self.uninstall_btn.setObjectName("cardUninstallBtn")
        self.uninstall_btn.setFixedSize(100, 32)
        self.uninstall_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.uninstall_btn.clicked.connect(lambda: self.uninstall_callback(self.pkg))
        action_layout.addWidget(self.uninstall_btn)
        
        layout.addWidget(self.action_area)
        self.action_area.hide()

    def update_icon(self):
        if self.pkg.get("icon") and os.path.exists(self.pkg["icon"]):
            pixmap = QPixmap(self.pkg["icon"]).scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.icon_label.setPixmap(pixmap)
        else:
            avatar = QPixmap(64, 64)
            avatar.fill(Qt.GlobalColor.transparent)
            painter = QPainter(avatar)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Use hash of name for deterministic color
            color_idx = hash(self.pkg["name"]) % 360
            color = QColor.fromHsv(color_idx, 160, 180)
            
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(0, 0, 64, 64, 16, 16)
            
            painter.setPen(Qt.GlobalColor.white)
            font = QFont("Inter", 24, QFont.Weight.Bold)
            painter.setFont(font)
            painter.drawText(avatar.rect(), Qt.AlignmentFlag.AlignCenter, self.pkg["name"][0].upper())
            painter.end()
            self.icon_label.setPixmap(avatar)

    def enterEvent(self, event):
        self.setProperty("hover", True)
        self.style().polish(self)
        self.action_area.show()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setProperty("hover", False)
        self.style().polish(self)
        self.action_area.hide()
        super().leaveEvent(event)

class SkeletonCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("skeletonCard")
        self.setFixedHeight(100)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(30)
        self.offset = 0

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Gradient shimmer
        gradient = QLinearGradient(self.offset - 100, 0, self.offset + 100, 0)
        gradient.setColorAt(0, QColor("#242424"))
        gradient.setColorAt(0.5, QColor("#2d2d2d"))
        gradient.setColorAt(1, QColor("#242424"))
        
        brush = QBrush(gradient)
        painter.setBrush(brush)
        painter.setPen(Qt.PenStyle.NoPen)
        
        # Icon placeholder
        painter.drawRoundedRect(16, 18, 64, 64, 16, 16)
        
        # Name placeholder
        painter.drawRoundedRect(96, 18, 200, 20, 4, 4)
        
        # Meta placeholder
        painter.drawRoundedRect(96, 46, 150, 12, 3, 3)
        
        # Description placeholder
        painter.drawRoundedRect(96, 70, 400, 12, 4, 4)
        
        self.offset += 8
        if self.offset > self.width() + 100:
            self.offset = -100
