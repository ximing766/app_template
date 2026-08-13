# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Agent Role

Always adopt the **PySide6 Desktop Engineer** agent role (defined in `.claude/agents/engineering-pyside6-desktop-engineer.md`) for every session. This means:
- Act as an expert Python desktop application engineer specializing in PySide6/Qt
- Follow all critical rules, technical patterns, and workflow processes defined in that agent file
- Use the communication style described there (frame decisions by layout needs, explain threading choices, flag QSS limitations and packaging pitfalls)
- Never block the event loop, respect Qt's ownership model, use signals for cross-component communication

## Project Overview

A Windows desktop application template built with Python 3.10+ and PySide6 (pure, no third-party UI frameworks). It provides frameless window chrome, theming, page-based navigation, user authentication, and auto-update as a starting point for building Qt desktop apps.

## Commands

| Action | Command |
|--------|---------|
| Run app | `conda run -n myenv python main.py` |
| Install dependencies | `pip install -r requirements.txt` |
| Build standalone exe | `.\build_lite.ps1` |
| Build + GitHub release | `.\build_lite.ps1 -r` |
| Release only (skip build) | `.\build_lite.ps1 -r -s` |

No test suite or linter is configured.

## Architecture

### Entry Point

`main.py` → creates `QApplication`, instantiates `MainWindow` (from `core/`), registers pages, then enters the Qt event loop.

### Page Plugin System

Pages are the main extension point. Each page inherits `pages/base_page.py:BasePage` and is registered in `main.py` via:

```python
page_manager.register_page("id", "Title", PageClass, icon="icon.svg", order=1, required_role="user")
```

Pages are lazily instantiated on first navigation. The `PageManager` handles routing, left-menu integration, and role-based visibility.

### Config System

`config/config_manager.py` (ConfigManager) — typed accessor for `config/config.json`. This is the single config interface for all new code.

Theme state is stored in `config.json` under `theme.current_theme` ("light" or "dark").

### Custom Window Frame

The app uses `Qt.FramelessWindowHint` with custom resize handling (native `startSystemResize`) and a custom title bar (`core/main_window.py:TitleBar`). Background image with configurable opacity is rendered in `MainWindow.paintEvent`.

### Database Layer

SQLite via SQLAlchemy ORM. `database/database_manager.py` provides a `session_scope()` context manager. Models in `database/models.py`.

### User Management

`user_mag/` contains login dialog, session/RBAC logic, and admin page. Login is shown at startup. Pages can gate on `required_role`.

### Icons

`core/icons.py` rasterizes SVGs through `QSvgRenderer` at the device pixel ratio and tints them, with a cache keyed by (path, size, color, dpr). Use `render_svg()` for custom painting and `svg_icon()` for a `QIcon`. Never scale a small raster up — that is what made icons look blurry.

## Key Conventions

- All UI is pure PySide6 — no third-party UI frameworks (no OneDark, no PyDracula, no qt-material).
- Widget styling uses dynamically generated QSS via `BasePage.apply_base_style(theme_name)`.
- SVG icons go through `core/icons.py`, referencing `assets/images/svg_icons/`.
- Window chrome (title bar, nav rail) is transparent-backed so the background image reads through; the container decides its own background in `_apply_window_style()`, never in `paintEvent`.
- App features belong in `pages/`, `core/`, or new top-level modules.
- Config values are accessed through `ConfigManager`.
- There is no auto-update mechanism — it was removed deliberately.

## Build Notes

- Build uses Nuitka via `build_lite.ps1`. The script references a hardcoded Conda env path that must be adjusted per machine.
- `requirements.txt` is UTF-16 encoded — some tools may need conversion to UTF-8 to parse it correctly.
