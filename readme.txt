사용법
pl_pokegra.narc:

이미지 규격:
1. 256*64 표준 포켓몬 스프라이트 이미지 규격 <도감번호>(*).png 1장 (64*64 4장으로 분리, front_normal, front_shiny, back_normal, back_shiny 순)
2. extractor로 생성된 160*80 <female/male>_<front/back>_<normal/shiny>.png 4장(성별 관계 없음, front_normal, front_shiny, back_normal, back_shiny)

파일 위치:
input\<M/F>\<도감번호>\ 경로에 배치.
파일 이름에 포함된 성별 정보는 무시.

프로그램 흐름:
1. 256*64 이미지를 160*80 4장으로 변환해서, 파일이 있던 장소에 그대로 <front/back>_<normal/shiny>.png 으로 저장
2. 원본 pl_pokegra.narc 파일 읽기
3. input에 준비된 파일을 narc에 삽입
3-1. input\<성별>\<도감번호>\(*)<front/back>_<normal/shiny>.png 각 정보가 가르키는 위치에 파일 삽입
4. pl_pokegra.narc 저장.

pl_otherpoke.narc:

이미지 규격:
1. 256*64 표준 포켓몬 스프라이트 이미지 규격 <도감번호>(*)<form>.png 1장
2. extractor로 생성된 160*80 <form>_<front/back>_<normal/shiny>.png form 하나당 4장 씩이 담긴 폴더 <포켓몬 이름>
파일 위치:
input에 배치. (1의 경우 파일을 직접, 2의 경우 <포켓몬 이름> 폴더를)

프로그램 흐름:
1. 256*64 이미지를 160*80 4장으로 변환해서, input\<포켓몬 이름> 폴더에 <form>_<front/back>_<normal/shiny>.png 으로 저장
2. 원본 pl_otherpoke.narc 파일 읽기
3. input에 준비된 파일을 narc에 삽입
3-1. input\<포켓몬 이름>\<form>_<front/back>_<normal/shiny>.png 각 정보가 가르키는 위치에 파일 삽입
4. pl_otherpoke.narc 저장.



