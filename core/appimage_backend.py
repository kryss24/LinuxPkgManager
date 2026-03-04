import os
import subprocess
from pathlib import Path

class AppImageBackend:
    @staticmethod
    def get_appimages():
        appimages = []
        scan_dirs = [
            Path.home() / "Applications",
            Path.home() / "Downloads",
            Path.home() / "Desktop",
            Path.home()
        ]
        
        for d in scan_dirs:
            if d.exists():
                try:
                    for f in d.iterdir():
                        if f.suffix.lower() == ".appimage":
                            stats = f.stat()
                            size = f"{stats.st_size / (1024*1024):.1f} MB"
                            appimages.append({
                                "name": f.name,
                                "path": str(f),
                                "version": "-",
                                "size": size,
                                "description": f"AppImage in {f.parent}",
                                "type": "AppImage",
                                "install_date": "Found locally"
                            })
                except: pass
        return appimages

    @staticmethod
    def create_desktop_file(name, path):
        """Creates a .desktop file in ~/.local/share/applications/"""
        try:
            apps_dir = Path.home() / ".local" / "share" / "applications"
            apps_dir.mkdir(parents=True, exist_ok=True)
            
            # Make the AppImage executable
            os.chmod(path, 0o755)
            
            desktop_file = apps_dir / f"{name.lower().replace(' ', '_')}.desktop"
            content = f"""[Desktop Entry]
Type=Application
Name={name.replace('.AppImage', '').replace('.appimage', '')}
Exec={path}
Icon=exec
Terminal=false
Categories=Utility;
Comment=Integrated by LinuxPkgManager
"""
            with open(desktop_file, "w") as f:
                f.write(content)
            return True
        except:
            return False

    @staticmethod
    def remove_appimage(path):
        try:
            os.remove(path)
            return True
        except: return False
