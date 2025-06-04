import os
import re
from PIL import Image
import numpy as np
from collections import Counter, defaultdict
from indexed_bitmap_handler import IndexedBitmapHandler, preprocess_reference_image_for_pokemon


# =============================================================================
# 파일 처리 유틸리티 함수들
# =============================================================================

def rgb_to_hex(rgb):
    """RGB를 HEX로 변환"""
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


def extract_number_from_filename(filename):
    """파일명에서 숫자 추출"""
    name_without_ext = os.path.splitext(filename)[0]
    match = re.match(r'^(\d+)', name_without_ext)
    if match:
        return int(match.group(1))
    return None


def generate_pokemon_filename(original_filename, suffix=""):
    """포켓몬 파일명 형식으로 변환: (male/female)_(back/front)_(normal/shiny).png"""
    _, ext = os.path.splitext(original_filename)
    if not ext:
        ext = '.png'

    shiny_status = 'shiny' if 'Shiny' in original_filename else 'normal'
    back_front = 'back' if 'Back' in original_filename else 'front'

    gender = 'male'
    if 'FBack' in original_filename or 'FFront' in original_filename:
        gender = 'female'
    if suffix:
        return f"{gender}_{back_front}_{shiny_status}_{suffix}{ext}"
    else:
        return f"{gender}_{back_front}_{shiny_status}{ext}"



def create_pokemon_folder(output_folder, dex_number):
    """포켓몬 폴더 생성"""
    folder_name = f"pokemon_{dex_number:03d}"
    pokemon_folder = os.path.join(output_folder, folder_name)

    if not os.path.exists(pokemon_folder):
        os.makedirs(pokemon_folder)
        print(f"  폴더 생성: {folder_name}")

    return pokemon_folder


def group_files_by_number(image_files):
    """파일들을 숫자별로 그룹화"""
    groups = defaultdict(list)
    shiny_files = defaultdict(list)

    for file_path in image_files:
        filename = os.path.basename(file_path)
        number = extract_number_from_filename(filename)

        if number is not None:
            if 'Shiny' in filename:
                shiny_files[number].append(file_path)
            else:
                groups[number].append(file_path)
        else:
            print(f"경고: 파일명에서 숫자를 찾을 수 없습니다: {filename}")

    return groups, shiny_files


def save_preprocessed_sprite(image, output_path):
    """전처리 완료된 이미지를 PNG로 저장"""
    # 최종 검증
    if image.size != (160, 80):
        print(f"    경고: 예상과 다른 크기 {image.size}")

    if image.mode != 'P':
        print(f"    경고: 팔레트 모드가 아님 {image.mode}")

    # PNG 저장
    image.save(output_path, "PNG", optimize=False)
    print(f"    저장 완료: {os.path.basename(output_path)}")


def save_original_image(shiny_file, pokemon_folder):
    """원본 Shiny 이미지를 저장"""
    original_filename = os.path.basename(shiny_file)
    new_filename = generate_pokemon_filename(original_filename, "original")
    output_path = os.path.join(pokemon_folder, new_filename)

    # 원본 이미지 복사
    original_image = Image.open(shiny_file)
    original_image.save(output_path, "PNG")

    return output_path, new_filename



# =============================================================================
# 팔레트 분석 및 기준 선택
# =============================================================================

def extract_palette_from_original_image(image_path, max_colors=16):
    """원본 이미지에서 빠른 팔레트 추출 (전처리 없이)"""
    print(f"    빠른 팔레트 분석: {os.path.basename(image_path)}")

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
    """원본 이미지들에서 빠른 팔레트 분석으로 최적 기준 선택"""
    print("  원본 이미지들의 빠른 팔레트 분석으로 기준 이미지 선택 중...")

    image_palettes = {}

    # 각 이미지의 팔레트 빠르게 추출
    for image_path in image_files:
        palette_colors, used_indices = extract_palette_from_original_image(image_path)
        if palette_colors:
            image_palettes[image_path] = palette_colors
        else:
            print(f"      팔레트 추출 실패: {os.path.basename(image_path)}")

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

    print(f"    ✅ 선택된 기준 이미지: {os.path.basename(best_path)} (호환성 점수: {best_score:.1f})")

    return best_path


# =============================================================================
# 기준 이미지 전처리
# =============================================================================

def extract_palette_from_processed_image(image: Image.Image, max_colors=16):
    """전처리된 이미지에서 팔레트 추출"""
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
    """선택된 기준 이미지만 포켓몬 포맷으로 전처리"""
    print(f"  기준 이미지를 포켓몬 포맷으로 전처리 중: {os.path.basename(reference_path)}")

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
# 개선된 Shiny 이미지 처리 (전처리 포함)
# =============================================================================

def extract_color_mapping_between_processed_images(reference_processed, shiny_processed):
    """두 전처리된 이미지 간의 색상 매핑 추출 (C# AlternatePalette 로직)"""
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
    """전처리된 기준 이미지에 색상 매핑을 적용하여 Shiny 팔레트 생성"""
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


def process_shiny_files_with_preprocessing(shiny_files_for_group, reference_path, processed_reference,
                                          pokemon_folder, is_diamond_pearl=False):
    """Shiny 파일들을 3단계로 처리하고 모두 저장"""
    if not shiny_files_for_group:
        return {}

    print(f"\n  🌟 Shiny 이미지 3단계 처리 및 저장 중...")

    processed_shinies = {}

    for shiny_file in shiny_files_for_group:
        shiny_filename = os.path.basename(shiny_file)
        print(f"    처리 중: {shiny_filename}")

        try:
            # === 1단계: 원본 이미지 저장 ===
            print(f"      1단계: 원본 이미지 저장")
            original_output_path, original_filename = save_original_image(shiny_file, pokemon_folder)
            print(f"        ✅ 원본 저장: {original_filename}")

            # === 2단계: 전처리된 이미지 저장 ===
            print(f"      2단계: 포켓몬 포맷 전처리 및 저장")
            shiny_processed = preprocess_reference_image_for_pokemon(shiny_file, is_diamond_pearl)

            if not shiny_processed:
                print(f"        ❌ 전처리 실패")
                continue

            # 전처리된 버전 저장
            preprocessed_filename = generate_pokemon_filename(shiny_filename, "preprocessed")
            preprocessed_output_path = os.path.join(pokemon_folder, preprocessed_filename)
            save_preprocessed_sprite(shiny_processed, preprocessed_output_path)

            # === 3단계: 색상 매핑 추출 ===
            print(f"      3단계: 색상 매핑 추출")
            color_mapping = extract_color_mapping_between_processed_images(processed_reference, shiny_processed)

            if not color_mapping:
                print(f"        ⚠️  색상 매핑 추출 실패")
                # 매핑 실패 시에는 전처리된 이미지를 최종 버전으로도 저장
                final_filename = generate_pokemon_filename(shiny_filename)
                final_output_path = os.path.join(pokemon_folder, final_filename)
                save_preprocessed_sprite(shiny_processed, final_output_path, "최종 버전 (매핑 실패)")
                processed_shinies[final_filename] = shiny_processed

                print(f"      📁 저장된 파일들:")
                print(f"        - {original_filename} (원본)")
                print(f"        - {preprocessed_filename} (전처리)")
                print(f"        - {final_filename} (최종 = 전처리)")
                continue

            # === 4단계: 매핑 적용하여 최종 Shiny 생성 및 저장 ===
            print(f"      4단계: 매핑 적용하여 최종 Shiny 생성")
            final_shiny = apply_color_mapping_to_processed_image(processed_reference, color_mapping)

            if final_shiny:
                # 최종 매핑 적용 버전 저장
                final_filename = generate_pokemon_filename(shiny_filename)
                final_output_path = os.path.join(pokemon_folder, final_filename)
                save_preprocessed_sprite(final_shiny, final_output_path, "최종 버전 (매핑 적용)")
                processed_shinies[final_filename] = final_shiny

                print(f"      📁 저장된 파일들:")
                print(f"        - {original_filename} (원본)")
                print(f"        - {preprocessed_filename} (전처리)")
                print(f"        - {final_filename} (최종 매핑)")
                print(f"      ✅ {shiny_filename} 3단계 처리 완료!")
            else:
                print(f"        ❌ 매핑 적용 실패, 전처리 버전을 최종으로 사용")
                # 매핑 적용 실패 시 전처리된 이미지를 최종 버전으로 저장
                final_filename = generate_pokemon_filename(shiny_filename)
                final_output_path = os.path.join(pokemon_folder, final_filename)
                save_preprocessed_sprite(shiny_processed, final_output_path, "최종 버전 (매핑 실패)")
                processed_shinies[final_filename] = shiny_processed

                print(f"      📁 저장된 파일들:")
                print(f"        - {original_filename} (원본)")
                print(f"        - {preprocessed_filename} (전처리)")
                print(f"        - {final_filename} (최종 = 전처리)")

        except Exception as e:
            print(f"      ❌ {shiny_filename} 처리 실패: {e}")
            continue

    return processed_shinies

# =============================================================================
# 일반 이미지 팔레트 매칭
# =============================================================================

def palette_match_to_reference(reference_palette, target_image_path, is_diamond_pearl=False):
    """대상 이미지를 기준 팔레트에 맞춰 변환"""
    print(f"      팔레트 매칭: {os.path.basename(target_image_path)}")

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
    """다른 이미지들을 전처리된 기준 팔레트에 맞춤"""
    print(f"  다른 이미지들을 기준 팔레트에 맞춰 변환 중...")

    processed_others = {}

    for image_path in other_image_files:
        if image_path == reference_path:
            continue  # 기준 이미지는 건너뛰기

        filename = os.path.basename(image_path)
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


def find_matching_normal_for_shiny(shiny_file, processed_images):
    """특정 Shiny 이미지에 대응하는 일반 이미지 찾기"""
    shiny_filename = os.path.basename(shiny_file)
    shiny_gender, shiny_direction, _ = parse_sprite_info(shiny_filename)

    target_pattern = f"{shiny_gender}_{shiny_direction}_normal.png"

    for filename, image in processed_images.items():
        if filename == target_pattern:
            print(f"        ✅ 매칭 대상: {filename}")
            return image, filename

    print(f"        ⚠️ 매칭되는 일반 이미지 없음: {target_pattern}")
    return None, None


def filter_matching_shiny_files(shiny_files_for_group, reference_path):
    """기준 이미지와 같은 성별의 Shiny 파일들만 필터링"""
    reference_filename = os.path.basename(reference_path)
    ref_gender, ref_direction, _ = parse_sprite_info(reference_filename)

    print(f"    기준 이미지 정보: {ref_gender} {ref_direction}")

    matching_shinies = []
    for shiny_file in shiny_files_for_group:
        shiny_filename = os.path.basename(shiny_file)
        shiny_gender, shiny_direction, is_shiny = parse_sprite_info(shiny_filename)

        if shiny_gender == ref_gender:  # 같은 성별만
            matching_shinies.append(shiny_file)
            print(f"      ✅ 매칭: {shiny_filename} ({shiny_gender} {shiny_direction})")
        else:
            print(f"      ❌ 제외: {shiny_filename} ({shiny_gender} {shiny_direction})")

    return matching_shinies


def parse_sprite_info(filename):
    """파일명에서 성별과 방향 정보 추출"""
    is_female = 'FBack' in filename or 'FFront' in filename or 'FShiny' in filename
    is_back = 'Back' in filename
    is_shiny = 'Shiny' in filename

    gender = 'female' if is_female else 'male'
    direction = 'back' if is_back else 'front'

    return gender, direction, is_shiny


def process_single_shiny_file(shiny_file, matching_normal_image, pokemon_folder, is_diamond_pearl):
    """단일 Shiny 파일을 3단계로 처리"""
    shiny_filename = os.path.basename(shiny_file)
    print(f"    처리 중: {shiny_filename}")

    try:

        # 2단계: 전처리
        shiny_processed = preprocess_reference_image_for_pokemon(shiny_file, is_diamond_pearl)
        preprocessed_filename = generate_pokemon_filename(shiny_filename, "preprocessed")
        preprocessed_output_path = os.path.join(pokemon_folder, preprocessed_filename)

        # 3단계: 색상 매핑 및 최종 생성
        color_mapping = extract_color_mapping_between_processed_images(matching_normal_image, shiny_processed)

        if color_mapping:
            final_shiny = apply_color_mapping_to_processed_image(matching_normal_image, color_mapping)
            final_filename = generate_pokemon_filename(shiny_filename)
            final_output_path = os.path.join(pokemon_folder, final_filename)
            save_preprocessed_sprite(final_shiny, final_output_path)

            return {final_filename: final_shiny}

    except Exception as e:
        print(f"      ❌ 처리 실패: {e}")

    return {}


# =============================================================================
# 그룹 처리 메인 함수
# =============================================================================

def process_group(group_number, group_files, shiny_files_for_group,
                  output_folder, is_diamond_pearl=False):
    """그룹 처리"""

    print(f"\n{'=' * 70}")
    print(f"그룹 {group_number} 처리 중 ({len(group_files)}개 파일)")
    if shiny_files_for_group:
        print(f"+ Shiny 파일 {len(shiny_files_for_group)}개")
    print(f"{'=' * 70}")

    # 포켓몬 폴더 생성
    pokemon_folder = create_pokemon_folder(output_folder, group_number)

    # 단일 파일 처리
    if len(group_files) == 1:
        return process_single_file(group_files[0], shiny_files_for_group, pokemon_folder, is_diamond_pearl)

    # 멀티 파일 처리
    return process_multiple_files(group_number, group_files, shiny_files_for_group, pokemon_folder, is_diamond_pearl)


def process_single_file(file_path, shiny_files_for_group, pokemon_folder, is_diamond_pearl):
    """단일 파일 처리"""
    print("  단일 파일 처리")

    filename = os.path.basename(file_path)
    new_filename = generate_pokemon_filename(filename)
    output_path = os.path.join(pokemon_folder, new_filename)

    # 포켓몬 포맷으로 전처리
    processed_image = preprocess_reference_image_for_pokemon(file_path, is_diamond_pearl)
    save_preprocessed_sprite(processed_image, output_path)

    print(f"  ✅ 단일 파일 처리 완료: {new_filename}")

    # Shiny 파일 처리 (전처리 포함)
    if shiny_files_for_group:
        process_shiny_files_with_preprocessing(shiny_files_for_group, file_path, processed_image, pokemon_folder,
                                               is_diamond_pearl)


def process_multiple_files(group_number, group_files, shiny_files_for_group, pokemon_folder, is_diamond_pearl):
    """멀티 파일 처리"""
    print("  멀티 파일 처리")

    # 1단계: 기준 이미지 선택
    reference_path = find_optimal_reference(group_files)
    if not reference_path:
        print("  기준 이미지를 선택할 수 없습니다.")
        return

    print(f"  ✅ 기준 이미지 선택: {os.path.basename(reference_path)}")

    # 2단계: 기준 이미지 전처리
    reference_image, reference_palette, reference_used_indices = preprocess_reference_only(
        reference_path, is_diamond_pearl
    )

    if not reference_palette:
        print("  기준 이미지 전처리에 실패했습니다.")
        return

    # 3단계: 기준 이미지 저장
    reference_filename = os.path.basename(reference_path)
    reference_new_filename = generate_pokemon_filename(reference_filename)
    reference_output_path = os.path.join(pokemon_folder, reference_new_filename)
    save_preprocessed_sprite(reference_image, reference_output_path)
    print(f"  ✅ 기준 이미지 저장: {reference_new_filename}")

    # 4단계: 기준 이미지와 같은 성별의 Shiny만 필터링
    if shiny_files_for_group:
        matching_shiny_files = filter_matching_shiny_files(shiny_files_for_group, reference_path)
        print(f"  ✅ 매칭되는 Shiny 파일: {len(matching_shiny_files)}개")
    else:
        matching_shiny_files = []

    # 5단계: 다른 일반 이미지들 처리
    processed_others = match_others_to_reference(
        reference_palette, group_files, reference_path, is_diamond_pearl
    )

    # 6단계: 다른 이미지들 저장
    processed_images = {reference_new_filename: reference_image}

    for image_path, matched_image in processed_others.items():
        filename = os.path.basename(image_path)
        new_filename = generate_pokemon_filename(filename)
        output_path = os.path.join(pokemon_folder, new_filename)

        save_preprocessed_sprite(matched_image, output_path)
        processed_images[new_filename] = matched_image
        print(f"  ✅ 저장 완료: {new_filename}")

    # 6단계: 필터링된 Shiny 파일들 처리
    processed_shinies = {}
    if matching_shiny_files:
        for shiny_file in matching_shiny_files:
            # 각 Shiny마다 개별적으로 매칭할 일반 이미지 찾기
            matching_normal, matching_filename = find_matching_normal_for_shiny(shiny_file, processed_images)

            if matching_normal:
                # 3단계 처리 (원본, 전처리, 매핑)
                shiny_result = process_single_shiny_file(
                    shiny_file, matching_normal, pokemon_folder, is_diamond_pearl
                )
                if shiny_result:
                    processed_shinies.update(shiny_result)

    # 7단계: 검증
    perform_verification(group_number, processed_images, processed_shinies, reference_palette)


def perform_verification(group_number, processed_images, processed_shinies, reference_palette):
    """팔레트 통일 및 포맷 호환성 검증"""
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

    # 결과 출력
    print(f"\n  그룹 {group_number} 처리 완료!")
    print(f"  - 일반 이미지: {len(processed_images)}개")
    print(f"  - Shiny 이미지: {len(processed_shinies)}개")
    print(f"  - 팔레트 통일: {'✅' if all_unified else '❌'}")
    print(f"  - 포맷 호환성: {'✅' if format_compatible else '❌'}")


# =============================================================================
# 메인 함수
# =============================================================================

def main():
    """메인 실행 함수"""
    print("=== 개선된 포켓몬 포맷 전처리 + 팔레트 구조 통일 도구 ===")
    print("Shiny 이미지도 완전 전처리 + 기준 선택 → 전처리 → 매핑 → 통일\n")

    # 설정
    input_folder = "./input"
    output_folder = "./output"
    is_diamond_pearl = False  # True로 설정하면 DP 포맷 사용

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    print(f"입력 폴더: {input_folder}")
    print(f"출력 폴더: {output_folder}")
    print(f"포맷: {'Diamond/Pearl' if is_diamond_pearl else 'Platinum'}")

    # 이미지 파일 찾기
    image_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.gif']
    image_files = []

    for file in os.listdir(input_folder):
        if any(file.lower().endswith(ext) for ext in image_extensions):
            image_files.append(os.path.join(input_folder, file))

    if not image_files:
        print("이미지 파일을 찾을 수 없습니다.")
        return

    print(f"\n{len(image_files)}개의 이미지를 발견했습니다.")

    # 파일들을 숫자별로 그룹화
    groups, shiny_files = group_files_by_number(image_files)

    if not groups and not shiny_files:
        print("그룹화할 수 있는 파일이 없습니다.")
        return

    print(f"\n{len(groups)}개의 일반 그룹과 {len(shiny_files)}개의 Shiny 그룹으로 분류되었습니다.")

    # 각 그룹별로 개선된 처리
    total_processed = 0
    successful_groups = 0
    all_groups = set(groups.keys()) | set(shiny_files.keys())

    for group_num in sorted(all_groups):
        group_files = groups.get(group_num, [])
        shiny_files_for_group = shiny_files.get(group_num, [])

        try:
            process_group(
                group_num, group_files, shiny_files_for_group,
                output_folder, is_diamond_pearl
            )
            successful_groups += 1
            total_processed += len(group_files) + len(shiny_files_for_group)
        except Exception as e:
            print(f"\n❌ 그룹 {group_num} 처리 실패: {e}")

    print(f"\n{'=' * 80}")
    print("🎯 최종 결과")
    print(f"{'=' * 80}")
    print(f"처리된 그룹 수: {successful_groups}/{len(all_groups)}개")
    print(f"총 처리된 이미지: {total_processed}개")
    print(f"결과 저장 위치: {output_folder}")

    print(f"\n🚀 개선된 처리 순서:")
    print("1. 기준 이미지 선택 (빠른 팔레트 분석)")
    print("2. 기준 이미지 전처리 (포켓몬 포맷)")
    print("3. Shiny 이미지 전처리 (포켓몬 포맷) ← 새로 추가!")
    print("4. 전처리된 이미지 간 색상 매핑 추출")
    print("5. 매핑 적용하여 Shiny 이미지 생성")
    print("6. 다른 이미지들 팔레트 매칭")

    print(f"\n🔧 적용된 전처리 (모든 이미지 동일):")
    print("- 8bpp 인덱스 포맷 변환 ✓")
    print("- 색상 표준화 (8의 배수 조정) ✓")
    print("- 팔레트 16색 제한 ✓")
    print("- 크기 조정 (64x64→80x80→160x80) ✓")
    print("- 팔레트 인덱스 구조 통일 ✓")
    print("- Shiny 이미지도 완전 전처리 ✓ ← 개선 사항!")
    print("- 포켓몬 NARC 완전 호환 ✓")

    print(f"\n✨ 주요 개선 사항:")
    print("- Shiny 이미지도 일반 이미지와 동일한 전처리 과정 거침")
    print("- 전처리 후 색상 매핑으로 더 정확한 Shiny 팔레트 생성")
    print("- 모든 이미지가 동일한 포맷 표준 준수")
    print("- C# 원본 코드의 AlternatePalette 로직 정확히 구현")

    print(f"\n완료! 모든 결과물이 '{output_folder}' 폴더에 저장되었습니다.")
    print("이제 pokemon_sprite_converter.py로 안전하게 NARC 파일을 생성할 수 있습니다.")


if __name__ == "__main__":
    main()