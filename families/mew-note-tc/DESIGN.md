# Mew Note TC／喵筆記體

Mew Note TC 是一套溫暖、好玩的臺灣繁體手寫體，適合標題、卡片、短文與趣味介面。
它用圓潤筆畫和貓尾收筆形成個性，但字形身分永遠優先。

貓尾每字最多一處，只能延伸既有終筆。浮在字上方的貓帽、游離裝飾和隨機尖刺一律
不合格。可讀文字中的貓尾要有節制，其餘字使用 `soft-terminal`；數學符號、組合
附加符號等容易被裝飾改變意思的字，使用 `neutral-safety`。

0.1 Preview 原定 9,120 個 encoded code points。兩個漢字批次因凍結字帖缺少精確
字形而暫不發布，所以本版實收 9,088 個：6,028 個漢字與 3,060 個非漢字，另有
93 個直排替代字。教育部 4,808 個常用字仍完整。平假名 93 字與片假名 96 字，
共 189 字，也完整收錄。
這個只適用於 0.1 Preview 的差異，記錄在
[`0.1-preview-9088.release-deviation.json`](release-deviations/0.1-preview-9088.release-deviation.json)。
每個正式字形都要重新製作 Mew Note 原稿；Clear Hand TC 只可提供字元身分與規格，
不可提供 raster、outline 或核准紀錄。

產品狀態是 0.1 Preview；字型內部 OpenType version 依首版規則使用 1.000。
目前使用漢字 v2 與 non-Han 兩個 active pilot；32 格都已通過獨立審查。漢字 v1
仍保留為 rejected history。所有 pilot 都只固定設計方向，不計入正式 coverage，
也不是 release approval。
