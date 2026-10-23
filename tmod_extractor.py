#!/usr/bin/env python3
"""
tmod_extractor.py
Standalone .tmod unpacker and metadata inspector for Terraria tModLoader 1.4+.
Matches exact binary protocol from Terraria.ModLoader.Core.TmodFile.
"""
import os
import sys
import struct
import zlib
from typing import Dict, Any, List

def read_7bit_encoded_int(f) -> int:
    count = 0
    shift = 0
    while True:
        b = f.read(1)
        if not b:
            raise EOFError("Unexpected end of stream while reading 7-bit encoded int")
        byte_val = ord(b)
        count |= (byte_val & 0x7F) << shift
        shift += 7
        if (byte_val & 0x80) == 0:
            break
    return count

def read_csharp_string(f) -> str:
    length = read_7bit_encoded_int(f)
    data = f.read(length)
    return data.decode('utf-8', errors='replace')

def unpack_tmod(tmod_path: str, output_dir: str = None) -> Dict[str, Any]:
    if not os.path.exists(tmod_path):
        raise FileNotFoundError(f"File not found: {tmod_path}")

    if output_dir is None:
        base_name = os.path.splitext(os.path.basename(tmod_path))[0]
        output_dir = os.path.join(os.path.dirname(tmod_path), f"{base_name}_extracted")

    os.makedirs(output_dir, exist_ok=True)

    with open(tmod_path, 'rb') as f:
        magic = f.read(4)
        if magic != b'TMOD':
            raise ValueError(f"Invalid .tmod file. Magic header mismatch: {magic}")

        tmodloader_version = read_csharp_string(f)
        file_hash = f.read(20)
        signature = f.read(256)
        data_len = struct.unpack('<I', f.read(4))[0]  # total data length / reserved
        file_table_len = struct.unpack('<i', f.read(4))[0]
        file_table_data = f.read(file_table_len)

        # Decompress file table using Deflate (raw without zlib wrapper)
        try:
            decompressed_table = zlib.decompress(file_table_data, -15)
        except Exception:
            try:
                decompressed_table = zlib.decompress(file_table_data)
            except Exception as e:
                raise ValueError(f"Failed to decompress file table: {e}")

        import io
        tbl_stream = io.BytesIO(decompressed_table)
        mod_name = read_csharp_string(tbl_stream)
        mod_version = read_csharp_string(tbl_stream)
        entry_count = struct.unpack('<i', tbl_stream.read(4))[0]

        entries = []
        for _ in range(entry_count):
            name = read_csharp_string(tbl_stream)
            length = struct.unpack('<i', tbl_stream.read(4))[0]
            c_length = struct.unpack('<i', tbl_stream.read(4))[0]
            entries.append({"name": name, "length": length, "compressed_length": c_length})

        # Now extract payload entries in sequence
        extracted_files = []
        for entry in entries:
            raw_bytes = f.read(entry["compressed_length"])
            if entry["length"] != entry["compressed_length"]:
                try:
                    file_content = zlib.decompress(raw_bytes, -15)
                except Exception:
                    file_content = zlib.decompress(raw_bytes)
            else:
                file_content = raw_bytes

            out_path = os.path.join(output_dir, entry["name"])
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(out_path, 'wb') as out_f:
                out_f.write(file_content)

            extracted_files.append({
                "name": entry["name"],
                "size": len(file_content),
                "path": out_path
            })

    return {
        "mod_name": mod_name,
        "mod_version": mod_version,
        "tmodloader_version": tmodloader_version,
        "extracted_dir": output_dir,
        "file_count": len(extracted_files),
        "files": extracted_files
    }

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 tmod_extractor.py <file.tmod> [out_dir]")
        sys.exit(1)
    res = unpack_tmod(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    print(f"Successfully unpacked {res['mod_name']} v{res['mod_version']} ({res['file_count']} files) -> {res['extracted_dir']}")
