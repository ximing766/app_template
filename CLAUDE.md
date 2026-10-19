# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## CodeGraph Usage (`.codegraph/` indexed)

This repository has a CodeGraph index. Follow the rules below to minimize token consumption and file-access round-trips.

### Decision Criteria — When to Use CodeGraph

| Scenario | Tool | Reason |
|----------|------|--------|
| 查找符号定义、调用链、跨文件引用 | `codegraph_explore` | 一次调用返回源码+调用路径，省去多次 grep/Read |
| 理解模块间依赖关系 | `codegraph_explore` | 自动追踪动态分派，grep 做不到 |
| 读取某个文件的当前带行号源码 | `codegraph_explore` 传文件名 | 等效 Read 但自动裁剪相关上下文 |
| 搜索纯文本 / 正则 / 不在代码中的内容 (config, .md, log) | `Grep` | CodeGraph 只索引代码符号 |
| 列出目录结构 / glob 文件名模式 | `Glob` | CodeGraph 不做路径搜索 |
| 确认文件是否存在、查看非代码文件 | `Read` / `Glob` | CodeGraph 不覆盖非代码资产 |

### Workflow — 标准访问流程

```
1. 收到任务 → 判断是否涉及代码理解/定位
       ├─ 是 → 优先 codegraph_explore (query = 符号名 / 文件名 / 自然语言问题)
       │        ├─ 返回足够信息 → 直接行动，不再 Read 已返回的文件
       │        └─ 信息不足 (符号被 deferred / 需要非代码文件) → 补充 Read/Grep
       └─ 否 (纯配置/资产/文本) → 直接 Glob/Read/Grep
```

### Rules

1. **CodeGraph First**: 任何涉及「这个函数在哪」「谁调用了它」「这个类怎么工作」的问题，第一个工具调用必须是 `codegraph_explore`，不要先 grep 再 explore。
2. **不要重复读取**: `codegraph_explore` 返回的源码视为已 Read —— 不要再对同一文件调用 Read。
3. **批量查询**: 一次 explore 可以传多个符号名（空格分隔），尽量合并查询而非逐个调用。
4. **自然语言也行**: query 支持自然语言问题，如 `"PageManager how does routing work"`，不必拆成精确符号名。
5. **Deferred 符号**: 如果返回中某符号标记为 deferred，再次 explore 指定该符号名即可加载完整源码。
6. **非代码文件走传统路径**: `.json`, `.md`, `.qss`, `.svg`, 日志等不在索引内，直接用 Read/Grep。
7. **编辑前确认行号**: explore 返回带行号的源码，编辑时直接用这些行号定位，无需额外 Read 确认。

### Cost Awareness

- 一次 `codegraph_explore` ≈ 1 tool call，通常替代 2-5 次 Grep + Read 组合。
- 目标：每个代码理解任务的工具调用次数 ≤ 2（1 次 explore + 至多 1 次补充）。
- 如果发现自己连续 grep 多个符号，停下来改用 explore 一次性获取。

---

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

### Serial Communication

`serial_comm/` provides the serial stack: `PortScanner` (background enumeration, includes
virtual ports via the Windows registry), `SerialManager.instance()` (process-wide singleton;
connections survive page navigation), `SerialWorker` (raw, binary-safe frame reads — bytes are
never split or stripped, so 0x0A/0x0D payloads arrive intact), and `pages/serial_page.py`
(auto-generated per-port control rows plus a console with TEXT/HEX views).

### MES Integration

`mes/` is the scaffold for uploading production test results to the company MES:
`TestResult`/`TestItem` (payload model), `MESConfig` (config.json → `"mes"` section),
`MESClient` (Qt signals, non-blocking `QThreadPool` uploads, bounded retry queue).
Endpoint/field mapping still needs aligning with the real API.

### Plotting

`plotting/` wraps pyqtgraph in `LivePlotWidget` (theme-aware, ring-buffered curves,
transparent background). pyqtgraph is imported lazily so a missing dependency does not
break the rest of the app.

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
