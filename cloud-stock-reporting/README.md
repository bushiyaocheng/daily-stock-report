# 云端科技股日报

这是一套 GitHub Actions 版云端自动化。它每天 09:00 香港时间运行，即使本机和 Codex 桌面端关闭，也会在 GitHub 云端生成 Markdown 日报。

## 这版已经修正

- SPCX 不再映射为小鹏/XPEV。
- 如果 SPCX 尚未取得正式交易数据，报告只做 SpaceX IPO/上市进展跟踪，不编造股价、涨跌幅、均线或 RSI。
- 如果 SPCX 上市后 Yahoo Finance 可取得日线数据，脚本会自动切换为行情分析。

## 使用方式

1. 新建一个 GitHub 仓库。
2. 把本目录里的所有文件放到仓库根目录，包括 `.github/workflows/daily-stock-report.yml`。
3. 在 GitHub 仓库的 `Settings -> Secrets and variables -> Actions` 里可选添加：
   - `SEC_USER_AGENT`：例如 `your-name@example.com`，用于访问 SEC 数据。
   - `SLACK_WEBHOOK_URL`：如果要把摘要推送到 Slack。
4. 推送到 GitHub 后，工作流会每天 01:00 UTC 运行，也就是香港时间 09:00。
5. 每次运行后的完整 Markdown 报告会出现在 GitHub Actions 的 artifact 里，也会写入 job summary。

## 标的

美股：

- SPCX / SpaceX：未上市时跟踪 IPO，上市后自动转行情。
- NVDA / NVIDIA。
- TSM / 台积电 ADR。

港股：

- 9988.HK / 阿里巴巴-W。
- 0700.HK / 腾讯控股。
- 3690.HK / 美团-W。

## 后续可加

- 邮件发送。
- 企业微信/飞书/Telegram 推送。
- 自动提交日报到仓库。
- 使用 OpenAI API 把数据整理成更像人工写作的深度报告。
