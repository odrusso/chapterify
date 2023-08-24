import {glob} from "glob";
import {orderBy} from "natural-orderby";
import {randomUUID} from "crypto";
import {promises as fs} from "fs";
import {execute, executeResult} from "./os";

const NANOSECONDS_IN_ONE_SECOND: number = 1e9
const NANOS_IN_ONE_MINUTE: number = 60 * NANOSECONDS_IN_ONE_SECOND
const NANOS_IN_ONE_HOUR: number = 60 * NANOS_IN_ONE_MINUTE


type FileMetadata = {
    filename: string,
    chapterStartTimeNs: number,
    chapterEndTimeNs: number,
    rawMetadata: string[],
}

const getNanosecondsForFile = async (filename: string): Promise<number> => {
    const command = `ffprobe -i "${filename}" -show_entries format=duration`
    const {stdout: ffprobeOutput} = await executeResult(command)
    const fileLengthSeconds: string = ffprobeOutput.split("\n")[1].split("=")[1]
    const fileLengthSecondsInteger: number = Math.round(+fileLengthSeconds)
    return fileLengthSecondsInteger * NANOSECONDS_IN_ONE_SECOND
}

const getMetadataLinesFromFile = async (filename: string): Promise<string[]> => {
    const command = `ffmpeg -i "${filename}" -f ffmetadata -v quiet -`
    const {stdout} = await executeResult(command)
    return stdout.split("\n")
}

const getMetadataElement = (element: string, metadata: string[]): string | undefined =>
    metadata
        .find(metadataLine => metadataLine.startsWith(element))
        ?.split("=")[1]
        ?.replace("\n", "")

const getChapterName = (fileMetadata: FileMetadata, index: number): string =>
    getMetadataElement('title', fileMetadata.rawMetadata) ?? `Chapter ${index + 1}`

const buildFfmpegCommand = (sortedInputAudioFilenames: string[], outputFileName: string, metadataFileName: string): string => {
    // We want -i file1.mp3 -i file2.mp3 -i file3.mp3 ... -i fileN.mp3 (with trailing space)
    const inputFileComponent = sortedInputAudioFilenames.reduce((current, filename) => current + `-i "${filename}" `, "")

    // We want [0:0][1:0][2:0][3:0]... for each input file (without trailing space)
    const filterChannelComponent = sortedInputAudioFilenames.reduce((current, _, index) => current + `[${index}:0]`, "")

    let command = "ffmpeg "
    command += inputFileComponent
    command += ` -i "${metadataFileName}" `
    command += ` -filter_complex '${filterChannelComponent}concat=n=${sortedInputAudioFilenames.length}:v=0:a=1[out]' `
    command += ` -map "[out]" `
    command += ` -map_metadata ${sortedInputAudioFilenames.length} `
    command += ` -c:a aac -vn -aac_coder fast `
    command += outputFileName

    return command
}

const buildCoverCommand = (coverImage: string, outputFileName: string): string =>
    `ffmpeg -i "${outputFileName}" -i "${coverImage}" -map 0 -map 1 -c copy -dn -disposition:v:0 attached_pic "cover-${outputFileName}"`

const buildMetadata = (fileMetadata: FileMetadata[]): string => {
    let metadata = ";FFMETADATA1\n"
    const initialMetadata = fileMetadata[0].rawMetadata
    metadata += `title=${getMetadataElement('album', initialMetadata) ?? 'unknown'}\n`
    metadata += `album=${getMetadataElement('album', initialMetadata) ?? 'unknown'}\n`
    metadata += `artist=${getMetadataElement('artist', initialMetadata) ?? 'unknown'}\n`

    // Add chapter markers to metadata
    fileMetadata.forEach((file, i) => {
        metadata += `[CHAPTER]\n`
        metadata += `START=${file.chapterStartTimeNs}\n`
        metadata += `END=${file.chapterEndTimeNs}\n`
        metadata += `title=${getChapterName(file, i)}\n`
    })

    return metadata
};

const buildMetadataForFiles = async (filenames: string[]) => {
    const fileMetadata: FileMetadata[] = []
    let cumulativeTime = 0
    for (const filename of filenames) {
        const chapterEndTime = cumulativeTime + await getNanosecondsForFile(filename)
        const rawMetadata = await getMetadataLinesFromFile(filename)
        fileMetadata.push({
            filename,
            chapterStartTimeNs: cumulativeTime,
            chapterEndTimeNs: chapterEndTime,
            rawMetadata: rawMetadata,
        })
        cumulativeTime = chapterEndTime
    }
    return fileMetadata;
};

const printProgress = (log: string, totalNanos: number, startTime: number, printer: Function) => {
    if (!log.startsWith("size=")) return

    const extractedTime: string[] | undefined = getMetadataElement('time', log.split(" "))?.split(":")
    if (!extractedTime) return

    const [hours, minutes, seconds] = extractedTime
    const nanos = (NANOS_IN_ONE_HOUR * +hours) + (NANOS_IN_ONE_MINUTE * +minutes) + (NANOSECONDS_IN_ONE_SECOND * +seconds)
    if (nanos < 0) return

    const currentPercentageCompleteDec = nanos / totalNanos
    const totalOf25 = Math.round(currentPercentageCompleteDec * 25)
    const currentRuntimeSeconds = (Date.now() - startTime) / 1000
    const estTotalTimeSeconds = currentRuntimeSeconds / currentPercentageCompleteDec
    const estRemainingTime = Math.round(estTotalTimeSeconds - currentRuntimeSeconds)

    printer(`Progress: [${'='.repeat(totalOf25)}${' '.repeat(25 - totalOf25)}] (${Math.round(currentPercentageCompleteDec * 100)}%) (${estRemainingTime} est remaining)`)
}

export const merge = async (inputGlob: string, outputFileName: string, coverImage?: string, printCallbackOverride?: Function) => {
    const inputAudioFilenames = await glob(inputGlob)
    const sortedInputAudioFilenames = orderBy(inputAudioFilenames)

    if (sortedInputAudioFilenames.length === 0) throw "No input files found"

    const fileMetadata = await buildMetadataForFiles(sortedInputAudioFilenames);

    // Build metadata from first file
    const metadata = buildMetadata(fileMetadata);

    // Create a temp file to store metadata
    const metadataFileName = `metadata-${randomUUID()}.txt`
    await fs.writeFile(metadataFileName, metadata)

    const command = buildFfmpegCommand(sortedInputAudioFilenames, outputFileName, metadataFileName)

    const printCallback = (stderr: string) => printProgress(stderr, fileMetadata[fileMetadata.length - 1].chapterEndTimeNs, startTime, printCallbackOverride ?? console.log)

    const startTime = Date.now()
    await execute(command, printCallback)

    await fs.unlink(metadataFileName)

    console.log("Done")

    if (!coverImage) return
    const renderWithCoverCommand = buildCoverCommand(coverImage!, outputFileName)
    await execute(renderWithCoverCommand)

    await fs.unlink(outputFileName)
    await fs.rename("cover-" + outputFileName, outputFileName)

    console.log("Done with cover")
}
