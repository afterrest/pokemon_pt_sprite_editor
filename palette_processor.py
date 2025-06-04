"""
palette_processor.py - 포켓몬 스프라이트 팔레트 처리 워크플로우

이 모듈은 현재의 파일 기반 워크플로우를 담당합니다.
palette_engine.py의 핵심 기능들을 호출하여 실제 파일 처리를 수행합니다.

TODO: 향후 pokemon_sprite_converter.py로 메인 워크플로우 이관시 이 파일은 제거될 예정
현재는 기존 기능 유지를 위해 임시로 분리한 상태입니다.
"""

import os
import re
from PIL import Image
from collections import defaultdict
from palette_engine import (
    find_optimal_reference,
    preprocess_reference_only,
    extract_color_mapping_between_processed_images,
    apply_color_mapping_to_processed_image,
    match_others_to_reference,
    perform_verification
)
from indexed_bitmap_handler import preprocess_reference_image_for_pokemon


# =============================================================================
# 파일 처리 유틸리티 함수들
# TODO: 이 섹션은 README 규격에 맞게 폴더 구조 기반으로 전면 수정 필요
# =============================================================================

def extract_number_from_filename(filename):
    """파일명에서 숫자 추출

    현재: 001MFront.png → 1
    TODO: 폴더 구조로 변경시 이 함수는 제거 예정
    """
    name_without_ext = os.path.splitext(filename)[0]
    match = re.match(r'^(\d+)', name_without_ext)
    if match:
        return int(match.group(1))
    return None


def generate_pokemon_filename(original_filename, suffix=""):
    """포켓몬 파일명 형식으로 변환: (male/female)_(back/front)_(normal/shiny).png

    현재: 001MFront.png → male_front_normal.png
    TODO: 폴더 구조 변경시 파일명 규칙도 단순화 가능
    """
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
    """포켓몬 폴더 생성

    현재: output/pokemon_001/ 형태로 생성
    TODO: NARC 직접 출력으로 변경시 이 함수는 불필요해짐
    """
    folder_name = f"pokemon_{dex_number:03d}"
    pokemon_folder = os.path.join(output_folder, folder_name)

    if not os.path.exists(pokemon_folder):
        os.makedirs(pokemon_folder)
        print(f"  폴더 생성: {folder_name}")

    return pokemon_folder


def group_files_by_number(image_files):
    """파일들을 숫자별로 그룹화

    현재: 파일명의 숫자로 그룹화 (001MFront.png, 001FBack.png → 그룹 1)
    TODO: 폴더 구조 스캔으로 대체
    - input/M/001/ 과 input/F/001/ 을 하나의 포켓몬으로 묶기
    - 성별별 처리 로직 추가
    """
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
    """전처리 완료된 이미지를 PNG로 저장

    KEEP: 이 함수는 검증용으로 계속 필요할 수 있음
    TODO: NARC 직접 출력시에도 중간 결과 저장용으로 사용
    """
    # 최종 검증
    if image.size != (160, 80):
        print(f"    경고: 예상과 다른 크기 {image.size}")

    if image.mode != 'P':
        print(f"    경고: 팔레트 모드가 아님 {image.mode}")

    # PNG 저장
    image.save(output_path, "PNG", optimize=False)
    print(f"    저장 완료: {os.path.basename(output_path)}")


def save_original_image(shiny_file, pokemon_folder):
    """원본 Shiny 이미지를 저장

    KEEP: 디버깅과 검증을 위해 유지
    """
    original_filename = os.path.basename(shiny_file)
    new_filename = generate_pokemon_filename(original_filename, "original")
    output_path = os.path.join(pokemon_folder, new_filename)

    # 원본 이미지 복사
    original_image = Image.open(shiny_file)
    original_image.save(output_path, "PNG")

    return output_path, new_filename


def parse_sprite_info(filename):
    """파일명에서 성별과 방향 정보 추출

    현재: 001MFront.png → ('male', 'front', False)
    TODO: 폴더 구조로 변경시 경로 기반 파싱으로 수정
    """
    is_female = 'FBack' in filename or 'FFront' in filename or 'FShiny' in filename
    is_back = 'Back' in filename
    is_shiny = 'Shiny' in filename

    gender = 'female' if is_female else 'male'
    direction = 'back' if is_back else 'front'

    return gender, direction, is_shiny


# =============================================================================
# Shiny 이미지 처리 워크플로우
# TODO: 이 섹션을 데이터 기반으로 단순화 필요
# =============================================================================

def process_shiny_files_with_preprocessing(shiny_files_for_group, reference_path, processed_reference,
                                           pokemon_folder, is_diamond_pearl=False):
    """Shiny 파일들을 3단계로 처리하고 모두 저장

    KEEP: 3단계 처리 로직 (원본→전처리→매핑) 유지
    TODO: 출력을 NARC 형식으로 변경시 중간 파일 저장 부분만 수정
    """
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
                save_preprocessed_sprite(shiny_processed, final_output_path)
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
                save_preprocessed_sprite(final_shiny, final_output_path)
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
                save_preprocessed_sprite(shiny_processed, final_output_path)
                processed_shinies[final_filename] = shiny_processed

                print(f"      📁 저장된 파일들:")
                print(f"        - {original_filename} (원본)")
                print(f"        - {preprocessed_filename} (전처리)")
                print(f"        - {final_filename} (최종 = 전처리)")

        except Exception as e:
            print(f"      ❌ {shiny_filename} 처리 실패: {e}")
            continue

    return processed_shinies


def find_matching_normal_for_shiny(shiny_file, processed_images):
    """특정 Shiny 이미지에 대응하는 일반 이미지 찾기

    KEEP: Shiny-Normal 매칭 로직
    """
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
    """기준 이미지와 같은 성별의 Shiny 파일들만 필터링

    KEEP: 성별별 매칭 로직 (현재는 파일명 기반)
    TODO: 폴더 구조 변경시 경로 기반으로 수정
    """
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


def process_single_shiny_file(shiny_file, matching_normal_image, pokemon_folder, is_diamond_pearl):
    """단일 Shiny 파일을 3단계로 처리

    KEEP: 개별 Shiny 처리 로직
    """
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
# TODO: 이 섹션을 README 규격에 맞게 수정 필요
# =============================================================================

def process_group(group_number, group_files, shiny_files_for_group,
                  output_folder, is_diamond_pearl=False):
    """그룹 처리

    현재: 파일명 숫자 기반 그룹 처리
    TODO: 성별별 도감번호 기반으로 변경
    - input/M/001/ + input/F/001/ → 하나의 포켓몬으로 처리
    - 출력을 NARC 인덱스로 매핑
    """
    print(f"\n{'=' * 70}")
    print(f"그룹 {group_number} 처리 중 ({len(group_files)}개 파일)")
    if shiny_files_for_group:
        print(f"+ Shiny 파일 {len(shiny_files_for_group)}개")
    print(f"{'=' * 70}")

    # 포켓몬 폴더 생성
    # TODO: NARC 직접 출력으로 변경시 이 부분 제거
    pokemon_folder = create_pokemon_folder(output_folder, group_number)

    # 단일 파일 처리
    if len(group_files) == 1:
        return process_single_file(group_files[0], shiny_files_for_group, pokemon_folder, is_diamond_pearl)

    # 멀티 파일 처리
    return process_multiple_files(group_number, group_files, shiny_files_for_group, pokemon_folder, is_diamond_pearl)


def process_single_file(file_path, shiny_files_for_group, pokemon_folder, is_diamond_pearl):
    """단일 파일 처리

    KEEP: 단일 파일 처리 로직
    """
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
    """멀티 파일 처리

    KEEP: 핵심 팔레트 통일 파이프라인
    """
    print("  멀티 파일 처리")

    # 1단계: 기준 이미지 선택 (palette_engine 함수 호출)
    reference_path = find_optimal_reference(group_files)
    if not reference_path:
        print("  기준 이미지를 선택할 수 없습니다.")
        return

    print(f"  ✅ 기준 이미지 선택: {os.path.basename(reference_path)}")

    # 2단계: 기준 이미지 전처리 (palette_engine 함수 호출)
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

    # 5단계: 다른 일반 이미지들 처리 (palette_engine 함수 호출)
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

    # 7단계: 검증 (palette_engine 함수 호출)
    verification_result = perform_verification(processed_images, processed_shinies, reference_palette)

    print(f"\n  그룹 {group_number} 처리 완료!")
    print(f"  - 일반 이미지: {len(processed_images)}개")
    print(f"  - Shiny 이미지: {len(processed_shinies)}개")

    return verification_result


# =============================================================================
# 메인 함수
# TODO: 전체 워크플로우를 README 규격에 맞게 수정 필요
# =============================================================================

def main():
    """메인 실행 함수

    현재 흐름:
    1. input/ 폴더에서 파일명 기반 그룹화
    2. 각 그룹별로 팔레트 통일 처리
    3. output/ 폴더에 PNG 파일들 저장

    TODO: README 규격 구현
    1. input/M/XXX/, input/F/XXX/ 폴더 구조 스캔
    2. 성별별 처리 후 NARC 인덱스 매핑
    3. pokemon_sprite_converter 호출하여 NARC 생성
    """
    print("=== 포켓몬 팔레트 처리 워크플로우 (현재 구현) ===")
    print("palette_engine.py의 핵심 기능들을 호출하여 파일 기반 처리 수행\n")

    # 설정
    # TODO: README 규격에 맞게 수정
    input_folder = "./input"  # TODO: input/M/, input/F/ 구조로 변경
    output_folder = "./output"  # TODO: NARC 직접 출력으로 변경
    is_diamond_pearl = False  # True로 설정하면 DP 포맷 사용

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    print(f"입력 폴더: {input_folder}")
    print(f"출력 폴더: {output_folder}")
    print(f"포맷: {'Diamond/Pearl' if is_diamond_pearl else 'Platinum'}")

    # 이미지 파일 찾기
    # TODO: 폴더 구조 스캔으로 변경
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
    # TODO: scan_gender_dex_folders()로 대체
    groups, shiny_files = group_files_by_number(image_files)

    if not groups and not shiny_files:
        print("그룹화할 수 있는 파일이 없습니다.")
        return

    print(f"\n{len(groups)}개의 일반 그룹과 {len(shiny_files)}개의 Shiny 그룹으로 분류되었습니다.")

    # 각 그룹별로 처리 (palette_engine의 핵심 기능들 활용)
    total_processed = 0
    successful_groups = 0
    all_groups = set(groups.keys()) | set(shiny_files.keys())

    for group_num in sorted(all_groups):
        group_files = groups.get(group_num, [])
        shiny_files_for_group = shiny_files.get(group_num, [])

        try:
            result = process_group(
                group_num, group_files, shiny_files_for_group,
                output_folder, is_diamond_pearl
            )
            if result:
                successful_groups += 1
                total_processed += len(group_files) + len(shiny_files_for_group)
        except Exception as e:
            print(f"\n❌ 그룹 {group_num} 처리 실패: {e}")

    # TODO: pokemon_sprite_converter 호출하여 NARC 생성
    # from pokemon_sprite_converter import convert_pngs_to_narc
    # convert_pngs_to_narc(output_folder, "new_pl_pokegra.narc", "pl_pokegra.narc")

    print(f"\n{'=' * 80}")
    print("🎯 최종 결과")
    print(f"{'=' * 80}")
    print(f"처리된 그룹 수: {successful_groups}/{len(all_groups)}개")
    print(f"총 처리된 이미지: {total_processed}개")
    print(f"결과 저장 위치: {output_folder}")

    print(f"\n🔧 현재 처리 순서 (palette_engine 활용):")
    print("1. find_optimal_reference() - 기준 이미지 선택")
    print("2. preprocess_reference_only() - 기준 이미지 전처리")
    print("3. extract_color_mapping_between_processed_images() - 색상 매핑")
    print("4. apply_color_mapping_to_processed_image() - Shiny 생성")
    print("5. match_others_to_reference() - 팔레트 매칭")
    print("6. perform_verification() - 품질 검증")

    print(f"\n⚠️  TODO: 향후 개선 사항")
    print("- 이 워크플로우는 pokemon_sprite_converter.py로 이관 예정")
    print("- palette_engine.py의 핵심 기능들은 유지")
    print("- 파일 기반 처리 → 데이터 기반 처리로 변경")

    print(f"\n완료! 모든 결과물이 '{output_folder}' 폴더에 저장되었습니다.")


if __name__ == "__main__":
    main()