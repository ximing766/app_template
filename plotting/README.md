# 参数绘图模块（pyqtgraph）

产测参数绘图的框架占位，后续页面可直接复用，无需重复搭建 pyqtgraph 基础。

## 目录结构

```
plotting/
├── __init__.py       # 导出 LivePlotWidget / PlotCurveSpec
└── live_plot.py      # 主题感知的实时曲线控件
```

## 快速使用

```python
from plotting import LivePlotWidget

plot = LivePlotWidget(title="Voltage", x_label="Sample", y_label="V")
layout.addWidget(plot)

plot.add_curve("ch1", name="Channel 1", color="#568af2")
plot.add_curve("ch2", name="Channel 2", color="#4CAF50")

plot.append("ch1", 3.31)            # x 自增
plot.append("ch1", 3.29, x=12.5)    # 指定 x
plot.clear()                        # 清采样但保留曲线定义
plot.clear_curves()                 # 移除所有曲线
```

## 特性

- **环形缓冲**：每条曲线默认保留最近 5000 点，超出自动丢弃最旧数据（`PlotCurveSpec.trim`）
- **自动网格 / 抗锯齿 / 降采样**：大数据量下保持流畅
- **主题跟随**：调用 `plot.apply_theme(is_light)` 同步坐标轴与文字颜色，背景透明以透出应用背景图
- **范围控制**：`set_x_range` / `set_y_range`（传 `None` 恢复自动范围）、`reset_view`

## 接入页面时的建议

1. 在页面 `init_content()` 中创建 `LivePlotWidget`，并加入布局
2. 在 `apply_base_style(theme_name)` 中调用 `plot.apply_theme(theme_name == "light")`
3. 数据源可以是串口线程信号（`SerialManager.data_received`）解析后的数值
4. 长时间运行注意只在必要时 `setData`，避免每帧重绘

## 依赖

- `pyqtgraph >= 0.13`（已在 requirements.txt）
- 缺少该依赖时控件会显示安装提示，不影响应用其它页面启动
