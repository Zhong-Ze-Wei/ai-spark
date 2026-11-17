# 观澜 · AI Sparks

**借具体变化，看更大的时代走势。**

[打开观澜首页 →](https://www.zz-home.site/ai-spark/)

以 2026 年 7 月 12 日至 11 月 16 日的社群交流为线索，整理 24 篇思想地图、14 场交锋、28 位群友的原声，以及工具实践和讨论编年。支持全文搜索、收藏、摘录导出与昼夜主题。

首页使用观澜水墨主题海报。布局随手机、平板和宽屏调整；主题图、样式、图标及图表运行库均已嵌入 HTML，下载 `index.html` 即可直接打开。

## 维护首页

```sh
npm ci
npm run build
npm run preview
```

- `src/home.html`：本期内容、交互与页面布局的可编辑源文件。
- `assets/guanlan-theme.png`：观澜水墨主题海报。
- `scripts/build-home.mjs`：编译 Tailwind，嵌入图表、图标和主题海报，生成独立的 `index.html`。
- `package-lock.json`：固定构建依赖的版本。
- `index.html`：网站入口，也是可离线打开的单文件版本。

修改源文件后运行 `npm run build`，将生成的 `index.html` 一并提交。服务器目录为 `/var/www/ai-spark/`；GitHub Pages 继续提供[镜像入口](https://zhong-ze-wei.github.io/ai-spark/)。

## 早期内容

既有独立页面与链接继续保留：

- [早期完整档案](https://www.zz-home.site/ai-spark/archive/)
- [38 个话题](https://www.zz-home.site/ai-spark/topics/)
- [177 段原话](https://www.zz-home.site/ai-spark/sources/)
- [从思考到工具：temper 与 aptum](https://www.zz-home.site/ai-spark/skills/)

`content/` 保存早期资料，`scripts/build.py` 重新生成这些独立页面，并保留本期首页。需要维护早期资料时运行：

```sh
python3 scripts/build.py
python3 scripts/check.py
```

`archive.html` 保留七章长文，`materials/` 保存补充阅读材料，`docs/community.md` 保存群公告。旧的 `#topic/t19`、`#person/p01` 等分享链接仍会转到相应独立页面。
