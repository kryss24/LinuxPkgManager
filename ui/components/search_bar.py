from PyQt6.QtWidgets import QLineEdit, QHBoxLayout, QLabel, QFrame, QWidget
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon, QPainter, QColor, QBrush, QPen

class SearchBar(QLineEdit):
    searchChanged = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("searchBar")
        self.setPlaceholderText("Search packages...")
        self.setClearButtonEnabled(True)
        self.setFixedWidth(350)
        self.setFixedHeight(36)
        
        # Debounce timer
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._emit_search)
        
        self.textChanged.connect(self._on_text_changed)

    def _on_text_changed(self, text):
        self._timer.start(150) # Debounce 150ms

    def _emit_search(self):
        self.searchChanged.emit(self.text())
