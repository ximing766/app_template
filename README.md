# app_template

一个基于 PySide6 开发的现代、简洁的模板。

## 核心特性
- **现代 UI 设计**：基于 PyOneDark 框架，提供流畅且美观的交互体验。
- **自定义通知系统**：在应用右上角弹出美化的、自动消失的消息提醒。
- **背景定制**：支持自定义背景图片、透明度及主题切换。
- **自动更新**：集成 GitHub Release 自动检查并提示在线升级。
- **一键打包**：提供 Nuitka 优化打包脚本，自动处理 Git 提交与 GitHub 发布。

## 开发环境
- Windows 11
- Python 3.10+
- PySide6 6.4.0+

## 快速开始
1. 安装依赖：`pip install -r requirements.txt`
2. 运行应用：`python main.py`
3. 打包发布：运行 `.\build_lite.ps1` (需安装 GitHub CLI `gh`)

## 项目结构
- `core/`: 核心逻辑与常量定义
- `gui/`: UI 组件与主题资源
- `pages/`: 功能页面实现
- `database/`: 数据存储管理
- `user_mag/`: 用户权限管理

## 许可证
MIT License
