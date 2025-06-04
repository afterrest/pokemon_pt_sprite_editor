import struct
import os
from typing import List, NamedTuple
from pathlib import Path


class FileEntry(NamedTuple):
    """NARC 파일 내 개별 파일 엔트리 정보"""
    offset: int
    size: int


class NarcReader:
    """NARC 파일 읽기/쓰기를 위한 클래스"""

    def __init__(self, filename: str = None):
        self.filename = filename
        self.entries_count = 0
        self.file_entries: List[FileEntry] = []
        self.total_size = 0

        if filename and os.path.exists(filename):
            self._parse_narc_file()

    def _parse_narc_file(self):
        """NARC 파일을 파싱하여 파일 엔트리 정보를 추출"""
        with open(self.filename, 'rb') as f:
            # NARC 헤더 읽기 (16바이트)
            header = f.read(16)
            if len(header) != 16:
                raise ValueError("Invalid NARC file: header too short")

            # 헤더 파싱
            magic = header[:4]  # "NARC"
            if magic != b'NARC':
                raise ValueError("Invalid NARC file: wrong magic signature")

            # 파일 크기 (offset 8, 4바이트)
            self.total_size = struct.unpack('<I', header[8:12])[0]

            # 첫 번째 섹션 오프셋 (offset 12, 2바이트)
            first_section_offset = struct.unpack('<H', header[12:14])[0]

            # BTAF 섹션으로 이동
            f.seek(first_section_offset)
            btaf_header = f.read(12)
            if len(btaf_header) != 12:
                raise ValueError("Invalid NARC file: BTAF header too short")

            # BTAF 헤더 파싱
            btaf_magic = btaf_header[:4]  # "BTAF"
            if btaf_magic != b'BTAF':
                raise ValueError("Invalid NARC file: BTAF section not found")

            btaf_size = struct.unpack('<I', btaf_header[4:8])[0]
            self.entries_count = struct.unpack('<I', btaf_header[8:12])[0]

            # 파일 엔트리 읽기
            self.file_entries = []
            for i in range(self.entries_count):
                entry_data = f.read(8)  # offset(4) + end_offset(4)
                if len(entry_data) != 8:
                    raise ValueError(f"Invalid NARC file: entry {i} data too short")

                start_offset, end_offset = struct.unpack('<II', entry_data)
                size = end_offset - start_offset
                self.file_entries.append(FileEntry(start_offset, size))

            # BTNF 섹션으로 이동하여 실제 파일 데이터 오프셋 계산
            btnf_offset = first_section_offset + btaf_size
            f.seek(btnf_offset)
            btnf_header = f.read(16)
            if len(btnf_header) != 16:
                raise ValueError("Invalid NARC file: BTNF header too short")

            btnf_size = struct.unpack('<I', btnf_header[4:8])[0]

            # 실제 파일 데이터의 시작 오프셋 계산
            file_data_base_offset = first_section_offset + btaf_size + btnf_size + 8

            # 파일 엔트리의 오프셋을 실제 파일 위치로 조정
            adjusted_entries = []
            for entry in self.file_entries:
                actual_offset = entry.offset + file_data_base_offset
                adjusted_entries.append(FileEntry(actual_offset, entry.size))

            self.file_entries = adjusted_entries

    def extract_file(self, file_id: int) -> bytes:
        """지정된 ID의 파일을 추출하여 바이트 데이터로 반환"""
        if file_id < 0 or file_id >= self.entries_count:
            raise IndexError(f"File ID {file_id} out of range (0-{self.entries_count - 1})")

        entry = self.file_entries[file_id]

        with open(self.filename, 'rb') as f:
            f.seek(entry.offset)
            return f.read(entry.size)

    def extract_all_files(self, output_dir: str) -> None:
        """모든 파일을 지정된 디렉토리에 추출"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        print(f"Extracting {self.entries_count} files to {output_dir}")

        for i in range(self.entries_count):
            file_data = self.extract_file(i)
            output_file = output_path / f"file_{i:04d}.bin"

            with open(output_file, 'wb') as f:
                f.write(file_data)

            print(f"Extracted: {output_file.name} ({len(file_data)} bytes)")

    def get_file_info(self) -> List[dict]:
        """모든 파일의 정보를 반환"""
        info_list = []
        for i, entry in enumerate(self.file_entries):
            info_list.append({
                'id': i,
                'offset': entry.offset,
                'size': entry.size
            })
        return info_list

    def __len__(self) -> int:
        """파일 개수 반환"""
        return self.entries_count


def unpack_narc(narc_file: str, output_dir: str) -> NarcReader:
    """NARC 파일을 언팩하는 함수

    Args:
        narc_file: 언팩할 NARC 파일 경로
        output_dir: 추출된 파일들을 저장할 디렉토리

    Returns:
        NarcReader: 파싱된 NARC 리더 인스턴스
    """
    if not os.path.exists(narc_file):
        raise FileNotFoundError(f"NARC file not found: {narc_file}")

    print(f"Unpacking NARC file: {narc_file}")

    reader = NarcReader(narc_file)
    reader.extract_all_files(output_dir)

    print(f"Successfully unpacked {len(reader)} files")
    return reader


def pack_narc(input_dir: str, output_narc: str) -> None:
    """폴더의 파일들을 NARC 파일로 패킹하는 함수

    Args:
        input_dir: 패킹할 파일들이 있는 폴더
        output_narc: 생성할 NARC 파일 경로
    """
    input_path = Path(input_dir)
    if not input_path.exists() or not input_path.is_dir():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    # .bin 파일들을 숫자 순으로 정렬
    files = sorted([f for f in input_path.glob("*.bin")],
                   key=lambda x: int(x.stem.split('_')[1]) if '_' in x.stem else 0)

    if not files:
        raise ValueError(f"No .bin files found in {input_dir}")

    print(f"Packing {len(files)} files into NARC: {output_narc}")

    # 파일 데이터들 읽기
    file_data_list = []
    for file_path in files:
        with open(file_path, 'rb') as f:
            data = f.read()
            file_data_list.append(data)
            print(f"Added: {file_path.name} ({len(data)} bytes)")

    # NARC 파일 생성
    with open(output_narc, 'wb') as narc_file:
        entries_count = len(file_data_list)

        # 각 섹션 크기 계산
        btaf_size = 12 + (entries_count * 8)  # 헤더(12) + 엔트리들(각 8바이트)
        btnf_size = 16  # 단순한 BTNF 헤더만

        # 4바이트 정렬을 위한 패딩 계산
        btaf_padded_size = ((btaf_size + 3) // 4) * 4
        btnf_padded_size = ((btnf_size + 3) // 4) * 4

        # 파일 데이터 오프셋들 계산
        file_offsets = []
        current_offset = 0

        for data in file_data_list:
            file_offsets.append(current_offset)
            current_offset += len(data)
            # 4바이트 정렬
            current_offset = ((current_offset + 3) // 4) * 4

        # 전체 파일 크기 계산
        total_file_data_size = current_offset
        total_narc_size = 16 + btaf_padded_size + btnf_padded_size + 8 + total_file_data_size

        # NARC 헤더 작성
        narc_file.write(b'NARC')  # magic
        narc_file.write(b'\xFF\xFE')  # byte order mark
        narc_file.write(b'\x00\x01')  # version
        narc_file.write(struct.pack('<I', total_narc_size))  # file size
        narc_file.write(struct.pack('<H', 16))  # header size
        narc_file.write(struct.pack('<H', 3))  # section count

        # BTAF 섹션 작성
        narc_file.write(b'BTAF')
        narc_file.write(struct.pack('<I', btaf_size))
        narc_file.write(struct.pack('<I', entries_count))

        # 파일 엔트리들 작성
        for i, offset in enumerate(file_offsets):
            start_offset = offset
            if i + 1 < len(file_offsets):
                end_offset = file_offsets[i + 1]
            else:
                end_offset = total_file_data_size

            narc_file.write(struct.pack('<I', start_offset))
            narc_file.write(struct.pack('<I', end_offset))

        # BTAF 패딩
        current_pos = narc_file.tell()
        padding_needed = btaf_padded_size - (current_pos - 16)
        if padding_needed > 0:
            narc_file.write(b'\x00' * padding_needed)

        # BTNF 섹션 작성 (단순한 버전)
        narc_file.write(b'BTNF')
        narc_file.write(struct.pack('<I', btnf_size))
        narc_file.write(b'\x00' * 8)  # 단순한 헤더

        # BTNF 패딩
        current_pos = narc_file.tell()
        btnf_start = 16 + btaf_padded_size
        padding_needed = btnf_padded_size - (current_pos - btnf_start)
        if padding_needed > 0:
            narc_file.write(b'\x00' * padding_needed)

        # GMIF 섹션 헤더
        narc_file.write(b'GMIF')
        narc_file.write(struct.pack('<I', 8 + total_file_data_size))

        # 파일 데이터들 작성
        for i, data in enumerate(file_data_list):
            narc_file.write(data)

            # 마지막 파일이 아니면 4바이트 정렬을 위한 패딩
            if i < len(file_data_list) - 1:
                current_pos = narc_file.tell()
                next_aligned_pos = ((current_pos + 3) // 4) * 4
                padding_needed = next_aligned_pos - current_pos
                if padding_needed > 0:
                    narc_file.write(b'\x00' * padding_needed)

    print(f"Successfully created NARC file: {output_narc}")


# 사용 예제
if __name__ == "__main__":
    # NARC 파일 언팩 예제
    unpack_narc("pl_pokegra.narc", "extracted_files/")

    # 폴더를 NARC 파일로 패킹 예제
    pack_narc("extracted_files/", "repacked.narc")

    pass