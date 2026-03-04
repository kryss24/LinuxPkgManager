import subprocess
import os
from PyQt6.QtCore import QThread, pyqtSignal

class SnapBackend:
    @staticmethod
    def is_available():
        return os.path.exists("/usr/bin/snap")

    @staticmethod
    def get_snaps():
        snaps = []
        try:
            exclude = {"core", "core18", "core20", "core22", "snapd", "bare", "gtk-common-themes"}
            res = subprocess.check_output(["snap", "list"], text=True)
            lines = res.splitlines()[1:]
            for line in lines:
                parts = line.split()
                if len(parts) >= 6:
                    name, version = parts[0], parts[1]
                    if name in exclude or name.startswith("gnome-"): continue
                    snaps.append({
                        "name": name,
                        "version": version,
                        "type": "Snap",
                        "description": f"Snap from {parts[4]}",
                        "icon": SnapBackend.find_icon(name),
                        "install_date": "Installed via Snap"
                    })
        except: pass
        return snaps

    @staticmethod
    def find_icon(name):
        # Snaps sometimes have icons in /var/lib/snapd/desktop/icons/
        icon_path = f"/var/lib/snapd/desktop/icons/{name}_icon.png"
        if os.path.exists(icon_path):
            return icon_path
        # Or look in standard locations if it's a popular app
        for ext in ["png", "svg"]:
            path = f"/usr/share/pixmaps/{name}.{ext}"
            if os.path.exists(path): return path
        return None

    @staticmethod
    def get_upgradable():
        upgradable = []
        try:
            res = subprocess.check_output(["snap", "refresh", "--list"], text=True)
            lines = res.splitlines()[1:]
            for line in lines:
                parts = line.split()
                if len(parts) >= 4:
                    upgradable.append({
                        "name": parts[0],
                        "version": parts[2], # new version
                        "type": "Snap",
                        "description": f"Update available: {parts[1]} -> {parts[2]}"
                    })
        except: pass
        return upgradable

    @staticmethod
    def search_snaps(query):
        results = []
        if not query or len(query) < 2: return results
        try:
            res = subprocess.check_output(["snap", "find", query], text=True)
            lines = res.splitlines()[1:]
            for line in lines[:50]:
                parts = line.split()
                if len(parts) >= 3:
                    results.append({
                        "name": parts[0],
                        "version": parts[1],
                        "description": parts[2],
                        "type": "Snap",
                        "install_date": f"Available from {parts[2]}"
                    })
        except: pass
        return results

    @staticmethod
    def get_history():
        history = []
        try:
            res = subprocess.check_output(["snap", "changes"], text=True)
            lines = res.splitlines()[1:]
            for line in lines:
                parts = line.split()
                if len(parts) >= 4:
                    date = f"{parts[2]} {parts[3]}"
                    summary = " ".join(parts[4:])
                    history.append({
                        "date": date,
                        "action": "Snap Change",
                        "package": summary,
                        "version": "-",
                        "type": "Snap"
                    })
            history.reverse()
        except: pass
        return history

class SnapWorker(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def run(self):
        try:
            if not SnapBackend.is_available():
                self.finished.emit([])
                return
            pkgs = SnapBackend.get_snaps()
            self.finished.emit(pkgs)
        except Exception as e:
            self.error.emit(str(e))
