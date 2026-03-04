# Changelog

All notable changes to LinuxPkgManager will be documented in this file.

## [2.0.0] - 2026-03-04

### Added
- **Orphan packages & cache cleanup** — detect unused dependencies and free disk space
- **Light/Dark theme toggle** — switch themes with preference saved in config
- **List/Grid view toggle** — choose your preferred package display mode
- **Advanced sorting** — sort by name, size, install date or type (APT/Snap)
- **Package updates** — see available updates with one-click update all
- **Installation history** — timeline of all installs/removals from dpkg.log and snap changes
- **Package discovery** — search and install packages from APT repos and Snap store
- **Flatpak support** — list, manage and uninstall Flatpak apps (if installed)
- **AppImage support** — detect AppImages in ~/Applications, ~/Downloads, ~/Desktop
- **Drag & drop .deb** — drop a .deb file to inspect and install it
- **Statistics dashboard** — disk usage charts, package categories, install timeline
- **PPA management** — list, enable/disable and remove PPAs

### Changed
- Redesigned UI with sidebar navigation
- Improved package cards with richer metadata
- Better async backend with QThread for all operations
- Preferences saved in ~/.config/linuxpkgmanager/config.json

## [1.0.0] - 2026-02-26

### Added
- Initial release
- Display manually installed APT and Snap packages
- Search and filter packages
- One-click uninstall with pkexec
- Dark theme UI built with PyQt6
- Async backend with QThread
- Toast notifications
