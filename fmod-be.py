#!/usr/bin/env python3

import os
import sys
import argparse
from pathlib import Path

def resolve_windows_dlls():
    if sys.platform != "win32":
        return

    try:
        import pyogg
        pyogg_dir = Path(pyogg.__file__).parent
        original_cwd = os.getcwd()
        os.chdir(pyogg_dir)
        from fsb5 import vorbis
        os.chdir(original_cwd)
        print("[System] Windows Vorbis DLLs resolved successfully via pyogg.")
    except ImportError:
        print("[Warning] 'pyogg' is not installed. Extraction of Vorbis audio might fail.")
    except Exception as e:
        print(f"[Warning] Failed to pre-load Vorbis DLLs: {e}")
resolve_windows_dlls()
import fsb5


def extract_bank(bank_path: Path, output_dir: Path, list_only: bool = False):
    if not bank_path.exists():
        print(f"Error: Bank file not found: {bank_path}")
        sys.exit(1)

    print(f"Reading bank file: {bank_path.name}...")
    bank_data = bank_path.read_bytes()

    fsb_offset = bank_data.find(b"FSB5")
    if fsb_offset == -1:
        print("Error: Could not find embedded FSB5 sample container in this bank file.")
        sys.exit(1)

    print(f"FSB5 sample container found at offset {hex(fsb_offset)}")
    fsb_data = bank_data[fsb_offset:]

    fsb = fsb5.FSB5(fsb_data)
    extension = fsb.get_sample_extension()
    print(f"Detected format: {extension.upper()} ({len(fsb.samples)} tracks)")

    if list_only:
        print("\nAvailable Tracks:")
        for idx, sample in enumerate(fsb.samples):
            size_mb = len(sample.data) / (1024 * 1024) if sample.data else 0
            print(f"  [{idx:02d}] {sample.name} ({size_mb:.2f} MB)")
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Extracting tracks to: {output_dir.resolve()}...\n")

    success_count = 0
    for idx, sample in enumerate(fsb.samples):
        track_name = sample.name if sample.name else f"track_{idx:02d}"
        if not track_name.endswith(f".{extension}"):
            track_name = f"{track_name}.{extension}"
            
        safe_name = "".join(c for c in track_name if c.isalnum() or c in " -_,.()&").strip()
        track_path = output_dir / safe_name

        try:
            audio_bytes = fsb.rebuild_sample(sample)
            track_path.write_bytes(audio_bytes)
            print(f"  [+] Extracted: {safe_name}")
            success_count += 1
        except Exception as e:
            print(f"  [-] Failed to extract track {idx} ({track_name}): {e}")

    print(f"\nFinished! Successfully extracted {success_count} of {len(fsb.samples)} tracks.")


def main():
    parser = argparse.ArgumentParser(
        description="Extract audio tracks from FMOD .bank / .assets.bank files."
    )
    parser.add_argument(
        "-i", "--input", 
        type=str, 
        required=True,
        help="Path to the FMOD bank file (e.g., music.bank)"
    )
    parser.add_argument(
        "-o", "--output", 
        type=str, 
        default="extracted_tracks",
        help="Output directory for extracted files (default: extracted_tracks)"
    )
    parser.add_argument(
        "-l", "--list", 
        action="store_true",
        help="List available tracks in the bank without extracting them"
    )

    args = parser.parse_args()
    
    bank_path = Path(args.input)
    output_dir = Path(args.output)
    
    extract_bank(bank_path, output_dir, list_only=args.list)


if __name__ == "__main__":
    main()
