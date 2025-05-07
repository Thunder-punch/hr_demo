import os
import json
import hashlib
import faiss
import numpy as np
from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer

# 경로 설정

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')              # hr_demo/data 폴더
PDF_DIR = os.path.join(BASE_DIR, 'pdfs')
CLEAN_DIR = os.path.join(BASE_DIR, 'clean')
DB_DIR = os.path.join(BASE_DIR, 'db')


os.makedirs(CLEAN_DIR, exist_ok=True)
os.makedirs(DB_DIR, exist_ok=True)

# 설정값
CHUNK_SIZE = 500
EMBED_BATCH = 100
MODEL_NAME = 'all-MiniLM-L6-v2'
seen_hashes = set()
model = SentenceTransformer(MODEL_NAME)

# ─────────────────────────────────────────────
# 유틸 함수

def extract_text_from_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text
    return text.strip()

def split_text(text, size=CHUNK_SIZE):
    return [text[i:i+size] for i in range(0, len(text), size)]

def is_duplicate(text):
    h = hashlib.sha256(text.encode()).hexdigest()
    if h in seen_hashes:
        return True
    seen_hashes.add(h)
    return False

def save_chunks(title, chunks):
    path = os.path.join(CLEAN_DIR, f"{title}.json")
    with open(path, 'w', encoding='utf-8') as f:
        json.dump({"chunks": chunks}, f, ensure_ascii=False)

def already_processed(title):
    path = os.path.join(CLEAN_DIR, f"{title}.json")
    return os.path.exists(path)

# ─────────────────────────────────────────────
# 벡터 DB

class FaissManager:
    def __init__(self, dim, save_dir, max_per_index=10000):
        self.dim = dim
        self.save_dir = save_dir
        self.max_per_index = max_per_index
        self.index = faiss.IndexFlatL2(dim)
        self.count = 0
        self.file_index = 1

    def add(self, vectors):
        self.index.add(vectors)
        self.count += len(vectors)
        if self.count >= self.max_per_index:
            self.flush()

    def flush(self):
        if self.count == 0:
            return
        path = os.path.join(self.save_dir, f"index_{self.file_index:03}.faiss")
        faiss.write_index(self.index, path)
        print(f"✅ 저장 완료: {path} ({self.count} vectors)")
        self.index = faiss.IndexFlatL2(self.dim)
        self.count = 0
        self.file_index += 1

# ─────────────────────────────────────────────
# 메인 실행

def run():
    pdf_files = [f for f in os.listdir(PDF_DIR) if f.endswith('.pdf')]
    print(f"🔍 PDF 파일 {len(pdf_files)}개 발견됨")

    chunk_buffer = []
    manager = FaissManager(dim=384, save_dir=DB_DIR)

    for idx, file in enumerate(pdf_files):
        title = os.path.splitext(file)[0]
        if already_processed(title):
            print(f"[{idx+1}] ⏭️ 이미 처리된 파일: {file}")
            continue

        path = os.path.join(PDF_DIR, file)
        try:
            text = extract_text_from_pdf(path)
            if len(text) < 200:
                print(f"[{idx+1}] ❌ 텍스트 추출 실패 또는 너무 짧음: {file}")
                continue

            chunks = split_text(text)
            final_chunks = [c for c in chunks if not is_duplicate(c)]
            if not final_chunks:
                print(f"[{idx+1}] ⚠️ 중복만 존재: {file}")
                continue

            save_chunks(title, final_chunks)
            chunk_buffer.extend(final_chunks)

            if len(chunk_buffer) >= EMBED_BATCH:
                vectors = model.encode(chunk_buffer)
                manager.add(vectors)
                chunk_buffer.clear()

            print(f"[{idx+1}] ✅ {file} - {len(final_chunks)} chunks")
        except Exception as e:
            print(f"[{idx+1}] ❌ 처리 실패: {file} | {str(e)}")

    if chunk_buffer:
        vectors = model.encode(chunk_buffer)
        manager.add(vectors)
        manager.flush()

# ─────────────────────────────────────────────

if __name__ == '__main__':
    run()
