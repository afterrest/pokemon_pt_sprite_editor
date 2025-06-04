import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from pokemon_sprite_converter import PokemonSpriteConverter


class OtherPokeConverter:
    """pl_otherpoke.narc 전용 변환기 - 특별한 폼과 언노운 처리"""

    def __init__(self, is_diamond_pearl: bool = False):
        self.is_diamond_pearl = is_diamond_pearl
        self.converter = PokemonSpriteConverter(is_diamond_pearl)

        # otherpoke.narc 구조 정의
        self.sprite_structure = self._define_sprite_structure()
        self.palette_structure = self._define_palette_structure()

    def _define_sprite_structure(self) -> Dict:
        """스프라이트 파일 구조 정의"""
        structure = {
            # Deoxys (0-7)
            'deoxys': {
                'range': (0, 8),
                'forms': ['normal', 'attack', 'defense', 'speed'],
                'pattern': 'back_front'  # back, front, back, front...
            },

            # Unown (8-63) - 28개 폼 * 2 (back/front)
            'unown': {
                'range': (8, 64),
                'forms': ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
                          'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
                          '!', '?'],
                'pattern': 'back_front'
            },

            # Castform (64-71)
            'castform': {
                'range': (64, 72),
                'forms': ['normal', 'sun', 'rain', 'hail'],
                'pattern': 'back_back_front_front'  # 특별한 패턴
            },

            # Burmy (72-77)
            'burmy': {
                'range': (72, 78),
                'forms': ['grass', 'sand', 'trash'],
                'pattern': 'back_front'
            },

            # Wormadam (78-83)
            'wormadam': {
                'range': (78, 84),
                'forms': ['grass', 'sand', 'trash'],
                'pattern': 'back_front'
            },

            # Shellos (84-87)
            'shellos': {
                'range': (84, 88),
                'forms': ['west', 'east'],
                'pattern': 'back_back_front_front'
            },

            # Gastrodon (88-91)
            'gastrodon': {
                'range': (88, 92),
                'forms': ['west', 'east'],
                'pattern': 'back_back_front_front'
            },

            # Cherrim (92-95)
            'cherrim': {
                'range': (92, 96),
                'forms': ['closed', 'blossom'],
                'pattern': 'back_back_front_front'  # 특별한 패턴
            },

            # Arceus (96-131) - 18개 폼
            'arceus': {
                'range': (96, 132),
                'forms': ['normal', 'fighting', 'flying', 'poison', 'ground', 'rock', 'bug', 'ghost',
                          'steel', 'fire', 'water', 'grass', 'electric', 'psychic', 'ice', 'dragon',
                          'dark', 'fairy'],
                'pattern': 'back_front'
            },

            'egg': {
                'range': (132, 133),
                'forms': ['normal'],  # 'egg' -> 'normal'로 변경
                'pattern': 'single'
            },

            # Manaphy Egg (133)
            'manaphy_egg': {
                'range': (133, 134),
                'forms': ['normal'],  # 'egg' -> 'normal'로 변경
                'pattern': 'single'
            },

            # Shaymin (134-137)
            'shaymin': {
                'range': (134, 138),
                'forms': ['land', 'sky'],
                'pattern': 'back_front'
            },

            # Rotom (138-149) - 6개 폼
            'rotom': {
                'range': (138, 150),
                'forms': ['normal', 'heat', 'wash', 'frost', 'fan', 'mow'],
                'pattern': 'back_front'
            },

            # Giratina (150-153)
            'giratina': {
                'range': (150, 154),
                'forms': ['altered', 'origin'],
                'pattern': 'back_front'
            },
            'substitute_doll': {
                'range': (248, 250),
                'forms': ['normal'],  # 'egg' -> 'normal'로 변경
                'pattern': 'back_front'
            },
            'substitute_doll_shadow': {
                'range': (251, 252),
                'forms': ['normal'],  # 'egg' -> 'normal'로 변경
                'pattern': 'single'
            }
        }

        return structure

    def _define_palette_structure(self) -> Dict:
        """팔레트 파일 구조 정의 (154부터 시작)"""
        return {
            'deoxys': {
                'form_palettes': {
                    'normal': {'normal': 154, 'shiny': 155},
                    'attack': {'normal': 154, 'shiny': 155},
                    'defense': {'normal': 154, 'shiny': 155},
                    'speed': {'normal': 154, 'shiny': 155}
                }
            },
            'unown': {
                'form_palettes': {
                    # 모든 언노운 글자가 같은 팔레트 공유
                    form: {'normal': 156, 'shiny': 157}
                    for form in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
                                 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '!', '?']
                }
            },
            'castform': {
                'form_palettes': {
                    'normal': {'normal': 158, 'shiny': 162},
                    'sun': {'normal': 159, 'shiny': 163},
                    'rain': {'normal': 160, 'shiny': 164},
                    'hail': {'normal': 161, 'shiny': 165}
                }
            },
            'burmy': {
                'form_palettes': {
                    'grass': {'normal': 166, 'shiny': 167},
                    'sand': {'normal': 168, 'shiny': 169},
                    'trash': {'normal': 170, 'shiny': 171}
                }
            },
            'wormadam': {
                'form_palettes': {
                    'grass': {'normal': 172, 'shiny': 173},
                    'sand': {'normal': 174, 'shiny': 175},
                    'trash': {'normal': 176, 'shiny': 177}
                }
            },
            'shellos': {
                'form_palettes': {
                    'west': {'normal': 178, 'shiny': 179},
                    'east': {'normal': 180, 'shiny': 181}
                }
            },
            'gastrodon': {
                'form_palettes': {
                    'west': {'normal': 182, 'shiny': 183},
                    'east': {'normal': 184, 'shiny': 185}
                }
            },
            'cherrim': {
                'form_palettes': {
                    'closed': {'normal': 186, 'shiny': 188},
                    'blossom': {'normal': 187, 'shiny': 189}
                }
            },
            'arceus': {
                'form_palettes': {
                    'normal': {'normal': 190, 'shiny': 191},
                    'fighting': {'normal': 192, 'shiny': 193},
                    'flying': {'normal': 194, 'shiny': 195},
                    'poison': {'normal': 196, 'shiny': 197},
                    'ground': {'normal': 198, 'shiny': 199},
                    'rock': {'normal': 200, 'shiny': 201},
                    'bug': {'normal': 202, 'shiny': 203},
                    'ghost': {'normal': 204, 'shiny': 205},
                    'steel': {'normal': 206, 'shiny': 207},
                    'fairy': {'normal': 208, 'shiny': 209},
                    'fire': {'normal': 210, 'shiny': 211},
                    'water': {'normal': 212, 'shiny': 213},
                    'grass': {'normal': 214, 'shiny': 215},
                    'electric': {'normal': 216, 'shiny': 217},
                    'psychic': {'normal': 218, 'shiny': 219},
                    'ice': {'normal': 220, 'shiny': 221},
                    'dragon': {'normal': 222, 'shiny': 223},
                    'dark': {'normal': 224, 'shiny': 225}
                }
            },
            # egg와 doll 관련은 shiny 없이 normal만
            'egg': {
                'form_palettes': {
                    'normal': {'normal': 226}  # shiny 제거
                }
            },
            'manaphy_egg': {
                'form_palettes': {
                    'normal': {'normal': 227}  # shiny 제거
                }
            },
            'shaymin': {
                'form_palettes': {
                    'land': {'normal': 228, 'shiny': 229},
                    'sky': {'normal': 230, 'shiny': 231}
                }
            },
            'rotom': {
                'form_palettes': {
                    'normal': {'normal': 232, 'shiny': 233},
                    'heat': {'normal': 234, 'shiny': 235},
                    'wash': {'normal': 236, 'shiny': 237},
                    'frost': {'normal': 238, 'shiny': 239},
                    'fan': {'normal': 240, 'shiny': 241},
                    'mow': {'normal': 242, 'shiny': 243}
                }
            },
            'giratina': {
                'form_palettes': {
                    'altered': {'normal': 244, 'shiny': 245},
                    'origin': {'normal': 246, 'shiny': 247}
                }
            },
            'substitute_doll': {
                'form_palettes': {
                    'normal': {'normal': 250}  # shiny 제거
                }
            },
            'substitute_doll_shadow': {
                'form_palettes': {
                    'normal': {'normal': 252}  # shiny 제거
                }
            },
        }

    def otherpoke_to_pngs(self, narc_file: str, output_dir: str) -> None:
        """pl_otherpoke.narc를 PNG들로 변환"""
        from narc_reader import NarcReader

        reader = NarcReader(narc_file)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        print(f"pl_otherpoke.narc 변환 시작: {len(reader)} 파일")

        # 각 포켓몬별로 처리
        for pokemon_name, sprite_info in self.sprite_structure.items():
            pokemon_dir = output_path / pokemon_name
            pokemon_dir.mkdir(exist_ok=True)

            try:
                self._extract_pokemon_sprites(reader, pokemon_name, sprite_info, pokemon_dir)
                print(f"{pokemon_name} 변환 완료")
            except Exception as e:
                print(f"{pokemon_name} 변환 실패: {e}")

        print(f"모든 스프라이트 PNG 변환 완료: {output_dir}")

    def _extract_pokemon_sprites(self, reader, pokemon_name: str, sprite_info: Dict, output_dir: Path):
        """개별 포켓몬의 스프라이트들을 추출"""
        start_idx, end_idx = sprite_info['range']
        forms = sprite_info['forms']
        pattern = sprite_info['pattern']

        # 팔레트 정보 가져오기
        palette_info = self.palette_structure.get(pokemon_name, {})

        if pattern == 'back_front':
            # 일반적인 back-front 교대 패턴
            for i, form_name in enumerate(forms):
                back_idx = start_idx + (i * 2)
                front_idx = start_idx + (i * 2) + 1

                if back_idx < end_idx and front_idx < end_idx:
                    self._extract_form_sprites(reader, output_dir, form_name, back_idx, front_idx, palette_info,
                                               pokemon_name)

        elif pattern == 'back_back_front_front':
            # Castform, Cherrim 패턴: 모든 back이 먼저, 그 다음 모든 front
            form_count = len(forms)
            for i, form_name in enumerate(forms):
                back_idx = start_idx + i
                front_idx = start_idx + form_count + i

                if back_idx < end_idx and front_idx < end_idx:
                    self._extract_form_sprites(reader, output_dir, form_name, back_idx, front_idx, palette_info,
                                               pokemon_name)

        elif pattern == 'single':
            # 단일 파일 (Egg 등) - normal 팔레트만 사용
            if start_idx < end_idx:
                sprite_data = reader.extract_file(start_idx)
                if len(sprite_data) > 48:  # 유효한 스프라이트 데이터인지 확인
                    # 폼별 팔레트 찾기
                    normal_palette, _ = self._find_palettes_for_form(reader, pokemon_name, forms[0], palette_info)
                    if not normal_palette:
                        normal_palette = self._create_default_palette()

                    output_file = output_dir / f"{forms[0]}.png"
                    self.converter.pokemon_to_png(sprite_data, normal_palette, str(output_file))

    def _extract_form_sprites(self, reader, output_dir: Path, form_name: str, back_idx: int, front_idx: int,
                              palette_info: Dict, pokemon_name: str):
        """특정 폼의 back/front 스프라이트를 추출"""
        try:
            # 스프라이트 데이터 추출
            back_data = reader.extract_file(back_idx)
            front_data = reader.extract_file(front_idx)

            if len(back_data) < 48 or len(front_data) < 48:
                print(f"  {form_name}: 스프라이트 데이터가 너무 작음 (건너뜀)")
                return

            # 팔레트 찾기 (폼별 팔레트 지원)
            normal_palette, shiny_palette = self._find_palettes_for_form(reader, pokemon_name, form_name, palette_info)

            if normal_palette:
                # 노말 버전
                back_file = output_dir / f"{form_name}_back_normal.png"
                front_file = output_dir / f"{form_name}_front_normal.png"
                self.converter.pokemon_to_png(back_data, normal_palette, str(back_file))
                self.converter.pokemon_to_png(front_data, normal_palette, str(front_file))

            # shiny 버전이 있는 경우만 생성
            if shiny_palette and self._has_shiny_palette(pokemon_name, form_name):
                back_file = output_dir / f"{form_name}_back_shiny.png"
                front_file = output_dir / f"{form_name}_front_shiny.png"
                self.converter.pokemon_to_png(back_data, shiny_palette, str(back_file))
                self.converter.pokemon_to_png(front_data, shiny_palette, str(front_file))

            print(f"  {form_name}: back#{back_idx}, front#{front_idx} 추출 완료")

        except Exception as e:
            print(f"  {form_name} 추출 실패: {e}")

    def _has_shiny_palette(self, pokemon_name: str, form_name: str) -> bool:
        """해당 폼이 shiny 팔레트를 가지고 있는지 확인"""
        palette_info = self.palette_structure.get(pokemon_name, {})
        form_palettes = palette_info.get('form_palettes', {})
        if form_name in form_palettes:
            return 'shiny' in form_palettes[form_name]
        return False

    def _find_palettes_for_form(self, reader, pokemon_name: str, form_name: str, palette_info: Dict) -> Tuple[
        Optional[bytes], Optional[bytes]]:
        """특정 폼에 해당하는 팔레트들을 찾기 (모든 포켓몬이 폼별 팔레트 사용)"""
        if not palette_info:
            # 기본 팔레트 사용
            default_palette = self._create_default_palette()
            return default_palette, default_palette

        normal_palette = None
        shiny_palette = None

        try:
            # 모든 포켓몬이 폼별 팔레트 사용
            form_palettes = palette_info.get('form_palettes', {})
            if form_name in form_palettes:
                form_palette_info = form_palettes[form_name]

                if 'normal' in form_palette_info and form_palette_info['normal'] < len(reader.file_entries):
                    normal_palette = reader.extract_file(form_palette_info['normal'])
                    print(f"    {pokemon_name} {form_name} 노말 팔레트: #{form_palette_info['normal']}")

                # shiny 팔레트가 정의되어 있는 경우만 추출
                if 'shiny' in form_palette_info and form_palette_info['shiny'] < len(reader.file_entries):
                    shiny_palette = reader.extract_file(form_palette_info['shiny'])
                    print(f"    {pokemon_name} {form_name} 색다른 팔레트: #{form_palette_info['shiny']}")
            else:
                print(f"    경고: {pokemon_name}의 {form_name} 폼에 대한 팔레트 정보 없음")

        except Exception as e:
            print(f"  팔레트 추출 실패: {e}")
            default_palette = self._create_default_palette()
            return default_palette, default_palette

        # 팔레트가 없으면 기본 팔레트 사용 (normal만)
        if not normal_palette:
            normal_palette = self._create_default_palette()

        return normal_palette, shiny_palette

    def _create_default_palette(self) -> bytes:
        """기본 그레이스케일 팔레트 생성"""
        header = bytes([
            82, 76, 67, 78, 255, 254, 0, 1, 72, 0, 0, 0, 16, 0, 1, 0,
            84, 84, 76, 80, 56, 0, 0, 0, 4, 0, 10, 0, 0, 0, 0, 0,
            32, 0, 0, 0, 16, 0, 0, 0
        ])

        # 16색 그레이스케일 팔레트
        colors = []
        for i in range(16):
            gray = i * 2  # 0-30 범위 (5비트)
            color_value = gray | (gray << 5) | (gray << 10)
            colors.append(color_value.to_bytes(2, 'little'))

        return header + b''.join(colors)

    def pngs_to_otherpoke(self, input_dir: str, output_narc: str, original_narc: str = None) -> None:
        """PNG들을 pl_otherpoke.narc로 변환"""
        from narc_reader import pack_narc, NarcReader

        input_path = Path(input_dir)
        temp_dir = Path("temp_otherpoke_data")
        temp_dir.mkdir(exist_ok=True)

        # 원본 구조 분석
        original_structure = None
        if original_narc and os.path.exists(original_narc):
            print(f"원본 otherpoke.narc 구조 분석 중: {original_narc}")
            original_reader = NarcReader(original_narc)
            original_structure = original_reader

        try:
            # 전체 파일 구조를 위한 최대 인덱스 계산
            max_sprite_index = 0
            max_palette_index = 0

            # 스프라이트 최대 인덱스 찾기
            for sprite_info in self.sprite_structure.values():
                _, end_idx = sprite_info['range']
                max_sprite_index = max(max_sprite_index, end_idx - 1)

            # 팔레트 최대 인덱스 찾기
            for palette_info in self.palette_structure.values():
                form_palettes = palette_info.get('form_palettes', {})
                for form_palette_info in form_palettes.values():
                    for palette_idx in form_palette_info.values():
                        max_palette_index = max(max_palette_index, palette_idx)

            total_files = max(max_sprite_index + 1, max_palette_index + 1)
            print(f"전체 파일 수: {total_files}")

            # 모든 파일 인덱스를 원본 데이터로 초기화 (원본 데이터 우선)
            for i in range(total_files):
                self._write_original_or_empty(temp_dir, i, i, original_structure)

            # 스프라이트 처리 - 실제 인덱스 위치에 직접 쓰기
            for pokemon_name, sprite_info in self.sprite_structure.items():
                pokemon_dir = input_path / pokemon_name
                if pokemon_dir.exists():
                    self._pack_pokemon_sprites_direct(pokemon_dir, temp_dir, pokemon_name,
                                                      sprite_info, original_structure)
                    print(f"{pokemon_name} 스프라이트 패킹 완료")

            # 팔레트 처리 - 실제 인덱스 위치에 직접 쓰기
            for pokemon_name, palette_info in self.palette_structure.items():
                pokemon_dir = input_path / pokemon_name
                self._pack_pokemon_palettes_direct(pokemon_dir, temp_dir, pokemon_name,
                                                   palette_info, original_structure)

            # NARC 파일 생성
            pack_narc(str(temp_dir), output_narc)
            print(f"pl_otherpoke.narc 생성 완료: {output_narc}")

        finally:
            # 임시 파일들 정리
            import shutil
            if temp_dir.exists():
                shutil.rmtree(temp_dir)

    def _pack_pokemon_sprites_direct(self, pokemon_dir: Path, temp_dir: Path, pokemon_name: str,
                                     sprite_info: Dict, original_structure) -> None:
        """포켓몬 스프라이트들을 실제 인덱스 위치에 직접 패킹"""
        start_idx, end_idx = sprite_info['range']
        forms = sprite_info['forms']
        pattern = sprite_info['pattern']

        if pattern == 'back_front':
            for i, form_name in enumerate(forms):
                back_idx = start_idx + (i * 2)
                front_idx = start_idx + (i * 2) + 1

                # Back sprite
                back_file = pokemon_dir / f"{form_name}_back_normal.png"
                if back_file.exists() and back_idx < end_idx:
                    sprite_data, _ = self.converter.png_to_pokemon(str(back_file))
                    with open(temp_dir / f"file_{back_idx:04d}.bin", 'wb') as f:
                        f.write(sprite_data)
                    print(f"  {form_name} back → #{back_idx}")

                # Front sprite
                front_file = pokemon_dir / f"{form_name}_front_normal.png"
                if front_file.exists() and front_idx < end_idx:
                    sprite_data, _ = self.converter.png_to_pokemon(str(front_file))
                    with open(temp_dir / f"file_{front_idx:04d}.bin", 'wb') as f:
                        f.write(sprite_data)
                    print(f"  {form_name} front → #{front_idx}")

        elif pattern == 'back_back_front_front':
            form_count = len(forms)
            # 모든 back sprites 먼저
            for i, form_name in enumerate(forms):
                back_idx = start_idx + i
                if back_idx < end_idx:
                    back_file = pokemon_dir / f"{form_name}_back_normal.png"
                    if back_file.exists():
                        sprite_data, _ = self.converter.png_to_pokemon(str(back_file))
                        with open(temp_dir / f"file_{back_idx:04d}.bin", 'wb') as f:
                            f.write(sprite_data)
                        print(f"  {form_name} back → #{back_idx}")

            # 그 다음 모든 front sprites
            for i, form_name in enumerate(forms):
                front_idx = start_idx + form_count + i
                if front_idx < end_idx:
                    front_file = pokemon_dir / f"{form_name}_front_normal.png"
                    if front_file.exists():
                        sprite_data, _ = self.converter.png_to_pokemon(str(front_file))
                        with open(temp_dir / f"file_{front_idx:04d}.bin", 'wb') as f:
                            f.write(sprite_data)
                        print(f"  {form_name} front → #{front_idx}")

        elif pattern == 'single':
            # 단일 파일
            if start_idx < end_idx:
                single_file = pokemon_dir / f"{forms[0]}.png"
                if single_file.exists():
                    sprite_data, _ = self.converter.png_to_pokemon(str(single_file))
                    with open(temp_dir / f"file_{start_idx:04d}.bin", 'wb') as f:
                        f.write(sprite_data)
                    print(f"  {forms[0]} → #{start_idx}")

    def _pack_pokemon_palettes_direct(self, pokemon_dir: Path, temp_dir: Path, pokemon_name: str,
                                      palette_info: Dict, original_structure) -> None:
        """포켓몬 팔레트들을 실제 인덱스 위치에 직접 패킹"""
        if 'form_palettes' not in palette_info:
            return

        form_palettes = palette_info.get('form_palettes', {})
        sprite_info = self.sprite_structure.get(pokemon_name, {})

        for form_name, form_palette_info in form_palettes.items():
            for palette_type in ['normal', 'shiny']:
                if palette_type in form_palette_info:
                    palette_idx = form_palette_info[palette_type]

                    # 적절한 PNG 파일 찾기
                    if sprite_info.get('pattern') == 'single':
                        png_file = pokemon_dir / f"{form_name}.png"
                    else:
                        png_file = pokemon_dir / f"{form_name}_back_{palette_type}.png"

                    if png_file.exists():
                        _, palette_data = self.converter.png_to_pokemon(str(png_file))
                        with open(temp_dir / f"file_{palette_idx:04d}.bin", 'wb') as f:
                            f.write(palette_data)
                        print(f"  팔레트: {pokemon_name} {form_name} {palette_type} → #{palette_idx}")

    def _write_original_or_empty(self, temp_dir: Path, file_index: int, original_index: int, original_structure):
        """원본 데이터 우선으로 작성, 없으면 빈 데이터"""
        if original_structure and original_index < len(original_structure.file_entries):
            # 원본 데이터 복사 우선
            try:
                original_data = original_structure.extract_file(original_index)
                with open(temp_dir / f"file_{file_index:04d}.bin", 'wb') as f:
                    f.write(original_data)
                return
            except:
                pass  # 원본 읽기 실패시 빈 데이터로 fallback

        # 원본이 없거나 읽기 실패시 빈 데이터
        with open(temp_dir / f"file_{file_index:04d}.bin", 'wb') as f:
            f.write(b'\x00' * 48)

    def _write_empty_or_original(self, temp_dir: Path, file_index: int, original_index: int, original_structure):
        """빈 데이터 또는 원본 데이터 작성 (기존 함수 유지)"""
        if original_structure and original_index < len(original_structure.file_entries):
            # 원본 데이터 복사
            try:
                original_data = original_structure.extract_file(original_index)
                with open(temp_dir / f"file_{file_index:04d}.bin", 'wb') as f:
                    f.write(original_data)
            except:
                # 원본 읽기 실패시 빈 데이터
                with open(temp_dir / f"file_{file_index:04d}.bin", 'wb') as f:
                    f.write(b'\x00' * 48)
        else:
            # 빈 데이터
            with open(temp_dir / f"file_{file_index:04d}.bin", 'wb') as f:
                f.write(b'\x00' * 48)


# 사용 예제 함수들
def convert_otherpoke_to_pngs(narc_file: str, output_dir: str, is_diamond_pearl: bool = False) -> None:
    """pl_otherpoke.narc를 PNG들로 변환하는 편의 함수"""
    converter = OtherPokeConverter(is_diamond_pearl)
    converter.otherpoke_to_pngs(narc_file, output_dir)


def convert_pngs_to_otherpoke(input_dir: str, output_narc: str, original_narc: str = None,
                              is_diamond_pearl: bool = False) -> None:
    """PNG들을 pl_otherpoke.narc로 변환하는 편의 함수"""
    converter = OtherPokeConverter(is_diamond_pearl)
    converter.pngs_to_otherpoke(input_dir, output_narc, original_narc)


# 메인 실행부
if __name__ == "__main__":
    # pl_otherpoke.narc → PNG 변환
    convert_otherpoke_to_pngs("pl_otherpoke.narc", "otherpoke_sprites/")

    # PNG → pl_otherpoke.narc 변환
    # convert_pngs_to_otherpoke("otherpoke_sprites/", "new_pl_otherpoke.narc", "pl_otherpoke.narc")

    pass