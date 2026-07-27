# Codex Font

Codex Font 是一個實驗性的開放字體計畫。我們用圖片生成工具寫出原稿，再逐字轉成
向量、檢查與核准。字型與原稿以 [SIL Open Font License 1.1](OFL.txt) 開放使用。

[前往試寫網站](https://jacoblincool.github.io/CodexFont/) ·
[回報問題](https://github.com/JacobLinCool/CodexFont/issues)

## 字體

| 字體 | 風格 | 版本 | 字集 |
|---|---|---|---:|
| Clear Hand TC／清楚手寫體 | 纖細、清楚，像原子筆或削尖鉛筆 | 0.1 Preview | 9,120／18,071 |
| Mew Note TC／喵筆記體 | 圓潤、溫暖，偶爾有一筆貓尾收筆 | 0.1 Preview | 9,088／18,071 |

兩款字體都完整收錄：

- 教育部 4,808 個常用漢字；
- 非漢字 3,060 個，包括英文、數字、標點、注音與常用符號；
- 平假名 93 個、片假名 96 個；
- 93 個直排替代字形。

Clear Hand TC 有 6,060 個漢字，完成 50.5%。Mew Note TC 有 6,028 個漢字，
完成 50.3%。最終目標是補齊
[`PROMPT.md`](PROMPT.md) 定義的 18,071 個 code points。

## 下載

Clear Hand TC：

- [TTF](dist/clear-hand-tc/font/ClearHandTC-Regular.ttf)
- [OTF](dist/clear-hand-tc/font/ClearHandTC-Regular.otf)
- [WOFF2](dist/clear-hand-tc/font/ClearHandTC-Regular.woff2)

Mew Note TC：

- [TTF](dist/mew-note-tc/font/MewNoteTC-Regular.ttf)
- [OTF](dist/mew-note-tc/font/MewNoteTC-Regular.otf)
- [WOFF2](dist/mew-note-tc/font/MewNoteTC-Regular.woff2)

詳細字集見 [`docs/COVERAGE.md`](docs/COVERAGE.md)，安裝方式見
[`docs/INSTALL.md`](docs/INSTALL.md)。

## 建置

需要 Python 3.11 或 3.12、[`uv`](https://docs.astral.sh/uv/) 與 Potrace。

```sh
uv sync
make dist
make test
make site
```

正式建置只使用已核准的原創 raster。可重建的逐字 PNG、SVG、中間字體與預覽不進
Git；Git LFS 只保存不可重建的原稿。

## 做一款新字體

使用 repository 內的
[`design-font-family` skill](.agents/skills/design-font-family/SKILL.md)。先描述用途、
字集、感覺與例句，工作流會帶你完成 pilot、原稿、檢查、字型與網站。

簡短流程見 [`docs/FONT_DESIGN_WORKFLOW.md`](docs/FONT_DESIGN_WORKFLOW.md)，完整建置
指令見 [`docs/BUILDING.md`](docs/BUILDING.md)。
