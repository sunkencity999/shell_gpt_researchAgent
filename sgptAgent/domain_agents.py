"""
Domain-specific research agents that provide specialized expertise and validation
for targeted research domains.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod

class DomainAgent(ABC):
    """Base class for domain-specific research agents."""
    
    def __init__(self, domain_name: str):
        self.domain_name = domain_name
    
    @abstractmethod
    def get_specialized_sources(self) -> List[str]:
        """Return list of domain-specific authoritative sources."""
        pass
    
    @abstractmethod
    def enhance_queries(self, queries: List[str], research_goal: str) -> List[str]:
        """Enhance queries with domain-specific targeting."""
        pass
    
    @abstractmethod
    def validate_content_relevance(self, content: str, research_goal: str) -> float:
        """Score content relevance for this domain (0.0 to 1.0)."""
        pass
    
    @abstractmethod
    def extract_domain_entities(self, text: str) -> List[str]:
        """Extract domain-specific entities from text."""
        pass
    
    def get_search_modifiers(self) -> List[str]:
        """Return search modifiers to improve domain-specific results."""
        return []
    
    def get_validation_criteria(self) -> Dict[str, Any]:
        """Return domain-specific validation criteria."""
        return {}

class MedicalHealthAgent(DomainAgent):
    """Specialized agent for medical and health research."""
    
    def __init__(self):
        super().__init__("Medical & Health")
        self.medical_terms = {
            'conditions': ['disease', 'syndrome', 'disorder', 'condition', 'illness', 'pathology'],
            'treatments': ['treatment', 'therapy', 'medication', 'drug', 'intervention', 'procedure'],
            'anatomy': ['heart', 'brain', 'liver', 'kidney', 'lung', 'blood', 'bone', 'muscle'],
            'specialties': ['cardiology', 'neurology', 'oncology', 'psychiatry', 'dermatology', 'endocrinology']
        }
    
    def get_specialized_sources(self) -> List[str]:
        return [
            "site:pubmed.ncbi.nlm.nih.gov",
            "site:mayoclinic.org",
            "site:webmd.com",
            "site:nih.gov",
            "site:cdc.gov",
            "site:who.int",
            "site:nejm.org",
            "site:bmj.com",
            "site:thelancet.com"
        ]
    
    def enhance_queries(self, queries: List[str], research_goal: str) -> List[str]:
        enhanced = []
        for query in queries:
            # Add medical context
            if not any(term in query.lower() for terms in self.medical_terms.values() for term in terms):
                query += " medical health clinical"
            
            # Add evidence-based modifier
            if "evidence" not in query.lower():
                query += " evidence based"
            
            enhanced.append(query)
        
        return enhanced
    
    def validate_content_relevance(self, content: str, research_goal: str) -> float:
        content_lower = content.lower()
        score = 0.0
        
        # Check for medical terminology
        for category, terms in self.medical_terms.items():
            matches = sum(1 for term in terms if term in content_lower)
            score += min(matches * 0.1, 0.3)  # Max 0.3 per category
        
        # Check for research quality indicators
        quality_indicators = ['study', 'research', 'clinical', 'peer reviewed', 'journal', 'trial']
        quality_matches = sum(1 for indicator in quality_indicators if indicator in content_lower)
        score += min(quality_matches * 0.05, 0.2)
        
        return min(score, 1.0)
    
    def extract_domain_entities(self, text: str) -> List[str]:
        entities = []
        text_lower = text.lower()
        
        # Extract medical conditions
        condition_patterns = [
            r'\b([A-Z][a-z]+ [A-Z][a-z]+ (?:disease|syndrome|disorder))\b',
            r'\b([A-Z][a-z]+(?:itis|osis|emia|pathy))\b'
        ]
        
        for pattern in condition_patterns:
            matches = re.findall(pattern, text)
            entities.extend(matches)
        
        return entities

class LegalComplianceAgent(DomainAgent):
    """Specialized agent for legal and compliance research."""
    
    def __init__(self):
        super().__init__("Legal & Compliance")
        self.legal_terms = {
            'documents': ['statute', 'regulation', 'code', 'law', 'act', 'ordinance', 'ruling'],
            'concepts': ['compliance', 'liability', 'jurisdiction', 'precedent', 'contract', 'tort'],
            'processes': ['litigation', 'arbitration', 'hearing', 'trial', 'appeal', 'settlement']
        }
    
    def get_specialized_sources(self) -> List[str]:
        return [
            "site:law.cornell.edu",
            "site:justia.com",
            "site:findlaw.com",
            "site:lexisnexis.com",
            "site:westlaw.com",
            "site:courtlistener.com",
            "site:regulations.gov",
            "site:sec.gov"
        ]
    
    def enhance_queries(self, queries: List[str], research_goal: str) -> List[str]:
        enhanced = []
        for query in queries:
            # Add legal context
            if not any(term in query.lower() for terms in self.legal_terms.values() for term in terms):
                query += " legal law regulation"
            
            # Add authoritative sources modifier
            query += " statute case law precedent"
            enhanced.append(query)
        
        return enhanced
    
    def validate_content_relevance(self, content: str, research_goal: str) -> float:
        content_lower = content.lower()
        score = 0.0
        
        # Check for legal terminology
        for category, terms in self.legal_terms.items():
            matches = sum(1 for term in terms if term in content_lower)
            score += min(matches * 0.1, 0.25)
        
        # Check for legal citations
        citation_patterns = [r'\d+\s+[A-Z][a-z]+\s+\d+', r'§\s*\d+', r'USC\s+\d+']
        for pattern in citation_patterns:
            if re.search(pattern, content):
                score += 0.2
                break
        
        return min(score, 1.0)
    
    def extract_domain_entities(self, text: str) -> List[str]:
        entities = []
        
        # Extract legal citations
        citation_patterns = [
            r'\b(\d+\s+[A-Z][a-z]+\s+\d+)\b',  # Case citations
            r'\b(\d+\s+USC\s+§?\s*\d+)\b',     # USC citations
            r'\b(\d+\s+CFR\s+§?\s*\d+)\b'      # CFR citations
        ]
        
        for pattern in citation_patterns:
            matches = re.findall(pattern, text)
            entities.extend(matches)
        
        return entities

class TechnologyAIAgent(DomainAgent):
    """Specialized agent for technology and AI research."""
    
    def __init__(self):
        super().__init__("Technology & AI")
        self.tech_terms = {
            'ai_ml': ['artificial intelligence', 'machine learning', 'deep learning', 'neural network', 'llm'],
            'programming': ['python', 'javascript', 'java', 'c++', 'framework', 'library', 'api'],
            'infrastructure': ['cloud', 'server', 'database', 'architecture', 'deployment', 'scalability']
        }
    
    def get_specialized_sources(self) -> List[str]:
        return [
            "site:arxiv.org",
            "site:github.com",
            "site:stackoverflow.com",
            "site:techcrunch.com",
            "site:arstechnica.com",
            "site:wired.com",
            "site:theverge.com",
            "site:ieee.org",
            "site:acm.org"
        ]
    
    def enhance_queries(self, queries: List[str], research_goal: str) -> List[str]:
        enhanced = []
        for query in queries:
            # Add technical specification context
            if "specification" not in query.lower() and "technical" not in query.lower():
                query += " technical specification"
            
            # Add recent developments modifier
            query += " 2023 2024 latest"
            enhanced.append(query)
        
        return enhanced
    
    def validate_content_relevance(self, content: str, research_goal: str) -> float:
        content_lower = content.lower()
        score = 0.0
        
        # Check for technical terminology
        for category, terms in self.tech_terms.items():
            matches = sum(1 for term in terms if term in content_lower)
            score += min(matches * 0.08, 0.25)
        
        # Check for technical indicators
        tech_indicators = ['algorithm', 'implementation', 'performance', 'benchmark', 'optimization']
        tech_matches = sum(1 for indicator in tech_indicators if indicator in content_lower)
        score += min(tech_matches * 0.05, 0.25)
        
        return min(score, 1.0)
    
    def extract_domain_entities(self, text: str) -> List[str]:
        entities = []
        
        # Extract technical terms and versions
        tech_patterns = [
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+v?\d+(?:\.\d+)*)\b',  # Software versions
            r'\b([A-Z]{2,}(?:-[A-Z]{2,})*)\b',  # Acronyms
            r'\b([a-z]+\.[a-z]+\.[a-z]+)\b'     # Package names
        ]
        
        for pattern in tech_patterns:
            matches = re.findall(pattern, text)
            entities.extend(matches)
        
        return entities

class BusinessFinanceAgent(DomainAgent):
    """Specialized agent for business and finance research."""
    
    def __init__(self):
        super().__init__("Business & Finance")
        self.business_terms = {
            'finance': ['revenue', 'profit', 'earnings', 'investment', 'valuation', 'market cap'],
            'business': ['strategy', 'competition', 'market share', 'growth', 'acquisition', 'merger'],
            'metrics': ['roi', 'ebitda', 'eps', 'pe ratio', 'debt', 'equity', 'cash flow']
        }
    
    def get_specialized_sources(self) -> List[str]:
        return [
            "site:bloomberg.com",
            "site:reuters.com",
            "site:wsj.com",
            "site:forbes.com",
            "site:marketwatch.com",
            "site:yahoo.com/finance",
            "site:morningstar.com",
            "site:sec.gov"
        ]
    
    def enhance_queries(self, queries: List[str], research_goal: str) -> List[str]:
        enhanced = []
        for query in queries:
            # Add financial context
            if not any(term in query.lower() for terms in self.business_terms.values() for term in terms):
                query += " financial business market"
            
            # Add recent data modifier
            query += " 2024 current quarter"
            enhanced.append(query)
        
        return enhanced
    
    def validate_content_relevance(self, content: str, research_goal: str) -> float:
        content_lower = content.lower()
        score = 0.0
        
        # Check for business/finance terminology
        for category, terms in self.business_terms.items():
            matches = sum(1 for term in terms if term in content_lower)
            score += min(matches * 0.1, 0.3)
        
        # Check for financial data indicators
        financial_patterns = [r'\$[\d,]+(?:\.\d{2})?[MBK]?', r'\d+(?:\.\d+)?%', r'Q[1-4]\s+\d{4}']
        for pattern in financial_patterns:
            if re.search(pattern, content):
                score += 0.15
                break
        
        return min(score, 1.0)
    
    def extract_domain_entities(self, text: str) -> List[str]:
        entities = []
        
        # Extract financial figures and companies
        financial_patterns = [
            r'\$[\d,]+(?:\.\d{2})?[MBK]?',  # Dollar amounts
            r'\b([A-Z]{2,5})\b(?=\s+stock|\s+shares|\s+ticker)',  # Stock tickers
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Inc|Corp|LLC|Ltd))\b'  # Company names
        ]
        
        for pattern in financial_patterns:
            matches = re.findall(pattern, text)
            entities.extend(matches)
        
        return entities

class SportsRecreationAgent(DomainAgent):
    """Specialized agent for sports and recreation research."""
    
    def __init__(self):
        super().__init__("Sports & Recreation")
        self.sports_terms = {
            'baseball': ['mlb', 'baseball', 'pitcher', 'batter', 'inning', 'runs', 'hits', 'rbi'],
            'football': ['nfl', 'football', 'quarterback', 'touchdown', 'yards', 'downs'],
            'basketball': ['nba', 'basketball', 'points', 'rebounds', 'assists', 'shooting'],
            'general': ['team', 'player', 'season', 'playoff', 'championship', 'statistics', 'record']
        }
    
    def get_specialized_sources(self) -> List[str]:
        return [
            "site:espn.com",
            "site:mlb.com",
            "site:nfl.com",
            "site:nba.com",
            "site:baseball-reference.com",
            "site:pro-football-reference.com",
            "site:basketball-reference.com", 
            "site:bleacherreport.com",
            "site:sports.yahoo.com"
        ]
    
    def enhance_queries(self, queries: List[str], research_goal: str) -> List[str]:
        enhanced = []
        for query in queries:
            # Add sports context and statistics
            if "statistics" not in query.lower() and "stats" not in query.lower():
                query += " statistics stats"
            
            # Add current season context
            query += " 2024 season current"
            enhanced.append(query)
        
        return enhanced
    
    def validate_content_relevance(self, content: str, research_goal: str) -> float:
        content_lower = content.lower()
        score = 0.0
        
        # Check for sports terminology
        for category, terms in self.sports_terms.items():
            matches = sum(1 for term in terms if term in content_lower)
            score += min(matches * 0.08, 0.25)
        
        # Check for statistical data
        stat_patterns = [r'\d+(?:\.\d+)?\s*(?:avg|era|rbi|hr)', r'\d+-\d+\s+record', r'\d+\s+wins?']
        for pattern in stat_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                score += 0.2
                break
        
        return min(score, 1.0)
    
    def extract_domain_entities(self, text: str) -> List[str]:
        entities = []
        
        # Extract team names and player statistics
        sports_patterns = [
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:vs\.?|@)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # Team matchups
            r'\b(\d+(?:\.\d+)?)\s+(avg|era|rbi|hr|td|yds)\b',  # Statistics
            r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\s+(?:pitched|threw|hit|scored)'  # Player names
        ]
        
        for pattern in sports_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if isinstance(matches[0], tuple) if matches else False:
                entities.extend([match for submatches in matches for match in submatches if match])
            else:
                entities.extend(matches)
        
        return entities

class GeneralAgent(DomainAgent):
    """General-purpose research agent for broad topics."""
    
    def __init__(self):
        super().__init__("General")
    
    def get_specialized_sources(self) -> List[str]:
        return [
            "site:wikipedia.org",
            "site:britannica.com",
            "site:reuters.com",
            "site:bbc.com",
            "site:npr.org"
        ]
    
    def enhance_queries(self, queries: List[str], research_goal: str) -> List[str]:
        # General enhancement - add comprehensive and recent modifiers
        enhanced = []
        for query in queries:
            enhanced_query = query
            if "comprehensive" not in query.lower():
                enhanced_query += " comprehensive overview"
            if "2024" not in query and "2023" not in query:
                enhanced_query += " recent current"
            enhanced.append(enhanced_query)
        return enhanced
    
    def validate_content_relevance(self, content: str, research_goal: str) -> float:
        # Basic relevance scoring using keyword overlap
        goal_words = set(research_goal.lower().split())
        content_words = set(content.lower().split())
        
        if not goal_words:
            return 0.5  # Neutral score if no goal words
        
        overlap = len(goal_words.intersection(content_words))
        return min(overlap / len(goal_words), 1.0)
    
    def extract_domain_entities(self, text: str) -> List[str]:
        # Extract general entities (capitalized phrases)
        entities = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        return [entity for entity in entities if len(entity.split()) <= 3]  # Limit to 3 words

# Domain agent factory
class DomainAgentFactory:
    """Factory for creating domain-specific agents."""
    
    _agents = {
        "General": GeneralAgent,
        "Medical & Health": MedicalHealthAgent,
        "Legal & Compliance": LegalComplianceAgent,
        "Technology & AI": TechnologyAIAgent,
        "Business & Finance": BusinessFinanceAgent,
        "Sports & Recreation": SportsRecreationAgent,
    }
    
    @classmethod
    def create_agent(cls, domain: str) -> DomainAgent:
        """Create a domain agent instance."""
        agent_class = cls._agents.get(domain, GeneralAgent)
        return agent_class()
    
    @classmethod
    def get_available_domains(cls) -> List[str]:
        """Get list of available domains."""
        return list(cls._agents.keys())
    
    @classmethod
    def register_agent(cls, domain: str, agent_class: type):
        """Register a new domain agent."""
        cls._agents[domain] = agent_class

def get_domain_agent(domain: str) -> DomainAgent:
    """Convenience function to get a domain agent."""
    return DomainAgentFactory.create_agent(domain)
