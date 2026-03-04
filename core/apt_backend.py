import subprocess
import os
import re
from PyQt6.QtCore import QThread, pyqtSignal

class AptBackend:
    @staticmethod
    def is_available():
        return os.path.exists("/usr/bin/apt")

    @staticmethod
    def get_system_install_date():
        try:
            res = subprocess.check_output(
                ["dpkg-query", "-W", "-f=${db-fsys:Last-Modified}\n", "ubuntu-minimal"],
                text=True
            ).strip()
            return int(res)
        except:
            return 0

    @staticmethod
    def get_manual_list():
        try:
            system_ts = AptBackend.get_system_install_date()
            manual_raw = set(subprocess.check_output(["apt-mark", "showmanual"], text=True).splitlines())

            blacklist_patterns = [
                "ubuntu-", "linux-", "grub-", "shim-", "yaru-", "gnome-",
                "language-", "fonts-", "lib", "plymouth", "xdg-", "xorg",
                "xkb-", "xcursor-", "ibus", "im-config", "gstreamer",
                "printer-driver-", "cups", "avahi-", "brltty", "wpasupplicant",
                "network-manager", "rfkill", "policykit-", "packagekit",
                "update-", "software-properties-", "apt-", "dpkg", "snap"
            ]

            whitelist = {
                "code", "git", "git-all", "nodejs", "npm", "docker-compose",
                "vlc", "firefox", "curl", "wget", "cmake", "clang",
                "build-essential", "python3-pip", "gradle", "maven",
                "openjdk-17-jdk", "openjdk-21-jdk", "postgresql",
                "mariadb-server", "php", "composer", "pandoc", "geany",
                "thunderbird", "libreoffice-writer", "libreoffice-calc",
                "libreoffice-impress", "transmission-gtk", "rhythmbox",
                "remmina", "snapd", "termius-app", "hashcat", "wireshark",
            }

            filtered = set()
            for pkg in manual_raw:
                if pkg in whitelist:
                    filtered.add(pkg)
                    continue

                if any(pkg.startswith(p) for p in blacklist_patterns):
                    continue

                try:
                    res = subprocess.check_output(
                        ["dpkg-query", "-W", "-f=${db-fsys:Last-Modified}\n", pkg],
                        text=True
                    ).strip()
                    pkg_ts = int(res)
                    if pkg_ts > system_ts + 86400:
                        filtered.add(pkg)
                except:
                    continue

            return filtered
        except:
            return set()

    @staticmethod
    def get_package_details(manual_list):
        packages = []
        try:
            res = subprocess.check_output(
                ["dpkg-query", "-W", "-f=${Package}\t${Version}\t${Description}\n"],
                text=True
            )
            for line in res.splitlines():
                parts = line.split('\t')
                if len(parts) >= 3:
                    name, version, desc = parts[0], parts[1], parts[2]
                    if name in manual_list:
                        icon = AptBackend.find_icon(name)
                        packages.append({
                            "name": name,
                            "version": version,
                            "description": desc,
                            "icon": icon,
                            "type": "APT",
                            "install_date": "Manual"
                        })
        except: pass
        return packages

    @staticmethod
    def find_icon(name):
        if os.path.exists(f"/usr/share/pixmaps/{name}.png"): return f"/usr/share/pixmaps/{name}.png"
        if os.path.exists(f"/usr/share/pixmaps/{name}.svg"): return f"/usr/share/pixmaps/{name}.svg"
        base_icon_dir = "/usr/share/icons/hicolor"
        for size in ["48x48", "64x64", "scalable"]:
            for ext in ["png", "svg"]:
                icon_path = os.path.join(base_icon_dir, size, "apps", f"{name}.{ext}")
                if os.path.exists(icon_path): return icon_path
        return None

    @staticmethod
    def get_upgradable():
        upgradable = []
        try:
            res = subprocess.check_output(["apt", "list", "--upgradable"], text=True, stderr=subprocess.DEVNULL)
            lines = res.splitlines()[1:]
            for line in lines:
                if '/' in line:
                    parts = line.split()
                    name = parts[0].split('/')[0]
                    version = parts[1]
                    upgradable.append({"name": name, "version": version, "type": "APT", "description": f"Update to {version} available"})
        except: pass
        return upgradable

    @staticmethod
    def search_packages(query):
        results = []
        if not query or len(query) < 2: return results
        try:
            res = subprocess.check_output(["apt-cache", "search", query], text=True)
            for line in res.splitlines()[:50]:
                if ' - ' in line:
                    name, desc = line.split(' - ', 1)
                    results.append({"name": name.strip(), "description": desc.strip(), "type": "APT", "version": "Latest", "install_date": "In repo"})
        except: pass
        return results

    @staticmethod
    def get_history():
        history = []
        log_file = "/var/log/dpkg.log"
        if os.path.exists(log_file):
            try:
                with open(log_file, "r") as f:
                    for line in f.readlines()[-200:]:
                        parts = line.split()
                        if len(parts) >= 5 and parts[2] in ["install", "upgrade", "remove"]:
                            history.append({"date": f"{parts[0]} {parts[1]}", "action": parts[2].capitalize(), "package": parts[3], "version": parts[4], "type": "APT"})
                history.reverse()
            except: pass
        return history

    @staticmethod
    def get_ppas():
        ppas = []
        sources_dir = "/etc/apt/sources.list.d/"
        if os.path.exists(sources_dir):
            for file in os.listdir(sources_dir):
                if file.endswith(".list") or file.endswith(".sources"):
                    path = os.path.join(sources_dir, file)
                    enabled = not file.endswith(".disabled")
                    
                    # Heuristic to clean up the name
                    name = file.replace(".list", "").replace(".sources", "").replace("_", "/").replace("-", ".")
                    
                    ppas.append({
                        "name": name,
                        "file": file,
                        "path": path,
                        "enabled": enabled,
                        "type": "PPA"
                    })
        return ppas

    @staticmethod
    def add_ppa(ppa_line):
        """Adds a PPA using add-apt-repository"""
        try:
            cmd = ["pkexec", "add-apt-repository", "-y", ppa_line]
            return subprocess.call(cmd) == 0
        except: return False

    @staticmethod
    def remove_ppa(ppa_name):
        """Removes a PPA using add-apt-repository --remove"""
        try:
            cmd = ["pkexec", "add-apt-repository", "--remove", "-y", ppa_name]
            return subprocess.call(cmd) == 0
        except: return False

    @staticmethod
    def toggle_ppa(ppa_file, enable=True):
        """Enables or disables a PPA by renaming the file"""
        try:
            sources_dir = "/etc/apt/sources.list.d/"
            old_path = os.path.join(sources_dir, ppa_file)
            if enable:
                new_file = ppa_file.replace(".disabled", "")
            else:
                new_file = ppa_file + ".disabled" if not ppa_file.endswith(".disabled") else ppa_file
            
            new_path = os.path.join(sources_dir, new_file)
            cmd = ["pkexec", "mv", old_path, new_path]
            return subprocess.call(cmd) == 0
        except: return False

    @staticmethod
    def get_deb_info(file_path):
        """Parses .deb file metadata using dpkg-deb --info"""
        try:
            res = subprocess.check_output(["dpkg-deb", "--info", file_path], text=True)
            info = {}
            for line in res.splitlines():
                if ": " in line:
                    key, val = line.split(": ", 1)
                    info[key.strip().lower()] = val.strip()
            return info
        except: return None

class PackageWorker(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    def run(self):
        try:
            if not AptBackend.is_available():
                self.finished.emit([])
                return
            manual = AptBackend.get_manual_list()
            pkgs = AptBackend.get_package_details(manual)
            self.finished.emit(pkgs)
        except Exception as e:
            self.error.emit(str(e))

class UninstallWorker(QThread):
    finished = pyqtSignal(bool, str)
    def __init__(self, pkg_name, pkg_type):
        super().__init__()
        self.pkg_name = pkg_name
        self.pkg_type = pkg_type
    def run(self):
        try:
            if self.pkg_type == "APT":
                cmd = ["pkexec", "apt-get", "remove", "--purge", "-y", self.pkg_name]
            elif self.pkg_type == "Snap":
                cmd = ["pkexec", "snap", "remove", self.pkg_name]
            elif self.pkg_type == "Flatpak":
                cmd = ["pkexec", "flatpak", "uninstall", "-y", self.pkg_name]
            elif self.pkg_type == "AppImage":
                # AppImage removal is just deleting the file
                if os.path.exists(self.pkg_name):
                    os.remove(self.pkg_name)
                    self.finished.emit(True, f"Removed AppImage {self.pkg_name}")
                    return
                else:
                    self.finished.emit(False, "AppImage file not found")
                    return
            else:
                self.finished.emit(False, "Unknown package type")
                return

            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = proc.communicate()
            self.finished.emit(proc.returncode == 0, f"Uninstalled {self.pkg_name}" if proc.returncode == 0 else stderr)
        except Exception as e:
            self.finished.emit(False, str(e))

class InstallWorker(QThread):
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(str)
    def __init__(self, pkg_name, pkg_type, action="install"):
        super().__init__()
        self.pkg_name = pkg_name
        self.pkg_type = pkg_type
        self.action = action
    def run(self):
        try:
            if self.pkg_type == "APT":
                if self.action == "install": cmd = ["pkexec", "apt-get", "install", "-y", self.pkg_name]
                else: cmd = ["pkexec", "apt-get", "install", "--only-upgrade", "-y", self.pkg_name]
            elif self.pkg_type == "Snap":
                cmd = ["pkexec", "snap", "install" if self.action == "install" else "refresh", self.pkg_name]
            elif self.pkg_type == "Flatpak":
                cmd = ["pkexec", "flatpak", "install" if self.action == "install" else "update", "-y", self.pkg_name]
            else: return
            self.progress.emit(f"Starting {self.action}...")
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            while True:
                line = proc.stdout.readline()
                if not line: break
                self.progress.emit(line.strip())
            proc.wait()
            self.finished.emit(proc.returncode == 0, f"Finished {self.action}")
        except Exception as e: self.finished.emit(False, str(e))
