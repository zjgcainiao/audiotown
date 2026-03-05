
**AudioTown** is a lightweight audio file oriented package that intends to do two things
- Explain this media folder to me. 
- It converts the lossless files (`.flac`) in your collection to more apple friendly format, `.m4a`. Supports both  high-quality _ALAC (Lossless)_ and _AAC (Lossy)_  as [codec](https://ffmpeg.org/ffmpeg-codecs.html). When it converts, it tries preserving metadata, including album artwork from source files.

# What to expect
1. `audiotown` contains three commands: `check`, `stats` and `convert`. This package requires `ffmepg` installed in the system. 
   1. To run them, type `auditown check` or `audio stats` or `audio convert`.
   2. Type `audiotown check` to run `check`. 
   3. The command checks if `ffmpeg` is installed.
2. `stats` acts as an executive assisant for audio media management. Personal media library are often messy. This command starts by searching the `folder` recursively and laser focus ONLY on audio files (filtered by suffix). It then prints out to the terminal a summary report about how it finds: 
   1. numbers of songs by formats, by encoding types,
   2. storage usage details, 
   3. what top artists, genre, album are to me ,
   4. are they lossless or lossy, and 
   5. detect potential unreadable or corrupt files. 
3. `stats` can export scanned records into a JSON file via `--report-path` flag.
4. `convert`. It converts all `.flac` files in a folder into lossless (`alac`) or lossy (`aac`) versions. a apple lossless encoded `.m4a` file can be recognized in Apple eco system but not usually for `.flac` files. 
   1. `--report-path` is available in `convert` too. To run it `audiocheck convert /path/to/flacs --encoder=alac --report-path=.`. The converted will be exported to a new folder `audiotown_export` in the same folder `path/to/flacs`. 
   2. `convert` also support `--dry-run` as a tool to preview changes made in a conversion.
   3. `convert` search files recursively so I can specify a high-level `folder` like `Media` or `myMediaHub`. Try with one ablum folder first.
   4. `converts` support `--bitrate` when the `--encoder=aac` is specified. the default bitrate kbps is `256k`. `128k` and `320k` are the other valid inputs.
   5. `convert` has a babit that searchs `cover.jpg` or `library.jpg` in the existing folder strucutre. if the source file does not contain an artwork, the command attempts to find such file and add it into output files whenever possible.


## Installation
1. Ensure I have [FFmpeg](https://ffmpeg.org/download.html) installed on the system. It is the powerhouse that does the conversion and other heavy work like probing `ffprobe`. I will need it installed and working. Mac users can installed it via [homebrew](https://formulae.brew.sh/formula/ffmpeg):`brew install ffmpeg`.
2. Python >3.10+. 
3. Requires `click` and `wcwidth` libaries.

```zsh
# [optional but recommended] set up a virutal env named `my_env`.
python3 -m venv my_env
source my_env/bin/activate
# check python version 3.10+
python --version 

# udpate pip
pip install --upgrade pip

pip install audiotown

# help
audiotown
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

# 2. check ffmpeg installation
audiotown check

# 3. show stats of a media folder 
cd /path/to/media/folder
audiotown stats . 
# alternatively 
audiotown stats  /path/to/media/folder
audiotown stats  /path/to/media/folder --report-path=.

# 4. convert all flac files  to alac (default) or aac based formats. logging is controlled by `--report-path`
# . means current directory
audiotown convert . --report-path=.
audiotown convert . --codec=alac --report-path=. --dry-run
audiotown convert . --codec=aac --bitrate=256k --report-path=. --dry-run

```

## Advanced Options
1. overview

  |Option|	Description|	Default|
  |:---|:---|---:|
  |--codec|	alac or aac. used with `convert`. |alac|
  |--bitrate|	Bitrate for AAC (128k, 256k, 320k). only useful when `--codec=aac`|	256k|
  |--dry-run|	Preview conversion without writing files	|False|
  |--report-path|	generates a full log, including report.json	|disabled|

2. Examples

   1. Run a preview to see what would be converted:

    ```zsh
    audiotown convert ./AlbumFolder --dry-run
    ```

   2. use `codec` and `--bitrate`. It means the desired codec used for the output. 
  
    ```zsh
    audiotown convert . --codec=alac 
    audiotown convert . --codec=aac --bitrate=256k 
    audiotown convert . --codec=aac --bitrate=128k 

    ```

   3. It does not make sense to specify `bitrate` for lossless `alac` so `bitrate` will be ignored.

    ```zsh
    cd /my/media/folder
    audiotown convert . --codec=alac --bitrate=128k 
    ```

# LICENSE
Licensed under the [MIT License]((https://github.com/zjgcainiao/audiotown/blob/main/LICENSE)).
