#!/usr/bin/python3
import argparse
import glob
import os
import uuid
from typing import NamedTuple

NANOSECONDS_IN_ONE_SECOND = 1e9
BYTES_IN_ONE_MEGABYTE = 1e6


class FileMetadata(NamedTuple):
    filename: str
    chapter_start_time_ns: int
    chapter_end_time_ns: int


def get_nanoseconds_for_file(file_name):
    if args.interactive:
        print(f"Getting nanoseconds for {file_name}")
        # input("Press any key to continue...")

    command = f"ffprobe -i \"{file_name}\" -show_entries format=duration"
    raw_ffprobe_output = os.popen(command).readlines()

    if args.interactive:
        print(f"Nanosecond output for {file_name}")
        print(raw_ffprobe_output)
        # input("Press any key to continue...")

    time_seconds = float(raw_ffprobe_output[1].rstrip().split("=")[1])
    return int(time_seconds * NANOSECONDS_IN_ONE_SECOND)


def concat_using_ffmpeg_filters(input_audio_files, output_filename, temp_metadata, audio_encoder="aac"):
    # We want -i file1.mp3 -i file2.mp3 -i file3.mp3 ... -i fileN.mp3
    ffmpeg_input_audio_files = ' -i \"' + ('\" -i \"'.join(input_audio_files)) + '\"'

    # We want [0:0][1:0][2:0][3:0]... for each input file
    # For [x:y], x is the index of the input, and y is the number of video channels we want to encode.
    ffmpeg_filter_audio_channels = ''.join([f"[{_}:0]" for _ in range(len(input_audio_files))])

    return 'ffmpeg' + \
           ffmpeg_input_audio_files + \
           ' -i ' + temp_metadata + \
           f' -filter_complex \'{ffmpeg_filter_audio_channels}concat=n={len(input_audio_files)}:v=0:a=1[out]\'' + \
           ' -map \"[out]\"' + \
           f' -map_metadata {len(input_audio_files)}' + \
           f' -c:a {audio_encoder} -vn' + \
           ' -aac_coder fast ' + \
           output_filename


def get_element_from_metadata(element_name, metadata_lines, override=None):
    if override is not None:
        return override
    derived_line = list(filter(lambda x: x.startswith(element_name), metadata_lines))
    if len(derived_line) != 1:
        print(f"Cannot find element {element_name} in metadata, reading 'unknown' instead")
        return "unknown"
    else:
        return derived_line[0].split("=")[1].rstrip()


def get_metadata_lines_from_file(filename):
    get_metadata_command = f'ffmpeg -i "{filename}" -f ffmetadata -v quiet -'
    return os.popen(get_metadata_command).readlines()


def get_chapter_name(metadata: FileMetadata, i: int, keep_chapter_names: bool):
    if keep_chapter_names:
        lines = get_metadata_lines_from_file(metadata.filename)
        expected_title = get_element_from_metadata("title", lines)
        if expected_title == "unknown":
            return f"Chapter {i + 1}"
        else:
            return expected_title
    else:
        return f"Chapter {i + 1}"


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(description="Turn a set of audio files into a .m4b audiobook file")
    arg_parser.add_argument("output_filename", help="filename of the final m4b file, extension included")
    arg_parser.add_argument("input_files", help="glob for the input audio files, i.e. './test/*.mp3'")
    arg_parser.add_argument("--encoder", help="override default (aac) encoder")
    arg_parser.add_argument("--author", help="override the author metadata")
    arg_parser.add_argument("--title", help="override the title metadata")
    arg_parser.add_argument("--cover_image", help="path to a jpg/png to embed as cover art")
    arg_parser.add_argument("--interactive", action="store_true",
                            help="more verbosity and requires user intervention")  # TODO: Implement, more.
    arg_parser.add_argument("--keep_chapter_names", action="store_true",
                            help="use title metadata from each file for chapter names")
    args = arg_parser.parse_args()

    input_audio_glob = args.input_files

    if args.cover_image:
        output_filename = "temp-merged.m4b"
    else:
        output_filename = args.output_filename

    encoder = args.encoder if args.encoder is not None else "aac"

    input_audio_filenames = glob.glob(input_audio_glob)
    input_audio_filenames.sort()

    if args.interactive:
        print("Files to be merged:")
        [print(_) for _ in input_audio_filenames]
        input("Press any key to continue...")

    if len(input_audio_filenames) == 0:
        print(f"No matching audio files were found")
        quit(1)

    files_metadata = []
    cumulative_time = 0  # In nanoseconds
    for filename in input_audio_filenames:
        chapter_end_time = cumulative_time + get_nanoseconds_for_file(filename)
        files_metadata.append(FileMetadata(filename, cumulative_time, chapter_end_time))
        cumulative_time = chapter_end_time

    initial_metadata = get_metadata_lines_from_file(input_audio_filenames[0])

    # Setup global metadata
    metadata = ";FFMETADATA1\n"
    metadata += f"title={get_element_from_metadata('title', initial_metadata, args.title)}\n"
    metadata += f"album={get_element_from_metadata('album', initial_metadata, args.title)}\n"
    metadata += f"artist={get_element_from_metadata('artist', initial_metadata, args.author)}\n"

    # Add all chapter markers to metadata
    # Timebase isn't set, so is defaulted to nanoseconds
    for i, file_metadata in enumerate(files_metadata):
        metadata += f'[CHAPTER]\nSTART={file_metadata.chapter_start_time_ns}\nEND={file_metadata.chapter_end_time_ns}\ntitle={get_chapter_name(file_metadata, i, args.keep_chapter_names)}\n'

    if args.interactive:
        print("=" * 10 + "METADATA" + "=" * 10)
        print(metadata)
        print("=" * 10 + "END METADATA" + "=" * 10)
        input("Press any key to continue...")

    # Create a temp file to store new metadata
    new_metadata_file_location = "metadata-" + str(uuid.uuid4()) + ".txt"

    # Write all the custom metadata to the new metadata file
    new_metadata_file = open(new_metadata_file_location, 'w+')
    new_metadata_file.write(metadata)
    new_metadata_file.close()

    command = concat_using_ffmpeg_filters(input_audio_filenames, output_filename, new_metadata_file_location, encoder)

    if args.interactive:
        print("Command to be run:")
        print(command)
        input("Press any key to continue...")

    os.system(command)
    os.system('rm -fr ' + new_metadata_file_location)

    if args.cover_image:
        # Rerender the file with cover art
        print("todo")
        cover_command = f"ffmpeg -i \"{output_filename}\" -i \"{args.cover_image}\" -map 0 -map 1 -c copy -dn -disposition:v:0 attached_pic \"cover-{output_filename}\""

        if args.interactive:
            print("Will attempt cover: " + args.cover_image)
            print("With command " + cover_command)
            print(cover_command)
            input("Press any key to continue...")

        os.system(cover_command)
        os.system(f"rm -f \"{output_filename}\"")
        os.system(f"mv \"cover-{output_filename}\" \"{args.output_filename}\"")
        output_filename = args.output_filename

    output_file_size_megabytes = os.path.getsize(output_filename) / BYTES_IN_ONE_MEGABYTE

    print(
        f"Audiobook file successfully created at {output_filename}, " +
        f"with {len(input_audio_filenames)} chapters, " +
        f"with a size of {output_file_size_megabytes:.2f}MB"
    )
