import subprocess
import os

class FlatpakBackend:
    @staticmethod
    def is_available():
        return os.path.exists("/usr/bin/flatpak")

    @staticmethod
    def get_installed():
        apps = []
        if not FlatpakBackend.is_available(): return apps
        try:
            # flatpak list --app --columns=name,application,version,size,origin
            res = subprocess.check_output([
                "flatpak", "list", "--app", 
                "--columns=name,application,version,size,origin"
            ], text=True)
            lines = res.splitlines()
            for line in lines:
                parts = line.split('	')
                if len(parts) >= 5:
                    name, app_id, version, size, origin = parts[0], parts[1], parts[2], parts[3], parts[4]
                    apps.append({
                        "name": name,
                        "id": app_id,
                        "version": version,
                        "size": size,
                        "origin": origin,
                        "description": f"Flatpak from {origin} ({size})",
                        "type": "Flatpak",
                        "install_date": "Installed via Flatpak"
                    })
        except: pass
        return apps

    @staticmethod
    def get_upgradable():
        upgradable = []
        if not FlatpakBackend.is_available(): return upgradable
        try:
            # flatpak remote-ls --updates
            res = subprocess.check_output(["flatpak", "remote-ls", "--updates", "--columns=name,application,version"], text=True)
            lines = res.splitlines()
            for line in lines:
                parts = line.split('	')
                if len(parts) >= 3:
                    upgradable.append({
                        "name": parts[0],
                        "id": parts[1],
                        "version": parts[2],
                        "type": "Flatpak",
                        "description": f"Update to {parts[2]} available"
                    })
        except: pass
        return upgradable

    @staticmethod
    def search_flatpaks(query):
        results = []
        if not query or not FlatpakBackend.is_available(): return results
        try:
            res = subprocess.check_output([
                "flatpak", "search", query, 
                "--columns=name,application,version,description"
            ], text=True)
            lines = res.splitlines()
            for line in lines[:50]:
                parts = line.split('	')
                if len(parts) >= 4:
                    results.append({
                        "name": parts[0],
                        "id": parts[1],
                        "version": parts[2],
                        "description": parts[3],
                        "type": "Flatpak",
                        "install_date": f"ID: {parts[1]}"
                    })
        except: pass
        return results
