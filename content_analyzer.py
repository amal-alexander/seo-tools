from collections import Counter
import re
from typing import Dict, List, Any
from bs4 import BeautifulSoup
import trafilatura
import nltk
from transformers import pipeline

class ContentAnalyzer:
    def __init__(self):
        # Initialize text generation pipeline
        try:
            self.generator = pipeline('text-generation', model='gpt2')
        except:
            self.generator = None

        self.default_stop_words = set([
            'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have',
            'i', 'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you',
            'do', 'at', 'this', 'but', 'his', 'by', 'from', 'they',
            'we', 'say', 'her', 'she', 'or', 'an', 'will', 'my', 'one',
            'all', 'would', 'there', 'their', 'what', 'so', 'up', 'out'
        ])

    def _tokenize_words(self, text: str) -> List[str]:
        """Simple word tokenizer using regex"""
        text = text.lower()
        words = re.findall(r'\b\w+\b', text)
        return words

    def _tokenize_sentences(self, text: str) -> List[str]:
        """Simple sentence tokenizer"""
        # Split on periods, exclamation marks, and question marks
        sentences = re.split(r'[.!?]+', text)
        # Remove empty sentences and strip whitespace
        return [s.strip() for s in sentences if s.strip()]

    def analyze_content(self, text: str, competitor_urls: List[str] = None) -> Dict[str, Any]:
        """Analyze content for various metrics including trigram analysis"""
        if not text:
            return {
                "word_count": 0,
                "readability_score": 0,
                "keyword_density": 0,
                "top_keywords": [],
                "trigram_analysis": [],
                "competitor_analysis": None
            }

        # Calculate basic metrics using custom tokenizers
        words = self._tokenize_words(text)
        word_count = len(words)

        try:
            # Calculate readability (Flesch Reading Ease)
            sentences = self._tokenize_sentences(text)
            num_sentences = len(sentences)
            syllables = sum([self._count_syllables(word) for word in words])
            if num_sentences > 0:
                readability_score = 206.835 - 1.015 * (word_count / num_sentences) - 84.6 * (syllables / word_count)
            else:
                readability_score = 0
        except Exception as e:
            print(f"Error calculating readability: {str(e)}")
            readability_score = 0

        # Calculate trigram density
        text_trigrams = self._get_trigram_density(text)

        # Analyze competitors if provided
        competitor_analysis = None
        if competitor_urls:
            competitor_analysis = self._analyze_competitors(text, competitor_urls)

        # Get keywords and density
        keywords = self._extract_keywords(text)
        keyword_density = len(keywords) / word_count if word_count > 0 else 0

        # Get top keywords
        top_keywords = Counter(keywords).most_common(10)

        return {
            "word_count": word_count,
            "readability_score": readability_score,
            "keyword_density": keyword_density,
            "top_keywords": top_keywords,
            "trigram_analysis": text_trigrams[:20],  # Top 20 trigrams
            "competitor_analysis": competitor_analysis
        }

    def get_ai_suggestions(self, content: str, meta_info: Dict[str, str]) -> Dict[str, Any]:
        """Get AI-powered suggestions using Hugging Face"""
        if not self.generator:
            return {
                "content_improvements": ["AI model not available"],
                "seo_recommendations": ["Model loading failed"],
                "keyword_suggestions": []
            }

        try:
            # Generate content improvement suggestions
            prompt = f"Content improvements for: {content[:200]}..."
            content_suggestions = self.generator(
                prompt,
                max_new_tokens=100,
                num_return_sequences=3,
                pad_token_id=self.generator.tokenizer.eos_token_id
            )

            # Generate SEO recommendations
            seo_prompt = f"SEO recommendations for website with title: {meta_info.get('title', '')}"
            seo_suggestions = self.generator(
                seo_prompt,
                max_new_tokens=100,
                num_return_sequences=3,
                pad_token_id=self.generator.tokenizer.eos_token_id
            )

            # Generate keyword suggestions
            keyword_prompt = f"Keywords related to: {meta_info.get('title', '')} {meta_info.get('meta_description', '')}"
            keyword_suggestions = self.generator(
                keyword_prompt,
                max_new_tokens=50,
                num_return_sequences=5,
                pad_token_id=self.generator.tokenizer.eos_token_id
            )

            return {
                "content_improvements": [sugg['generated_text'] for sugg in content_suggestions],
                "seo_recommendations": [sugg['generated_text'] for sugg in seo_suggestions],
                "keyword_suggestions": [sugg['generated_text'] for sugg in keyword_suggestions]
            }
        except Exception as e:
            return {
                "content_improvements": ["Error generating suggestions"],
                "seo_recommendations": [str(e)],
                "keyword_suggestions": []
            }

    def _get_trigram_density(self, text: str) -> List[Dict[str, Any]]:
        """Calculate trigram frequencies in the text"""
        words = self._tokenize_words(text)

        # Generate trigrams manually
        trigrams = []
        for i in range(len(words) - 2):
            trigrams.append((words[i], words[i+1], words[i+2]))

        # Count trigram frequencies
        trigram_freq = Counter(trigrams)
        total_trigrams = len(trigrams) if trigrams else 1

        # Format results
        return [
            {
                "trigram": " ".join(t),
                "count": count,
                "density": count / total_trigrams
            }
            for t, count in trigram_freq.most_common()
        ]

    def _analyze_competitors(self, main_text: str, competitor_urls: List[str]) -> Dict[str, Any]:
        """Compare content with competitor websites"""
        main_trigrams = set(" ".join(t) for t in self._get_trigram_density(main_text))
        competitor_data = []

        for url in competitor_urls:
            try:
                # Fetch competitor content
                downloaded = trafilatura.fetch_url(url)
                competitor_text = trafilatura.extract(downloaded)

                if competitor_text:
                    # Get competitor trigrams
                    competitor_trigrams = set(" ".join(t) for t in self._get_trigram_density(competitor_text))

                    # Calculate overlap and unique phrases
                    common_phrases = main_trigrams.intersection(competitor_trigrams)
                    unique_to_competitor = competitor_trigrams - main_trigrams

                    competitor_data.append({
                        "url": url,
                        "common_phrases": list(common_phrases)[:10],  # Top 10 common phrases
                        "unique_phrases": list(unique_to_competitor)[:10],  # Top 10 unique phrases
                        "similarity_score": len(common_phrases) / len(main_trigrams) if main_trigrams else 0
                    })

            except Exception as e:
                competitor_data.append({
                    "url": url,
                    "error": str(e)
                })

        return {
            "analyzed_competitors": len(competitor_data),
            "competitor_insights": competitor_data
        }

    def _count_syllables(self, word: str) -> int:
        """Count syllables in a word"""
        word = word.lower()
        count = 0
        vowels = "aeiouy"
        if word[0] in vowels:
            count += 1
        for index in range(1, len(word)):
            if word[index] in vowels and word[index - 1] not in vowels:
                count += 1
        if word.endswith("e"):
            count -= 1
        if count == 0:
            count += 1
        return count

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        # Remove common words and punctuation
        text = re.sub(r'[^\w\s]', '', text.lower())
        words = self._tokenize_words(text)
        keywords = [word for word in words if word not in self.default_stop_words and len(word) > 2]
        return keywords