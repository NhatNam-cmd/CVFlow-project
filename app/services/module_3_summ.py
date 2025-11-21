"""
module_3_summ.py

Module 3 - Tóm tắt văn bản bằng NLTK (Extractive Summarization).

Yêu cầu từ CVFlow:
- Tóm tắt dựa trên tần suất từ (frequency-based).
- Loại bỏ stopwords & dấu câu.
- Chọn ra các câu quan trọng nhất.
- Thiết kế module phải tuân thủ interface BaseSummarizer.
"""

import string
from typing import List
from abc import ABC, abstractmethod

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize


# Tải tài nguyên NLTK
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt")

try:
    nltk.data.find("corpora/stopwords")
except LookupError:
    nltk.download("stopwords")


class BaseSummarizer(ABC):
    """Interface chuẩn cho mọi summarizer."""

    @abstractmethod
    def summarize(self, text: str) -> str:
        """Nhận văn bản đầu vào → trả về văn bản tóm tắt."""
        pass


class NLTKSummarizer(BaseSummarizer):
    """
    Tóm tắt văn bản bằng phương pháp thống kê:

    Quy trình:
    1) sentence tokenize → tách câu
    2) word tokenize + lọc từ
    3) tính tần suất từ (frequency)
    4) chấm điểm từng câu
    5) chọn top N câu quan trọng nhất
    """

    def __init__(self, max_sentences: int = 3):
        self.max_sentences = max_sentences
        self.stopwords = set(stopwords.words("english"))
        self.punctuation = set(string.punctuation)

    def _word_frequency(self, text: str) -> dict:
        """Tính tần suất xuất hiện của các từ hợp lệ."""
        words = word_tokenize(text.lower())
        freq = {}

        for w in words:
            if w in self.stopwords:
                continue
            if w in self.punctuation:
                continue
            if not w.isalpha():
                continue

            freq[w] = freq.get(w, 0) + 1

        return freq

    def _score_sentences(self, sentences: List[str], freq: dict) -> dict:
        """Chấm điểm câu dựa trên tổng điểm các từ trong câu."""
        scores = {}

        for sentence in sentences:
            words = word_tokenize(sentence.lower())
            if not words:
                continue

            score = sum(freq.get(w, 0) for w in words)
            scores[sentence] = score / len(words)

        return scores

    def summarize(self, text: str) -> str:
        """Hàm chính: tóm tắt văn bản."""
        text = text.strip()
        if not text:
            return ""

        sentences = sent_tokenize(text)

        # Nếu văn bản quá ngắn, trả về nguyên bản
        if len(sentences) <= self.max_sentences:
            return text

        freq = self._word_frequency(text)
        if not freq:
            return text

        scores = self._score_sentences(sentences, freq)

        # Lấy các câu có điểm cao nhất
        ranked_sentences = sorted(scores, key=scores.get, reverse=True)
        top_sentences = ranked_sentences[: self.max_sentences]

        # Giữ nguyên thứ tự xuất hiện ban đầu
        summary = [s for s in sentences if s in top_sentences]

        return " ".join(summary)


if __name__ == "__main__":
    # Test nhanh Module 3
    sample_text = """
    Python is a widely used programming language.
    It is popular for data science, AI, machine learning, and automation.
    Developers love Python because it is simple and powerful.
    Python also has a huge ecosystem of libraries.
    """

    summarizer = NLTKSummarizer(max_sentences=2)
    print(summarizer.summarize(sample_text))
