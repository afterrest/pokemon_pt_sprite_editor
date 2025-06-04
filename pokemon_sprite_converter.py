import struct
import os
from PIL import Image, ImagePalette
import numpy as np
from typing import List, Tuple, Optional
from pathlib import Path


class PokemonSpriteConverter:
    """포켓몬 4세대 스프라이트 ↔ PNG 변환기"""

    def __init__(self, is_diamond_pearl: bool = False):
        """
        Args:
            is_diamond_pearl: True면 DP 포맷, False면 Platinum 포맷
        """
        self.is_diamond_pearl = is_diamond_pearl

    def pokemon_to_png(self, sprite_data: bytes, palette_data: bytes, output_path: str) -> None:
        """포켓몬 스프라이트 데이터를 PNG로 변환

        Args:
            sprite_data: 포켓몬 스프라이트 바이너리 데이터 (6448 bytes)
            palette_data: 팔레트 바이너리 데이터 (72 bytes)
            output_path: 저장할 PNG 파일 경로
        """
        # 팔레트 파싱
        palette = self._parse_palette(palette_data)

        # 스프라이트 이미지 생성
        image = self._parse_sprite(sprite_data)

        # 팔레트 적용
        image.putpalette(palette)

        # PNG로 저장
        image.save(output_path, "PNG")
        print(f"PNG 저장 완료: {output_path}")

    def png_to_pokemon(self, png_path: str) -> Tuple[bytes, bytes]:
        """PNG를 포켓몬 스프라이트 데이터로 변환

        Args:
            png_path: 변환할 PNG 파일 경로

        Returns:
            (sprite_data, palette_data): 스프라이트와 팔레트 바이너리 데이터
        """
        # PNG 로드 및 검증
        image = self._load_and_validate_png(png_path)

        # 스프라이트 데이터 생성
        sprite_data = self._create_sprite_data(image)

        # 팔레트 데이터 생성
        palette_data = self._create_palette_data(image)

        return sprite_data, palette_data

    def _parse_sprite(self, sprite_data: bytes) -> Image.Image:
        """포켓몬 스프라이트 바이너리를 Image로 변환"""
        if len(sprite_data) != 6448:
            raise ValueError(f"Invalid sprite data size: {len(sprite_data)} (expected 6448)")

        # 48바이트 헤더 건너뛰기
        pixel_data = sprite_data[48:]

        # 16비트 값들을 읽기 (3200개 = 6400바이트)
        pixel_array = []
        for i in range(0, 6400, 2):
            value = struct.unpack('<H', pixel_data[i:i + 2])[0]
            pixel_array.append(value)

        # 암호화 해제
        seed = pixel_array[0]
        if not self.is_diamond_pearl:
            # Platinum 복호화
            for j in range(3200):
                pixel_array[j] ^= (seed & 0xFFFF)
                seed = (seed * 1103515245 + 24691) & 0xFFFFFFFF
        else:
            # Diamond/Pearl 복호화
            seed = pixel_array[3199]
            for j in range(3199, -1, -1):
                pixel_array[j] ^= (seed & 0xFFFF)
                seed = (seed * 1103515245 + 24691) & 0xFFFFFFFF

        # 4비트 픽셀로 변환 (160x80 = 12800 픽셀)
        pixels = []
        for value in pixel_array:
            pixels.append(value & 0xF)
            pixels.append((value >> 4) & 0xF)
            pixels.append((value >> 8) & 0xF)
            pixels.append((value >> 12) & 0xF)

        # 이미지 생성
        image = Image.new('P', (160, 80))
        image.putdata(pixels)

        return image

    def _parse_palette(self, palette_data: bytes) -> List[int]:
        """팔레트 바이너리를 RGB 팔레트로 변환"""
        if len(palette_data) != 72:
            raise ValueError(f"Invalid palette data size: {len(palette_data)} (expected 72)")

        # 40바이트 헤더 건너뛰기
        color_data = palette_data[40:]

        # 16개 색상 파싱 (각 2바이트, BGR555 포맷)
        palette = []
        for i in range(0, 32, 2):
            color_value = struct.unpack('<H', color_data[i:i + 2])[0]

            # BGR555에서 RGB로 변환
            r = ((color_value & 0x1F) << 3)
            g = (((color_value >> 5) & 0x1F) << 3)
            b = (((color_value >> 10) & 0x1F) << 3)

            palette.extend([r, g, b])

        # 256색 팔레트로 확장 (나머지는 검은색)
        while len(palette) < 768:  # 256 * 3
            palette.extend([0, 0, 0])

        return palette

    def _load_and_validate_png(self, png_path: str) -> Image.Image:
        """PNG 파일을 로드하고 검증"""
        if not os.path.exists(png_path):
            raise FileNotFoundError(f"PNG file not found: {png_path}")

        image = Image.open(png_path)

        # 인덱스 컬러로 변환
        if image.mode != 'P':
            if image.mode in ['RGB', 'RGBA']:
                image = image.convert('P', palette=Image.ADAPTIVE, colors=16)
            else:
                image = image.convert('P')

        # 크기 검증 및 조정
        if image.size == (64, 64):
            # 64x64를 80x80으로 확장 (8픽셀 패딩)
            new_image = Image.new('P', (80, 80), 0)
            new_image.paste(image, (8, 8))
            image = new_image

        if image.size == (80, 80):
            # 80x80을 160x80으로 확장 (좌우 복사)
            new_image = Image.new('P', (160, 80), 0)
            new_image.paste(image, (0, 0))
            new_image.paste(image, (80, 0))
            image = new_image

        if image.size != (160, 80):
            raise ValueError(f"Invalid image size: {image.size} (expected 160x80, 80x80, or 64x64)")

        # 팔레트 크기 검증
        palette = image.getpalette()
        if palette is None:
            raise ValueError("Image has no palette")

        # 16색으로 제한
        pixel_data = list(image.getdata())
        max_color = max(pixel_data) if pixel_data else 0
        if max_color >= 16:
            print(f"Warning: Image uses {max_color + 1} colors, reducing to 16...")
            # 간단한 색상 매핑 (실제로는 더 정교한 알고리즘 필요)
            pixel_data = [min(pixel, 15) for pixel in pixel_data]
            image.putdata(pixel_data)

        return image

    def _create_sprite_data(self, image: Image.Image) -> bytes:
        """Image를 포켓몬 스프라이트 바이너리로 변환"""
        # 픽셀 데이터 추출
        pixels = list(image.getdata())

        # 4픽셀을 하나의 16비트 값으로 패킹
        pixel_array = []
        for i in range(0, len(pixels), 4):
            value = (pixels[i] & 0xF) | \
                    ((pixels[i + 1] & 0xF) << 4) | \
                    ((pixels[i + 2] & 0xF) << 8) | \
                    ((pixels[i + 3] & 0xF) << 12)
            pixel_array.append(value)

        # 암호화
        seed = 0
        if not self.is_diamond_pearl:
            # Platinum 암호화
            for j in range(3200):
                pixel_array[j] ^= (seed & 0xFFFF)
                seed = (seed * 1103515245 + 24691) & 0xFFFFFFFF
        else:
            # Diamond/Pearl 암호화
            seed = 31315
            for value in pixel_array:
                seed += value
            seed &= 0xFFFFFFFF

            for j in range(3199, -1, -1):
                pixel_array[j] ^= (seed & 0xFFFF)
                seed = (seed * 1103515245 + 24691) & 0xFFFFFFFF

        # 헤더 생성
        header = bytes([
            82, 71, 67, 78, 255, 254, 0, 1, 48, 25, 0, 0, 16, 0, 1, 0,
            82, 65, 72, 67, 32, 25, 0, 0, 10, 0, 20, 0, 3, 0, 0, 0,
            0, 0, 0, 0, 1, 0, 0, 0, 0, 25, 0, 0, 24, 0, 0, 0
        ])

        # 픽셀 데이터를 바이너리로 변환
        pixel_bytes = b''.join(struct.pack('<H', value) for value in pixel_array)

        return header + pixel_bytes

    def _create_palette_data(self, image: Image.Image) -> bytes:
        """Image 팔레트를 포켓몬 팔레트 바이너리로 변환"""
        palette = image.getpalette()
        if palette is None:
            # 기본 그레이스케일 팔레트
            palette = []
            for i in range(16):
                gray = i * 17  # 0-255 범위로 확장
                palette.extend([gray, gray, gray])

        # 헤더 생성
        header = bytes([
            82, 76, 67, 78, 255, 254, 0, 1, 72, 0, 0, 0, 16, 0, 1, 0,
            84, 84, 76, 80, 56, 0, 0, 0, 4, 0, 10, 0, 0, 0, 0, 0,
            32, 0, 0, 0, 16, 0, 0, 0
        ])

        # 16색 팔레트를 BGR555 포맷으로 변환
        color_data = []
        for i in range(16):
            if i * 3 + 2 < len(palette):
                r = palette[i * 3] >> 3  # 8비트 -> 5비트
                g = palette[i * 3 + 1] >> 3
                b = palette[i * 3 + 2] >> 3
            else:
                r = g = b = 0

            # BGR555 포맷으로 패킹
            color_value = (r & 0x1F) | ((g & 0x1F) << 5) | ((b & 0x1F) << 10)
            color_data.append(struct.pack('<H', color_value))

        return header + b''.join(color_data)

    def standardize_colors(self, image: Image.Image) -> Image.Image:
        """색상을 포켓몬 포맷에 맞게 표준화 (8의 배수로 조정)"""
        palette = image.getpalette()
        if palette is None:
            return image

        # RGB 값을 8의 배수로 조정
        standardized_palette = []
        for i in range(0, len(palette), 3):
            if i + 2 < len(palette):
                r = palette[i] - (palette[i] % 8)
                g = palette[i + 1] - (palette[i + 1] % 8)
                b = palette[i + 2] - (palette[i + 2] % 8)
                standardized_palette.extend([r, g, b])

        # 256색까지 확장
        while len(standardized_palette) < 768:
            standardized_palette.extend([0, 0, 0])

        new_image = image.copy()
        new_image.putpalette(standardized_palette)
        return new_image


def convert_narc_to_pngs(narc_file: str, output_dir: str, is_diamond_pearl: bool = False) -> None:
    """NARC 파일에서 모든 포켓몬 스프라이트를 PNG로 변환

    Args:
        narc_file: 포켓몬 스프라이트 NARC 파일
        output_dir: PNG 파일들을 저장할 디렉토리
        is_diamond_pearl: DP 포맷 여부
    """
    from narc_reader import NarcReader

    reader = NarcReader(narc_file)
    converter = PokemonSpriteConverter(is_diamond_pearl)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    pokemon_count = len(reader) // 6
    print(f"총 {pokemon_count}마리 포켓몬 스프라이트 변환 시작...")

    for pokemon_id in range(pokemon_count):
        base_index = pokemon_id * 6
        pokemon_dir = output_path / f"pokemon_{pokemon_id:03d}"
        pokemon_dir.mkdir(exist_ok=True)

        try:
            # 4개 스프라이트 (암컷 뒷모습, 수컷 뒷모습, 암컷 앞모습, 수컷 앞모습)
            sprite_names = ["female_back", "male_back", "female_front", "male_front"]

            for i, sprite_name in enumerate(sprite_names):
                sprite_entry = reader.file_entries[base_index + i]
                if sprite_entry.size == 6448:  # 스프라이트 데이터
                    sprite_data = reader.extract_file(base_index + i)

                    # 노말 팔레트
                    if base_index + 4 < len(reader.file_entries):
                        normal_palette_entry = reader.file_entries[base_index + 4]
                        if normal_palette_entry.size == 72:
                            normal_palette = reader.extract_file(base_index + 4)
                            output_file = pokemon_dir / f"{sprite_name}_normal.png"
                            converter.pokemon_to_png(sprite_data, normal_palette, str(output_file))

                    # 색다른 팔레트
                    if base_index + 5 < len(reader.file_entries):
                        shiny_palette_entry = reader.file_entries[base_index + 5]
                        if shiny_palette_entry.size == 72:
                            shiny_palette = reader.extract_file(base_index + 5)
                            output_file = pokemon_dir / f"{sprite_name}_shiny.png"
                            converter.pokemon_to_png(sprite_data, shiny_palette, str(output_file))

            print(f"포켓몬 #{pokemon_id:03d} 변환 완료")

        except Exception as e:
            print(f"포켓몬 #{pokemon_id:03d} 변환 실패: {e}")

    print(f"모든 스프라이트 PNG 변환 완료: {output_dir}")


def convert_pngs_to_narc(input_dir: str, output_narc: str, original_narc: str = None,
                         is_diamond_pearl: bool = False) -> None:
    """PNG 파일들을 포켓몬 스프라이트 NARC 파일로 변환

    Args:
        input_dir: PNG 파일들이 있는 디렉토리
        output_narc: 생성할 NARC 파일
        original_narc: 원본 NARC 파일 (구조 참조용, 선택사항)
        is_diamond_pearl: DP 포맷 여부
    """
    from narc_reader import pack_narc, NarcReader

    input_path = Path(input_dir)
    converter = PokemonSpriteConverter(is_diamond_pearl)
    temp_dir = Path("temp_narc_data")
    temp_dir.mkdir(exist_ok=True)

    # 원본 NARC 구조 분석
    original_structure = None
    if original_narc and os.path.exists(original_narc):
        print(f"원본 NARC 구조 분석 중: {original_narc}")
        original_reader = NarcReader(original_narc)
        original_structure = {}

        pokemon_count = len(original_reader) // 6
        for pokemon_id in range(pokemon_count):
            base_index = pokemon_id * 6
            sprite_slots = []

            # 4개 스프라이트 슬롯의 유효성 확인
            for i in range(4):
                if base_index + i < len(original_reader.file_entries):
                    entry = original_reader.file_entries[base_index + i]
                    sprite_slots.append(entry.size > 0 and entry.size == 6448)
                else:
                    sprite_slots.append(False)

            original_structure[pokemon_id] = {
                'sprite_slots': sprite_slots,  # [female_back, male_back, female_front, male_front]
                'has_normal_palette': base_index + 4 < len(original_reader.file_entries) and
                                      original_reader.file_entries[base_index + 4].size == 72,
                'has_shiny_palette': base_index + 5 < len(original_reader.file_entries) and
                                     original_reader.file_entries[base_index + 5].size == 72
            }

        print(f"원본 구조 분석 완료: {pokemon_count}마리 포켓몬")

    try:
        file_index = 0

        # 포켓몬 디렉토리들을 순서대로 처리
        pokemon_dirs = sorted([d for d in input_path.iterdir() if d.is_dir() and d.name.startswith("pokemon_")])

        for pokemon_dir in pokemon_dirs:
            # 포켓몬 ID 추출
            pokemon_id = int(pokemon_dir.name.split('_')[1])
            sprite_names = ["female_back", "male_back", "female_front", "male_front"]

            normal_palette_data = None
            shiny_palette_data = None

            # 원본 구조 정보 가져오기
            structure_info = original_structure.get(pokemon_id) if original_structure else None

            # 4개 스프라이트 처리
            for i, sprite_name in enumerate(sprite_names):
                normal_png = pokemon_dir / f"{sprite_name}_normal.png"
                shiny_png = pokemon_dir / f"{sprite_name}_shiny.png"

                # 원본에서 이 슬롯이 유효했는지 확인
                should_have_sprite = True
                if structure_info and not structure_info['sprite_slots'][i]:
                    should_have_sprite = False
                    print(f"포켓몬 #{pokemon_id:03d}: {sprite_name} 슬롯은 원본에 없음 (빈 데이터 유지)")

                if should_have_sprite and normal_png.exists():
                    sprite_data, palette_data = converter.png_to_pokemon(str(normal_png))

                    # 스프라이트 데이터 저장
                    with open(temp_dir / f"file_{file_index:04d}.bin", 'wb') as f:
                        f.write(sprite_data)

                    # 첫 번째 유효한 스프라이트에서 노말 팔레트 추출
                    if normal_palette_data is None:
                        normal_palette_data = palette_data

                    print(f"포켓몬 #{pokemon_id:03d}: {sprite_name} 변환 완료")
                else:
                    # 빈 스프라이트 데이터 생성 (원본 구조 유지)
                    if structure_info and structure_info['sprite_slots'][i]:
                        # 원본에는 있었지만 PNG가 없는 경우
                        empty_data = b'\x00' * 6448
                        print(f"포켓몬 #{pokemon_id:03d}: {sprite_name} PNG 없음 (빈 데이터로 대체)")
                    else:
                        # 원본에도 없었던 경우 - 더 작은 빈 데이터
                        empty_data = b'\x00' * 48  # 헤더만
                        if not should_have_sprite:
                            print(f"포켓몬 #{pokemon_id:03d}: {sprite_name} 원본 구조 유지 (최소 데이터)")

                    with open(temp_dir / f"file_{file_index:04d}.bin", 'wb') as f:
                        f.write(empty_data)

                file_index += 1

                # 색다른 팔레트 추출 (PNG가 있고 아직 추출하지 않았을 때만)
                if should_have_sprite and shiny_png.exists() and shiny_palette_data is None:
                    _, shiny_palette_data = converter.png_to_pokemon(str(shiny_png))

            # 노말 팔레트 저장
            should_have_normal_palette = True
            if structure_info and not structure_info['has_normal_palette']:
                should_have_normal_palette = False

            if should_have_normal_palette and normal_palette_data:
                with open(temp_dir / f"file_{file_index:04d}.bin", 'wb') as f:
                    f.write(normal_palette_data)
                print(f"포켓몬 #{pokemon_id:03d}: 노말 팔레트 저장")
            else:
                # 빈 팔레트 데이터
                empty_palette = b'\x00' * (72 if should_have_normal_palette else 40)
                with open(temp_dir / f"file_{file_index:04d}.bin", 'wb') as f:
                    f.write(empty_palette)
                if not should_have_normal_palette:
                    print(f"포켓몬 #{pokemon_id:03d}: 노말 팔레트 원본 구조 유지")
            file_index += 1

            # 색다른 팔레트 저장
            should_have_shiny_palette = True
            if structure_info and not structure_info['has_shiny_palette']:
                should_have_shiny_palette = False

            if should_have_shiny_palette:
                if shiny_palette_data:
                    with open(temp_dir / f"file_{file_index:04d}.bin", 'wb') as f:
                        f.write(shiny_palette_data)
                    print(f"포켓몬 #{pokemon_id:03d}: 색다른 팔레트 저장")
                else:
                    # 노말 팔레트 복사 또는 빈 데이터
                    palette_to_save = normal_palette_data if normal_palette_data else b'\x00' * 72
                    with open(temp_dir / f"file_{file_index:04d}.bin", 'wb') as f:
                        f.write(palette_to_save)
                    print(f"포켓몬 #{pokemon_id:03d}: 색다른 팔레트 (노말 팔레트 복사)")
            else:
                # 빈 팔레트 데이터
                empty_palette = b'\x00' * 40
                with open(temp_dir / f"file_{file_index:04d}.bin", 'wb') as f:
                    f.write(empty_palette)
                print(f"포켓몬 #{pokemon_id:03d}: 색다른 팔레트 원본 구조 유지")
            file_index += 1

        # NARC 파일 생성
        pack_narc(str(temp_dir), output_narc)
        print(f"NARC 파일 생성 완료: {output_narc}")

        if original_structure:
            print("원본 NARC 구조를 참조하여 성별별 스프라이트 슬롯을 정확히 보존했습니다.")

    finally:
        # 임시 파일들 정리
        import shutil
        if temp_dir.exists():
            shutil.rmtree(temp_dir)


# 사용 예제
if __name__ == "__main__":
    # 단일 스프라이트 변환 예제
    converter = PokemonSpriteConverter(is_diamond_pearl=False)

    # PNG → 포켓몬 포맷
    # sprite_data, palette_data = converter.png_to_pokemon("pikachu.png")

    # 포켓몬 포맷 → PNG
    # converter.pokemon_to_png(sprite_data, palette_data, "converted_pikachu.png")

    # NARC 파일 전체 변환
    # convert_narc_to_pngs("pl_pokegra.narc", "extracted_sprites/")
    convert_pngs_to_narc("output/", "new_pl_pokegra.narc", "pl_pokegra.narc")

    pass