#!/usr/bin/python3
# Concatenate audio files in m4b files and add chapter markers, if available.
import argparse
import glob
import os
from typing import NamedTuple

NANOSECONDS_IN_ONE_SECOND = 1e9
BYTES_IN_ONE_MEGABYTE = 1e6


class FileMetadata(NamedTuple):
    filename: str
    chapter_start_time_ns: int
    chapter_end_time_ns: int


def get_nanoseconds_for_file(file_name):
    command = f"ffprobe -i '{file_name}' -show_entries format=duration"
    raw_ffprobe_output = os.popen(command).readlines()
    time_seconds = float(raw_ffprobe_output[1].rstrip().split("=")[1])
    return int(time_seconds * NANOSECONDS_IN_ONE_SECOND)


def concat_using_ffmpeg_filters(input_audio_files, output_filename, temp_metadata, audio_encoder="aac"):
    # We want -i file1.mp3 -i file2.mp3 -i file3.mp3 ... -i fileN.mp3
    ffmpeg_input_audio_files = " -i '" + ("' -i '".join(input_audio_files)) + "'"

    # We want [0:0][1:0][2:0][3:0]... for each input file
    # For [x:y], x is the index of the input, and y is the number of video channels we want to encode.
    ffmpeg_filter_audio_channels = ''.join([f"[{_}:0]" for _ in range(len(input_audio_files))])

    return 'ffmpeg' + \
           ffmpeg_input_audio_files + \
           ' -i ' + temp_metadata + \
           f' -filter_complex \'{ffmpeg_filter_audio_channels}concat=n={len(input_audio_files)}:v=0:a=1[out]\'' + \
           " -map '[out]'" + \
           f' -map_metadata {len(input_audio_files)}' + \
           f' -c:a {audio_encoder} -vn' + \
           ' -aac_coder fast ' + \
           output_filename


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(description="Turn a set of audio files into a .m4b audiobook file")
    arg_parser.add_argument("output_filename", help="filename of the final m4b file, extension included")
    arg_parser.add_argument("input_files", help="glob for the input audio files, i.e. './test/*.mp3'")
    arg_parser.add_argument("--encoder", help="override default (aac) encoder")
    # arg_parser.add_argument("--interactive", help="more verbosity and requires user intervention")
    # arg_parser.add_argument("--author", help="override the author metadata")
    # arg_parser.add_argument("--title", help="override the title metadata")
    # arg_parser.add_argument("--keep_chapter_names", action="store_true", help="use title metadata from each file for chapter names")
    args = arg_parser.parse_args()

    input_audio_glob = args.input_files
    output_filename = args.output_filename
    encoder = args.encoder if args.encoder is not None else "aac"

    input_audio_filenames = glob.glob(input_audio_glob)
    input_audio_filenames.sort()

    if len(input_audio_filenames) == 0:
        print(f"No matching audio files were found")
        quit(1)

    files_metadata = []
    cumulative_time = 0  # In nanoseconds
    for filename in input_audio_filenames:
        chapter_end_time = cumulative_time + get_nanoseconds_for_file(filename)
        files_metadata.append(FileMetadata(filename, cumulative_time, chapter_end_time))
        cumulative_time = chapter_end_time

    metadata_command = f'ffmpeg -i "{input_audio_filenames[0]}" -f ffmetadata -v quiet -'
    metadata = os.popen(metadata_command).read()

    # Timebase isn't set, so is defaulted to nanoseconds
    for i, file_metadata in enumerate(files_metadata):
        metadata += f'[CHAPTER]\nSTART={file_metadata.chapter_start_time_ns}\nEND={file_metadata.chapter_end_time_ns}\ntitle=Chapter {i + 1}\n'

    temp_metadata = os.popen('mktemp').read().strip()
    metafile = open(temp_metadata, 'w')
    metafile.write(metadata)
    metafile.close()

    command = concat_using_ffmpeg_filters(input_audio_filenames, output_filename, temp_metadata, encoder)

    os.system(command)
    os.system('rm -fr ' + temp_metadata)

    output_file_size_megabytes = os.path.getsize(output_filename) / BYTES_IN_ONE_MEGABYTE

    print(
        f"Audiobook file successfully created at {output_filename}, " +
        f"with {len(input_audio_filenames)} chapters, " +
        f"with a size of {output_file_size_megabytes:.2f}MB"
    )
