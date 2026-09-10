import re
import math
from collections import Counter

class NoggimigoIntentAI:
    """
    Advanced local NLP Semantic Intent Classifier for Noggimigo AI.
    Uses pure-Python TF-IDF vectorization, N-gram tokenization, character-level distance,
    and cosine similarity heuristics to classify student intent without heavy dependencies.
    """
    def __init__(self):
        self.stopwords = {
            "i", "think", "maybe", "the", "a", "an", "is", "it", "guess", "umm", "uhh",
            "please", "can", "you", "would", "like", "so", "well", "just", "my", "answer"
        }

        # Dynamic Intent Library mapping intent tags to semantic exemplar phrases & keywords
        self.intent_library = {
            "1/4": [
                "one fourth", "quarter", "1/4", "1-4", "one-fourth", "a quarter",
                "one quarter", "0.25", "25 percent", "one part out of four"
            ],
            "3/4": [
                "three fourths", "three quarters", "3/4", "3-4", "three-fourths",
                "0.75", "75 percent", "three parts out of four"
            ],
            "1/2": [
                "half", "one half", "two fourths", "1/2", "0.5", "50 percent", "one-half"
            ],
            "1/8": [
                "one eighth", "1/8", "0.125", "an eighth", "one-eighth"
            ],
            "subtract 4": [
                "subtract 4", "minus 4", "take away 4", "subtract four", "minus four", "sub 4"
            ],
            "3": [
                "three", "3", "3.0", "equals three"
            ],
            "hint": [
                "help", "hint", "clue", "stuck", "confused", "don't know", "i am lost",
                "give me a hint", "explain this", "can you help"
            ]
        }
        self._build_idf_corpus()

    def _build_idf_corpus(self):
        """Computes Inverse Document Frequency (IDF) dictionary from intent exemplar corpus."""
        doc_count = len(self.intent_library)
        doc_freqs = Counter()

        for phrases in self.intent_library.values():
            unique_words_in_doc = set()
            for phrase in phrases:
                unique_words_in_doc.update(self.tokenize_and_clean(phrase))
            for word in unique_words_in_doc:
                doc_freqs[word] += 1

        self.idf = {}
        for word, count in doc_freqs.items():
            self.idf[word] = math.log((doc_count + 1.0) / (count + 1.0)) + 1.0

    def add_intent(self, intent_tag: str, exemplars: list):
        """Dynamically registers or updates an intent category."""
        if intent_tag in self.intent_library:
            self.intent_library[intent_tag].extend(exemplars)
        else:
            self.intent_library[intent_tag] = exemplars
        self._build_idf_corpus()

    def tokenize_and_clean(self, raw_text: str) -> list:
        """Converts text to lowercase, strips non-alphanumeric punctuation (preserving slashes and decimals)."""
        clean_words = re.sub(r'[^\w/\.]', ' ', raw_text.lower()).split()
        return [word for word in clean_words if word not in self.stopwords]

    def _get_ngrams(self, tokens: list, n: int = 2) -> list:
        """Generates n-grams from a list of tokens."""
        ngrams = []
        for i in range(len(tokens) - n + 1):
            ngrams.append(" ".join(tokens[i:i+n]))
        return ngrams

    def _vectorize_tf_idf(self, tokens: list) -> dict:
        """Creates TF-IDF vector dict for a list of tokens."""
        tf = Counter(tokens)
        total = max(1, len(tokens))
        vec = {}
        for word, count in tf.items():
            term_freq = count / total
            idf_val = self.idf.get(word, 1.0)
            vec[word] = term_freq * idf_val
        return vec

    def _cosine_similarity(self, vec1: dict, vec2: dict) -> float:
        """Computes cosine similarity between two sparse TF-IDF vectors."""
        intersection = set(vec1.keys()) & set(vec2.keys())
        dot_product = sum(vec1[x] * vec2[x] for x in intersection)
        mag1 = math.sqrt(sum(v ** 2 for v in vec1.values()))
        mag2 = math.sqrt(sum(v ** 2 for v in vec2.values()))
        if mag1 == 0 or mag2 == 0:
            return 0.0
        return dot_product / (mag1 * mag2)

    def _string_similarity(self, s1: str, s2: str) -> float:
        """Jaccard character bi-gram similarity for fuzzy spelling matching."""
        s1, s2 = s1.lower(), s2.lower()
        if s1 == s2:
            return 1.0
        set1 = set(s1[i:i+2] for i in range(len(s1)-1))
        set2 = set(s2[i:i+2] for i in range(len(s2)-1))
        if not set1 or not set2:
            return 0.0
        intersection = set1 & set2
        union = set1 | set2
        return len(intersection) / len(union)

    def predict_intent(self, user_sentence: str, min_confidence: float = 0.2) -> dict:
        """
        Semantic Intent Prediction:
        Calculates hybrid TF-IDF Cosine Similarity, N-gram overlap, and Fuzzy String Similarity
        to return predicted intent, confidence score, and classification breakdown.
        """
        user_sentence_clean = user_sentence.strip().lower()
        tokens = self.tokenize_and_clean(user_sentence_clean)
        
        if not tokens:
            return {"intent": None, "confidence": 0.0, "match_type": "EMPTY_INPUT"}

        user_vec = self._vectorize_tf_idf(tokens)
        user_bigrams = set(self._get_ngrams(tokens, n=2))

        best_intent = None
        highest_score = 0.0
        best_match_type = "NONE"

        for intent, exemplars in self.intent_library.items():
            for exemplar in exemplars:
                # 1. Exact string match check
                if user_sentence_clean == exemplar.lower():
                    return {
                        "intent": intent,
                        "confidence": 1.0,
                        "match_type": "EXACT_MATCH",
                        "matched_exemplar": exemplar
                    }

                exemplar_tokens = self.tokenize_and_clean(exemplar)
                exemplar_vec = self._vectorize_tf_idf(exemplar_tokens)
                
                # 2. TF-IDF Cosine Similarity
                cosine_sim = self._cosine_similarity(user_vec, exemplar_vec)

                # 3. N-gram similarity boost
                exemplar_bigrams = set(self._get_ngrams(exemplar_tokens, n=2))
                ngram_sim = 0.0
                if user_bigrams and exemplar_bigrams:
                    ngram_sim = len(user_bigrams & exemplar_bigrams) / len(user_bigrams | exemplar_bigrams)

                # 4. Fuzzy String Similarity
                fuzzy_sim = self._string_similarity(user_sentence_clean, exemplar)

                # Combined Hybrid Semantic Score
                hybrid_score = (0.50 * cosine_sim) + (0.30 * ngram_sim) + (0.20 * fuzzy_sim)

                # Keyword exact token inclusion boost
                if any(t == exemplar.lower() for t in tokens):
                    hybrid_score = max(hybrid_score, 0.85)

                if hybrid_score > highest_score:
                    highest_score = hybrid_score
                    best_intent = intent
                    best_match_type = "SEMANTIC_HYBRID"

        if highest_score < min_confidence:
            return {
                "intent": None,
                "confidence": round(highest_score, 4),
                "match_type": "BELOW_THRESHOLD"
            }

        return {
            "intent": best_intent,
            "confidence": round(highest_score, 4),
            "match_type": best_match_type
        }

# --- Quick AI Test Runner ---
if __name__ == "__main__":
    ai = NoggimigoIntentAI()
    
    test_phrases = [
        "I guess it's a quarter",
        "umm three fourths maybe?",
        "give me a hint please",
        "minus four from both sides",
        "waffles and ice cream"
    ]
    
    print("====================================================")
    print("   NOGGIMIGO LOCAL NLP SEMANTIC INTENT CLASSIFIER   ")
    print("====================================================\n")
    
    for phrase in test_phrases:
        res = ai.predict_intent(phrase)
        print(f"Input:       \"{phrase}\"")
        print(f"Prediction:  {res['intent']} (Confidence: {res['confidence']}, Match: {res['match_type']})\n")
