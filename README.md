Professional FLAC to Apple-friendly audio converter.

**AudioTown** is a lightweight CLI utility designed to bridge the gap between high-fidelity FLAC collections and the Apple ecosystem. It converts your library into high-quality _ALAC (Lossless)_ or _AAC (Lossy)_ while preserving metadata, including album artwork.

# Features

1. Lossless or Lossy: Choose between ALAC for bit-perfect archives or AAC for mobile storage.
2. Smart Artwork: * Preserves existing embedded covers.
3. When enabled, it automatically finds and embeds external cover.jpg or folder.png.
4. Converts PNG covers to MJPEG for maximum Apple compatibility.
5. Metadata Integrity: Transfers all tags (Artist, Album, Date, Genre) from source to destination.
6. Dry Run Mode: Preview your changes before touching a single file.
7. Informed stats for any selected media folder (audio only). Run `audiotown stats .`.

# Installation
1. Ensure you have FFmpeg installed on your system.
2. requires `click` and `wcwidth` libaries. Python >3.10+.

```zsh
# Clone the repo
git clone https://github.com/your-username/audiotown.git
cd audiotown
```
```zsh
# [optional but recommended] set up a virutal env named `my_env`.
python3 -m venv my_env
source my_env/bin/activate

# install dependencies 
pip install .
```
# 🛠 Usage

```txt
audiotown [OPTIONS] COMMAND [ARGS]...
Options:
  -h, --help  Show this message and exit.
Commands:
  check    Verify that FFmpeg and dependencies are correctly installed.
  convert  Convert FLACs in FOLDER to Apple-friendly formats.
  stats    Stats Dashboard & Optimization tool.
```

## Examples
1. The simplest way to use `AudioTown` is to run it in a folder containing FLAC files: `audiotown convert /path/to/album/folder --codec=alac --report-path=/path/to/report/folder --dry-run`. The file search is resursive.
2. the output files from `audio convert` are under the subfolder `audiotown_converted/` within `/path/to/album/folder`.
3. The `/path/to/report/folder` can be `.` or any specified directories.
4. use `--dry-run` to preview any perceived changes.
5. The conversion supports: `flac --> alac` or `flac --> aac`

```zsh
# 1. show additional help 
audiotown
audiotown -h
audiotown --help

# 2. convert all flac files  to alac (default) or aac based formats. logging is controlled by `--report-path`
# . means current directory
audiotown convert . --report-path=.
audiotown convert . --codec=alac --report-path=. --dry-run
audiotown convert . --codec=aac --report-path=. --dry-run

# 3. show stats of a media folder 
audiotown stats . 
audiotown stats  /path/to/media/folder

# 4. check ffmpeg installation
audiotown check

```

## Advanced Options
    |Option|	Description|	Default|
    |:---|:---|:---:|
    |--codec|	alac or aac	|alac|
    |--bitrate|	Bitrate for AAC (128k, 256k, 320k)|	256k|
    |--embedded-art|	Skip artwork embedding	|False|
    |--dry-run|	Preview conversion without writing files	|False|

1. Examples
 ```zsh
 audiotown convert ./AlbumFolder --codec aac --bitrate 320k
 ```
1. Run a preview to see what would be converted:

 ```zsh
 audiotown convert . --dry-run
 ```
# LICENSE
Licensed under the [MIT License](./LICENSE).

Version: 1.0