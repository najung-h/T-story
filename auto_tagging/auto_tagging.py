# auto_tagging.py
import re, os, requests
from typing import List, Set
from collections import Counter

# pip install konlpy
from konlpy.tag import Okt

# pip install scikit-learn
from sklearn.feature_extraction.text import TfidfVectorizer


# ------------------------------
# 0) 전역 캐시 (선택 성능 최적화)
# ------------------------------
_STOPWORDS_CACHE: Set[str] | None = None



# ------------------------------
# 1) 텍스트 전처리
# ------------------------------
def clean_text(text: str) -> str:
    # 개행 제거 + HTML 제거 + 특수문자 제거 + 다중 공백 정리
    text = text.replace("\r", " ").replace("\n", " ")
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[^가-힣a-zA-Z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()


# ------------------------------
# 2) GitHub 한국어 불용어 로드
# ------------------------------
def get_korean_stopwords_from_github() -> set:
    url = "https://raw.githubusercontent.com/stopwords-iso/stopwords-ko/master/stopwords-ko.txt"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            words = {w.strip() for w in r.text.split("\n") if w.strip()}
            print(f"🌐 GitHub 한국어 불용어 {len(words)}개 불러옴")
            return words
    except Exception as e:
        print("⚠️ GitHub 불용어 불러오기 실패:", e)
    return set()


# ------------------------------
# 3) 불용어 병합 (기본 + GitHub + 로컬)
# ------------------------------
def load_stopwords() -> set:
    global _STOPWORDS_CACHE
    if _STOPWORDS_CACHE is not None:
        return _STOPWORDS_CACHE

    base_stopwords = {
        # 조사/대명사/흔한 서술어
        "것","수","등","더","및","때","저","그","이","가","은","는","의","에","을","를",
        "와","과","도","으로","하다","있다","되다","같다","않다","좋다","많다",
        # 흔한 서술/연결/형식어
        "이번","때문","관련","대한","이후","이전","경우","위해","사용","발생","문제","수준","기준","부분",
        "상황","적용","통해","작업","결과","진행","사항","으로","에서","부터","까지",
        "그리고","하지만","또한","그래서","같습니다","있습니다","합니다","입니다",
        # 일반 명사(분야 무관하게 너무 일반적)
        "서비스","팀","회사","사용자","기능","정보"
    }

    github_stop = get_korean_stopwords_from_github()

    local_stop = set()
    if os.path.exists("./stopwords.txt"):
        with open("./stopwords.txt", "r", encoding="utf-8") as f:
            local_stop = {line.strip() for line in f if line.strip()}
            print(f"📘 로컬 불용어 {len(local_stop)}개 불러옴")

    merged = base_stopwords | github_stop | local_stop
    print(f"✅ 최종 불용어 {len(merged)}개 사용 중")
    _STOPWORDS_CACHE = merged
    return merged


# ------------------------------
# 4) 토크나이즈 + 필터 (공용)
# ------------------------------
def tokenize_and_filter(text: str, stopwords: set) -> List[str]:
    """
    - Okt 명사 추출
    - 불용어 제거
    - 한 글자 제거
    - 의미 빈약 접미(함/됨/성) 제거
    - 숫자 단독(선택) 제거
    """
    okt = Okt()
    text = clean_text(text)
    nouns = okt.nouns(text)

    tokens = []
    for n in nouns:
        if len(n) <= 1:
            continue
        if n in stopwords:
            continue
        if n.endswith(("함", "됨", "성")):  # 예: 발생 -> '발생'은 base_stopwords에 있지만, '발생됨' 같은 류 방지
            continue
        if n.isdigit():
            continue
        tokens.append(n)
    return tokens


# ------------------------------
# 5) 빈도 기반 키워드
# ------------------------------
def extract_keywords(text: str, top_n: int = 10, stopwords: set | None = None) -> List[str]:
    stopwords = stopwords or load_stopwords()
    tokens = tokenize_and_filter(text, stopwords)
    count = Counter(tokens)
    return [w for w, _ in count.most_common(top_n)]


# ------------------------------
# 6) TF-IDF 기반 키워드 (불용어 적용)
# ------------------------------
def extract_keywords_tfidf(text: str, top_n: int = 10, stopwords: set | None = None) -> List[str]:
    """
    한국어 TF-IDF는 기본 토크나이저가 부적합하므로,
    ① Okt로 사전 토크나이즈 → ② 불용어/필터 → ③ 공백-조인 → ④ 벡터라이저
    """

    stopwords = stopwords or load_stopwords()
    tokens = tokenize_and_filter(text, stopwords)
    pretokenized = " ".join(tokens)

    vectorizer = TfidfVectorizer(
        max_features=2000,
        tokenizer=None,          # 미사용 (이미 공백 토큰화됨)
        token_pattern=r"(?u)\b\w+\b",  # 토큰은 공백 분리로 들어오므로 모든 단어 허용
        lowercase=False          # 이미 정규화됨
    )
    X = vectorizer.fit_transform([pretokenized])
    scores = X.toarray()[0]
    terms = vectorizer.get_feature_names_out()

    top_idx = scores.argsort()[-top_n:][::-1]
    return [terms[i] for i in top_idx]


# ------------------------------
# 7) 자동 태깅 (제목 가중치 옵션)
# ------------------------------
def auto_tag_post(title: str, content: str, use_tfidf: bool = False, title_boost: bool = True) -> List[str]:
    stop = load_stopwords()

    # 제목 가중치: 제목을 본문 앞에 2번 더 붙여서(=가중치↑) 중요 단어가 상위로 오도록
    text = (f"{title} " * (3 if title_boost else 1)) + content

    tags = (
        extract_keywords_tfidf(text, top_n=8, stopwords=stop)
        if use_tfidf
        else extract_keywords(text, top_n=8, stopwords=stop)
    )
    # 원형 보존 정렬
    return sorted(set(tags), key=tags.index)



# ------------------------------
# 8) 입력
# ------------------------------
def get_post_content():
    print("❗️❗️input.txt에 미리 복붙해두시는 것을 강력 추천드립니다 -> 추후 2번 선택❗️❗️")
    choice = input("📂 텍스트 입력 방식 선택 (1: 직접 입력 / 2: txt 파일 불러오기): ").strip()
    if choice == "1":
        return input("\n✏️ 포스트 내용을 한 줄로 입력하세요:\n> ")
    elif choice == "2":
        file_path = input("\n📄 불러올 txt 파일 경로를 입력하세요 (기본: ./input.txt): ").strip() or "./input.txt"
        if file_path == "./input.txt":
            print(f"📂 기본 파일 경로로 진행합니다: {file_path}")
        if not os.path.exists(file_path):
            print("🚫 파일을 찾을 수 없습니다.")
            return ""
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read().replace("\r", " ").replace("\n", " ")
    else:
        print("⚠️ 잘못된 선택입니다. 기본값(빈 내용)으로 진행합니다.")
        return ""
    

# ------------------------------
# 9) 저장
# ------------------------------
def save_tags_to_file(tags: List[str], title: str, out_dir: str = "tag_result"):
    os.makedirs(out_dir, exist_ok=True)
    safe_title = re.sub(r"[^가-힣a-zA-Z0-9]", "_", title.strip())
    output_path = os.path.join(out_dir, f"tag_result_{safe_title}.txt")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"✅ 제목: {title}\n\n")
        f.write("✅ 자동 생성된 태그 목록\n\n")
        for tag in tags:
            f.write(f"- {tag}\n")

    print(f"\n💾 태그가 '{output_path}' 파일로 저장되었습니다!")


# ------------------------------
# 10) 실행
# ------------------------------
if __name__ == "__main__":
    print("🚀 Auto Tagging 시작!")
    title = input("📝 포스트 제목을 입력하세요: ").strip()
    content = get_post_content()
    if not content:
        print("❌ 본문이 비어 있습니다. 종료합니다.")
        raise SystemExit

    mode = input("\n⚙️ TF-IDF 기반 분석을 사용할까요? (y/n): ").strip().lower()
    use_tfidf = (mode == "y")

    tags = auto_tag_post(title, content, use_tfidf=use_tfidf, title_boost=True)
    print("\n✅ 자동 생성된 태그:")
    print(", ".join(tags))
    save_tags_to_file(tags, title)