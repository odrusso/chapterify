![Chapterify](assets/banner.png)

A little Python app that merges any audio files into a chapterised audiobook, 
ready for most modern audiobook readers.

### Getting started
- Grab `chapterize.py`
- Make sure you've got `ffmpeg` and `python 3.2+` installed
- Run `python chapterize.py -h`, which shows simple usage

### Usage
#### Standard merge and chapterize
`python chapterize.py aesops-fables.m4b /downloads/fables/*.mp3`

This will take all mp3 files in the given directory, and merge them into a single .m4b file.  
There will be one chapter per input mp3 file, all labeled sequentially as `Chapter 1` through `Chapter N`.  
Audio will be re-encoded using the standard `aac` encoder in `ffmpeg`.

#### Verbose merge
`python chapterize.py aesops-fables.m4b /downloads/fables/*.mp3 --interactive`

As above, but will give you more opportunity to see what's happening, and stop the process if something doesn't work.

#### Advanced usage
- `--encoder [ffmpeg-encoder]` lets you specify an ffmpeg encoder other than `aac`, for example `aac-at` maybe work best on macOS systems.
- `--title [title]` overrides the automatically used title metadata, which is pulled from the first audio file
- `--author [author]` overrides the automatically used author metadata, which is pulled from the first audio file
- `--keep-chapter-names` will stop the default behaviour of using squential chapter numbering, and instead use the title metadata from each audio file

### Thanks
Inspired by [this repo](https://github.com/Geremia/chapterize). Thanks!