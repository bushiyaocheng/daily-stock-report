# Daily Tech Stock Report

这是一个用 GitHub Actions 自动生成的中文科技股与互联网股票行情日报项目。代码会在云端定时运行，抓取可用行情、新闻和 SEC 数据，生成 Markdown 报告并上传为 GitHub Actions artifact，同时写入 job summary。

## 代码目的

本项目的目标是每天自动整理上一交易日的重点科技、AI、半导体、商业航天和港股互联网标的表现，形成一份便于复盘的观察清单。

报告重点关注：

- 上一交易日价格表现、成交量、日内区间和涨跌幅。
- MA20、MA50、RSI14 等基础技术指标。
- 近期新闻、SEC 文件或上市/IPO 进展。
- AI 算力、半导体、商业航天、云、机器人和港股互联网相关风险与催化剂。
- 数据源缺失时明确说明缺口，不编造行情或指标。

本报告仅用于行情复盘和研究观察，不构成投资建议。

## 重点跟踪标的

### 美股与主题 ETF

| 代码 | 名称 | 跟踪重点 |
|---|---|---|
| `NVDA` | NVIDIA / 英伟达 | AI 算力、GPU、数据中心、半导体景气度、技术趋势与成交量。 |
| `TSM` | TSMC ADR / 台积电 ADR | 先进制程、AI 芯片代工、半导体供应链与估值变化。 |
| `NASA` | Tema Space Innovators ETF | 商业航天主题 ETF；注意这不是美国国家航空航天局股票。重点关注主题资金、持仓集中度、SPCX/商业航天相关敞口和波动风险。 |
| `SPCX` | SpaceX | IPO/上市进展、SEC 文件、定价区间、首日流动性、锁定期、估值可比性；若 Yahoo Finance 暂无可靠日线数据，则只做进展跟踪，不编造股价或技术指标。 |

### 港股互联网

| 代码 | 名称 | 跟踪重点 |
|---|---|---|
| `9988.HK` | 阿里巴巴-W | 电商、云、AI 应用、回购、估值修复和南向资金。 |
| `0700.HK` | 腾讯控股 | 游戏、广告、金融科技、AI 产品化、回购和行业相对强弱。 |
| `3690.HK` | 美团-W | 本地生活竞争、利润率、消费复苏、外卖与到店业务趋势。 |

### 扩展播报标的

报告还会补充科技、AI、半导体、算力、云和机器人方向的新闻播报，当前新闻监控包括：`NVDA`、`TSM`、`NASA`、`AMD`、`AVGO`、`SMCI`、`TSLA`、`ROK`。

## 运行方式

Workflow 文件位于：

```text
.github/workflows/daily-stock-report.yml
```

当前配置：

```yaml
on:
  schedule:
    # 09:07 Asia/Hong_Kong = 01:07 UTC.
    - cron: "7 1 * * *"
  workflow_dispatch:
```

说明：GitHub Actions 的 `schedule` 使用 UTC，并且不是强实时定时器。GitHub 可能因为平台负载导致 scheduled workflow 延迟甚至跳过。为便于排查，workflow 已加入 schedule diagnostics，会在日志和 job summary 中记录：

- 触发事件类型。
- `github.event.schedule`。
- run id / run attempt / commit SHA。
- UTC 当前时间。
- 香港时间当前时间。
- 预期调度时间。

也可以在 GitHub Actions 页面手动执行 `workflow_dispatch` 来测试报告生成。

## 输出内容

每次运行会生成一个 Markdown 文件：

```text
reports/tech_stock_report_YYYY-MM-DD.md
```

文件日期使用香港时间，避免在香港时间凌晨运行时出现 UTC 日期和正文生成时间不一致的问题。

报告结构包括：

1. 摘要结论。
2. 美股重点标的表。
3. SPCX / SpaceX IPO 或上市后行情跟踪。
4. 美股科技、AI 与机器人播报。
5. 港股互联网个股表。
6. 催化剂与风险。

## 数据源与环境变量

主要依赖：

- `yfinance`：美股、ETF、ADR 和港股行情。
- Yahoo Finance RSS：相关新闻。
- SEC submissions API：SPCX/SpaceX 相关 SEC 文件跟踪。
- `pandas`：指标计算与表格整理。

可选 Secrets：

| 变量 | 用途 |
|---|---|
| `SEC_USER_AGENT` | 访问 SEC API 时使用的 User-Agent，建议设置为可联系邮箱。 |
| `SLACK_WEBHOOK_URL` | 如需推送摘要到 Slack，可配置 Incoming Webhook。 |

## 注意事项

- `NASA` 是 ETF 代码，不代表 NASA 政府机构股票。
- `SPCX` 如无法取得可靠日线交易数据，只做上市/IPO/SEC 文件跟踪。
- Yahoo Finance 可能限流或暂时不可用，报告会明确说明缺口。
- 本项目生成的是自动化行情复盘，不替代人工研究和风控判断。
