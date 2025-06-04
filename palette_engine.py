"""
palette_engine.py - 포켓몬 스프라이트 팔레트 처리 핵심 엔진

이 모듈은 팔레트 분석, 색상 매핑, 전처리 등의 핵심 알고리즘만 포함합니다.
파일 처리나 워크플로우와 무관한 순수한 이미지 처리 로직만 담당합니다.

KEEP: 이 파일의 모든 함수는 매우 정교하므로 함부로 수정하지 말 것!
TODO: pokemon_sprite_converter.py에서 이 모듈의 함수들을 호출하게 될 예정
"""

from PIL import Image
import numpy as np
from collections import Counter
from indexed_bitmap_handler import preprocess_reference_image_for_pokemon


def rgb_to_hex(rgb):
    """RGB를 HEX로 변환

    KEEP: 디버깅 및 로깅용 유틸리티
    """
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


# =============================================================================
# 팔레트 분석 및 기준 선택
# KEEP: 이 섹션의 로직은 매우 정교하므로 수정하지 말고 그대로 유지
# =============================================================================

def extract_palette_from_original_image(image_path, max_colors=16):
    """원본 이미지에서 빠른 팔레트 추출 (전처리 없이)

    KEEP: 최적 기준 이미지 선택을 위한 핵심 로직

    Args:
        image_path: 이미지 파일 경로
        max_colors: 최대 색상 수 (기본 16)

    Returns:
        tuple: (palette_colors, used_indices) 또는 (None, None)
    """
    print(f"    빠른 팔레트 분석: {image_path.split('/')[-1]}")

    img = Image.open(image_path)

    # 인덱스 컬러로 변환 (빠른 분석용)
    if img.mode != 'P':
        img = img.convert('P', palette=Image.ADAPTIVE, colors=max_colors)

    # 팔레트 정보 추출
    palette = img.getpalette()
    if not palette:
        print("      경고: 팔레트가 없는 이미지")
        return None, None

    # 실제 사용된 인덱스 확인
    pixels = list(img.getdata())
    used_indices = set(pixels)
    max_used_index = max(used_indices) if used_indices else 0

    # RGB 값으로 변환
    palette_colors = []
    for i in range(min(max_used_index + 1, max_colors)):
        if i * 3 + 2 < len(palette):
            r, g, b = palette[i * 3:i * 3 + 3]
            palette_colors.append((r, g, b))
        else:
            palette_colors.append((0, 0, 0))

    print(f"      {len(palette_colors)}개 색상 발견")

    return palette_colors, used_indices


def find_optimal_reference(image_files):
    """원본 이미지들에서 빠른 팔레트 분석으로 최적 기준 선택

    KEEP: 이 알고리즘은 매우 정교함. 팔레트 호환성 기반 최적화

    Args:
        image_files: 이미지 파일 경로 리스트

    Returns:
        str: 최적 기준 이미지 경로 또는 None
    """
    print("  원본 이미지들의 빠른 팔레트 분석으로 기준 이미지 선택 중...")

    image_palettes = {}

    # 각 이미지의 팔레트 빠르게 추출
    for image_path in image_files:
        palette_colors, used_indices = extract_palette_from_original_image(image_path)
        if palette_colors:
            image_palettes[image_path] = palette_colors
        else:
            print(f"      팔레트 추출 실패: {image_path.split('/')[-1]}")

    if not image_palettes:
        print("    분석 가능한 이미지가 없습니다")
        return None

    # 팔레트 호환성 기반으로 최적 기준 선택
    candidate_scores = []

    for ref_path, ref_palette in image_palettes.items():
        total_score = 0

        for target_path, target_palette in image_palettes.items():
            if ref_path == target_path:
                continue

            # 팔레트 간 호환성 점수 계산
            mapping_distance = 0
            for target_color in target_palette:
                min_distance = min(
                    sum((a - b) ** 2 for a, b in zip(target_color, ref_color)) ** 0.5
                    for ref_color in ref_palette
                )
                mapping_distance += min_distance

            total_score += mapping_distance

        candidate_scores.append((ref_path, total_score))

    # 점수가 가장 낮은 (호환성이 가장 좋은) 이미지 선택
    best_path, best_score = min(candidate_scores, key=lambda x: x[1])

    print(f"    ✅ 선택된 기준 이미지: {best_path.split('/')[-1]} (호환성 점수: {best_score:.1f})")

    return best_path


def extract_palette_from_processed_image(image: Image.Image, max_colors=16):
    """전처리된 이미지에서 팔레트 추출

    KEEP: 전처리 후 팔레트 정보 추출용

    Args:
        image: PIL Image 객체 (팔레트 모드)
        max_colors: 최대 색상 수

    Returns:
        tuple: (palette_colors, used_indices) 또는 (None, None)
    """
    if image.mode != 'P':
        raise ValueError("이미지가 팔레트 모드가 아닙니다")

    # 팔레트 정보 추출
    palette = image.getpalette()
    if not palette:
        return None, None

    # 실제 사용된 인덱스 확인
    pixels = list(image.getdata())
    used_indices = set(pixels)
    max_used_index = max(used_indices) if used_indices else 0

    # RGB 값으로 변환
    palette_colors = []
    for i in range(min(max_used_index + 1, max_colors)):
        if i * 3 + 2 < len(palette):
            r, g, b = palette[i * 3:i * 3 + 3]
            palette_colors.append((r, g, b))
        else:
            palette_colors.append((0, 0, 0))

    return palette_colors, used_indices


def preprocess_reference_only(reference_path, is_diamond_pearl=False):
    """선택된 기준 이미지만 포켓몬 포맷으로 전처리

    KEEP: indexed_bitmap_handler의 전처리 파이프라인 활용

    Args:
        reference_path: 기준 이미지 파일 경로
        is_diamond_pearl: DP 포맷 여부

    Returns:
        tuple: (processed_image, reference_palette, reference_used_indices) 또는 (None, None, None)
    """
    print(f"  기준 이미지를 포켓몬 포맷으로 전처리 중: {reference_path.split('/')[-1]}")

    try:
        # 포켓몬 포맷으로 전처리
        processed_image = preprocess_reference_image_for_pokemon(reference_path, is_diamond_pearl)

        # 전처리된 이미지의 팔레트 추출
        reference_palette, reference_used_indices = extract_palette_from_processed_image(processed_image)

        if not reference_palette:
            print(f"    전처리 실패: 팔레트 추출 불가")
            return None, None, None

        print(f"    ✅ 기준 이미지 전처리 완료: {len(reference_palette)}색")

        return processed_image, reference_palette, reference_used_indices

    except Exception as e:
        print(f"    전처리 실패: {e}")
        return None, None, None


# =============================================================================
# C# AlternatePalette 로직 재현 - 핵심 색상 매핑
# KEEP: 이 섹션은 C# 원본 코드를 정확히 재현한 핵심 기능. 절대 수정하지 말 것!
# =============================================================================

def extract_color_mapping_between_processed_images(reference_processed, shiny_processed):
    """두 전처리된 이미지 간의 색상 매핑 추출 (C# AlternatePalette 로직)

    KEEP: 이 함수는 C# 원본 코드를 정확히 재현한 핵심 로직
    절대 수정하지 말 것!

    Args:
        reference_processed: 기준 이미지 (PIL Image, 팔레트 모드)
        shiny_processed: Shiny 이미지 (PIL Image, 팔레트 모드)

    Returns:
        dict: {reference_color: shiny_color} 매핑 또는 None
    """
    print(f"      전처리된 이미지 간 색상 매핑 추출")

    try:
        # 두 이미지 모두 팔레트 모드여야 함
        if reference_processed.mode != 'P' or shiny_processed.mode != 'P':
            print(f"        오류: 이미지가 팔레트 모드가 아님")
            return None

        # 크기가 같아야 함
        if reference_processed.size != shiny_processed.size:
            print(f"        오류: 이미지 크기가 다름")
            return None

        # 픽셀 데이터 및 팔레트 추출
        ref_pixels = list(reference_processed.getdata())
        shiny_pixels = list(shiny_processed.getdata())
        ref_palette = reference_processed.getpalette()
        shiny_palette = shiny_processed.getpalette()

        if not ref_palette or not shiny_palette:
            print(f"        오류: 팔레트 추출 실패")
            return None

        # 색상 매핑 관계 추출 (C# AlternatePalette 로직과 동일)
        color_mapping = {}  # reference_color -> shiny_color

        # 기준 이미지의 각 팔레트 인덱스에 대해 Shiny 색상 찾기
        for ref_idx in range(16):  # 16색만 처리
            if ref_idx * 3 + 2 >= len(ref_palette):
                continue

            ref_color = (
                ref_palette[ref_idx * 3],
                ref_palette[ref_idx * 3 + 1],
                ref_palette[ref_idx * 3 + 2]
            )

            # 이 인덱스가 사용되는 첫 번째 픽셀 위치 찾기
            for pixel_pos in range(len(ref_pixels)):
                if ref_pixels[pixel_pos] == ref_idx:
                    # 같은 위치의 Shiny 픽셀에서 색상 가져오기
                    shiny_idx = shiny_pixels[pixel_pos]

                    if shiny_idx * 3 + 2 < len(shiny_palette):
                        shiny_color = (
                            shiny_palette[shiny_idx * 3],
                            shiny_palette[shiny_idx * 3 + 1],
                            shiny_palette[shiny_idx * 3 + 2]
                        )
                        color_mapping[ref_color] = shiny_color
                        break

        print(f"        색상 매핑 {len(color_mapping)}개 추출")

        # 매핑 예시 출력
        for i, (ref_color, shiny_color) in enumerate(list(color_mapping.items())[:3]):
            ref_hex = rgb_to_hex(ref_color)
            shiny_hex = rgb_to_hex(shiny_color)
            print(f"          {ref_hex} → {shiny_hex}")

        return color_mapping

    except Exception as e:
        print(f"        색상 매핑 추출 실패: {e}")
        return None


def apply_color_mapping_to_processed_image(processed_reference, color_mapping):
    """전처리된 기준 이미지에 색상 매핑을 적용하여 Shiny 팔레트 생성

    KEEP: 색상 매핑을 팔레트에 적용하는 핵심 로직

    Args:
        processed_reference: 전처리된 기준 이미지 (PIL Image)
        color_mapping: 색상 매핑 딕셔너리

    Returns:
        PIL Image: 새로운 Shiny 이미지 또는 None
    """
    print(f"      전처리된 이미지에 색상 매핑 적용 중...")

    if processed_reference.mode != 'P':
        print(f"        오류: 전처리된 이미지가 팔레트 모드가 아님")
        return None

    # 전처리된 기준 이미지의 팔레트 추출
    ref_palette = processed_reference.getpalette()
    if not ref_palette:
        print(f"        오류: 팔레트 추출 실패")
        return None

    # 새로운 Shiny 팔레트 생성
    new_shiny_palette = []

    for i in range(16):  # 16색만 처리
        if i * 3 + 2 < len(ref_palette):
            ref_color = (
                ref_palette[i * 3],
                ref_palette[i * 3 + 1],
                ref_palette[i * 3 + 2]
            )

            # 색상 매핑에서 대응하는 Shiny 색상 찾기
            if ref_color in color_mapping:
                shiny_color = color_mapping[ref_color]
                new_shiny_palette.append(shiny_color)
            else:
                # 매핑되지 않은 색상은 가장 가까운 매핑 찾기
                min_distance = float('inf')
                best_shiny_color = ref_color  # 기본값

                for mapped_ref_color, mapped_shiny_color in color_mapping.items():
                    distance = sum((a - b) ** 2 for a, b in zip(ref_color, mapped_ref_color))
                    if distance < min_distance:
                        min_distance = distance
                        best_shiny_color = mapped_shiny_color

                new_shiny_palette.append(best_shiny_color)
        else:
            new_shiny_palette.append((0, 0, 0))

    # 새로운 Shiny 이미지 생성
    new_shiny_image = Image.new('P', processed_reference.size)

    # 기준 이미지와 동일한 픽셀 구조 복사
    reference_pixels = list(processed_reference.getdata())
    new_shiny_image.putdata(reference_pixels)

    # Shiny 팔레트 적용
    flat_palette = []
    for color in new_shiny_palette:
        flat_palette.extend(color)

    # 256색까지 확장
    while len(flat_palette) < 768:
        flat_palette.extend([0, 0, 0])

    new_shiny_image.putpalette(flat_palette)

    print(f"        ✅ Shiny 팔레트 적용 완료")

    return new_shiny_image


# =============================================================================
# 팔레트 매칭 및 통일
# KEEP: 팔레트 통일 핵심 로직
# =============================================================================

def palette_match_to_reference(reference_palette, target_image_path, is_diamond_pearl=False):
    """대상 이미지를 기준 팔레트에 맞춰 변환

    KEEP: 팔레트 매칭 알고리즘은 정교하므로 유지

    Args:
        reference_palette: 기준 팔레트 색상 리스트
        target_image_path: 대상 이미지 파일 경로
        is_diamond_pearl: DP 포맷 여부

    Returns:
        PIL Image: 매칭된 이미지 또는 None
    """
    print(f"      팔레트 매칭: {target_image_path.split('/')[-1]}")

    # 1. 대상 이미지도 포켓몬 포맷으로 전처리
    target_processed = preprocess_reference_image_for_pokemon(target_image_path, is_diamond_pearl)

    # 2. 전처리된 대상 이미지의 팔레트 추출
    target_palette, target_used_indices = extract_palette_from_processed_image(target_processed)

    if not target_palette:
        print(f"        오류: 대상 이미지 팔레트 추출 실패")
        return None

    print(f"        대상 팔레트: {len(target_palette)}색")

    # 3. 팔레트 매칭 수행
    color_mapping = {}  # target_index -> reference_index
    new_palette = [(0, 0, 0)] * 16

    # 기준 팔레트를 새 팔레트에 복사
    for i, color in enumerate(reference_palette):
        if i < 16:
            new_palette[i] = color

    # 대상 이미지의 각 색상을 기준 팔레트에서 찾아 매핑
    for target_idx in target_used_indices:
        if target_idx >= len(target_palette):
            continue

        target_color = target_palette[target_idx]

        # 기준 팔레트에서 가장 가까운 색상 찾기
        best_match_idx = None
        min_distance = float('inf')

        for ref_idx, ref_color in enumerate(reference_palette):
            if ref_idx >= 16:
                break

            distance = sum((a - b) ** 2 for a, b in zip(target_color, ref_color)) ** 0.5

            if distance < min_distance:
                min_distance = distance
                best_match_idx = ref_idx

        if best_match_idx is not None:
            color_mapping[target_idx] = best_match_idx

    # 4. 픽셀 데이터 재매핑
    pixels = list(target_processed.getdata())
    new_pixels = [color_mapping.get(pixel, 0) for pixel in pixels]

    # 5. 새로운 이미지 생성
    new_image = Image.new('P', target_processed.size)
    new_image.putdata(new_pixels)

    # 6. 통일된 팔레트 적용
    flat_palette = []
    for color in new_palette:
        flat_palette.extend(color)

    while len(flat_palette) < 768:
        flat_palette.extend([0, 0, 0])

    new_image.putpalette(flat_palette)

    print(f"        팔레트 매칭 완료!")

    return new_image


def match_others_to_reference(reference_palette, other_image_files, reference_path, is_diamond_pearl=False):
    """다른 이미지들을 전처리된 기준 팔레트에 맞춤

    KEEP: 그룹 내 모든 이미지의 팔레트 통일 로직

    Args:
        reference_palette: 기준 팔레트 색상 리스트
        other_image_files: 다른 이미지 파일 경로 리스트
        reference_path: 기준 이미지 파일 경로 (제외용)
        is_diamond_pearl: DP 포맷 여부

    Returns:
        dict: {image_path: matched_image} 딕셔너리
    """
    print(f"  다른 이미지들을 기준 팔레트에 맞춰 변환 중...")

    processed_others = {}

    for image_path in other_image_files:
        if image_path == reference_path:
            continue  # 기준 이미지는 건너뛰기

        filename = image_path.split('/')[-1]
        print(f"    변환 중: {filename}")

        try:
            # 대상 이미지를 기준 팔레트에 맞춰 변환
            matched_image = palette_match_to_reference(reference_palette, image_path, is_diamond_pearl)

            if matched_image:
                processed_others[image_path] = matched_image
                print(f"      ✅ 변환 완료")
            else:
                print(f"      ❌ 변환 실패")

        except Exception as e:
            print(f"      변환 실패: {e}")
            continue

    return processed_others


# =============================================================================
# 검증 및 품질 관리
# KEEP: 검증 로직은 품질 관리에 중요
# =============================================================================

def perform_verification(processed_images, processed_shinies, reference_palette):
    """팔레트 통일 및 포맷 호환성 검증

    KEEP: 검증 로직은 품질 관리에 중요

    Args:
        processed_images: 처리된 일반 이미지 딕셔너리
        processed_shinies: 처리된 Shiny 이미지 딕셔너리
        reference_palette: 기준 팔레트

    Returns:
        dict: 검증 결과 {'unified': bool, 'compatible': bool}
    """
    print(f"\n  📋 검증 단계")

    # 팔레트 통일 검증
    reference_palette_flat = []
    for color in reference_palette:
        reference_palette_flat.extend(color)

    all_unified = True
    all_images = {**processed_images, **processed_shinies}

    for filename, img in all_images.items():
        if img.mode == 'P':
            img_palette = img.getpalette()
            if img_palette and img_palette[:48] == reference_palette_flat[:48]:
                print(f"    ✅ {filename}: 팔레트 완전 일치")
            else:
                print(f"    ❌ {filename}: 팔레트 불일치")
                all_unified = False
        else:
            print(f"    ⚠️  {filename}: 팔레트 모드 아님")
            all_unified = False

    # 포켓몬 포맷 호환성 검증
    format_compatible = True

    for filename, img in all_images.items():
        # 크기 검증
        if img.size != (160, 80):
            print(f"    ❌ {filename}: 크기 불일치 {img.size}")
            format_compatible = False

        # 팔레트 모드 및 색상 수 검증
        if img.mode != 'P':
            print(f"    ❌ {filename}: 팔레트 모드 아님")
            format_compatible = False
        else:
            used_colors = len(set(img.getdata()))
            if used_colors > 16:
                print(f"    ❌ {filename}: 색상 수 초과 ({used_colors}색)")
                format_compatible = False

    print(f"  - 팔레트 통일: {'✅' if all_unified else '❌'}")
    print(f"  - 포맷 호환성: {'✅' if format_compatible else '❌'}")

    return {
        'unified': all_unified,
        'compatible': format_compatible
    }


# =============================================================================
# 통합 API 함수들 (향후 pokemon_sprite_converter.py에서 호출용)
# TODO: 이 섹션은 향후 확장 예정
# =============================================================================

def process_pokemon_palette_unification(pokemon_sprites_data, is_diamond_pearl=False):
    """포켓몬 하나의 모든 스프라이트 팔레트 통일

    TODO: pokemon_sprite_converter.py에서 호출할 통합 API

    Args:
        pokemon_sprites_data: {sprite_type: image_data} 딕셔너리
        is_diamond_pearl: DP 포맷 여부

    Returns:
        dict: {sprite_type: (processed_sprite_data, palette_data)}
    """
    # TODO: 구현 필요
    # 1. 기준 이미지 선택
    # 2. 모든 스프라이트 전처리
    # 3. 팔레트 통일
    # 4. Shiny 색상 매핑
    # 5. 검증
    pass


def process_single_sprite_type(normal_sprite_data, shiny_sprite_data=None, is_diamond_pearl=False):
    """단일 스프라이트 타입의 팔레트 통일

    TODO: 간단한 Normal-Shiny 쌍 처리용 API

    Args:
        normal_sprite_data: 일반 스프라이트 데이터
        shiny_sprite_data: Shiny 스프라이트 데이터 (선택사항)
        is_diamond_pearl: DP 포맷 여부

    Returns:
        tuple: (unified_normal_data, unified_shiny_data, unified_palette)
    """
    # TODO: 구현 필요
    pass