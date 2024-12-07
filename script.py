import os
import re
import argparse
import csv
import shutil
import math

def extract_tags_from_content(content):
    # Match tags of form #tag or tag (optional #)
    tag_pattern = re.compile(r'(?:#)?([A-Za-z0-9_\-]+)')
    return set(tag_pattern.findall(content))

def log(level, message, verbose):
    if not verbose:
        return
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'

    level_color = {
        "INFO": GREEN,
        "DEBUG": YELLOW,
        "ERROR": RED
    }

    color = level_color.get(level, RESET)
    print(f"{color}[{level}]     {message}{RESET}")

def safe_read_file(filepath, verbose):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        # Replace unusual line terminators
        content = content.replace('\u2028', '\n').replace('\u2029', '\n')
        return content
    except Exception as e:
        log("ERROR", f"Could not read file {filepath}: {e}", verbose)
        return None

def safe_copy_file(source, dest, verbose):
    try:
        shutil.copyfile(source, dest)
        return True
    except Exception as e:
        log("ERROR", f"Could not copy file {source} to {dest}: {e}", verbose)
        return False

def main():
    parser = argparse.ArgumentParser(description="Analyze links between markdown notes of a second brain")

    parser.add_argument("-i", "--input_dir", required=True, help="Path to the directory containing .md files")
    parser.add_argument("-o", "--output_csv", required=True, help="Path to the output CSV file")

    # Tag filters
    parser.add_argument("--ignore-tags", nargs='*', default=[], help="List of tags to ignore (if a note has any of these, it will be excluded)")
    parser.add_argument("--select-tags", nargs='*', default=[], help="List of tags to select (a note must have all these tags to be included)")

    # Copy constraints
    parser.add_argument("--copy-top", type=int, default=None, help="Copy the top N most linked notes to the destination folder")
    parser.add_argument("--copy-top-percent", type=float, default=None, help="Copy the top P% of the most linked notes to the destination folder")
    parser.add_argument("--copy-until-size", type=float, default=None, help="Copy notes by descending order until reaching X MB total size")
    parser.add_argument("--copy-dest", type=str, default=None, help="Destination folder for copying the notes")

    # Combine all filtered selected notes into one .md file
    parser.add_argument("--combine-md", type=str, default=None, help="Combine all selected notes into one .md file with an empty line between them")

    # Additional options
    parser.add_argument("-v", "--verbose", action="store_true", help="Increase output verbosity")
    parser.add_argument("--no-csv", action="store_true", help="Do not generate CSV output")
    parser.add_argument("--dry-run", action="store_true", help="Perform a trial run with no changes made (no CSV, no copy, no combine)")

    args = parser.parse_args()

    input_dir = args.input_dir
    output_csv = args.output_csv

    ignore_tags = set(args.ignore_tags)
    select_tags = set(args.select_tags)

    copy_top = args.copy_top
    copy_top_percent = args.copy_top_percent
    copy_until_size = args.copy_until_size
    copy_dest = args.copy_dest

    combine_md = args.combine_md
    verbose = args.verbose
    no_csv = args.no_csv
    dry_run = args.dry_run

    log("INFO", "Starting analysis...", verbose)
    log("INFO", f"Input directory: {input_dir}", verbose)
    log("INFO", f"Output CSV: {output_csv}", verbose)
    if dry_run:
        log("INFO", "Dry-run mode: no changes will be made.", verbose)

    # Get all .md files
    md_files = [f for f in os.listdir(input_dir) if f.endswith(".md")]
    log("INFO", f"Found {len(md_files)} markdown files.", verbose)

    # Map from note_name to filename
    notes = {os.path.splitext(f)[0]: f for f in md_files}

    # Regex for code blocks
    code_block_pattern = re.compile(r'```.*?```', re.DOTALL)

    note_tags = {}
    filtered_candidates = {}
    for note_name, filename in notes.items():
        filepath = os.path.join(input_dir, filename)
        content = safe_read_file(filepath, verbose)
        if content is None:
            # If we can't read the file, skip it
            continue
        # Remove code blocks before extracting tags
        clean_content = re.sub(code_block_pattern, '', content)
        tags_in_note = extract_tags_from_content(clean_content)
        note_tags[note_name] = tags_in_note

    # Filtering notes by tags
    def note_passes_filter(note_name):
        tags_in_note = note_tags.get(note_name, set())
        if select_tags and not select_tags.issubset(tags_in_note):
            return False
        if ignore_tags and not tags_in_note.isdisjoint(ignore_tags):
            return False
        return True

    filtered_notes = {n: notes[n] for n in notes.keys() if n in note_tags and note_passes_filter(n)}

    log("INFO", f"After tag filtering, {len(filtered_notes)} notes remain.", verbose)

    # Regex for [[ ... ]] links
    link_pattern = re.compile(r'\[\[([^\]]+)\]\]')

    outgoing_links = {note: set() for note in filtered_notes.keys()}
    for i, (note_name, filename) in enumerate(filtered_notes.items(), start=1):
        filepath = os.path.join(input_dir, filename)
        content = safe_read_file(filepath, verbose)
        if content is None:
            # If we can't read this file now (though we did before?), skip its links
            continue

        found_links = link_pattern.findall(content)
        for link in found_links:
            target = link.strip()
            if target in filtered_notes.keys() and target != note_name:
                outgoing_links[note_name].add(target)

        log("DEBUG", f"Processed {i}/{len(filtered_notes)}: {filename} | Outgoing links: {len(outgoing_links[note_name])}", verbose)

    incoming_links_count = {note: 0 for note in filtered_notes.keys()}
    for note in filtered_notes.keys():
        for source_note, targets in outgoing_links.items():
            if note in targets:
                incoming_links_count[note] += 1

    data_for_csv = []
    for note in filtered_notes.keys():
        filename = filtered_notes[note]
        filepath = os.path.join(input_dir, filename)
        # If file isn't accessible here, skip
        if not os.path.isfile(filepath):
            log("ERROR", f"File {filepath} not found or inaccessible during size check.", verbose)
            continue
        try:
            file_size = os.path.getsize(filepath)  # in bytes
        except Exception as e:
            log("ERROR", f"Could not get size for {filepath}: {e}", verbose)
            file_size = 0
        out_count = len(outgoing_links[note])
        in_count = incoming_links_count[note]
        total_count = out_count + in_count
        data_for_csv.append((filename, out_count, in_count, total_count, file_size))

    data_for_csv.sort(key=lambda x: x[3], reverse=True)

    if not no_csv and not dry_run:
        log("INFO", "Writing CSV output...", verbose)
        try:
            with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile, delimiter=';')
                writer.writerow(["nom_du_fichier", "nombre_liens_sortants", "nombre_liens_entrants", "total_liens", "file_size"])
                for row in data_for_csv:
                    writer.writerow(row)
            log("INFO", "CSV written successfully.", verbose)
        except Exception as e:
            log("ERROR", f"Could not write CSV {output_csv}: {e}", verbose)
    elif no_csv:
        log("INFO", "--no-csv used, no CSV output generated.", verbose)
    elif dry_run:
        log("INFO", "Dry-run mode, no CSV output generated.", verbose)

    num_notes = len(data_for_csv)

    max_notes_limit = None
    if copy_top is not None and copy_top > 0:
        max_notes_limit = copy_top

    if copy_top_percent is not None and 0 < copy_top_percent <= 100:
        count = math.floor((copy_top_percent / 100.0) * num_notes)
        if count > 0:
            if max_notes_limit is not None:
                max_notes_limit = min(max_notes_limit, count)
            else:
                max_notes_limit = count

    max_size_bytes = None
    if copy_until_size is not None and copy_until_size > 0:
        max_size_bytes = int(copy_until_size * 1024 * 1024)

    notes_to_copy = []
    total_size = 0

    for row in data_for_csv:
        filename = row[0]
        file_size = row[4]

        if max_notes_limit is not None and len(notes_to_copy) >= max_notes_limit:
            break
        if max_size_bytes is not None and total_size + file_size > max_size_bytes:
            break

        notes_to_copy.append(row)
        total_size += file_size

    if notes_to_copy:
        log("INFO", f"Selected {len(notes_to_copy)} notes for copying.", verbose)
    else:
        log("INFO", "No notes selected for copying based on constraints.", verbose)

    if dry_run:
        log("INFO", "Dry-run mode: No actual copying or combining performed.", verbose)
        if notes_to_copy:
            log("INFO", "The following notes would have been copied:", verbose)
            for r in notes_to_copy:
                log("INFO", f" - {r[0]} ({r[4]} bytes)", verbose)
        return

    if notes_to_copy and copy_dest is not None:
        log("INFO", f"Copying {len(notes_to_copy)} notes to {copy_dest}", verbose)
        if not os.path.exists(copy_dest):
            try:
                os.makedirs(copy_dest)
            except Exception as e:
                log("ERROR", f"Could not create directory {copy_dest}: {e}", verbose)
        for i, row in enumerate(notes_to_copy, start=1):
            filename = row[0]
            source_path = os.path.join(input_dir, filename)
            dest_path = os.path.join(copy_dest, filename)
            if safe_copy_file(source_path, dest_path, verbose):
                log("DEBUG", f"Copied {i}/{len(notes_to_copy)}: {filename}", verbose)
            else:
                log("ERROR", f"Failed to copy {filename}, skipping.", verbose)

    # Combine only the selected notes (notes_to_copy) if requested
    if combine_md is not None and notes_to_copy:
        log("INFO", f"Combining {len(notes_to_copy)} selected notes into {combine_md}", verbose)
        try:
            with open(combine_md, 'w', encoding='utf-8') as out_md:
                for i, row in enumerate(notes_to_copy):
                    filename = row[0]
                    source_path = os.path.join(input_dir, filename)
                    content = safe_read_file(source_path, verbose)
                    if content is None:
                        log("ERROR", f"Skipping {filename} in combination due to read error.", verbose)
                        continue
                    out_md.write(content)
                    if i < len(notes_to_copy) - 1:
                        out_md.write("\n\n")
            log("INFO", "Combination done.", verbose)
        except Exception as e:
            log("ERROR", f"Could not write combined file {combine_md}: {e}", verbose)
    elif combine_md is not None:
        log("INFO", "No notes to combine.", verbose)

    log("INFO", "Processing complete.", verbose)

if __name__ == "__main__":
    main()
