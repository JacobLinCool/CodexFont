# 建置

## 環境

需要 Python 3.11 或 3.12、[`uv`](https://docs.astral.sh/uv/) 與 Potrace。

```sh
uv sync
```

原創 raster、字序、審查與核准都在 repository 中。逐字 PNG、SVG、中間字體與
預覽會在 `build/` 重新產生，不進 Git。

## 常用指令

```sh
make validate-imagegen   # 驗證 Clear Hand TC
make validate-mew-note   # 驗證 Mew Note TC
make release-preview     # 在 build/ 建置兩款字體
make dist                # 重建正式 dist/
make reproducibility     # 獨立重建並逐檔比對兩份 release
make test                # 執行測試
make hygiene             # 檢查 repository 與 Git LFS
make site                # 建置 GitHub Pages 網站
```

直接執行 `make` 會跑 `dist` 與 `test`。
每款字體只會原子替換自己的 `dist/<family-id>/`；建字器拒絕把整個 `dist/`
當作目的地，因此平行建置不會刪除另一款字體。

## 資料流

1. 凍結唯一的 Unicode 字序。
2. 用圖片生成工具寫出白底黑字原稿。
3. 比對字帖，檢查字形身分與筆畫。
4. 用固定的 Potrace 與 quadratic pipeline 轉成向量。
5. 檢查輪廓、尖刺、格線污染與小尺寸可讀性。
6. 人工查看黑底白字與白底黑字 proof。
7. 以 SHA-256 固定通過的原稿、報告與審查。
8. 只用已核准資料建置 TTF、OTF、WOFF 與 WOFF2。

其他字型只能當字帖，不能提供正式 raster 或 outline。缺字也不能用 fallback 偽裝成
本字體的 coverage。

## 成品不變量

Clear Hand TC 必須符合：

- `cmap` 恰好 9,120 個 code points；
- 6,060 個漢字與 3,060 個非漢字；
- 9,103 個可見 encoded glyph 與 17 個語意空白 glyph；
- 93 個不編碼的直排替代字形；
- 含 `.notdef` 的 glyph order 恰好 9,214；

Mew Note TC 必須符合：

- `cmap` 恰好 9,088 個 code points；
- 6,028 個漢字與 3,060 個非漢字；
- 9,071 個可見 encoded glyph 與 17 個語意空白 glyph；
- 93 個不編碼的直排替代字形；
- 含 `.notdef` 的 glyph order 恰好 9,182；
- release approval 必須固定 0.1 Preview 的 9,120 → 9,088 偏差紀錄。

兩款字體共同符合：

- 所有正式輪廓沒有 micro edge 或 acute micro turn；
- `vert` 與 `vrt2` 各有 93 個替代；
- TTF、OTF、WOFF、WOFF2 的字集、輪廓、metrics 與 feature 一致；
- `OS/2.fsType = 0`，授權為 OFL 1.1；
- 兩次乾淨建置的輸出雜湊一致。

兩款字體的 `report.json` 記錄來源、核准、OpenType、proof 與成品 SHA-256。

## 輸出

```text
dist/clear-hand-tc/font/   Clear Hand TC
dist/mew-note-tc/font/     Mew Note TC
dist/clear-hand-tc/proof/  Clear Hand TC 最終 proof
dist/mew-note-tc/proof/    Mew Note TC 最終 proof
build/site/                可直接部署的網站
```

字集細節見 [`COVERAGE.md`](COVERAGE.md)，設計流程見
[`FONT_DESIGN_WORKFLOW.md`](FONT_DESIGN_WORKFLOW.md)。
