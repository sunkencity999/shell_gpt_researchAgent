import sys
import os
import importlib.util
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.console import Console

class _SuppressStdoutStderr:
    def __enter__(self):
        self._stdout = sys.stdout
        self._stderr = sys.stderr
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')
    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.close()
        sys.stderr.close()
        sys.stdout = self._stdout
        sys.stderr = self._stderr

with _SuppressStdoutStderr():
    from sgptAgent.llm_functions.ollama import OllamaClient
    from sgptAgent.config import cfg
    from sgptAgent.web_search import search_web_with_fallback, fetch_url_text
    from sgptAgent.query_enhancement import enhance_search_query, score_search_results, query_enhancer

from dotenv import load_dotenv
load_dotenv()

class ResearchAgent:
    def __init__(self, model=None, temperature=0.7, max_tokens=2048, system_prompt="", ctx_window=2048):
        self.model = model or cfg.get("DEFAULT_MODEL")
        # Remove 'ollama/' prefix if present
        if self.model.startswith('ollama/'):
            self.model = self.model.split('/', 1)[1]
        self.llm = OllamaClient()
        self.memory = []  # Simple in-memory history for now
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt
        self.ctx_window = ctx_window

    def plan(self, goal: str, audience: str = "", tone: str = "", improvement: str = "") -> list:
        """Use the LLM to break down the research goal into steps, with context."""
        context = ""
        if audience:
            context += f"Intended audience: {audience}. "
        if tone:
            context += f"Preferred tone/style: {tone}. "
        if improvement:
            context += f"Special instructions: {improvement}. "
        
        prompt = (
            f"{context}\nYou are a research assistant. Break down the following research goal into simple, direct questions that work well for web search. Each question should be:\n\n"
            f"- SHORT and SPECIFIC (under 10 words)\n"
            f"- Use SIMPLE language, not academic jargon\n"
            f"- Focus on FACTS and NAMES, not abstract concepts\n"
            f"- Avoid complex philosophical or theoretical questions\n\n"
            f"IMPORTANT: Respond with ONLY a clean bullet list of SHORT questions. No explanations, reasoning, or commentary.\n\n"
            f"Research goal: {goal}\n\n"
            f"Format your response as:\n"
            f"- Who was [specific person]?\n"
            f"- What happened in [specific event]?\n"
            f"- When did [specific thing] occur?\n"
            f"etc."
        )
        response = self.llm.chat(self.model, prompt, temperature=self.temperature, max_tokens=self.max_tokens)
        return response

    def web_search(self, query: str, max_results: int = 10) -> list:
        """Search the web and return results."""
        return search_web_with_fallback(query, max_results=max_results)

    def fetch_and_summarize_url(self, url: str, snippet: str = "", audience: str = "", tone: str = "", improvement: str = "") -> str:
        """Fetch content from URL and summarize it."""
        try:
            content = fetch_url_text(url)
            if not content or len(content.strip()) < 100:
                return f"Unable to fetch meaningful content from {url}. Snippet: {snippet}"
            
            context = ""
            if audience:
                context += f"Intended audience: {audience}. "
            if tone:
                context += f"Preferred tone/style: {tone}. "
            if improvement:
                context += f"Special instructions: {improvement}. "
            
            prompt = f"{context}Summarize the following content in 2-3 sentences, focusing on the key information:\n\n{content[:2000]}"
            summary = self.llm.chat(self.model, prompt, temperature=self.temperature, max_tokens=self.max_tokens)
            return summary
        except Exception as e:
            return f"Error processing {url}: {str(e)}. Snippet: {snippet}"

    def validate_content_relevance(self, summaries: list, goal: str, min_relevance_threshold: float = 0.3) -> tuple:
        """Validate that summaries are relevant to the research goal before synthesis."""
        if not summaries:
            return [], "No summaries provided for validation."
        
        relevant_summaries = []
        irrelevant_count = 0
        
        # Extract key terms from the research goal
        goal_lower = goal.lower()
        goal_keywords = set(word.strip('.,!?()[]{}":;') for word in goal_lower.split() 
                           if len(word) > 2 and word not in ['the', 'and', 'or', 'but', 'for', 'with', 'this', 'that'])
        
        for summary in summaries:
            summary_lower = summary.lower()
            
            # Check for error indicators
            error_indicators = [
                "error message", "page not found", "copyright", "terms and conditions", 
                "login to access", "cannot be provided", "generic webpage", "corrupted pdf",
                "unable to fetch", "access denied", "404", "403", "500", "client error",
                "i apologize", "i'm unable", "i cannot", "not related to", "appears to be"
            ]
            
            if any(indicator in summary_lower for indicator in error_indicators):
                irrelevant_count += 1
                continue
            
            # Calculate keyword overlap
            summary_words = set(word.strip('.,!?()[]{}":;') for word in summary_lower.split())
            overlap = len(goal_keywords.intersection(summary_words))
            relevance_score = overlap / len(goal_keywords) if goal_keywords else 0
            
            if relevance_score >= min_relevance_threshold:
                relevant_summaries.append(summary)
            else:
                irrelevant_count += 1
        
        validation_msg = f"Content validation: {len(relevant_summaries)} relevant, {irrelevant_count} irrelevant summaries"
        return relevant_summaries, validation_msg

    def synthesize(self, summaries: list, goal: str, audience: str = "", tone: str = "", improvement: str = "") -> str:
        """Synthesize multiple summaries into a coherent answer with content validation."""
        if not summaries:
            return "No relevant information found to synthesize."
        
        # Validate content relevance before synthesis
        relevant_summaries, validation_msg = self.validate_content_relevance(summaries, goal)
        print(f" {validation_msg}")
        
        if not relevant_summaries:
            return f"""I apologize, but I was unable to find relevant information to answer your research question: "{goal}"

The search results contained content that was not related to your specific question. This could be due to:
1. Limited availability of specific data on this topic
2. Search queries not targeting the right sources
3. The information you're looking for may require access to specialized databases

**Suggestions:**
- Try rephrasing your research question with more specific terms
- Consider breaking down your question into smaller, more focused parts
- Look for official sources, academic papers, or industry-specific databases
- Try using more specific keywords related to your topic

**Alternative approach:** You might want to search for more specific aspects of your topic or try different keyword combinations to get more targeted results."""
        
        # Enhanced synthesis with data quality awareness
        context = ""
        if audience:
            context += f"Intended audience: {audience}. "
        if tone:
            context += f"Preferred tone/style: {tone}. "
        if improvement:
            context += f"Special instructions: {improvement}. "
        
        combined_summaries = "\n\n".join(relevant_summaries)
        
        # Enhanced prompt with data quality instructions
        prompt = f"""{context}Based on the following research summaries, provide a comprehensive answer to the research goal: '{goal}'

IMPORTANT INSTRUCTIONS:
1. Only use information that is directly relevant to the research question
2. If the summaries contain conflicting information, acknowledge the conflicts
3. If specific data (like statistics, dates, numbers) is missing, explicitly state what information is needed
4. Provide concrete evidence and data to support your conclusions
5. If you cannot provide a definitive answer due to insufficient data, clearly explain what additional information would be needed

Research Goal: {goal}

Summaries:
{combined_summaries}

Provide a well-structured, evidence-based response that directly addresses the research question."""
        
        synthesis = self.llm.chat(self.model, prompt, temperature=self.temperature, max_tokens=self.max_tokens)
        return synthesis

    def critique_and_find_gaps(self, synthesis: str, goal: str) -> tuple:
        """Critique the synthesis and identify specific data gaps for targeted searches."""
        
        # Check if synthesis indicates insufficient data
        insufficient_data_indicators = [
            "unable to find", "no relevant information", "cannot provide", "insufficient data",
            "not related to", "appears to be", "i apologize", "i'm unable", "i cannot", "not related to", "appears to be"
        ]
        
        synthesis_lower = synthesis.lower()
        has_insufficient_data = any(indicator in synthesis_lower for indicator in insufficient_data_indicators)
        
        if has_insufficient_data:
            # Generate specific search queries based on the research goal
            gaps = self.generate_targeted_search_queries(goal)
            critique = f"The synthesis indicates insufficient relevant data was found. Generated {len(gaps)} targeted search queries to find specific information."
            return critique, gaps
        
        # Standard critique for cases with some relevant data
        prompt = f"""Review this research synthesis for the goal '{goal}' and identify any important gaps or missing information:

{synthesis}

Focus on identifying specific, searchable gaps such as:
- Missing statistics or numerical data
- Lack of recent information (2020-2024)
- Missing comparisons between specific entities
- Absence of expert opinions or analysis
- Missing context or background information

Provide:
1. A brief critique of the synthesis quality
2. List of specific, searchable gaps (one per line, starting with '-')

Make each gap a specific search query that could find the missing information."""
        
        response = self.llm.chat(self.model, prompt, temperature=self.temperature, max_tokens=self.max_tokens)
        
        lines = response.split('\n')
        gaps = [line.strip('- ').strip() for line in lines if line.strip().startswith('-')]
        critique = response
        
        return critique, gaps[:3]  # Limit to 3 gaps
    
    def generate_targeted_search_queries(self, goal: str) -> list:
        """Generate specific search queries based on the research goal when initial search fails."""
        goal_lower = goal.lower()
        queries = []
        
        # Generic query enhancement patterns
        if 'better' in goal_lower or 'compare' in goal_lower:
            # Extract entities for comparison
            words = goal.split()
            entities = [word.strip('.,!?()[]{}'":;") for word in words if word[0].isupper() and len(word) > 2]
            
            if len(entities) >= 2:
                entity1, entity2 = entities[0], entities[1]
                queries.extend([
                    f"{entity1} {entity2} statistics comparison recent years",
                    f"{entity1} performance metrics vs {entity2}",
                    f"{entity1} {entity2} head to head record"
                ])
        
        # Time-based queries
        if any(term in goal_lower for term in ['decade', 'years', 'recent', 'this']):
            base_query = goal.replace('this decade', '2015-2024').replace('recent years', '2020-2024')
            queries.append(f"{base_query} statistics data")
        
        # Fallback: break down the goal into component searches
        if not queries:
            words = [word.strip('.,!?()[]{}'":;") for word in goal.split() if len(word) > 3]
            if len(words) >= 2:
                queries.extend([
                    f"{' '.join(words[:3])} statistics",
                    f"{' '.join(words[-3:])} data analysis",
                    f"{goal} official statistics"
                ])
        
        return queries[:5]  # Limit to 5 targeted queries

    def add_domain_targeting(self, query: str, domain: str) -> str:
        """Add domain-specific targeting to the search query."""
        # Don't add domain targeting for historical, biographical, or sensitive topics
        sensitive_keywords = ['assassin', 'murder', 'kill', 'death', 'crime', 'history', 'historical', 'biography', 'war', 'politics']
        query_lower = query.lower()
        
        if any(keyword in query_lower for keyword in sensitive_keywords):
            return query  # Return original query without domain filtering
        
        if domain == 'general':
            return query
        elif domain == 'technology':
            return f"{query} site:techcrunch.com OR site:arstechnica.com OR site:wired.com OR site:theverge.com"
        elif domain == 'business':
            return f"{query} site:bloomberg.com OR site:reuters.com OR site:wsj.com OR site:forbes.com"
        elif domain == 'science':
            return f"{query} site:nature.com OR site:science.org OR site:ncbi.nlm.nih.gov OR site:pubmed.ncbi.nlm.nih.gov"
        elif domain == 'health':
            return f"{query} site:mayoclinic.org OR site:webmd.com OR site:nih.gov OR site:cdc.gov"
        elif domain == 'finance':
            return f"{query} site:marketwatch.com OR site:yahoo.com/finance OR site:morningstar.com"
        elif domain == 'education':
            return f"{query} site:edu OR site:khanacademy.org OR site:coursera.org"
        elif domain == 'politics':
            return f"{query} site:politico.com OR site:reuters.com OR site:apnews.com"
        else:
            return query
    
    def write_report(self, synthesis: str, web_results_md: list, goal: str, audience: str = "", tone: str = "", improvement: str = "", citation_style: str = "APA", filename: str = None) -> str:
        """Write a formatted research report."""
        if not filename:
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"research_report_{timestamp}.md"
        
        report_content = f"""# Research Report

## Research Goal
{goal}

## Executive Summary
{synthesis}

## Sources and References
"""
        
        for i, source in enumerate(getattr(self, 'sources', []), 1):
            report_content += f"{i}. [{source.get('title', f'Source {i}')}]({source.get('href', '')})\n"
        
        report_content += f"\n## Detailed Web Results\n"
        for result in web_results_md:
            report_content += f"{result}\n\n"
        
        report_path = os.path.join(os.getcwd(), filename)
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        return report_path

    def run(self, goal: str, audience: str = "", tone: str = "", improvement: str = "",
            num_results=10, temperature=0.7, max_tokens=2048, system_prompt="", ctx_window=2048, citation_style="APA", filename=None, progress_callback=None):
        """Main research orchestration with enhanced query construction."""
        
        # Update instance parameters
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt
        self.ctx_window = ctx_window
        
        total_steps = 4 + num_results  # Plan, Search, N x Summarize, Synthesize, Write
        current_step = 0
        
        def emit(desc, substep=None, percent=None, log=None):
            if progress_callback:
                progress_callback(desc, '', substep, percent, log)
        
        # Planning step
        emit("Planning research steps...", substep="Planning", percent=int(100 * current_step/total_steps), log="Started planning.")
        steps = self.plan(goal, audience=audience, tone=tone, improvement=improvement)
        current_step += 1
        emit("Planning complete!", substep="Planning", percent=int(100 * current_step/total_steps), log="Planning complete.")

        # --- Multi-Step Web Reasoning ---
        if isinstance(steps, str):
            # Filter out reasoning model thinking process and extract only bullet points
            lines = steps.split('\n')
            filtered_lines = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Skip reasoning model thinking patterns (expanded list)
                thinking_patterns = [
                    "okay,", "wait,", "let me", "i need to", "i should", "first,", "actually,", 
                    "hmm,", "so,", "now,", "then,", "next,", "also,", "however,", "but,",
                    "the user", "the exploiter", "the main", "since", "given that",
                    "looking at", "considering", "thinking about", "based on", "this means",
                    "in other words", "essentially", "basically", "furthermore", "moreover",
                    "therefore", "consequently", "as a result", "this suggests", "it seems",
                    "perhaps", "maybe", "possibly", "likely", "probably", "clearly",
                    "obviously", "certainly", "definitely", "undoubtedly", "without doubt"
                ]
                
                line_lower = line.lower()
                if any(pattern in line_lower[:25] for pattern in thinking_patterns):
                    continue
                
                # Skip overly complex academic-style questions
                if len(line) > 100 or "methodology" in line_lower or "contextual factors" in line_lower:
                    continue
                    
                # Only keep lines that look like bullet points or simple questions
                if (line.startswith(('-', '*', '•', '1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')) or 
                    line.endswith('?') or 
                    ('what' in line_lower or 'who' in line_lower or 'when' in line_lower or 
                     'where' in line_lower or 'how' in line_lower or 'which' in line_lower)):
                    
                    # Simplify complex questions
                    simplified = self.simplify_search_query(line)
                    if simplified and len(simplified) > 3:
                        filtered_lines.append(simplified)
            
            steps_list = [s.strip('-*• \t') for s in filtered_lines if s.strip('-*• \t')]
        else:
            steps_list = steps
        
        # --- Enhanced entity extraction and filtering ---
        import re
        
        # Use enhanced entity extraction from query_enhancement module
        def extract_entities(text):
            """Enhanced entity extraction using the new query enhancement module."""
            entities_dict = query_enhancer.extract_entities_advanced(text)
            # Flatten all entity types into a single list for backward compatibility
            all_entities = []
            for entity_type, entity_list in entities_dict.items():
                all_entities.extend(entity_list)
            return all_entities
        
        meta_patterns = [
            r"^to address the research goal",
            r"^here is the breakdown",
            r"^the following sub-questions",
            r"^let's break down",
            r"^step \d+",
            r"^sub-question[s]?:",
            r"^overall plan",
            r"^summary$",
        ]
        
        def is_meta_instruction(s):
            s_l = s.lower().strip()
            return any(re.match(pat, s_l) for pat in meta_patterns)
        
        # Extract entities/keywords for filtering using enhanced extraction
        ALL_TEXT = goal + '\n' + '\n'.join(steps_list)
        ENTITY_KEYWORDS = extract_entities(ALL_TEXT)
        goal_keywords = set(goal.lower().split())
        
        def contains_entity_or_keyword(s):
            s_l = s.lower()
            return any(ent.lower() in s_l for ent in ENTITY_KEYWORDS) or any(word in s_l for word in goal_keywords)
        
        def is_entity_present(text, entities):
            text_l = text.lower()
            for ent in entities:
                ent_l = ent.lower()
                if ent_l and ent_l in text_l:
                    return True
            return False

        def is_entity_loose(text, entities):
            text_l = text.lower()
            for ent in entities:
                for i in range(len(ent)):
                    for j in range(i+4, len(ent)+1):
                        sub = ent[i:j].lower()
                        if sub and sub in text_l:
                            return True
            return False

        def is_semantically_similar(text, goal, threshold=0.6):
            sim_path = os.path.join(os.path.dirname(__file__), 'semantic_similarity.py')
            spec = importlib.util.spec_from_file_location('semantic_similarity', sim_path)
            if spec is not None:
                semantic_mod = importlib.util.module_from_spec(spec)
                sys.modules['semantic_similarity'] = semantic_mod
                spec.loader.exec_module(semantic_mod)
                return semantic_mod.is_semantically_similar(text, goal, threshold)
            return True

        def extract_noun_phrases(text):
            import re
            tokens = re.findall(r'\b(?:[A-Z][a-z]+|[a-z]{4,}|\d+)\b', text)
            phrases = set()
            for i in range(len(tokens)):
                if i+1 < len(tokens):
                    phrases.add((tokens[i] + ' ' + tokens[i+1]).lower())
                if i+2 < len(tokens):
                    phrases.add((tokens[i] + ' ' + tokens[i+1] + ' ' + tokens[i+2]).lower())
                if len(tokens[i]) > 5:
                    phrases.add(tokens[i].lower())
            return list(phrases)

        all_text = goal + '\n' + '\n'.join(steps_list)
        PHRASE_KEYWORDS = extract_noun_phrases(all_text)
        if not PHRASE_KEYWORDS:
            PHRASE_KEYWORDS = [w.lower() for w in all_text.split() if len(w) > 3]

        STOPWORDS = {"performance", "cost", "controller", "ecosystem", "feature", "aspect", "specification", "price", "game", "graphics", "library", "system", "device", "option", "value", "review", "comparison", "experience"}

        def multi_phrase_match(text, phrases, min_matches=2, stopwords=None):
            matches = [phrase for phrase in phrases if phrase in text]
            if stopwords:
                matches = [m for m in matches if m not in stopwords or len(matches) > 1]
            multi_word = any(' ' in m for m in matches)
            return (len(set(matches)) >= min_matches) or multi_word

        def is_well_formed_result(result):
            text = (result.get('title', '') + ' ' + result.get('snippet', '')).strip()
            if len(text) < 40:
                return False
            alpha = sum(c.isalpha() for c in text)
            if alpha / max(1, len(text)) < 0.7:
                return False
            generic_words = [
                "marketing", "psychology", "literature review", "digital literacy", "health", "policing", "sleep", "PMC", "journal", "explanation", "SAT", "test", "answer explanation", "systematic review"
            ]
            if any(gw in text.lower() for gw in generic_words):
                return False
            return True

        steps_list = [s for s in steps_list if s and s.lower() != goal.lower() and not is_meta_instruction(s) and contains_entity_or_keyword(s)]
        
        if steps_list:
            step_summaries = []
            step_summaries_md = []
            
            for idx, step in enumerate(steps_list, 1):
                emit(f"Step {idx}/{len(steps_list)}: {step}", substep=f"Step {idx}", percent=int(100 * (current_step+idx-1)/total_steps), log=f"Sub-question: {step}")
                
                # Extract search query from step
                m = re.search(r'\(Main topic: ([^)]+)\)', step)
                if m:
                    search_query = m.group(1).strip()
                else:
                    if step.lstrip().startswith('+'):
                        search_query = re.sub(r'^\+[^:]*:\s*', '', step).strip()
                    else:
                        search_query = step.strip()
                
                # Skip empty or invalid search queries
                if not search_query or len(search_query.strip()) < 3:
                    emit(f"Skipping invalid query: '{search_query}'", substep=f"Step {idx}", percent=int(100 * (current_step+idx-1)/total_steps), log="Skipped empty/invalid query")
                    continue
                
                # Create a simple fallback query from the original step
                simple_query = self.create_simple_query(search_query, goal)
                
                # Use enhanced query construction
                enhanced_result = enhance_search_query(search_query, research_goal=goal, context_steps=steps_list)
                enhanced_queries = enhanced_result.get('enhanced_queries', [search_query])
                fallback_queries = enhanced_result.get('fallback_queries', [search_query, simple_query])
                
                # Progressive search strategy with multiple fallback levels
                results = []
                search_attempts = 0
                max_attempts = 5
                
                # Strategy 1: Try primary enhanced queries with domain-specific targeting
                for enhanced_query in enhanced_queries[:3]:
                    if search_attempts >= max_attempts:
                        break
                    
                    # Add domain-specific source targeting for better results
                    domain = enhanced_result.get('domain', 'general')
                    targeted_query = self.add_domain_targeting(enhanced_query, domain)
                    
                    emit(f"Searching with enhanced query: '{targeted_query}'", substep=f"Step {idx}", percent=int(100 * (current_step+idx-1)/total_steps), log=f"Enhanced query: {targeted_query}")
                    query_results = self.web_search(targeted_query, max_results=num_results)
                    search_attempts += 1
                    
                    if query_results and len(query_results) >= 3:  # Good results threshold
                        results.extend(query_results)
                        emit(f"Found {len(query_results)} results with enhanced query", substep=f"Step {idx}", percent=int(100 * (current_step+idx-1)/total_steps), log="Enhanced query successful")
                        break
                    elif query_results:
                        results.extend(query_results)  # Keep partial results
                
                # Strategy 2: Try fallback queries if primary didn't yield enough results
                if len(results) < 3 and fallback_queries:
                    for fallback_query in fallback_queries[:2]:
                        if search_attempts >= max_attempts:
                            break
                        emit(f"Trying fallback query: '{fallback_query}'", substep=f"Step {idx}", percent=int(100 * (current_step+idx-1)/total_steps), log=f"Fallback query: {fallback_query}")
                        query_results = self.web_search(fallback_query, max_results=num_results)
                        search_attempts += 1
                        
                        if query_results:
                            results.extend(query_results)
                            if len(results) >= 3:
                                break
                
                # Strategy 3: Try simple fallback queries if still not enough results
                if len(results) < 3:
                    emit(f"Trying simple fallback query: '{simple_query}'", substep=f"Step {idx}", percent=int(100 * (current_step+idx-1)/total_steps), log=f"Simple fallback: {simple_query}")
                    query_results = self.web_search(simple_query, max_results=num_results)
                    if query_results:
                        results.extend(query_results)
                
                # Strategy 4: Final fallback to original query with domain keywords
                if len(results) < 2:
                    domain = enhanced_result.get('domain', 'general')
                    domain_enhanced_query = f"{search_query} {domain}" if domain != 'general' else search_query
                    
                    emit(f"Final fallback with domain enhancement: '{domain_enhanced_query}'", substep=f"Step {idx}", percent=int(100 * (current_step+idx-1)/total_steps), log="Final fallback strategy")
                    query_results = self.web_search(domain_enhanced_query, max_results=num_results)
                    
                    if query_results:
                        results.extend(query_results)
                    elif search_query != domain_enhanced_query:
                        # Last resort: pure original query
                        emit(f"Last resort: original query '{search_query}'", substep=f"Step {idx}", percent=int(100 * (current_step+idx-1)/total_steps), log="Original query fallback")
                        results = self.web_search(search_query, max_results=num_results)
                
                # Score and rank results using enhanced relevance scoring
                if results:
                    scored_results = score_search_results(search_query, results, entities=enhanced_result.get('entities', {}))
                    results = sorted(scored_results, key=lambda x: x.get('relevance_score', 0), reverse=True)
                    emit(f"Ranked {len(results)} results by relevance", substep=f"Step {idx}", percent=int(100 * (current_step+idx-1)/total_steps), log="Applied relevance scoring")
                
                # Filter results with multiple fallback levels
                filtered_results = [r for r in results if is_entity_present((r.get('title','') + ' ' + r.get('snippet','')), ENTITY_KEYWORDS) and multi_phrase_match((r.get('title','') + ' ' + r.get('snippet','')).lower(), PHRASE_KEYWORDS, min_matches=2, stopwords=STOPWORDS) and is_well_formed_result(r)]
                
                if not filtered_results:
                    filtered_results = [r for r in results if is_entity_present((r.get('title','') + ' ' + r.get('snippet','')), ENTITY_KEYWORDS) and multi_phrase_match((r.get('title','') + ' ' + r.get('snippet','')).lower(), PHRASE_KEYWORDS, min_matches=1, stopwords=STOPWORDS) and is_well_formed_result(r)]
                
                if not filtered_results:
                    filtered_results = [r for r in results if is_entity_present((r.get('title','') + ' ' + r.get('snippet','')), ENTITY_KEYWORDS) and is_semantically_similar((r.get('title','') + ' ' + r.get('snippet','')).lower(), step, threshold=0.75) and is_well_formed_result(r)]
                
                if not filtered_results:
                    emit(f"No relevant web results found for step '{step}'. Skipping.", substep=f"Step {idx}", percent=int(100 * (current_step+idx-1)/total_steps), log="No relevant results after all filtering.")
                    continue
                
                step_md = []
                for ridx, r in enumerate(filtered_results, 1):
                    step_md.append(f"### {ridx}. [{r['title']}]({r['href']})\n{r['snippet']}")
                step_summaries_md.append(f"#### Step {idx}: {step}\n" + "\n".join(step_md))
                
                summaries = []
                for r in filtered_results:
                    summary = self.fetch_and_summarize_url(r['href'], r.get('snippet', ''), audience=audience, tone=tone, improvement=improvement)
                    summaries.append(summary)
                
                # Filter summaries for relevance
                def is_relevant_summary(summary, goal):
                    goal_words = set(goal.lower().split())
                    summary_words = set(summary.lower().split())
                    overlap = goal_words.intersection(summary_words)
                    error_phrases = [
                        "error message", "page not found", "copyright", "terms and conditions", "login to access", "cannot be provided", "generic webpage", "Elsevier", "faq", "frequently asked questions", "no relevant results"
                    ]
                    if any(phrase in summary.lower() for phrase in error_phrases):
                        return False
                    return len(overlap) > 0 or goal.lower() in summary.lower()
            
                filtered_summaries = [s for s in summaries if is_relevant_summary(s, goal)]
                if not filtered_summaries:
                    filtered_summaries = summaries
            
                step_summary = self.synthesize(filtered_summaries, step, audience=audience, tone=tone, improvement=improvement)
                step_summaries.append(step_summary)
            
            # Synthesize all step summaries into a final answer
            emit("Synthesizing multi-step research summary...", substep="Synthesizing", percent=int(100 * (current_step+len(steps_list))/total_steps), log="Synthesizing final answer from all steps.")
            synthesis = self.synthesize(step_summaries, goal, audience=audience, tone=tone, improvement=improvement)
            current_step += len(steps_list)
            emit("Synthesis complete!", substep="Synthesizing", percent=int(100 * current_step/total_steps), log="Synthesis complete.")
            
            # Reflective refinement loop on final synthesis
            MAX_REFINE = 3
            for refine_iter in range(MAX_REFINE):
                critique, gaps = self.critique_and_find_gaps(synthesis, goal)
                if not gaps:
                    break
                emit(f"Refinement iteration {refine_iter+1}: Found gaps, performing additional search...", substep="Refinement", percent=int(100 * current_step/total_steps), log=f"Gaps: {gaps}")
                for gap in gaps:
                    gap_results = self.web_search(gap, max_results=2)
                    for r in gap_results:
                        gap_summary = self.fetch_and_summarize_url(r['href'], r.get('snippet', ''), audience=audience, tone=tone, improvement=improvement)
                        step_summaries.append(gap_summary)
                        step_summaries_md.append(f"[Refinement] {gap}: {gap_summary}")
                synthesis = self.synthesize(step_summaries, goal, audience=audience, tone=tone, improvement=improvement)
            
            web_results_md = step_summaries_md
            summaries_md = step_summaries_md
            summaries = step_summaries
        else:
            # Fallback to original single-step logic if no steps detected
            emit("Searching the web...", substep="Web Search", percent=int(100 * current_step/total_steps), log="Starting web search...")
            results = self.web_search(goal, max_results=num_results)
            current_step += 1
            emit(f"Found {len(results)} web results.", substep="Web Search", percent=int(100 * current_step/total_steps), log=f"Found {len(results)} web results.")
            
            web_results_md = []
            self.sources = []
            for idx, r in enumerate(results, 1):
                web_results_md.append(f"### {idx}. [{r['title']}]({r['href']})\n{r['snippet']}")
                self.sources.append({"title": r.get("title", f"Source {idx}"), "href": r.get("href", ""), "snippet": r.get("snippet", "")})
            
            summaries = []
            summaries_md = []
            for idx, r in enumerate(results, 1):
                emit(f"Summarizing result {idx}/{len(results)}", substep=f"Summarizing {idx}/{len(results)}", percent=int(100 * (current_step+idx-1)/total_steps), log=f"Summarizing {r['title']}")
                summary = self.fetch_and_summarize_url(r['href'], r.get('snippet', ''), audience=audience, tone=tone, improvement=improvement)
                summaries.append(summary)
                summaries_md.append(f"### {idx}. [{r['title']}]({r['href']})\n{summary}")
            
            current_step += len(results)
            emit("Summarization complete!", substep="Summarizing", percent=int(100 * current_step/total_steps), log="All web results summarized.")
            
            def is_relevant_summary(summary, goal):
                goal_words = set(goal.lower().split())
                summary_words = set(summary.lower().split())
                overlap = goal_words.intersection(summary_words)
                error_phrases = [
                    "error message", "page not found", "copyright", "terms and conditions", "login to access", "cannot be provided", "generic webpage", "Elsevier", "faq", "frequently asked questions", "no relevant results"
                ]
                if any(phrase in summary.lower() for phrase in error_phrases):
                    return False
                return len(overlap) > 0 or goal.lower() in summary.lower()
            
            filtered_summaries = [s for s in summaries if is_relevant_summary(s, goal)]
            if not filtered_summaries:
                filtered_summaries = summaries
            
            emit("Synthesizing research summary...", substep="Synthesizing", percent=int(100 * (current_step+1)/total_steps), log="Synthesizing report.")
            synthesis = self.synthesize(filtered_summaries, goal, audience=audience, tone=tone, improvement=improvement)
            current_step += 1
            emit("Synthesis complete!", substep="Synthesizing", percent=int(100 * current_step/total_steps), log="Synthesis complete.")
        
        # Write report
        emit("Writing research report...", substep="Writing Report", percent=int(100 * (current_step+1)/total_steps), log="Writing final report.")
        report_path = self.write_report(synthesis, web_results_md, goal, audience=audience, tone=tone, improvement=improvement, citation_style=citation_style, filename=filename)
        current_step += 1
        emit("Research complete!", substep="Complete", percent=100, log=f"Report saved to {report_path}")
        
        return report_path

    def simplify_search_query(self, query: str) -> str:
        """Simplify complex search queries."""
        # Remove unnecessary words and phrases
        unnecessary_words = ["what is", "who is", "where is", "when is", "how is", "why is"]
        for word in unnecessary_words:
            query = query.replace(word, "")
        
        # Remove punctuation
        query = query.replace(",", "").replace(".", "").replace("?", "").replace("!", "")
        
        # Remove extra whitespace
        query = " ".join(query.split())
        
        return query

    def create_simple_query(self, query: str, goal: str) -> str:
        """Create a simple fallback query from the original step."""
        # Remove unnecessary words and phrases
        unnecessary_words = ["what is", "who is", "where is", "when is", "how is", "why is"]
        for word in unnecessary_words:
            query = query.replace(word, "")
        
        # Remove punctuation
        query = query.replace(",", "").replace(".", "").replace("?", "").replace("!", "")
        
        # Remove extra whitespace
        query = " ".join(query.split())
        
        # Add goal context to the query
        query += " " + goal
        
        return query

if __name__ == "__main__":
    print("\nShell GPT Research Agent\n========================\n")
    try:
        goal = input("Enter your research goal: ").strip()
        if not goal:
            print("No research goal entered. Exiting.")
        else:
            agent = ResearchAgent()
            agent.run(goal)
    except (KeyboardInterrupt, EOFError):
        print("\nExiting.")
