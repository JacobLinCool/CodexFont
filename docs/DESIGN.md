# Clear Hand TC 細筆手寫設計系統

## 設計目標

Clear Hand TC 呈現原子筆或削尖鉛筆仔細寫下的自然手寫感：筆跡纖細、端點柔和、
粗細近似一致，字面清楚並保有些微的人手節奏。它不模仿毛筆墨塊、頓筆或強烈粗細
對比，也不以不規則尖刺製造「手寫」效果。

code point 身分、筆畫拓撲與小尺寸辨識永遠優先於裝飾性的個人筆勢。風格不能讓
標點方向、數學符號拓撲、附加符號位置或漢字部件變得含糊。

## Imagegen-first 原稿

Version 0.1 Preview 的 6,060 個漢字、3,043 個可見非漢字與 93 個直排替代 glyph 都以
圖片生成工具建立新的白底黑字 raster 原稿。原稿要像同一支細筆、同一位書寫者在
穩定節奏下完成，但不把每字機械地套用同一組部件。

其他字形只能作為視覺字帖，用來核對 Unicode 身分與大致結構。正式輪廓不讀取、
變形或拼接其他字型的 outline。

## 筆畫與轉折

- 主要筆畫保持細而清楚，避免為縮圖可見度任意加粗；
- 起筆與收筆可以略帶速度差，但不能形成游離碎墨或針狀突出；
- 橫、豎與斜線保留自然角度差，不追求僵硬的幾何一致；
- 折畫轉向要圓順且明確，內角保留 counter，外角不得產生尖刺；
- 點、鉤、箭頭、根號與積分符號必須保住各自身分；
- 圈字、負圈字、雙圈字、實心幾何圖形與區塊元素不能混用填色拓撲；
- 複雜漢字優先保住部件分區、內白與視覺層級。

## 字面與 metrics

字型使用 1,024 units per em。漢字、全形字元、CJK 標點、幾何／方框／區塊等依
凍結 profile 使用全形 metrics；ASCII、Latin、Greek、IPA 與一般符號使用各字
來源比例或明確固定寬度。ASCII 數字共用 620-unit tabular advance。

112 個可見 nonspacing mark 的水平與垂直 advance 均為 0，並保存 canonical
combining class 與 mark placement。17 個語意空白 glyph 沒有輪廓，但保留精確
spacing metrics。兩個直排假名反覆記號使用 2,048-unit vertical advance；其餘
正常直排 advance 依凍結 profile 為 1,024 或 0。

93 個 `.vert` glyph 不編碼。正式字型只繼承對應 base glyph 的水平與垂直
advance；bearing 保存已核准 preview 的 authored placement。建字器以 HarfBuzz
逐字確認正式 `vert`／`vrt2` placed bounds 與 preview 完全一致。

## 向量品質

Raster 分格後以受控 Potrace 與 quadratic conversion 建立 closed simple
contours。方框繪製與區塊元素採兩階段處理：圖片生成原稿決定原創的連通拓撲、
單／雙線、粗細、填色 pattern 與相對分數；向量階段再依凍結的 Unicode identity
把既有輪廓做標準 font-metric normalization，將必要端點與 1/8、1/4、1/2 等
邊界精確對齊 1,024-unit em。這一步不合成筆畫、不替換輪廓，也不讀取其他字型。
`source_ink_bbox_normalized` 只記錄分格後的原稿位置，不是 Unicode identity 或
release metric；尤其 U+2574–U+257B 的對稱單臂線，不會只因原稿 ink bbox 跨過
cell 中線而被拒絕。其精確 named half-em 與 em-boundary contact 由 Unicode 名稱
經 `_edge_target_bounds` 決定。
逐字報告中的 `edge_contacts` 是 Unicode identity 所要求的邊界，
`edge_contact_pixels` 保存原始 raster 的實測接觸像素數，
`vector_edge_contacts` 則保存正規化後的實際 outline 結果，三者可分開稽核。

每批都要檢查：

- glyph 與 code point 身分正確；
- 沒有缺筆、多筆、錯誤連橋、錯誤填色或格線污染；
- 沒有孤立微粒、退化輪廓、異常小邊或不必要的邊界接觸；
- `micro_edge_count = 0`；
- `acute_micro_turn_count = 0`；
- 非漢字與直排候選的 `micro_thorn_points_removed = 0`；早期漢字批曾對 14 字執行
  受控清理，但只有清理後輪廓重新量測為零 micro-edge／acute-turn 才能進入成品；
- 方框／區塊的 required semantic edge contact 與最終 vector bounds 完全相符；
- 12、16、20、32、56 px 黑字白底與白字黑底均清楚可辨。

人工 review 同時核對原稿身分、向量結果與 lossless 小尺寸 proof。任何錯誤都必須
重新產生原稿、重新向量化與重新核准；不能直接編修 approval 或放寬門檻。

## OpenType 行為

正式字型包含：

- `kern`：常用拉丁 kerning class 與標點 pair；
- `mark`／`mkmk`：組合附加符號定位；
- `vert`／`vrt2`：93 個直排替代關係。

發行 proof 另以正式字型的最終 metrics 與 HarfBuzz `ttb` shaping 渲染全部 93
個直排替代字，提供黑白雙極性樣張。

TTF、OTF、WOFF、WOFF2 使用同一套 quadratic `glyf`、glyph order、metrics 與
OpenType feature。正式 CSS 的 family name 為 `Clear Hand TC`。

## 版本界線

Version 0.1 Preview 完成 9,120 個編碼 code points，並完整涵蓋教育部
4,808 個常用字；精確範圍見
[`COVERAGE.md`](COVERAGE.md)。這仍不是 `PROMPT.md` 的 18,071-codepoint
最終全量。未來擴充必須延續同一套 imagegen 原稿、逐字向量檢查與雜湊核准流程。
