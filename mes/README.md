# MES 集成模块（测试结果上传）

面向公司 MES 系统的网络通信骨架，用于后续上传各项产测结果。
传输、重试、队列与 Qt 信号均已实现，**只需按真实 MES 接口对齐 URL 与字段名**。

## 目录结构

```
mes/
├── __init__.py       # 导出 MESClient / MESConfig / TestResult / TestItem
├── mes_config.py     # 连接配置（config.json 的 "mes" 节）
├── test_record.py    # 测试结果数据模型 + JSON payload
├── mes_worker.py     # 后台 HTTP 上传任务（QThreadPool）
└── mes_client.py     # Qt 客户端（信号 + 失败重试队列）
```

## 配置

`config/config.json` 中新增 `mes` 节：

```json
"mes": {
    "enabled": false,
    "base_url": "https://mes.example.com",
    "upload_path": "/api/v1/test-results",
    "api_key": "",
    "timeout": 10,
    "max_retries": 3,
    "verify_tls": true
}
```

- `enabled` 为 `false` 时上传直接跳过（触发 `upload_skipped`）
- `base_url` 为空同样视为未配置
- `api_key` 会同时写入 `Authorization: Bearer ...` 与 `X-API-Key`

代码中读取/保存配置：

```python
from mes import MESConfig

config = MESConfig.from_config_manager(config_manager)
config.enabled = True
config.base_url = "https://mes.example.com"
config.save(config_manager)          # 写回 config.json
```

## 组测结果

```python
from mes import TestItem, TestResult

result = TestResult(
    serial_number="SN20251019001",
    product="MODEL-X",
    station="FCT-01",
    operator="admin",
)
result.add_item(TestItem("voltage_3v3", 3.31, "V", lower_limit=3.2, upper_limit=3.4))
result.add_item(TestItem("current_idle", 0.42, "A", lower_limit=0.0, upper_limit=0.5))
result.add_item(TestItem("boot", True))
print(result.overall_passed())       # True
```

`TestItem.is_pass()` 会同时校验 `passed` 与上下限；`TestResult.overall_passed()`
要求所有项通过。

## 上传

```python
from mes import MESClient

client = MESClient(config)
client.upload_started.connect(lambda rid: print("start", rid))
client.upload_succeeded.connect(lambda rid, body: print("ok", rid, body))
client.upload_failed.connect(lambda rid, err: print("fail", rid, err))
client.upload_skipped.connect(lambda rid, reason: print("skip", rid, reason))

client.upload_result(result)
```

- 上传在 `QThreadPool` 线程执行，**不阻塞 GUI**
- 失败（网络错误 / 5xx / 408 / 429）时 payload 进入内存重试队列（上限 50 条），
  可用 `client.retry_pending()` 重新发送，`client.pending_count()` 查询数量
- 4xx（除 408/429）不重试，直接上报失败
- 重试退避：0.5s → 1s → 2s → 4s

## 待对接事项

1. 将 `TestResult.to_payload()` 的字段名映射到 MES 实际字段（`serialNumber` / `items[]` 等）
2. 确认鉴权方式（Bearer / X-API-Key / 签名 / 时间戳）
3. 如 MES 需要离线补传，可将重试队列持久化到本地 SQLite（`database/` 已有依赖）
4. 若需代理或双向 TLS，在 `MESConfig.extra_headers` 与 `mes_worker` 中扩展

## 依赖

仅使用标准库 `urllib`（无新增第三方依赖）。
