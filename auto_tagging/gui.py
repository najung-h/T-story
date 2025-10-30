# gui.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from datetime import datetime

# 네 로직 import
from auto_tagging import (
    auto_tag_post, save_tags_to_file, load_stopwords
)

ROOT = Path(__file__).parent
INPUT_PATH = ROOT / "input.txt"
STOPWORDS_PATH = ROOT / "stopwords.txt"
OUT_DIR = ROOT / "tag_result"
OUT_DIR.mkdir(exist_ok=True)

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Auto Tagging (Tkinter)")
        self.geometry("980x680")
        self.minsize(900, 600)

        # 상태값
        self.var_tfidf = tk.BooleanVar(value=False)
        self.var_title_boost = tk.BooleanVar(value=True)

        # --- 상단: 제목/옵션/버튼 ---
        top = ttk.Frame(self, padding=(8, 8, 8, 0))
        top.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(top, text="제목").grid(row=0, column=0, sticky="w")
        self.ent_title = ttk.Entry(top)
        self.ent_title.grid(row=0, column=1, sticky="we", padx=6)
        top.columnconfigure(1, weight=1)

        ttk.Checkbutton(top, text="TF-IDF 사용", variable=self.var_tfidf).grid(row=0, column=2, padx=6)
        ttk.Checkbutton(top, text="제목 가중치", variable=self.var_title_boost).grid(row=0, column=3, padx=6)

        ttk.Button(top, text="input.txt 열기", command=self.load_from_file).grid(row=0, column=4, padx=6)
        ttk.Button(top, text="실행", style="Accent.TButton", command=self.run).grid(row=0, column=5, padx=6)
        ttk.Button(top, text="저장", command=self.save).grid(row=0, column=6, padx=6)

        # --- 좌우 패널 ---
        pan = ttk.Panedwindow(self, orient="horizontal")
        pan.pack(fill="both", expand=True, padx=8, pady=8)

        # 좌: 본문 입력
        left = ttk.Frame(pan)
        pan.add(left, weight=3)
        ttk.Label(left, text="본문 (여기에 붙여넣거나 input.txt로 불러오기)").pack(anchor="w")
        self.txt = tk.Text(left, wrap="word")
        self.txt.pack(fill="both", expand=True)

        # 우: 결과/로그
        right = ttk.Frame(pan)
        pan.add(right, weight=2)

        ttk.Label(right, text="생성된 태그").pack(anchor="w")
        self.lst = tk.Listbox(right, height=12)
        self.lst.pack(fill="both", expand=True)

        ttk.Label(right, text="로그").pack(anchor="w", pady=(8,0))
        self.log = tk.Text(right, height=8)
        self.log.pack(fill="both", expand=False)

        # 스타일 (Windows 11/10에서 버튼 강조)
        try:
            style = ttk.Style(self)
            style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"))
        except Exception:
            pass

        # 초기 input.txt 로드
        if INPUT_PATH.exists():
            try:
                self.txt.delete("1.0", tk.END)
                self.txt.insert(tk.END, INPUT_PATH.read_text(encoding="utf-8", errors="ignore"))
                self.write_log(f"input.txt 불러옴: {INPUT_PATH}")
            except Exception as e:
                self.write_log(f"input.txt 로드 실패: {e}")

    # ---------- 유틸 ----------
    def write_log(self, msg: str):
        self.log.insert(tk.END, f"{msg}\n")
        self.log.see(tk.END)

    # ---------- 콜백 ----------
    def load_from_file(self):
        path = filedialog.askopenfilename(
            initialdir=str(ROOT),
            filetypes=[("Text", "*.txt"), ("All", "*.*")]
        )
        if not path:
            return
        try:
            text = Path(path).read_text(encoding="utf-8", errors="ignore")
            self.txt.delete("1.0", tk.END)
            self.txt.insert(tk.END, text)
            self.write_log(f"파일 로드: {path}")
        except Exception as e:
            messagebox.showerror("오류", f"파일 열기 실패\n{e}")

    def run(self):
        title = self.ent_title.get().strip()
        content = self.txt.get("1.0", tk.END).strip()
        if not content:
            messagebox.showwarning("알림", "본문이 비어 있습니다.")
            return
        if not title:
            # 제목 비었으면 임시 제목 부여
            title = f"untitled_{datetime.now().strftime('%H%M%S')}"
            self.ent_title.insert(0, title)

        try:
            # 불용어는 내부에서 load_stopwords() 호출됨 (캐시 사용)
            tags = auto_tag_post(
                title=title,
                content=content,
                use_tfidf=self.var_tfidf.get(),
                title_boost=self.var_title_boost.get()
            )

            # 리스트 갱신
            self.lst.delete(0, tk.END)
            for t in tags:
                self.lst.insert(tk.END, t)

            self.write_log(f"태그 {len(tags)}개 생성: {', '.join(tags)}")

        except Exception as e:
            messagebox.showerror("오류", f"분석 중 오류가 발생했습니다.\n{e}")
            self.write_log(f"[오류] {e}")

    def save(self):
        title = self.ent_title.get().strip() or "untitled"
        tags = [self.lst.get(i) for i in range(self.lst.size())]
        if not tags:
            messagebox.showinfo("알림", "저장할 태그가 없습니다. 먼저 실행을 눌러주세요.")
            return
        try:
            save_tags_to_file(tags, title, out_dir=str(OUT_DIR))
            out = OUT_DIR / f"tag_result_{''.join([c if c.isalnum() else '_' for c in title])}.txt"
            self.write_log(f"저장 완료: {out}")
            messagebox.showinfo("완료", f"태그 저장 완료\n{out}")
        except Exception as e:
            messagebox.showerror("오류", f"저장 실패\n{e}")
            self.write_log(f"[오류] 저장 실패: {e}")

if __name__ == "__main__":
    App().mainloop()
