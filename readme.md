![Chapterify](assets/banner.png)

A little TypeScript script that merges any audio files into a chapterised audiobook, 
ready for most modern audiobook readers.

### Getting started
- Make sure you've got `ffmpeg` installed
- `pnpm install`
- `ts-node --esm src/chapterize_cli.ts --help`

### Usage
#### Standard merge and chapterize
`ts-node --esm src/chapterize_cli.ts aesops-fables.m4b /downloads/fables/*.mp3`

This will take all mp3 files in the given directory, and merge them into a single .m4b file.  
There will be one chapter per input mp3 file, all labeled sequentially as `Chapter 1` through `Chapter N`.  
Audio will be re-encoded using the standard `aac` encoder in `ffmpeg`.

### Thanks
Inspired by [this repo](https://github.com/Geremia/chapterize). Thanks!