# 來源與授權

## 正式字形

Clear Hand TC 與 Mew Note TC 的每個可見 glyph 都從專案自己的白底黑字 raster
開始，再經向量化、檢查與核准。

其他字型只用來確認 Unicode 身分與筆畫。正式建置不匯入、描摹、變形或拼接外部
outline，也不把系統 fallback 算成 coverage。

## 保存內容

Repository 保存：

- 凍結的 code point 清單；
- 原創 raster 原稿；
- 圖片生成呼叫與來源雜湊；
- 最終人工 review 與 release approval；
- 正式字體、必要 proof 與 `report.json`。

逐字預覽、SVG、逐字 JSON、中間字體與其他可重建產物不進 Git。Git LFS 只保存
不可重建的原創 raster。

Clear Hand TC 的來源在 `sources/imagegen/`。Mew Note TC 使用獨立的
`families/mew-note-tc/sources/imagegen/`，不重用 Clear Hand 的 raster、outline、
review 或 approval。

## 字集

兩款字體都由以下清單組成：

```text
sources/imagegen/repertoires/common-3000.json
sources/imagegen/repertoires/moe-common-extension-1844.json
sources/imagegen/repertoires/dictionary-salience-extension-1216.json
sources/imagegen/repertoires/nonhan-3060.json
sources/imagegen/repertoires/vertical-93.json
```

Mew Note TC 另保存一份 family-local 投影，字序相同，但來源與核准鏈完全分開。
本次發布暫緩兩個無法由凍結字帖精確核對的漢字批次；原因與 32 個 code points
記在 Mew Note release approval。

17 個 spacing／control code points 依 Unicode 語意保留空輪廓和正確 metrics。
93 個直排替代不進 `cmap`，只由 `vert`／`vrt2` 使用。

## 授權

字型軟體、原創 raster、可修改來源與建置程式依 SIL Open Font License 1.1
發布。OFL 允許使用、研究、修改、嵌入與再散布；完整條款見 [`OFL.txt`](../OFL.txt)。
