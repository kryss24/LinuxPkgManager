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
            # Exclude core/system snaps
            exclude = {"core", "core18", "core20", "core22", "snapd", "bare", "gtk-common-themes", "gnome-3-28-1804", "gnome-3-34-1804", "gnome-3-38-2004", "gnome-42-2204", "wine-platform-6-stable", "wine-platform-runtime"}
            
            res = subprocess.check_output(["snap", "list"], text=True)
            lines = res.splitlines()[1:] # skip header
            for line in lines:
                parts = line.split()
                if len(parts) >= 6:
                    name, version, rev, tracking, pub, notes = parts[0], parts[1], parts[2], parts[3], parts[4], parts[5]
                    # Exclude gnome-*
                    if name in exclude or name.startswith("gnome-"):
                        continue
                        
                    snaps.append({
                        "name": name,
                        "version": version,
                        "description": f"Snap from {pub}",
                        "icon": SnapBackend.find_icon(name),
                        "type": "Snap",
                        "install_date": "Installed via Snap" # Snap list doesn't easily show date in summary
                    })
        except Exception as e:
            print(f"Snap fetch error: {e}")
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
