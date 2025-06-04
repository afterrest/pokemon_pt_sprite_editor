import os
from PIL import Image, ImageDraw
import glob


def process_images(input_folder, output_folder):
    """
    256x64 이미지를 처리하여 64x64 이미지들로 분할하고 변환하는 함수
    """
    # output 폴더가 없으면 생성
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 입력 폴더에서 이미지 파일들 찾기 (png, jpg, jpeg 지원)
    image_extensions = ['*.png', '*.jpg', '*.jpeg', '*.PNG', '*.JPG', '*.JPEG']
    image_files = []
    for extension in image_extensions:
        image_files.extend(glob.glob(os.path.join(input_folder, extension)))

    if not image_files:
        print("입력 폴더에서 이미지 파일을 찾을 수 없습니다.")
        return

    print(f"총 {len(image_files)}개의 이미지를 처리합니다.")

    for idx, image_path in enumerate(image_files):
        try:
            # 파일명에서 확장자 제거
            base_name = os.path.splitext(os.path.basename(image_path))[0]

            print(f"[{idx + 1}/{len(image_files)}] 처리 중: {base_name}")

            # 이미지 열기
            img = Image.open(image_path)

            # 이미지 크기 확인
            if img.size != (256, 64):
                print(f"  경고: {base_name}의 크기가 256x64가 아닙니다. ({img.width}x{img.height}) 건너뜁니다.")
                continue

            # 256x64 이미지를 64x64 4개로 분할
            sprites = []
            for i in range(4):
                left = i * 64
                sprite = img.crop((left, 0, left + 64, 64))
                sprites.append(sprite)

            # 앞의 3개 스프라이트 처리
            suffixes = ['_Front.png', '_Shiny.png', '_Back.png']

            for i in range(3):
                print(f"  처리 중: {base_name}{suffixes[i]}")

                # 80x80 캔버스 생성 (배경색 #90B0B0)
                expanded_img = Image.new('RGB', (80, 80), color='#90B0B0')

                # 64x64 이미지를 중앙에 배치 (8픽셀 여백)
                expanded_img.paste(sprites[i], (8, 8))

                # 160x80 이미지 생성 (80x80 이미지를 2개 나란히)
                final_img = Image.new('RGB', (160, 80), color='#90B0B0')
                final_img.paste(expanded_img, (0, 0))  # 왼쪽에 첫 번째
                final_img.paste(expanded_img, (80, 0))  # 오른쪽에 두 번째 (동일한 이미지)

                # 파일 저장
                output_path = os.path.join(output_folder, f"{base_name}{suffixes[i]}")
                final_img.save(output_path)

            print(f"  완료: {base_name}")

        except Exception as e:
            print(f"  오류 발생 ({base_name}): {str(e)}")
            continue

    print("모든 이미지 처리가 완료되었습니다.")


def main():
    # 폴더 경로 설정
    input_folder = r"C:\game\pokemon\spriteEditor\gen3sprite"  # 입력 폴더
    output_folder = r"C:\game\pokemon\spriteEditor\gen4sprite"  # 출력 폴더

    # 입력 폴더 존재 확인
    if not os.path.exists(input_folder):
        print(f"입력 폴더 '{input_folder}'가 존재하지 않습니다.")
        print("현재 디렉토리에 'input' 폴더를 만들고 256x64 이미지들을 넣어주세요.")
        return

    # 이미지 처리 실행
    process_images(input_folder, output_folder)


if __name__ == "__main__":
    main()