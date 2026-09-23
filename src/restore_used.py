# -*- coding: utf-8 -*-
"""Rebuild the Wikimedia video inputs for the editable v4 project.

Only assets used in v4 are downloaded, sequentially, with an honest source list
in vsel.json. Do not run this module in parallel against Wikimedia Commons.
Install imageio-ffmpeg and FFmpeg first (see README_v4.md).
"""
import json, os, subprocess, time
import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()
stock = list(json.load(open('vsel.json', encoding='utf-8')).values())
# name: (source index in vsel.json, source in-point, source length, timeline length)
USED = {
    'kostivere': (1, 2, 6, 5.6),
    'halong': (11, 0, 6, 4.6),
    'halong_boat': (13, 1, 6, 5.6),
    'janicja_a': (3, 62, 4, 4.1),
    'planina': (29, 18, 4, 4.1),
    'coral': (6, 2, 7.6, 7.6),
    'redsea': (8, 3, 6.6, 6.6),
    'clouds': (27, 2, 6.5, 6.4),
    'rain': (23, 3, 6.6, 6.6),
    'monsoon': (28, 3, 6.6, 6.6),
    'seep': (22, 1, 5.4, 5.4),
    'rak': (30, 10, 6.6, 6.6),
    'drip': (5, 5, 5.6, 5.6),
    'forest': (9, 0, 4, 5.1),
}


def fetch(name, i, start):
    v = stock[i]
    source = v['url'].split('?')[0].split('/commons/')[1]
    filename = source.split('/')[-1]
    out = f'vraw/{i:02d}.webm'
    if os.path.isfile(out) and os.path.getsize(out) > 500_000:
        return out
    urls = [f'https://upload.wikimedia.org/wikipedia/commons/transcoded/{source}/{filename}.{q}'
            for q in ('1080p.vp9.webm', '720p.vp9.webm', '720p.webm')]
    os.makedirs('vraw', exist_ok=True)
    for u in urls:
        print('Download', name, u.split('/')[-1][-65:], flush=True)
        r = subprocess.run(['curl', '--fail', '--location', '--silent', '--show-error',
                            '--retry', '3', '--retry-delay', '5', '--max-time', '400',
                            '--user-agent', 'KarstFieldNotes/3.0 (educational Wikimedia credit)',
                            '--range', '0-65000000', '-o', out, u])
        if r.returncode or not os.path.isfile(out) or os.path.getsize(out) < 500_000:
            time.sleep(4)
            continue
        # Commons returns an error page for some parallel downloads; verify
        # FFmpeg can read a frame at the precise edit decision point.
        check = subprocess.run([FF, '-v', 'error', '-ss', str(start), '-i', out,
                                '-frames:v', '1', '-f', 'null', '-'], capture_output=True)
        if check.returncode == 0 and b'Invalid data' not in check.stderr:
            print('  received', round(os.path.getsize(out) / 1024 / 1024, 1), 'MiB', flush=True)
            return out
        time.sleep(5)
    raise RuntimeError(f'Could not recover footage {name} ({v["title"]})')


def make_clip(name, i, start, source_len, length):
    if os.path.isfile(f'clips/{name}.mp4') and os.path.getsize(f'clips/{name}.mp4') > 500_000:
        return
    raw = fetch(name, i, start)
    os.makedirs('clips', exist_ok=True)
    speed = length / source_len
    base = ('setpts={:.5f}*(PTS-STARTPTS),'.format(speed)
            + 'scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,')
    if name == 'drip':
        # Terra X / ZDF source has a logo in the lower-left corner. A genuine
        # crop/reframe removes that pixel area; no pixel-painting or false credit.
        base += 'crop=iw/1.35:ih/1.35:(iw-iw/1.35)*0.55:(ih-ih/1.35)*0.10,'
        base += 'scale=1920:1080,'
    base += 'fps=24,eq=saturation=1.05'
    dest = f'clips/{name}.mp4'
    subprocess.run([FF, '-y', '-loglevel', 'error', '-ss', str(start),
                    '-t', str(source_len), '-i', raw, '-an', '-vf', base,
                    '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '16',
                    '-x264-params', 'threads=1:rc-lookahead=8',
                    '-pix_fmt', 'yuv420p', dest], check=True)
    print('Built', dest, flush=True)


if __name__ == '__main__':
    for n, args in USED.items():
        make_clip(n, *args)
        time.sleep(3)
