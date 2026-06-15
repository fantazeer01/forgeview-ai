# Current Status: ForgeViewAI

Last updated: 2026-06-15.

## Project State

ForgeViewAI is a documentation-heavy automation and trading operations project with several working foundations:

- BTC Spot Bot workflow source in the repository.
- BTC Futures Paper Bot workflow source in the repository.
- documented newer exports for Spot v88 STABILITY FIX and Futures v22 EXIT SAFETY outside the repository download folder.
- project docs for overview, roadmap, backlog, bot version history, and future Codex tasks.
- growth assets for content prompts, lead-system MVP, automation map offer, and a local shorts generator.

The project is not yet a packaged SaaS product. The current best business loop is manual and Telegram-first: publish useful lessons, start conversations, deliver free Automation Maps, and convert some users into paid Automation Audits.

## Content Machine State

Content Machine v2 is prepared, not deployed.

Current assets:

- `growth/content-machine-v2/PROMPTS.md` defines the content rules.
- `growth/content-machine-v2/IMPLEMENTATION_REPORT.md` records the implementation.
- `growth/lead-system-mvp/content_queue_map.csv` contains ready MAP offer posts.
- `growth/shorts-generator/` can render text-slide vertical videos locally.

Core rule:

Public content must lead with a mistake, bug, lesson, insight, principle, workflow insight, automation insight, or operational takeaway. Internal events are context only.

Known state:

- No automatic publishing is documented as deployed.
- YouTube upload remains manual for the shorts generator MVP.
- Image generation is optional for MVP content.
- `gpt-image-1` is the documented default if image generation is used; `gpt-image-2` should not be assumed available.

## Spot Bot State

Repository source:

```text
spot-bot/BTC Bot - v87 CLEAN COMMANDS (1).json
```

Documented newer export:

```text
%USERPROFILE%\Downloads\BTC Bot - v88 STABILITY FIX.json
```

Current behavior and purpose:

- BTCUSDT spot testnet workflow.
- Long-only trading.
- 15-minute schedule.
- Uses 15m Binance candles and derived 1h, 2h, and 4h trend.
- Uses RSS news sentiment as a score adjustment.
- Supports stop loss, take profit, timed exit, and bearish reversal exit.
- Supports Telegram controls.

Important v88 safety focus:

- avoid phantom internal positions after failed Binance orders;
- commit planned position only after confirmed order response;
- expose `shortScore` and `bearishExitSignal`;
- close using existing `position.qty`;
- preserve scoring, thresholds, and risk parameters.

Known issues:

- Spot v88 still needs import and controlled validation in n8n.
- Telegram mode text may not match actual thresholds.
- News fields are computed but not fully surfaced downstream.
- Original adaptive cooldown code may still include unreachable logic outside current fix scope.

## Futures Bot State

Repository source:

```text
spot-bot/futures-bot/BTC Futures Paper Bot - v21 QUALITY FILTERS (1).json
```

Documented newer export:

```text
%USERPROFILE%\Downloads\BTC Futures Paper Bot - v22 EXIT SAFETY.json
```

Current behavior and purpose:

- BTCUSDT futures paper trading workflow.
- Supports LONG and SHORT signals.
- Includes v21 short quality filters.
- Tracks internal paper position, paper PnL, wins, and losses.
- Supports Telegram controls.

Verified v22 safety result:

- Futures v22 EXIT SAFETY was documented as PASS.
- Normal cooldown and loss cooldown apply only to `OPEN_LONG` and `OPEN_SHORT`.
- `CLOSE_LONG` and `CLOSE_SHORT` are not blocked by cooldown logic.

Known issues:

- Paper PnL does not fully model leverage, fees, slippage, funding, or liquidation.
- `Execute Futures Demo Order` remains disconnected in paper mode.
- Futures AGGRESSIVE mode currently has a higher min score than ACTIVE.
- Duplicate cooldown output fields remain in the base object.
- Long-side quality filters are not yet equivalent to short-side filters.

## GitHub State

GitHub state is not fully verifiable from this local environment because the `git` command is not available in the current PowerShell session.

Known repository state from files:

- project files are present locally;
- docs and workflow JSON exports exist in the workspace;
- current docs reference exports stored outside the repository under the user Downloads folder;
- no GitHub remote, branch, commit, or PR status was verified during this documentation update.

Operational rule:

Before claiming repository cleanliness, branch status, or pushed changes, verify Git availability or use an available GitHub connector.

## Known Problems

- Stable Spot v88 import is not yet validated in n8n.
- Telegram webhook URLs need verification after workflow import.
- Telegram STATUS lacks enough diagnostics to explain decisions without opening n8n.
- LAST ERROR needs richer context.
- Spot mode text mismatch should be fixed without changing thresholds.
- News fields should be returned consistently to avoid fake `NO_NEWS` style fallbacks.
- n8n import checklist is still a proposed task.
- Growth workflows are prepared as assets but not proven as deployed automation.
- First 10 MAP conversations have not been documented as completed.
