import numpy as np
import os
from PIL import Image
from typing import List, Tuple, Optional, Set
from collections import Counter


class IndexedBitmapHandler:
    """C# IndexedBitmapHandler.cs의 파이썬 재구현"""

    def __init__(self):
        pass

    def convert_to_8bpp_indexed_csharp_style(self, image: Image.Image) -> Image.Image:
        """C# Convert 함수 정확 재현: RGB를 8bpp 인덱스로 변환"""

        if image.mode == 'P':
            return image

        print(f"    C# 스타일 8bpp 변환: {image.mode} → Format8bppIndexed")

        if image.mode in ['RGB', 'RGBA']:
            # 알파 채널 처리
            if image.mode == 'RGBA':
                background = Image.new('RGB', image.size, (0, 0, 0))
                background.paste(image, mask=image.split()[-1])
                image = background

            # C# 로직 재현: 픽셀별 정확한 색상 매칭
            width, height = image.size
            pixels = list(image.getdata())

            new_palette = []  # 발견된 색상들 (C# newPalette)
            pixel_indices = []  # 각 픽셀의 인덱스 (C# array)

            # 첫 번째 픽셀로 시작
            if pixels:
                first_color = pixels[0]
                new_palette.append(first_color)
                pixel_indices.append(0)
                print(f"      첫 번째 색상: {first_color}")

            # 나머지 픽셀들 처리 (C# 로직과 동일)
            for i, pixel_color in enumerate(pixels[1:], 1):
                match_found = False

                # 기존 팔레트에서 정확한 색상 찾기
                for j, palette_color in enumerate(new_palette):
                    if pixel_color == palette_color:  # C#: if (Pixel == newPalette[j])
                        pixel_indices.append(j)
                        match_found = True
                        break

                if not match_found:
                    # 새로운 색상 발견
                    if len(new_palette) >= 256:  # C#: if (index >= 256)
                        print(f"      변환 실패: 256색 초과 ({len(new_palette)}색)")
                        return None

                    new_palette.append(pixel_color)
                    pixel_indices.append(len(new_palette) - 1)

            print(f"      총 {len(new_palette)}색 발견")

            # 16색으로 제한 (포켓몬 포맷)
            if len(new_palette) > 16:
                print(f"      16색으로 제한 필요: {len(new_palette)}색 → 16색")

                # 사용빈도 기반으로 상위 16색 선택
                from collections import Counter
                color_counts = Counter(pixels)
                most_common_colors = [color for color, count in color_counts.most_common(16)]

                # 색상 매핑 테이블 생성
                color_mapping = {}
                for i, color in enumerate(most_common_colors):
                    color_mapping[color] = i

                # 매핑되지 않은 색상을 가장 가까운 색상으로 매핑
                for color in new_palette:
                    if color not in color_mapping:
                        min_distance = float('inf')
                        best_match = 0

                        for mapped_color in most_common_colors:
                            distance = sum((a - b) ** 2 for a, b in zip(color, mapped_color))
                            if distance < min_distance:
                                min_distance = distance
                                best_match = color_mapping[mapped_color]

                        color_mapping[color] = best_match

                # 픽셀 인덱스 재매핑
                pixel_indices = [color_mapping[pixels[i]] for i in range(len(pixels))]
                new_palette = most_common_colors

            # PIL Image 생성
            new_image = Image.new('P', (width, height))
            new_image.putdata(pixel_indices)

            # 팔레트 설정
            flat_palette = []
            for color in new_palette:
                flat_palette.extend(color)

            # 16색 미만이면 검은색으로 채움
            while len(flat_palette) < 48:  # 16 * 3
                flat_palette.extend([0, 0, 0])

            # 256색까지 확장
            while len(flat_palette) < 768:  # 256 * 3
                flat_palette.extend([0, 0, 0])

            new_image.putpalette(flat_palette)
            print(f"      C# 스타일 8bpp 변환 완료")

            return new_image

        elif image.mode == 'L':  # 그레이스케일
            # 그레이스케일을 16색 팔레트로 변환
            image = image.convert('P', palette=Image.ADAPTIVE, colors=16)
            print(f"      그레이스케일 → 16색 팔레트 변환 완료")

        return image

    def convert_to_8bpp_indexed(self, image: Image.Image) -> Image.Image:
        """C# Convert 함수 재현: 다양한 포맷을 8bpp 인덱스로 변환"""

        if image.mode == 'P':
            return image

        print(f"    포맷 변환: {image.mode} → 8bpp Indexed")

        # C# 스타일 정확한 변환 사용
        return self.convert_to_8bpp_indexed_csharp_style(image)

    def standardize_colors(self, image: Image.Image) -> Image.Image:
        """C# StandardizeColors 함수 재현: RGB 값을 8의 배수로 조정"""

        if image.mode != 'P':
            raise ValueError("Image must be in palette mode")

        palette = image.getpalette()
        if not palette:
            return image

        print(f"    색상 표준화 중...")

        # 원본 색상과 표준화된 색상 비교용
        changes_made = False

        standardized_palette = []
        for i in range(0, min(len(palette), 48), 3):  # 16색만 처리
            original_r, original_g, original_b = palette[i:i + 3]

            # 8의 배수로 조정
            std_r = original_r - (original_r % 8)
            std_g = original_g - (original_g % 8)
            std_b = original_b - (original_b % 8)

            standardized_palette.extend([std_r, std_g, std_b])

            if (std_r != original_r) or (std_g != original_g) or (std_b != original_b):
                changes_made = True

        # 16색 미만이면 검은색으로 채움
        while len(standardized_palette) < 48:
            standardized_palette.extend([0, 0, 0])

        # 256색 팔레트로 확장
        while len(standardized_palette) < 768:
            standardized_palette.extend([0, 0, 0])

        if changes_made:
            print(f"      색상이 8의 배수로 조정되었습니다")
        else:
            print(f"      모든 색상이 이미 표준화되어 있습니다")

        new_image = image.copy()
        new_image.putpalette(standardized_palette)
        return new_image

    def palette_size(self, image: Image.Image) -> int:
        """C# PaletteSize 함수 재현: 실제 사용된 색상 수 반환"""

        if image.mode != 'P':
            return 0

        pixels = list(image.getdata())
        if not pixels:
            return 0

        max_index = max(pixels)
        return max_index + 1

    def shrink_palette(self, image: Image.Image, used_indices: Optional[Set[int]] = None) -> Image.Image:
        """C# ShrinkPalette 함수 재현: 사용되지 않는 색상 제거"""

        if image.mode != 'P':
            return image

        if used_indices is None:
            used_indices = self.get_used_indices(image)

        print(f"    팔레트 압축 중: {len(used_indices)}색 사용됨")

        if len(used_indices) <= 16:
            print(f"      이미 16색 이하입니다")
            return image

        # 사용빈도 순으로 상위 16색 선택
        pixels = list(image.getdata())
        color_counts = Counter(pixels)

        # 가장 많이 사용된 16색 선택
        most_common_colors = [color for color, count in color_counts.most_common(16)]

        print(f"      상위 16색으로 압축합니다")

        # 색상 매핑 테이블 생성
        color_mapping = {}
        for i, old_index in enumerate(most_common_colors):
            color_mapping[old_index] = i

        # 매핑되지 않은 색상은 가장 가까운 색상으로 매핑
        palette = image.getpalette()
        for pixel_index in used_indices:
            if pixel_index not in color_mapping:
                # 가장 가까운 색상 찾기
                if pixel_index * 3 + 2 < len(palette):
                    target_color = palette[pixel_index * 3:pixel_index * 3 + 3]

                    min_distance = float('inf')
                    best_match = 0

                    for mapped_index in most_common_colors:
                        if mapped_index * 3 + 2 < len(palette):
                            mapped_color = palette[mapped_index * 3:mapped_index * 3 + 3]
                            distance = sum((a - b) ** 2 for a, b in zip(target_color, mapped_color))
                            if distance < min_distance:
                                min_distance = distance
                                best_match = color_mapping[mapped_index]

                    color_mapping[pixel_index] = best_match
                else:
                    color_mapping[pixel_index] = 0

        # 픽셀 데이터 재매핑
        new_pixels = [color_mapping.get(pixel, 0) for pixel in pixels]

        # 새로운 팔레트 생성
        new_palette = []
        for i in range(16):
            if i < len(most_common_colors):
                old_index = most_common_colors[i]
                if old_index * 3 + 2 < len(palette):
                    new_palette.extend(palette[old_index * 3:old_index * 3 + 3])
                else:
                    new_palette.extend([0, 0, 0])
            else:
                new_palette.extend([0, 0, 0])

        # 256색까지 확장
        while len(new_palette) < 768:
            new_palette.extend([0, 0, 0])

        # 새 이미지 생성
        new_image = Image.new('P', image.size)
        new_image.putdata(new_pixels)
        new_image.putpalette(new_palette)

        print(f"      팔레트 압축 완료: 16색")

        return new_image

    def get_used_indices(self, image: Image.Image) -> Set[int]:
        """이미지에서 실제 사용된 색상 인덱스 반환"""

        if image.mode != 'P':
            return set()

        pixels = list(image.getdata())
        return set(pixels)

    def resize_with_padding(self, image: Image.Image, top: int, bottom: int, left: int, right: int) -> Image.Image:
        """C# Resize 함수 재현: 패딩 추가"""

        new_width = image.width + left + right
        new_height = image.height + top + bottom

        # 배경색은 이미지의 첫 번째 픽셀 색상 사용
        pixels = list(image.getdata())
        background_color = pixels[0] if pixels else 0

        new_image = Image.new('P', (new_width, new_height), background_color)

        # 팔레트 복사
        if image.getpalette():
            new_image.putpalette(image.getpalette())

        # 원본 이미지 붙여넣기
        new_image.paste(image, (left, top))

        return new_image

    def concat_horizontal(self, first: Image.Image, second: Image.Image) -> Image.Image:
        """C# Concat 함수 재현: 이미지 좌우 연결"""

        new_width = first.width + second.width
        new_height = max(first.height, second.height)

        # 배경색
        pixels = list(first.getdata())
        background_color = pixels[0] if pixels else 0

        new_image = Image.new('P', (new_width, new_height), background_color)

        # 팔레트 복사
        if first.getpalette():
            new_image.putpalette(first.getpalette())

        # 이미지들 붙여넣기
        new_image.paste(first, (0, 0))
        new_image.paste(second, (first.width, 0))

        return new_image

    def check_size_pokemon_format(self, image: Image.Image, filename: str = "",
                                  sprite_number: int = 2, is_diamond_pearl: bool = False) -> Image.Image:
        """C# CheckSize 함수 재현: 포켓몬 포맷에 맞는 크기 조정"""

        print(f"    크기 검사 및 조정: {image.size}")

        width, height = image.size

        # 64x64 → 80x80 (8픽셀 패딩)
        if width == 64 and height == 64:
            print(f"      64x64 → 80x80 (8픽셀 패딩)")
            image = self.resize_with_padding(image, 8, 8, 8, 8)
            width, height = 80, 80

        # 80x80 → 160x80 처리
        if width == 80 and height == 80:
            if sprite_number < 2 and is_diamond_pearl:
                # DP 백스프라이트: 세로 확장
                print(f"      80x80 → 80x160 (DP 백스프라이트)")
                image = self.resize_with_padding(image, 0, 80, 0, 0)
            else:
                # 일반적인 경우: 좌우 복사
                print(f"      80x80 → 160x80 (좌우 복사)")
                image = self.concat_horizontal(image, image)

        # 최종 크기 검증
        final_width, final_height = image.size
        print(f"      최종 크기: {final_width}x{final_height}")

        return image

    def alternate_palette_csharp_style(self, parent_image: Image.Image, child_image: Image.Image) -> List[
        Tuple[int, int, int]]:
        """C# AlternatePalette 함수 재현: 부모-자식 이미지 간 색상 매핑으로 새 팔레트 생성"""

        print(f"    AlternatePalette 매핑 생성 중...")

        # 부모 이미지 검증
        if parent_image.mode != 'P':
            print(f"      오류: 부모 이미지가 팔레트 모드가 아님 ({parent_image.mode})")
            return None

        # 자식 이미지를 8bpp 인덱스로 변환 (크기는 조정하지 않음)
        if child_image.mode != 'P':
            child_image = self.convert_to_8bpp_indexed_csharp_style(child_image)
            if child_image is None:
                print(f"      오류: 자식 이미지 8bpp 변환 실패")
                return None

        # 크기 일치 확인
        if parent_image.size != child_image.size:
            print(f"      경고: 크기 불일치 - 부모: {parent_image.size}, 자식: {child_image.size}")
            # 자식 이미지를 부모와 같은 크기로 조정
            child_image = child_image.resize(parent_image.size, Image.NEAREST)

        # 픽셀 데이터 추출
        parent_pixels = list(parent_image.getdata())
        child_pixels = list(child_image.getdata())

        if len(parent_pixels) != len(child_pixels):
            print(f"      오류: 픽셀 수 불일치")
            return None

        # 부모와 자식 팔레트 추출
        parent_palette = parent_image.getpalette()
        child_palette = child_image.getpalette()

        if not parent_palette or not child_palette:
            print(f"      오류: 팔레트 추출 실패")
            return None

        # C# AlternatePalette 로직 재현
        new_palette = [(0, 0, 0)] * 16  # 새로운 팔레트 초기화

        # 부모 팔레트의 각 인덱스에 대해 매핑 찾기
        for parent_idx in range(16):
            # 부모 이미지에서 이 인덱스가 사용되는 첫 번째 픽셀 찾기
            child_color_found = False

            for pixel_pos in range(len(parent_pixels)):
                if parent_pixels[pixel_pos] == parent_idx:
                    # 같은 위치의 자식 픽셀에서 색상 가져오기
                    child_idx = child_pixels[pixel_pos]

                    # 자식 팔레트에서 해당 색상 추출
                    if child_idx * 3 + 2 < len(child_palette):
                        r = child_palette[child_idx * 3]
                        g = child_palette[child_idx * 3 + 1]
                        b = child_palette[child_idx * 3 + 2]
                        new_palette[parent_idx] = (r, g, b)
                        child_color_found = True
                        break

            if not child_color_found:
                # 해당 인덱스가 사용되지 않으면 부모 색상 유지
                if parent_idx * 3 + 2 < len(parent_palette):
                    r = parent_palette[parent_idx * 3]
                    g = parent_palette[parent_idx * 3 + 1]
                    b = parent_palette[parent_idx * 3 + 2]
                    new_palette[parent_idx] = (r, g, b)
                else:
                    new_palette[parent_idx] = (0, 0, 0)

        print(f"      AlternatePalette 매핑 완료")

        # 매핑 결과 출력 (처음 몇 개만)
        for i in range(min(4, 16)):
            if parent_idx * 3 + 2 < len(parent_palette):
                parent_color = (
                    parent_palette[i * 3],
                    parent_palette[i * 3 + 1],
                    parent_palette[i * 3 + 2]
                )
                new_color = new_palette[i]
                print(f"        인덱스 {i}: {parent_color} → {new_color}")

        return new_palette

    def preprocess_for_pokemon_format(self, image_path: str, auto_color: bool = True,
                                          auto_convert: bool = True, allow_shrinking: bool = True,
        sprite_number: int = 2, is_diamond_pearl: bool = False) -> Image.Image:
        """포켓몬 포맷에 맞게 이미지 전처리 (C# CheckSize 전체 파이프라인 재현)"""

        print(f"  포켓몬 포맷 전처리 시작: {image_path}")

        # 1. 이미지 로드
        image = Image.open(image_path)
        print(f"    원본: {image.size}, {image.mode}")

        # 2. 8bpp 인덱스로 변환
        if image.mode != 'P':
            if auto_convert:
                image = self.convert_to_8bpp_indexed(image)
            else:
                raise ValueError(f"이미지가 8bpp 인덱스 포맷이 아닙니다: {image.mode}")

        # 3. 색상 표준화
        if auto_color:
            image = self.standardize_colors(image)

        # 4. 팔레트 크기 검증 및 압축
        palette_size = self.palette_size(image)
        print(f"    팔레트 크기: {palette_size}색")

        if palette_size > 16:
            if allow_shrinking:
                image = self.shrink_palette(image)
            else:
                print(f"      경고: 16색을 초과합니다 ({palette_size}색)")

        # 5. 크기 조정
        image = self.check_size_pokemon_format(image, image_path, sprite_number, is_diamond_pearl)

        print(f"    전처리 완료: {image.size}")
        return image


def preprocess_reference_image_for_pokemon(image_path: str, is_diamond_pearl: bool = False) -> Image.Image:
    """기준 이미지를 포켓몬 포맷에 맞게 전처리하는 헬퍼 함수"""

    handler = IndexedBitmapHandler()

    # 파일명에서 스프라이트 정보 추출
    filename = os.path.basename(image_path).lower()
    sprite_number = 2  # 기본값

    if 'back' in filename:
        if 'female' in filename or 'f' in filename:
            sprite_number = 0
        else:
            sprite_number = 1
    elif 'front' in filename:
        if 'female' in filename or 'f' in filename:
            sprite_number = 2
        else:
            sprite_number = 3

    return handler.preprocess_for_pokemon_format(
        image_path=image_path,
        auto_color=True,
        auto_convert=True,
        allow_shrinking=True,
        sprite_number=sprite_number,
        is_diamond_pearl=is_diamond_pearl
    )


# 테스트 함수
def test_preprocessing(image_path: str):
    """전처리 테스트"""

    print(f"=== 전처리 테스트: {image_path} ===")

    try:
        processed_image = preprocess_reference_image_for_pokemon(image_path)

        # 결과 저장
        output_path = image_path.replace('.png', '_preprocessed.png')
        processed_image.save(output_path)

        print(f"전처리 완료: {output_path}")
        print(f"최종 크기: {processed_image.size}")
        print(f"최종 모드: {processed_image.mode}")

        # 팔레트 정보
        palette = processed_image.getpalette()
        if palette:
            used_indices = set(processed_image.getdata())
            print(f"사용된 색상: {len(used_indices)}개")

        return True

    except Exception as e:
        print(f"전처리 실패: {e}")
        return False


if __name__ == "__main__":
    import os

    # 테스트 실행
    test_files = [
        "./input/001FFront.png",
        "./input/001MBack.png"
    ]

    for test_file in test_files:
        if os.path.exists(test_file):
            test_preprocessing(test_file)
        else:
            print(f"테스트 파일이 존재하지 않음: {test_file}")