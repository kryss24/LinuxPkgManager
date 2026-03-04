from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtProperty, QPropertyAnimation, QRect, QEasingCurve
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QBrush

class StatCard(QFrame):
    def __init__(self, title, value, unit="", color="#3584e4", parent=None):
        super().__init__(parent)
        self.setObjectName("statCard")
        self.setFixedSize(200, 100)
        self.setStyleSheet(f"""
            QFrame#statCard {{
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 12px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #a0a0a0; font-size: 11px; font-weight: bold; text-transform: uppercase;")
        layout.addWidget(title_label)
        
        val_layout = QHBoxLayout()
        val_label = QLabel(str(value))
        val_label.setStyleSheet(f"color: {color}; font-size: 24px; font-weight: 800;")
        val_layout.addWidget(val_label)
        
        unit_label = QLabel(unit)
        unit_label.setStyleSheet("color: #666666; font-size: 13px; margin-top: 8px;")
        val_layout.addWidget(unit_label)
        val_layout.addStretch()
        
        layout.addLayout(val_layout)

class SimpleBarChart(QWidget):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.data = data # list of (label, value, color)
        self.setFixedHeight(180)

    def paintEvent(self, event):
        if not self.data: return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        margin = 40
        w = self.width() - 2 * margin
        h = self.height() - 40
        
        max_val = max(v[1] for v in self.data) if self.data else 1
        bar_w = (w // len(self.data)) - 10
        
        for i, (label, val, color) in enumerate(self.data):
            bar_h = int((val / max_val) * h)
            x = margin + i * (bar_w + 10)
            y = self.height() - 20 - bar_h
            
            # Draw bar
            painter.setBrush(QBrush(QColor(color)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(x, y, bar_w, bar_h, 4, 4)
            
            # Label
            painter.setPen(QColor("#a0a0a0"))
            painter.setFont(QFont("Inter", 9))
            painter.drawText(QRect(x, self.height() - 15, bar_w, 15), Qt.AlignmentFlag.AlignCenter, label)

class StatsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("statsView")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 20, 40, 40)
        layout.setSpacing(30)

        # Title
        title = QLabel("System Statistics")
        title.setObjectName("appTitle")
        layout.addWidget(title)

        # 1. Cards Row
        self.cards_layout = QHBoxLayout()
        self.cards_layout.setSpacing(20)
        layout.addLayout(self.cards_layout)

        # 2. Charts Section
        self.charts_container = QFrame()
        self.charts_container.setStyleSheet("background-color: #2d2d2d; border-radius: 12px; border: 1px solid #3d3d3d;")
        chart_layout = QVBoxLayout(self.charts_container)
        chart_layout.setContentsMargins(20, 20, 20, 20)
        
        chart_title = QLabel("Packages per Type")
        chart_title.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 10px;")
        chart_layout.addWidget(chart_title)
        
        self.bar_chart = SimpleBarChart([])
        chart_layout.addWidget(self.bar_chart)
        
        layout.addWidget(self.charts_container)
        layout.addStretch()

    def update_stats(self, packages):
        # Clear cards
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        apt_c = sum(1 for p in packages if p["type"] == "APT")
        snap_c = sum(1 for p in packages if p["type"] == "Snap")
        flat_c = sum(1 for p in packages if p["type"] == "Flatpak")
        app_c = sum(1 for p in packages if p["type"] == "AppImage")
        
        self.cards_layout.addWidget(StatCard("Total Packages", len(packages), color="#ffffff"))
        self.cards_layout.addWidget(StatCard("APT Repos", apt_c, color="#3584e4"))
        self.cards_layout.addWidget(StatCard("Snap Store", snap_c, color="#ec4899"))
        self.cards_layout.addWidget(StatCard("Flatpaks", flat_c, color="#33d17a"))
        self.cards_layout.addStretch()
        
        # Update Chart
        chart_data = [
            ("APT", apt_c, "#3584e4"),
            ("Snap", snap_c, "#ec4899"),
            ("Flatpak", flat_c, "#33d17a"),
            ("AppImage", app_c, "#f6d32d")
        ]
        self.bar_chart.data = chart_data
        self.bar_chart.update()
