import subprocess
import os
from PyQt6.QtCore import QThread, pyqtSignal


class AptBackend:

    @staticmethod
    def is_available():
        return os.path.exists("/usr/bin/apt")

    @staticmethod
    def get_system_install_date():
        """Date d'installation du système = date d'install de 'ubuntu-minimal'"""
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

            # Paquets à toujours afficher même s'ils matchent la blacklist
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

                # Garder uniquement ce qui a été installé après le système (+1 jour)
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
        except Exception as e:
            print(f"APT fetch error: {e}")
        return packages

    @staticmethod
    def find_icon(name):
        if os.path.exists(f"/usr/share/pixmaps/{name}.png"):
            return f"/usr/share/pixmaps/{name}.png"
        if os.path.exists(f"/usr/share/pixmaps/{name}.svg"):
            return f"/usr/share/pixmaps/{name}.svg"

        base_icon_dir = "/usr/share/icons/hicolor"
        for size in ["48x48", "64x64", "scalable"]:
            for ext in ["png", "svg"]:
                icon_path = os.path.join(base_icon_dir, size, "apps", f"{name}.{ext}")
                if os.path.exists(icon_path):
                    return icon_path

        return None


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
            else:
                cmd = ["pkexec", "snap", "remove", self.pkg_name]

            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate()

            if process.returncode == 0:
                self.finished.emit(True, f"Successfully uninstalled {self.pkg_name}")
            else:
                self.finished.emit(False, stderr or "Unknown error occurred")
        except Exception as e:
            self.finished.emit(False, str(e))
