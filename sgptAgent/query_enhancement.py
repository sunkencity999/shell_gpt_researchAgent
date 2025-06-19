"""
Enhanced query construction and entity recognition module for ResearchAgent.
Implements NER, query expansion, and context-aware query rewriting.
"""

import re
import os
import sys
from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict, Counter

# Optional imports with fallbacks
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    print("[WARNING] spaCy not available. Falling back to regex-based entity extraction.")

try:
    import nltk
    from nltk.corpus import wordnet
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False
    print("[WARNING] NLTK not available. Query expansion will be limited.")

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("[WARNING] scikit-learn not available. Advanced relevance scoring disabled.")


class QueryEnhancer:
    """Enhanced query construction with NER, expansion, and context awareness."""
    
    def __init__(self):
        self.nlp = None
        self.domain_keywords = self._load_domain_keywords()
        self.synonym_cache = {}
        self._initialize_nlp()
    
    def _initialize_nlp(self):
        """Initialize NLP components with fallbacks."""
        global SPACY_AVAILABLE, NLTK_AVAILABLE, SKLEARN_AVAILABLE
        
        if SPACY_AVAILABLE:
            try:
                # Try to load English model
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                try:
                    # Fallback to larger model
                    self.nlp = spacy.load("en_core_web_md")
                except OSError:
                    print("[WARNING] No spaCy English model found. Install with: python -m spacy download en_core_web_sm")
                    SPACY_AVAILABLE = False
        
        if NLTK_AVAILABLE:
            try:
                # Download required NLTK data
                nltk.download('wordnet', quiet=True)
                nltk.download('omw-1.4', quiet=True)
                nltk.download('punkt', quiet=True)
                nltk.download('stopwords', quiet=True)
            except Exception as e:
                print(f"[WARNING] NLTK data download failed: {e}")
    
    def _load_domain_keywords(self) -> Dict[str, List[str]]:
        """Load domain-specific keywords for query enhancement."""
        return {
            'sports': [
                'team', 'player', 'game', 'season', 'championship', 'league', 'score', 'win', 'loss', 'record', 'statistics', 'performance',
                'vs', 'versus', 'compare', 'comparison', 'better', 'best', 'worst', 'ranking', 'standings', 'playoff', 'tournament',
                'decade', 'years', 'career', 'stats', 'ERA', 'batting', 'pitching', 'defense', 'offense', 'wins', 'losses'
            ],
            'technology': [
                'software', 'hardware', 'algorithm', 'system', 'platform', 'framework', 'API', 'database', 'security', 'performance',
                'vs', 'versus', 'compare', 'comparison', 'better', 'best', 'benchmark', 'evaluation', 'review', 'analysis',
                'latest', 'new', 'update', 'version', 'features', 'specifications', 'requirements', 'compatibility'
            ],
            'business': [
                'company', 'market', 'revenue', 'profit', 'strategy', 'competition', 'industry', 'growth', 'investment', 'financial',
                'vs', 'versus', 'compare', 'comparison', 'better', 'performance', 'metrics', 'KPI', 'ROI', 'analysis',
                'quarterly', 'annual', 'fiscal', 'earnings', 'stock', 'valuation', 'market share', 'competitive advantage'
            ],
            'science': [
                'research', 'study', 'experiment', 'data', 'analysis', 'theory', 'hypothesis', 'methodology', 'findings', 'publication',
                'compare', 'comparison', 'versus', 'meta-analysis', 'systematic review', 'evidence', 'results', 'conclusions',
                'recent', 'latest', 'current', 'peer-reviewed', 'journal', 'academic', 'scholarly', 'empirical'
            ],
            'health': [
                'treatment', 'diagnosis', 'symptoms', 'disease', 'medicine', 'therapy', 'patient', 'clinical', 'medical', 'healthcare',
                'compare', 'comparison', 'versus', 'efficacy', 'effectiveness', 'safety', 'side effects', 'outcomes', 'prognosis',
                'clinical trial', 'study', 'research', 'evidence-based', 'guidelines', 'recommendations', 'best practices'
            ],
            'politics': [
                'government', 'policy', 'election', 'legislation', 'political', 'democracy', 'vote', 'candidate', 'party', 'administration',
                'compare', 'comparison', 'versus', 'debate', 'position', 'stance', 'record', 'polling', 'approval rating',
                'term', 'tenure', 'presidency', 'congress', 'senate', 'house', 'supreme court', 'federal', 'state', 'local'
            ],
            'finance': [
                'investment', 'stock', 'bond', 'portfolio', 'return', 'risk', 'market', 'trading', 'valuation', 'analysis',
                'compare', 'comparison', 'versus', 'performance', 'benchmark', 'yield', 'dividend', 'growth', 'volatility',
                'bull market', 'bear market', 'recession', 'inflation', 'interest rate', 'economic', 'financial'
            ],
            'education': [
                'school', 'university', 'college', 'student', 'teacher', 'curriculum', 'degree', 'program', 'course', 'learning',
                'compare', 'comparison', 'versus', 'ranking', 'rating', 'accreditation', 'admission', 'tuition', 'quality',
                'academic', 'scholarship', 'graduation', 'enrollment', 'faculty', 'research', 'campus', 'online'
            ],
            'general': [
                'compare', 'comparison', 'versus', 'vs', 'better', 'best', 'worst', 'difference', 'analysis', 'review',
                'pros', 'cons', 'advantages', 'disadvantages', 'benefits', 'drawbacks', 'evaluation', 'assessment'
            ]
        }
    
    def extract_entities_advanced(self, text: str) -> Dict[str, List[str]]:
        """Extract entities using spaCy NER with fallback to regex."""
        entities = {
            'PERSON': [],
            'ORG': [],
            'GPE': [],  # Geopolitical entities
            'DATE': [],
            'MONEY': [],
            'PRODUCT': [],
            'EVENT': [],
            'OTHER': []
        }
        
        if self.nlp and SPACY_AVAILABLE:
            # Use spaCy NER
            doc = self.nlp(text)
            for ent in doc.ents:
                label = ent.label_
                if label in ['PERSON', 'ORG', 'GPE', 'DATE', 'MONEY', 'PRODUCT', 'EVENT']:
                    entities[label].append(ent.text.strip())
                else:
                    entities['OTHER'].append(ent.text.strip())
        else:
            # Fallback to regex-based extraction
            entities = self._extract_entities_regex(text)
        
        # Clean and deduplicate
        for key in entities:
            entities[key] = list(set([e for e in entities[key] if len(e.strip()) > 1]))
        
        return entities
    
    def _extract_entities_regex(self, text: str) -> Dict[str, List[str]]:
        """Fallback regex-based entity extraction."""
        entities = defaultdict(list)
        
        # Organizations and proper nouns (multi-word)
        org_pattern = r'\b([A-Z][a-zA-Z]+(?: [A-Z][a-zA-Z0-9]+)+)\b'
        for match in re.finditer(org_pattern, text):
            entities['ORG'].append(match.group(1))
        
        # Single capitalized words (potential names/places)
        name_pattern = r'\b([A-Z][a-zA-Z]{2,})\b'
        for match in re.finditer(name_pattern, text):
            word = match.group(1)
            if word not in ['The', 'This', 'That', 'These', 'Those', 'When', 'Where', 'What', 'How', 'Why']:
                entities['OTHER'].append(word)
        
        # Dates and years
        date_pattern = r'\b(19|20)\d{2}(?:-\d{2}(?:-\d{2})?)?\b|\b\d{1,2}/\d{1,2}/\d{2,4}\b'
        for match in re.finditer(date_pattern, text):
            entities['DATE'].append(match.group(0))
        
        # Money amounts
        money_pattern = r'\$[\d,]+(?:\.\d{2})?|\b\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:dollars?|USD|million|billion)\b'
        for match in re.finditer(money_pattern, text, re.IGNORECASE):
            entities['MONEY'].append(match.group(0))
        
        return dict(entities)
    
    def detect_domain(self, text: str) -> str:
        """Detect the primary domain/topic of the research query with improved scoring."""
        text_lower = text.lower()
        domain_scores = {}
        
        # Check for comparison keywords first
        comparison_keywords = ['vs', 'versus', 'compare', 'comparison', 'better', 'best', 'worst', 'difference']
        is_comparison = any(keyword in text_lower for keyword in comparison_keywords)
        
        for domain, keywords in self.domain_keywords.items():
            score = 0
            keyword_matches = []
            
            for keyword in keywords:
                if keyword in text_lower:
                    # Weight scoring based on keyword importance
                    if keyword in comparison_keywords:
                        score += 2  # Comparison keywords get higher weight
                    elif keyword in ['team', 'player', 'company', 'research', 'treatment', 'government']:
                        score += 3  # Domain-specific core keywords get highest weight
                    else:
                        score += 1  # Regular keywords
                    keyword_matches.append(keyword)
            
            # Bonus for multiple keyword matches in same domain
            if len(keyword_matches) > 2:
                score += len(keyword_matches) * 0.5
            
            # Special handling for general domain
            if domain == 'general' and is_comparison and not domain_scores:
                score += 1  # Boost general domain for comparison queries without clear domain
            
            if score > 0:
                domain_scores[domain] = score
        
        # If multiple domains detected, prefer the one with highest score
        if domain_scores:
            # For comparison queries, prefer specific domains over general
            if is_comparison and len(domain_scores) > 1 and 'general' in domain_scores:
                # Remove general if other domains are present for comparisons
                other_domains = {k: v for k, v in domain_scores.items() if k != 'general'}
                if other_domains:
                    domain_scores = other_domains
            
            return max(domain_scores, key=domain_scores.get)
        
        return 'general'
    
    def expand_query_with_synonyms(self, query: str, max_synonyms: int = 3) -> List[str]:
        """Expand query with synonyms using WordNet."""
        if not NLTK_AVAILABLE:
            return [query]
        
        expanded_queries = [query]
        words = re.findall(r'\b\w+\b', query.lower())
        
        for word in words:
            if word in self.synonym_cache:
                synonyms = self.synonym_cache[word]
            else:
                synonyms = []
                try:
                    synsets = wordnet.synsets(word)
                    for synset in synsets[:2]:  # Limit to first 2 synsets
                        for lemma in synset.lemmas()[:2]:  # Limit to first 2 lemmas
                            synonym = lemma.name().replace('_', ' ')
                            if synonym != word and len(synonym) > 2:
                                synonyms.append(synonym)
                except Exception:
                    pass
                
                self.synonym_cache[word] = synonyms[:max_synonyms]
                synonyms = self.synonym_cache[word]
            
            # Create expanded queries with synonyms
            for synonym in synonyms:
                expanded_query = query.replace(word, synonym, 1)
                if expanded_query not in expanded_queries:
                    expanded_queries.append(expanded_query)
        
        return expanded_queries[:5]  # Limit to 5 total queries
    
    def generate_contextual_queries(self, main_query: str, entities: Dict[str, List[str]], 
                                  domain: str) -> List[str]:
        """Generate context-aware queries based on entities and domain."""
        queries = [main_query]
        
        # Entity-focused queries
        if entities.get('ORG'):
            for org in entities['ORG'][:2]:
                queries.append(f'"{org}" {main_query}')
        
        if entities.get('PERSON'):
            for person in entities['PERSON'][:2]:
                queries.append(f'"{person}" {main_query}')
        
        if entities.get('GPE'):
            for place in entities['GPE'][:2]:
                queries.append(f'{main_query} {place}')
        
        # Date-specific queries
        if entities.get('DATE'):
            for date in entities['DATE'][:2]:
                queries.append(f'{main_query} {date}')
        
        # Domain-specific enhancements
        domain_keywords = self.domain_keywords.get(domain, [])
        if domain_keywords:
            # Add most relevant domain keywords
            for keyword in domain_keywords[:3]:
                if keyword.lower() not in main_query.lower():
                    queries.append(f'{main_query} {keyword}')
        
        # Comparative queries if multiple entities
        if len(entities.get('ORG', [])) >= 2:
            org1, org2 = entities['ORG'][:2]
            queries.append(f'"{org1}" vs "{org2}"')
            queries.append(f'compare "{org1}" "{org2}"')
        
        # Remove duplicates while preserving order
        seen = set()
        unique_queries = []
        for query in queries:
            if query.lower() not in seen:
                seen.add(query.lower())
                unique_queries.append(query)
        
        return unique_queries[:8]  # Limit to 8 queries max
    
    def enhance_query(self, original_query: str, research_goal: str = "", 
                     context_steps: List[str] = None) -> Dict[str, any]:
        """Main method to enhance a query with all improvements and fallback strategies."""
        context_steps = context_steps or []
        
        # Combine all text for entity extraction
        full_text = f"{research_goal} {original_query} " + " ".join(context_steps)
        
        # Extract entities
        entities = self.extract_entities_advanced(full_text)
        
        # Detect domain
        domain = self.detect_domain(full_text)
        
        # Generate multiple types of enhanced queries with fallback strategies
        enhanced_queries = []
        
        # Strategy 1: Synonym expansion (always works)
        try:
            expanded_queries = self.expand_query_with_synonyms(original_query)
            enhanced_queries.extend(expanded_queries)
        except Exception:
            enhanced_queries.append(original_query)  # Fallback to original
        
        # Strategy 2: Entity-based contextual queries
        try:
            contextual_queries = self.generate_contextual_queries(original_query, entities, domain)
            enhanced_queries.extend(contextual_queries)
        except Exception:
            # Fallback: simple entity addition if available
            if entities.get('ORG'):
                enhanced_queries.append(f'{original_query} {entities["ORG"][0]}')
            if entities.get('PERSON'):
                enhanced_queries.append(f'{original_query} {entities["PERSON"][0]}')
        
        # Strategy 3: Domain-specific query enhancement
        try:
            domain_queries = self._generate_domain_specific_queries(original_query, domain, entities)
            enhanced_queries.extend(domain_queries)
        except Exception:
            # Fallback: add basic domain keywords
            domain_keywords = self.domain_keywords.get(domain, [])
            if domain_keywords:
                enhanced_queries.append(f'{original_query} {domain_keywords[0]}')
        
        # Strategy 4: Temporal and comparative fallbacks
        try:
            fallback_queries = self._generate_fallback_queries(original_query, entities, research_goal)
            enhanced_queries.extend(fallback_queries)
        except Exception:
            pass  # Silent fallback
        
        # Remove duplicates while preserving order
        seen = set()
        unique_queries = []
        for query in enhanced_queries:
            query_clean = query.strip().lower()
            if query_clean and query_clean not in seen and len(query.strip()) > 2:
                seen.add(query_clean)
                unique_queries.append(query.strip())
        
        # Ensure we always have at least the original query
        if not unique_queries:
            unique_queries = [original_query]
        elif original_query not in unique_queries:
            unique_queries.insert(0, original_query)
        
        # Limit to reasonable number of queries
        final_queries = unique_queries[:10]
        
        return {
            'original_query': original_query,
            'enhanced_queries': final_queries,
            'entities': entities,
            'domain': domain,
            'primary_query': final_queries[0],
            'fallback_queries': final_queries[1:] if len(final_queries) > 1 else [original_query]
        }
    
    def _generate_domain_specific_queries(self, query: str, domain: str, entities: Dict) -> List[str]:
        """Generate domain-specific enhanced queries."""
        queries = []
        domain_keywords = self.domain_keywords.get(domain, [])
        
        # Add domain-specific terms
        for keyword in domain_keywords[:3]:
            if keyword.lower() not in query.lower():
                queries.append(f'{query} {keyword}')
        
        # Domain-specific patterns
        if domain == 'sports':
            queries.extend([
                f'{query} statistics',
                f'{query} performance analysis',
                f'{query} season records'
            ])
        elif domain == 'business':
            queries.extend([
                f'{query} financial performance',
                f'{query} market analysis',
                f'{query} competitive comparison'
            ])
        elif domain == 'technology':
            queries.extend([
                f'{query} technical specifications',
                f'{query} performance benchmarks',
                f'{query} feature comparison'
            ])
        elif domain == 'science':
            queries.extend([
                f'{query} research studies',
                f'{query} scientific evidence',
                f'{query} peer reviewed'
            ])
        
        return queries
    
    def _generate_fallback_queries(self, query: str, entities: Dict, research_goal: str) -> List[str]:
        """Generate fallback queries when other strategies fail."""
        queries = []
        
        # Temporal fallbacks
        current_year = 2025
        queries.extend([
            f'{query} {current_year}',
            f'{query} recent',
            f'{query} latest',
            f'{query} current'
        ])
        
        # Comparison fallbacks
        comparison_words = ['vs', 'versus', 'compare', 'comparison', 'better']
        if any(word in query.lower() for word in comparison_words):
            queries.extend([
                f'{query} analysis',
                f'{query} pros cons',
                f'{query} differences',
                f'{query} advantages disadvantages'
            ])
        
        # Question-based fallbacks
        if '?' not in query:
            queries.extend([
                f'what is {query}',
                f'how does {query} work',
                f'why {query}'
            ])
        
        # Research-specific fallbacks
        if research_goal and len(research_goal) > 10:
            # Extract key terms from research goal
            goal_words = [word for word in research_goal.split() if len(word) > 3]
            if goal_words:
                queries.append(f'{query} {goal_words[0]}')
        
        return queries


class RelevanceScorer:
    """Advanced relevance scoring for search results."""
    
    def __init__(self):
        self.vectorizer = None
        if SKLEARN_AVAILABLE:
            self.vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2)
            )
    
    def score_results(self, query: str, results: List[Dict], entities: Dict[str, List[str]] = None) -> List[Dict]:
        """Score and rank results by relevance."""
        if not results:
            return results
        
        scored_results = []
        
        for result in results:
            score = self._calculate_relevance_score(query, result, entities)
            result_copy = result.copy()
            result_copy['relevance_score'] = score
            scored_results.append(result_copy)
        
        # Sort by relevance score (descending)
        scored_results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        return scored_results
    
    def _calculate_relevance_score(self, query: str, result: Dict, entities: Dict[str, List[str]]) -> float:
        """Calculate relevance score for a single result."""
        title = result.get('title', '')
        snippet = result.get('snippet', '')
        text = f"{title} {snippet}".lower()
        query_lower = query.lower()
        
        score = 0.0
        
        # Basic keyword matching
        query_words = set(re.findall(r'\b\w+\b', query_lower))
        text_words = set(re.findall(r'\b\w+\b', text))
        keyword_overlap = len(query_words.intersection(text_words)) / max(len(query_words), 1)
        score += keyword_overlap * 0.3
        
        # Entity presence bonus
        entity_score = 0
        total_entities = 0
        for entity_type, entity_list in entities.items():
            for entity in entity_list:
                total_entities += 1
                if entity.lower() in text:
                    entity_score += 1
        
        if total_entities > 0:
            score += (entity_score / total_entities) * 0.4
        
        # Title relevance bonus
        if any(word in title.lower() for word in query_words):
            score += 0.2
        
        # Exact phrase matching bonus
        if query_lower in text:
            score += 0.1
        
        # TF-IDF similarity if available
        if self.vectorizer and SKLEARN_AVAILABLE:
            try:
                tfidf_score = self._tfidf_similarity(query, text)
                score += tfidf_score * 0.3
            except Exception:
                pass
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _tfidf_similarity(self, query: str, text: str) -> float:
        """Calculate TF-IDF cosine similarity."""
        try:
            documents = [query, text]
            tfidf_matrix = self.vectorizer.fit_transform(documents)
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return float(similarity)
        except Exception:
            return 0.0


# Global instances
query_enhancer = QueryEnhancer()
relevance_scorer = RelevanceScorer()


def enhance_search_query(query: str, research_goal: str = "", context_steps: List[str] = None) -> Dict:
    """Main function to enhance a search query."""
    return query_enhancer.enhance_query(query, research_goal, context_steps)


def score_search_results(query: str, results: List[Dict], entities: Dict[str, List[str]] = None) -> List[Dict]:
    """Main function to score and rank search results."""
    entities = entities or {}
    return relevance_scorer.score_results(query, results, entities)
