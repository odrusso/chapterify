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
There will be on chapter per input mp3 file, all labeled sequentially as `Chapter 1` through `Chapter N`.
Audio will be re-encoded using the standard `aac` encoder in `ffmpeg`.

#### Verbose merge
`python chapterize.py aesops-fables.m4b /downloads/fables/*.mp3 --interactive`

#### Advanced usage
`python chapterize.py aesops-fables.m4b /downloads/fables/*.mp3 --encoder aac_at --author Aesop --title "Aesops Fables" --keep_chapter_names`
