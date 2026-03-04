import subprocess
import os
from PyQt6.QtCore import QThread, pyqtSignal

class MaintenanceWorker(QThread):
    finished = pyqtSignal(str, bool, str, object)

    def __init__(self, action="scan_orphans"):
        super().__init__()
        self.action = action

    def run(self):
        if self.action == "scan_orphans":
            self.scan_orphans()
        elif self.action == "clean_orphans":
            self.clean_orphans()
        elif self.action == "scan_cache":
            self.scan_cache()
        elif self.action == "clean_cache":
            self.clean_cache()

    def scan_orphans(self):
        try:
            res = subprocess.check_output(["apt-get", "-s", "autoremove"], text=True)
            orphans = []
            size = "0 KB"
            for line in res.splitlines():
                if line.startswith("Remv "):
                    orphans.append(line.split()[1])
                elif "unlocked from your system" in line or "operation," in line:
                    if "of additional" in line:
                        size = line.split("operation,")[1].split("of additional")[0].strip()
            self.finished.emit("scan_orphans", True, f"Found {len(orphans)} orphans", (orphans, size))
        except Exception as e:
            self.finished.emit("scan_orphans", False, str(e), ([], "0 KB"))

    def scan_cache(self):
        try:
            # Use pkexec to have permission to read /var/cache/apt/archives/partial
            res = subprocess.check_output(["pkexec", "du", "-sh", "/var/cache/apt/archives/"], text=True)
            size = res.split()[0]
            self.finished.emit("scan_cache", True, f"Cache size: {size}", size)
        except Exception as e:
            self.finished.emit("scan_cache", False, str(e), "0 KB")

    def clean_orphans(self):
        try:
            cmd = ["pkexec", "apt-get", "autoremove", "-y"]
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = proc.communicate()
            success = proc.returncode == 0
            self.finished.emit("clean_orphans", success, "System cleaned" if success else stderr, None)
        except Exception as e:
            self.finished.emit("clean_orphans", False, str(e), None)

    def clean_cache(self):
        try:
            cmd = ["pkexec", "apt-get", "clean"]
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = proc.communicate()
            success = proc.returncode == 0
            self.finished.emit("clean_cache", success, "Cache cleared" if success else stderr, None)
        except Exception as e:
            self.finished.emit("clean_cache", False, str(e), None)
