#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prompt / Response 블록을 Notion 토글로 붙여넣기 좋게 변환하는 스크립트.

지원 입력 포맷:
  1) 마크다운 헤더형
        ## Prompt:
        <프롬프트>
        ## Response:
        <응답>
  2) 라벨형
        Prompt:
        <프롬프트>
        Response:
        <응답>

출력 모드(택1):
  A) 기본(Markdown 유사)  : 토글 비슷한 들여쓰기 (상황에 따라 인용/리스트 처리될 수 있음)
  B) --html               : <details><summary>...</summary>...</details> (붙여넣기 환경에 따라 코드블록 처리될 수 있음)
  C) --toggle             : "아이콘 + 들여쓰기" 기반 토글 전용 포맷 (TXT→Notion 붙여넣기에 안정적)

옵션:
  --no-labels : "Prompt:" / "Response:" 라벨 제거
  --html      : HTML <details>/<summary> 포맷으로 출력
  --toggle    : 토글 전용 포맷으로 출력 (권장)

예시:
  python to_notion_toggle.py --in chat.txt --toggle --no-labels --out notion.md
"""

import re
import sys
import argparse
import html

def _normalize_prompt_line(prompt_block: str) -> str:
    """프롬프트 블록(여러 줄)을 한 줄로 요약"""
    return " ".join(line.strip() for line in prompt_block.strip().splitlines() if line.strip()) or "(빈 프롬프트)"

def _parse_pairs(text: str):
    """텍스트에서 (prompt, response) 페어들을 추출"""
    # 1) 마크다운 헤더형
    pattern_h = re.compile(
        r'##\s*Prompt:\s*(.*?)\s*##\s*Response:\s*(.*?)(?=\n##\s*Prompt:|\Z)',
        re.DOTALL | re.IGNORECASE
    )
    matches = pattern_h.findall(text)
    if matches:
        return matches

    # 2) 라벨형
    pattern_p = re.compile(
        r'^\s*Prompt:\s*(.*?)\s*^\s*Response:\s*(.*?)(?=^\s*Prompt:|\Z)',
        re.DOTALL | re.IGNORECASE | re.MULTILINE
    )
    matches2 = pattern_p.findall(text)
    if matches2:
        return matches2

    # 매칭이 전혀 안 되면 전체를 하나의 응답으로 취급 (프롬프트는 빈 값)
    return [("", text)]

def convert_to_toggle_md(text: str, no_labels: bool = False) -> str:
    """마크다운 유사(기본) 출력: 토글처럼 보이게 들여쓰기 구성"""
    out_lines = []
    pairs = _parse_pairs(text)
    for prompt, response in pairs:
        title = _normalize_prompt_line(prompt)
        if no_labels:
            out_lines.append(f"> {title}")
        else:
            out_lines.append(f"> Prompt: {title}")
        resp_lines = response.strip("\n").splitlines()
        if not no_labels:
            out_lines.append("\tResponse:")
        for line in resp_lines:
            out_lines.append("\t" + line if line.strip() else "")
        out_lines.append("")
    return "\n".join(out_lines).rstrip() + "\n"

def _escape_html(s: str) -> str:
    """HTML 안전하게 이스케이프"""
    return html.escape(s, quote=True)

def convert_to_toggle_html(text: str, no_labels: bool = False) -> str:
    """HTML <details>/<summary> 출력"""
    blocks = []
    pairs = _parse_pairs(text)
    for prompt, response in pairs:
        title = _normalize_prompt_line(prompt)
        summary = title if no_labels else f"Prompt: {title}"
        summary_html = _escape_html(summary)
        resp = response.strip("\n")
        if no_labels:
            body = resp
        else:
            body = "Response:\n" + resp if resp else "Response:"
        body_html = _escape_html(body).replace("\n", "<br>")
        block = f"<details><summary>{summary_html}</summary>\n{body_html}\n</details>"
        blocks.append(block)
    return "\n\n".join(blocks) + "\n"

def convert_to_toggle_plain(text: str, no_labels: bool = False, bullet: str = "▸ ", indent: str = "    ") -> str:
    """
    토글 전용 출력(권장):
      ▸ <제목>
          <본문 (들여쓰기)>
    """
    out_lines = []
    pairs = _parse_pairs(text)
    for prompt, response in pairs:
        title = _normalize_prompt_line(prompt)
        # 제목 라벨 처리
        line_title = (title if no_labels else f"Prompt: {title}")
        out_lines.append(f"{bullet}{line_title}")
        # 본문 라벨 처리
        resp = response.strip("\n")
        if not no_labels:
            out_lines.append(f"{indent}Response:")
        for ln in resp.splitlines():
            if ln.strip():
                out_lines.append(f"{indent}{ln}")
            else:
                out_lines.append("")  # 빈 줄은 그대로 유지
        out_lines.append("")  # 블록 간 공백
    return "\n".join(out_lines).rstrip() + "\n"

def main():
    ap = argparse.ArgumentParser(description="Prompt/Response -> Notion 토글 변환기")
    ap.add_argument("--in", dest="infile", default=None, help="입력 파일 경로 (기본: stdin)")
    ap.add_argument("--out", dest="outfile", default=None, help="출력 파일 경로 (기본: stdout)")
    ap.add_argument("--no-labels", action="store_true", help="'Prompt:' / 'Response:' 라벨 제거")
    ap.add_argument("--html", action="store_true", help="HTML <details>/<summary> 포맷으로 출력")
    ap.add_argument("--toggle", action="store_true", help="아이콘 + 들여쓰기 기반 토글 전용 포맷으로 출력")
    ap.add_argument("--bullet", default="▸ ", help="토글 제목 앞에 붙일 기호(기본: '▸ ')")
    ap.add_argument("--indent", default="    ", help="본문 들여쓰기(기본: 공백 4칸). 예: '\\t' 또는 '  '")
    args = ap.parse_args()

    # 입력 읽기
    if args.infile:
        with open(args.infile, "r", encoding="utf-8") as f:
            raw = f.read()
    else:
        raw = sys.stdin.read()

    # 들여쓰기 커스터마이즈 지원
    indent = "\t" if args.indent == r"\t" else args.indent

    # 변환
    if args.html:
        converted = convert_to_toggle_html(raw, no_labels=args.no_labels)
    elif args.toggle:
        converted = convert_to_toggle_plain(raw, no_labels=args.no_labels, bullet=args.bullet, indent=indent)
    else:
        converted = convert_to_toggle_md(raw, no_labels=args.no_labels)

    # 출력
    if args.outfile:
        with open(args.outfile, "w", encoding="utf-8") as f:
            f.write(converted)
    else:
        sys.stdout.write(converted)

if __name__ == "__main__":
    main()
