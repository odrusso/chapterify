// import {program} from "commander";
// import {merge} from "./helpers.ts";
//
// program
//     .name("Chapterify")
//     .description("Turn a set of audio files into a .m4b audiobook file")
//     .argument("output_filename", "filename of the final m4b file, extension included")
//     .argument("input_files", "glob for the input audio files, i.e. './test/*.mp3'")
//     .option("-c, --cover-image <value>", "path to a jpg/png to embed as cover art")
//
// program.parse()
//
// const outputFileName = program.args[0]
// const inputGlob = program.args[1]
// const coverImage = program.opts().coverImage
//
// await merge(inputGlob, outputFileName, coverImage)
