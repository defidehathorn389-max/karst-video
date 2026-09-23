# 喀斯特：中国南方的石头森林 — v4

**成片**：[`喀斯特_中国南方的石头森林_v4.mp4`](喀斯特_中国南方的石头森林_v4.mp4)  
1920 × 1080 / 24fps / 7分33秒 / H.264 + AAC，约 98MiB。

v4 继续升级动画，尤其是 **04:15–04:57 的地貌演化** 和 **05:14–05:44 的地下世界**。

- `v4graphics.py` 新增原创程序化立体地形：岩面随坡度受光，地形高度在石林、峰丛、峰林和孤峰四阶段之间连续插值，缓慢推进镜头。
- 洞穴与天坑图解重画为分层岩壁、地下水、矿物沉积与崩塌剖面，保留科普示意属性。
- `premium.py` 中的地图、海底沉积、岩层褶皱、溶蚀化学、时间轴及章节设计沿用上一轮的视觉升级；`render.py` 管理时间线与字幕。
- 与 v3 的四组同帧对照：[`preview/v4/v3_vs_v4.jpg`](preview/v4/v3_vs_v4.jpg)。

旁白、字幕、实拍镜头、时长均未改变。斯洛文尼亚、越南等境外素材有真实地点标注，不冒充中国景点。图解属于**原创科普示意**，不是对某地实景的测绘复原，也没有复制第三方纪录片动画。

## 重新渲染

需要 Python 3.13、`curl`、`pycairo`、`pillow`、`numpy`、`imageio-ffmpeg`。如本工作区的中间视频素材已清理，先通过 Commons 恢复（来源及授权详见 `vsel.json`）：

```bash
python -m pip install pycairo pillow numpy imageio-ffmpeg
python restore_used.py
python render.py info
# 依次渲染，勿并行。约 2GB 内存时后半段应拆为三个短分段。
python render.py render 2 0
python -c "import render; render.render(5441,7400,'parts/p1a.mp4')"
python -c "import render; render.render(7400,9050,'parts/p1b.mp4')"
python -c "import render; render.render(9050,10883,'parts/p1c.mp4')"
cat > parts/list.txt <<'EOF'
file 'p0.mp4'
file 'p1a.mp4'
file 'p1b.mp4'
file 'p1c.mp4'
EOF
FF=$(python -c 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())')
"$FF" -y -f concat -safe 0 -i parts/list.txt -i audio/mix.m4a \
  -map 0:v:0 -map 1:a:0 -c:v copy -c:a copy -movflags +faststart -shortest v4_master.mp4
```

`img/`、`world50.json`、`c.json`、`audio/mix.m4a`、`script/` 与 `credits.tsv` 为项目输入。视频来源、作者、许可证详见 `render.py` 中的 `VCRED`、`vsel.json`；照片见 `credits.tsv`，片内也有署名。部分背景概念画面由 AI 辅助生成；地形、剖面等动画由程序原创绘制。

## GitHub 发布

已发布在 [v4.0 Releases](../../releases/tag/v4.0)；仓库根目录 `karst.mp4` 是 1080p 压缩版，高清母版 [karst_v4_1080p_HQ.mp4](../../releases/download/v4.0/karst_v4_1080p_HQ.mp4) 在发布页。旧版仍留在历史 Release 中供对比。
