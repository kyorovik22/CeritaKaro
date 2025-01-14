import re
import json
from transformers import pipeline  # type: ignore
from difflib import get_close_matches

# Load dataset cerita
with open("cerita1.json", "r", encoding="utf-8") as f:
    stories = json.load(f)

# Inisialisasi IndoBERT-QA
qa_pipeline = pipeline(
    "question-answering",
    model="Rifky/Indobert-QA",
    tokenizer="Rifky/Indobert-QA"
)

# Preprocessing teks untuk menyamakan format
def preprocess_text(text):
    return re.sub(r"[^\w\s]", "", text.lower())

# Fungsi mencari cerita yang paling cocok berdasarkan judul
def find_story_by_title(input_title):
    processed_titles = [preprocess_text(story["judul"]) for story in stories.values()]
    close_matches = get_close_matches(preprocess_text(input_title), processed_titles, n=1, cutoff=0.6)
    if close_matches:
        for story in stories.values():
            if preprocess_text(story["judul"]) == close_matches[0]:
                return story
    return None

# Fungsi menjawab pertanyaan dengan IndoBERT-QA
def answer_question_with_bert(question, context):
    try:
        result = qa_pipeline({"question": question, "context": context})
        return result["answer"]
    except Exception as e:
        return "Maaf, saya tidak bisa menjawab pertanyaan itu."

# Fungsi utama memproses pertanyaan
def process_question_bert(question, story_title=None):
    if not story_title:
        return "Anda belum memilih cerita. Gunakan /cerita untuk memilih cerita terlebih dahulu."

    story = find_story_by_title(story_title)
    if story:
        context = story["teks"]
        answer = answer_question_with_bert(question, context)
        return f"Judul: {story['judul']}\nJawaban: {answer}"
    else:
        return "Cerita yang dimaksud tidak ditemukan. Silakan coba lagi."

