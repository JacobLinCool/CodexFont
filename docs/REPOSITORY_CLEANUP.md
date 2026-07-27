# Repository 清理

Repository 只保留能製作、審查與發布目前字體的檔案。

保留：

- 無法重建的原創 raster；
- 凍結字集、review、approval 與雜湊；
- 製作程式、測試、skill 與文件；
- 正式字體和最後一組審查 proof。

不保留：

- 外部參考字體；
- 可重建的逐字 PNG、SVG、中間字體與 build cache；
- 已被取代的實驗；
- 與目前版本無關的歷史紀錄。

Clear Hand TC 的舊批次核准仍直接固定一部分 proof。這些 proof 是目前版本的
審查依據，不是無關歷史；等核准鏈改版後才能移除。

Git LFS 只存原創 raster。其他大型檔案若能重建，就不進 Git。

清理檢查：

```sh
uv run python -m scripts.repository_hygiene
```
