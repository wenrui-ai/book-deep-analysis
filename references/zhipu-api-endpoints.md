# 智谱 API 端点 + 额度池说明

## 两个端点

| 端点 | URL | 适用 |
|---|---|---|
| Coding Plan | `https://open.bigmodel.cn/api/coding/paas/v4/chat/completions` | Coding Plan 套餐用户 |
| 通用余额 | `https://open.bigmodel.cn/api/paas/v4/chat/completions` | 按量付费用户 |

**Coding Plan 用户走 coding 端点 = ¥0 内部额度。用错端点会报 429。**

脚本默认走 Coding Plan 端点。通用余额用户改环境变量：
```bash
export ZHIPU_API_URL="https://open.bigmodel.cn/api/paas/v4/chat/completions"
```

## 模型选择

| 任务 | 推荐模型 | 类型 | Coding Plan 可用 |
|---|---|---|---|
| OCR（扫描件 PDF） | glm-4.6v | 视觉 | ✅ |
| 概念卡提炼 | glm-5.2 | 纯文本 | ✅ |
| OCR 备选 | glm-4v-flash | 视觉 | ✅ |
| 概念提炼备选 | glm-4-flash | 纯文本 | ✅ |

**不要混用**：视觉模型做 OCR，纯文本模型做提炼，效率最高。

## 常见错误码

| HTTP | code | 含义 | 修法 |
|---|---|---|---|
| 429 | 1113 | 余额不足 | 充值 / 换 Coding Plan 端点 |
| 429 | 1301 | QPS 限流 | 降并发 / 增重试等待 |
| 403 | 1311 | 套餐权限限制 | 升级套餐 |
| 400 | 1210 | 参数非法 | 检查模型名 / messages 格式 |

## 环境变量一览

| 变量 | 默认值 | 说明 |
|---|---|---|
| `ZHIPU_API_KEY` | （必填） | API Key |
| `ZHIPU_API_URL` | Coding Plan 端点 | API 端点 URL |
| `ZHIPU_OCR_MODEL` | glm-4.6v | OCR 用的模型 |
| `ZHIPU_TEXT_MODEL` | glm-5.2 | 概念提炼用的模型 |

## Key 安全规则

1. **Key 只走环境变量**，不要硬编码进任何文件
2. **不要把 Key 写进代码注释**（即使是示例注释）
3. **不要把 Key 写进 Git** —— `.gitignore` 已排除 `.env` / `*.key`
4. **跨 shell 不继承** —— 每次新终端都要重新 export，或在脚本内部做兜底
