# Auto Tagging — 블로그 포스트 자동 태그 생성기

본 레포는 한국어 텍스트를 기반으로 자동으로 주제 태그를 생성하는 Python 스크립트입니다.
KoNLPy(Okt) 형태소 분석기와 TF-IDF 알고리즘을 활용해,
블로그나 티스토리 포스트의 핵심 키워드를 자동으로 추출합니다.

<br>

<br>

# 사용 방법

<br>

## 1. 글 입력하기

input.txt 파일에 여러분의 글(포스트 내용)을 그대로 복붙합니다.

프로젝트 폴더 구조 예시
```css
📁 프로젝트 폴더 구조 예시
├── auto_tagging.py
├── input.txt      ← 여기에 글을 복붙
├── stopwords.txt  ← (선택) 불용어 추가
└── tag_result/    ← 결과 자동 저장 폴더
```

<br><br>

## 2. 불용어(stopwords) 추가/수정하기

불필요한 단어(예: ‘이번’, ‘때문’, ‘서비스’)를 더 걸러내고 싶다면 stopwords.txt 파일을 편집합니다.

한 줄에 한 단어씩 입력하면 됩니다.

예시:
```txt
이번
때문
관련
서비스
사용자
```


참고 : stopwords.txt + GitHub 공개 불용어 + 기본 내장 불용어가 자동 병합되어 사용됩니다.

<br><br>

## 3. 실행하기

터미널(또는 CMD, PowerShell)에서 다음 명령어를 입력합니다.

`python auto_tagging.py`


실행 후 아래와 같은 순서로 진행됩니다.

```bash
🚀 Auto Tagging 시작!
📝 포스트 제목을 입력하세요: 인프라 장애 대응 보고서
📂 텍스트 입력 방식 선택 (1: 직접 입력 / 2: txt 파일 불러오기): 2
📄 불러올 txt 파일 경로를 입력하세요 (기본: ./input.txt):
📂 기본 파일 경로로 진행합니다: ./input.txt
🌐 GitHub 한국어 불용어 700개 불러옴
📘 로컬 불용어 68개 불러옴
✅ 최종 불용어 820개 사용 중
⚙️ TF-IDF 기반 분석을 사용할까요? (y/n): y

✅ 자동 생성된 태그:
배포, 로그, 서버, 복구, 인프라, 알림, 원인, 대응

💾 태그가 'tag_result/tag_result_인프라_장애_대응_보고서.txt' 파일로 저장되었습니다!
```

<br><br>

## 4. 결과 확인하기

tag_result/ 폴더에 자동으로 생성된 파일을 열어보면 다음과 같습니다.

```txt
✅ 제목: 인프라 장애 대응 보고서

✅ 자동 생성된 태그 목록

- 배포
- 로그
- 서버
- 복구
- 인프라
- 알림
- 원인
- 대응

```

<br><br>

## 옵션 설명

| 옵션                       | 설명                                   |
| ------------------------ | ------------------------------------ |
| **TF-IDF 모드 (y/n)**      | 단어 빈도 대신 중요도 기반 추출 (더 정교하지만 느림)      |
| **stopwords.txt**        | 직접 추가한 불용어를 반영 (내장 + GitHub 사전과 병합됨) |
| **title_boost**          | 제목 단어의 가중치 높이기 (중요 키워드가 상위로 노출됨)     |
| **out_dir="tag_result"** | 결과 저장 폴더 지정 (기본값: `tag_result/`)     |

<br><br>

## 작동 원리 요약

1.**텍스트 정제 (전처리)**

- HTML 태그, 특수문자, 개행 제거
- 공백 정규화, 소문자 변환

2.**형태소 분석 (Okt)**

- 명사만 추출
- 불용어, 한 글자, 접미사(함/됨/성) 필터링

3.**키워드 가중치 계산**

- 단순 빈도(`Counter`)
- 또는 TF-IDF(`sklearn.TfidfVectorizer`)

4.**중복 제거 및 정렬**

- 순서 유지(set + sorted)

5.**결과 파일 저장**

- 제목 기반 안전한 파일명으로 `tag_result/` 폴더에 저장

<br><br>

## 의존성

```bash
pip install konlpy scikit-learn requests
```

<br><br>

## 개발 메모

- 한국어 불용어는 [stopwords-iso/stopwords-ko](https://github.com/stopwords-iso/stopwords-ko) 공개 사전을 자동으로 불러옵니다.
- 로컬 `stopwords.txt`를 수정하면 추가적인 필터링이 즉시 반영됩니다.
- TF-IDF 분석 시에는 사전 토크나이즈된 텍스트를 사용해 한국어 인식률을 향상시켰습니다.

<br><br>

## 예시 활용 아이디어

- 블로그 글의 핵심 태그 자동 생성
- 뉴스 기사 요약 태깅
- 데이터 전처리용 키워드 추출
- 검색엔진용 인덱싱 키워드 생성

<br><br>

## 🧑‍💻 Author

**Developed by:** 나정현 (Jung Hyun Na)
 **GitHub:** https://github.com/najungh

<br><br>