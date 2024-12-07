# Markdown Link Analyzer & Filter for Obsidian Notes

**Purpose:**  
It allows you to analyze internal links between Markdown notes, filter them by tags, select subsets based on various constraints (like file size, number of notes, or percentage), combine selected notes into one file, and optionally copy them to a separate directory.

This script was developed to prepare your Obsidian-based "second brain" notes before providing them to an AI.

**Key Characteristics:**  
- **Non-destructive:** The script does not modify your original notes.  
- **Flexible Filtering:** Select or ignore notes by tags, apply multiple constraints (top notes, top percentage, size limit) simultaneously.  
- **CSV Output:** Generate a CSV report of all filtered notes and their link statistics.  
- **Optional Bulk Copy & Combination:** Copy selected notes into a specified folder or combine them into one `.md` file, to easily manage or export them.  
- **Verbose & Dry-Run Modes:** Offers detailed logging and a dry-run mode to preview actions without making changes.

---

## Features

1. **Tag Filtering**:  
   - `--select-tags`: Only include notes that contain all specified tags.  
   - `--ignore-tags`: Exclude any notes that contain any of these tags.

   Tags can be specified with or without a `#` prefix (e.g., `#tag` or `tag`).

2. **Link Analysis**:  
   The script finds all internal links in your notes (`[[Link]]`) and computes:
   - Outgoing links (number of links a note points to)
   - Incoming links (number of links pointing to a note)
   - Total links (sum of incoming and outgoing)

3. **CSV Generation**:  
   By default, it generates a CSV with:
   - `nom_du_fichier`
   - `nombre_liens_sortants`
   - `nombre_liens_entrants`
   - `total_liens`
   - `file_size` (in bytes)

   This CSV helps you understand note connectivity and importance.

4. **Filtering by Constraints**:  
   - `--copy-top N`: Copy top N notes by total links.
   - `--copy-top-percent P`: Copy top P% of notes by total links.
   - `--copy-until-size X`: Copy notes in descending order until total size reaches X MB.

   These constraints can be combined. The script stops selecting once **any** of the set limits is reached.

5. **No CSV & Dry-Run**:
   - `--no-csv`: Skip CSV generation.  
   - `--dry-run`: Simulate the process without creating the CSV, copying, or combining notes. Useful for previewing the outcome.

6. **Combine Selected Notes**:  
   - `--combine-md "output_file.md"`: Combine only the selected notes into one Markdown file, separated by a blank line. This lets you create a single file containing the subset of notes that fit your criteria.

7. **Robustness**:  
   - Handles unusual line terminators (`\u2028`, `\u2029`) by converting them to standard newlines.  
   - Ignores tags found in code blocks.  
   - Displays errors if files are unreadable or if copying fails (but continues processing other notes).

8. **Verbose Output**:  
   - `-v` or `--verbose`: Shows detailed logs, including `[INFO]`, `[DEBUG]`, and `[ERROR]` messages with color coding. This helps you understand exactly what the script is doing.

---

## Requirements

- Python 3.6 or higher.
- A set of `.md` files in the specified directory.
- Sufficient read permissions on your notes directory, and write permissions where CSV or combined files will be created.

---

## Usage Examples

**Basic Analysis with CSV:**  
```bash
python -u "path/to/script.py" \
  -i "/path/to/obsidian/vault" \
  -o "links.csv"
```
This analyzes all `.md` files in the given directory, filters none (no tag arguments), and produces a `links.csv` summary.

**Filter by Tag & Generate CSV:**  
```bash
python -u "path/to/script.py" \
  -i "/path/to/obsidian/vault" \
  -o "links.csv" \
  --select-tags NP
```
Only notes containing the `NP` tag are included, CSV is generated.

**Ignore Certain Tags and Copy the Top 10 Notes:**  
```bash
python -u "path/to/script.py" \
  -i "/path/to/obsidian/vault" \
  -o "links.csv" \
  --select-tags NP \
  --ignore-tags archived \
  --copy-top 10 \
  --copy-dest "/path/to/top_notes" \
  -v
```
Select notes with `NP`, exclude those with `archived`, then copy the top 10 (by total links) to `top_notes` folder, and be verbose about it.

**No CSV & Just Copy Until 30MB:**  
```bash
python -u "path/to/script.py" \
  -i "/path/to/obsidian/vault" \
  -o "links.csv" \
  --select-tags NP \
  --no-csv \
  --copy-until-size 30 \
  --copy-dest "/path/to/top_notes" \
  -v
```
Do not generate CSV, just copy as many NP-tagged notes as possible without exceeding 30MB total.

**Dry-Run with Multiple Constraints:**  
```bash
python -u "path/to/script.py" \
  -i "/path/to/obsidian/vault" \
  -o "links.csv" \
  --select-tags NP \
  --copy-top 5 \
  --copy-top-percent 10 \
  --copy-until-size 10 \
  --copy-dest "/path/to/top_notes" \
  --dry-run \
  -v
```
This will show which notes would be selected under these constraints without actually copying or writing anything. Good for testing combinations.

**Combine Selected Notes into One File:**  
```bash
python -u "path/to/script.py" \
  -i "/path/to/obsidian/vault" \
  -o "links.csv" \
  --select-tags NP \
  --copy-top 5 \
  --combine-md "selected_notes.md" \
  -v
```
Select top 5 NP-tagged notes (by total links), produce a CSV, and combine those 5 notes into `selected_notes.md`.

---

## Notes

- The script does not alter or remove any content from your original `.md` files.
- If you encounter unreadable files or permission issues, the script logs them as errors and skips those notes.

---
