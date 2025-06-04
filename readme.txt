사용법

input:

이미지 규격:
1. 256*64 표준 포켓몬 스프라이트 이미지 규격 <도감번호>(*).png 1장 (64*64 4장으로 분리, front_normal, front_shiny, back_normal, back_shiny 순)
2. extractor로 생성된 160*80 <female/male>_<front/back>_<normal/shiny>.png 4장(성별 관계 없음, front_normal, front_shiny, back_normal, back_shiny)

파일 위치:
input\<male/female>\<도감번호>\ 경로에 배치.
파일 이름에 포함된 성별 정보는 무시.

프로그램 흐름:
1. 256*64 이미지를 160*80 4장으로 변환해서, <front/back>_<normal/shiny>.png 으로 저장
