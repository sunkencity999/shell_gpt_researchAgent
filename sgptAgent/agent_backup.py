import sys
import os
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
            f"{context}\nYou are a research assistant. Break down the following research goal into the smallest number of sub-questions needed to answer it directly and completely. Only include sub-questions that are strictly necessary and directly related to the goal. Do not include generic, unrelated, or redundant research topics. Each sub-question must reference the main topic.\n\nResearch goal: {goal}\nRespond with a bullet list."
        )
        steps = self.llm.generate(
            prompt, model=self.model,
            temperature=0.2, max_tokens=self.max_tokens,  # lower temp for focus
            system_prompt=self.system_prompt, context_window=self.ctx_window
        )
        # Filter out generic/unrelated/redundant steps (post-process)
        filtered_steps = []
        for s in steps.splitlines():
            s_clean = s.strip('-*• \t')
            if not s_clean:
                continue
            # Must mention the main topic (goal) or its key terms
            if goal.lower().split()[0] not in s_clean.lower() and not any(word in s_clean.lower() for word in goal.lower().split()):
                continue
            # Filter out generic patterns
            if any(generic in s_clean.lower() for generic in ["history", "overview", "definition", "introduction", "background", "future directions", "controversy", "general"]):
                continue
            filtered_steps.append(s_clean)
        self.memory.append({"goal": goal, "plan": filtered_steps, "audience": audience, "tone": tone, "improvement": improvement})
        return filtered_steps

    def web_search(self, query: str, max_results: int = 3) -> list:
        """Perform a real web search (with fallback) and return results."""
        return search_web_with_fallback(query, max_results=max_results)

    def fetch_and_summarize_url(self, url: str, snippet: str = "", audience: str = "", tone: str = "", improvement: str = "") -> str:
        """Fetch URL content and summarize it with the LLM. Returns summary or error message."""
        text = fetch_url_text(url, snippet)
        print(f"[DEBUG] Extracted text length: {len(text)} for {url}")
        print(f"[DEBUG] Extracted text preview: {text[:300].replace(chr(10),' ')}")
        if not text or len(text.strip()) < 100:
            return f"[Fetch failed: insufficient content from {url}]"
        context = ""
        if audience:
            context += f"Intended audience: {audience}. "
        if tone:
            context += f"Preferred tone/style: {tone}. "
        if improvement:
            context += f"Special instructions: {improvement}. "
        prompt = (
            f"{context}\nWrite a detailed, multi-paragraph summary of the following web page content. "
            "Make it suitable for a research report. Include all key findings, context, and implications.\n\n"
            f"Content:\n{text}"
        )
        print(f"[DEBUG] Prompt length: {len(prompt)}")
        print(f"[DEBUG] Prompt preview: {prompt[:500].replace(chr(10),' ')})")
        try:
            summary = self.llm.generate(
                prompt, model=self.model,
                temperature=self.temperature, max_tokens=self.max_tokens,
                system_prompt=self.system_prompt, context_window=self.ctx_window
            )
            print(f"[DEBUG] LLM returned summary of length {len(summary) if summary else 0}")
            return summary
        except Exception as e:
            print(f"[ERROR] LLM summarization failed: {e}")
            return f"[Error summarizing: {e}]"

    def summarize(self, text: str) -> str:
        prompt = (
            "Write a detailed, multi-paragraph summary of the following web page content. "
            "Make it suitable for a research report. Include all key findings, context, and implications.\n\n"
            f"Content:\n{text}"
        )
        return self.llm.generate(prompt, model=self.model)

    def critique_and_find_gaps(self, synthesis: str, goal: str):
        """
        Use the LLM to critique the synthesized answer for missing info or ambiguity and extract gaps as a list of follow-up queries.
        Returns (critique, gaps_list). If no gaps, gaps_list will be empty.
        """
        prompt = (
            f"You are a critical research assistant. Review the following synthesized research answer for the goal: {goal}\n"
            f"Answer:\n{synthesis}\n"
            "List any missing information, ambiguities, or unanswered aspects as a bullet list of specific follow-up research questions.\n"
            "If the answer is fully complete and no gaps remain, reply with 'NO GAPS'.\n"
        )
        critique = self.llm.generate(prompt, model=self.model, temperature=0.2, max_tokens=512, system_prompt=self.system_prompt, context_window=self.ctx_window)
        # Extract gaps as list
        gaps = []
        if 'NO GAPS' in critique.upper():
            return critique, gaps
        for line in critique.splitlines():
            line = line.strip('-*• 	')
            if line and not line.lower().startswith('missing') and len(line) > 8:
                gaps.append(line)
        return critique, gaps

    def synthesize(self, summaries: list, goal: str, audience: str = "", tone: str = "", improvement: str = "") -> str:
        context = ""
        if audience:
            context += f"Intended audience: {audience}. "
        if tone:
            context += f"Preferred tone/style: {tone}. "
        if improvement:
            context += f"Special instructions: {improvement}. "
        prompt = (
            f"{context}\nYou are an expert research analyst. Your task is to extract, merge, cross-reference, and DEEPLY ANALYZE the factual information, data, and findings from the following summaries.\n"
            "- ALWAYS keep the original research goal in mind at every stage. Every conclusion and synthesis must be directly responsive to the research goal, not just the summaries.\n"
            "- Use the research goal as the primary context for all analysis and cross-check every finding and conclusion against it.\n"
            "- If information is missing or insufficient to answer the goal, clearly state what is missing and do not hallucinate.\n"
            "- Go beyond surface-level synthesis to deliver deep insight and clarity.\n"
            "Do NOT ask the user questions, request further instructions, or include meta-commentary about your process.\n"
            "If technical topics are present, explain them clearly for the intended audience.\n"
            f"\nRESEARCH GOAL: {goal}\n\n"
            "Summaries:\n" + "\n---\n".join(summaries)
        )
        print(f"[DEBUG] Passing research goal to LLM synthesis: {goal}")
        return self.llm.generate(
            prompt, model=self.model,
            temperature=self.temperature, max_tokens=self.max_tokens,
            system_prompt=self.system_prompt, context_window=self.ctx_window
        )

    def generate_bibliography(self, sources, style="APA"):
        """Generate bibliography section for a list of sources. Supports APA and MLA."""
        bib_lines = []
        for idx, src in enumerate(sources, 1):
            title = src.get('title', 'Untitled')
            url = src.get('href', '')
            # For now, no author/date extraction
            if style.upper() == "MLA":
                # MLA: Title. Website, URL.
                bib = f"{idx}. [{title}]({url})."
            else:  # APA
                # APA: Title. (n.d.). Website. URL
                bib = f"{idx}. {title}. (n.d.). [Link]({url})"
            bib_lines.append(bib)
        return '\n'.join(bib_lines)

    def run(self, goal: str, audience: str = "", tone: str = "", improvement: str = "",
            num_results=10, temperature=0.7, max_tokens=2048, system_prompt="", ctx_window=2048, citation_style="APA", filename=None, progress_callback=None):
        self.filename = filename
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt
        self.ctx_window = ctx_window
        console = Console()
        console.rule("[bold blue]Shell GPT Research Agent Progress")
        console.print(f"[bold]Goal:[/bold] {goal}")
        if audience:
            console.print(f"[bold]Audience:[/bold] {audience}")
        if tone:
            console.print(f"[bold]Tone/Style:[/bold] {tone}")
        if improvement:
            console.print(f"[bold]Improvement Goal:[/bold] {improvement}")
        self.citation_style = citation_style
        self.sources = []
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
            steps_list = [s.strip('-*• \t') for s in steps.split('\n') if s.strip('-*• \t')]
        else:
            steps_list = steps
        # --- Stricter filtering: remove meta-instructions, empty, goal restatement, and steps lacking entities/keywords ---
        import re
        
        # Use enhanced entity extraction from query_enhancement module
        def extract_entities(text):
            """Enhanced entity extraction using the new query enhancement module."""
            from sgptAgent.query_enhancement import query_enhancer
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
                # Allow substring match, ignore case
                if ent_l and ent_l in text_l:
                    return True
            return False

        # Broadened entity matching: allow fuzzy/partial matches for any entity substring (case-insensitive, last fallback)
        def is_entity_loose(text, entities):
            text_l = text.lower()
            for ent in entities:
                # Try all non-empty substrings of the entity (length >= 4)
                for i in range(len(ent)):
                    for j in range(i+4, len(ent)+1):
                        sub = ent[i:j].lower()
                        if sub and sub in text_l:
                            return True
            return False

        def is_well_formed_result(result):
            text = (result.get('title', '') + ' ' + result.get('snippet', '')).strip()
            if len(text) < 40:
                return False
            alpha = sum(c.isalpha() for c in text)
            if alpha / max(1, len(text)) < 0.7:
                return False
            # Avoid generic academic/medical/marketing content (very basic)
            generic_words = [
                "marketing", "psychology", "literature review", "digital literacy", "health", "policing", "sleep", "PMC", "journal", "explanation", "SAT", "test", "answer explanation", "systematic review"
            ]
            if any(gw in text.lower() for gw in generic_words):
                return False
            return True

        def extract_salient_phrases(phrases):
            multi = [p for p in phrases if ' ' in p]
            if multi:
                return multi[:2]
            else:
                return phrases[:2]

        # 1. Strictest: require at least 1 entity AND 2 distinct noun phrases, well-formed
        def is_relevant_result(result, phrase_keywords):
            text = (result.get('title', '') + ' ' + result.get('snippet', '')).lower()
            return is_entity_present(text, ENTITY_KEYWORDS) and multi_phrase_match(text, phrase_keywords, min_matches=2, stopwords=STOPWORDS) and is_well_formed_result(result)
        
        # 2. Fallback: entity present, single-phrase match, well-formed
        def is_relevant_result_fallback(result, phrase_keywords):
            text = (result.get('title', '') + ' ' + result.get('snippet', '')).lower()
            return is_entity_present(text, ENTITY_KEYWORDS) and multi_phrase_match(text, phrase_keywords, min_matches=1, stopwords=STOPWORDS) and is_well_formed_result(result)
        
        # 3. Fallback: entity present, semantic similarity (threshold 0.75), well-formed
        def is_relevant_result_semantic(result, goal):
            text = (result.get('title', '') + ' ' + result.get('snippet', '')).lower()
            return is_entity_present(text, ENTITY_KEYWORDS) and is_semantically_similar(text, goal, threshold=0.75) and is_well_formed_result(result)
        
        # 4. Fallback: if no entity present at all, allow strict phrase/semantic filtering (for ultra-rare queries)
        def is_relevant_result_no_entity(result, phrase_keywords, goal):
            text = (result.get('title', '') + ' ' + result.get('snippet', '')).lower()
            return multi_phrase_match(text, phrase_keywords, min_matches=2, stopwords=STOPWORDS) and is_well_formed_result(result)
        
        # 5. Fallback: focused query from salient phrases
        def is_relevant_result_focused(result, focused_query):
            text = (result.get('title', '') + ' ' + result.get('snippet', '')).lower()
            return is_entity_present(text, ENTITY_KEYWORDS) and multi_phrase_match(text, focused_query, min_matches=2, stopwords=STOPWORDS) and is_well_formed_result(result)
        
        # 6. Fallback: broadened entity matching (fuzzy/substring) if all else fails
        def is_relevant_result_broadened(result):
            text = (result.get('title', '') + ' ' + result.get('snippet', '')).lower()
            return is_entity_loose(text, ENTITY_KEYWORDS) and is_well_formed_result(result)
        
        for idx, step in enumerate(steps_list, 1):
            emit(f"Step {idx}/{len(steps_list)}: {step}", substep=f"Step {idx}", percent=int(100 * (current_step+idx-1)/total_steps), log=f"Sub-question: {step}")
            # --- Pinpoint and fix the query ---
            import re
            # If the step contains a parenthetical '(Main topic: ...)', extract and use that as the query
            m = re.search(r'\(Main topic: ([^)]+)\)', step)
            if m:
                search_query = m.group(1).strip()
            else:
                # Otherwise, use the step, but strip any instructional prefix (like '+ This sub-question ...')
                if step.lstrip().startswith('+'):
                    # Remove leading '+ ...' and any following ':'
                    search_query = re.sub(r'^\+[^:]*:\s*', '', step).strip()
                else:
                    search_query = step.strip()
            # --- Dynamic, entity-aware, domain-agnostic query augmentation ---
            # Extract all entities and years/time ranges from goal and sub-questions
            all_text = goal + '\n' + '\n'.join(steps_list)
            
            # Use enhanced query construction from query_enhancement module
            enhanced_queries = enhance_search_query(search_query, context=all_text)
            
            # Try enhanced queries in order of priority
            results = []
            for enhanced_query in enhanced_queries[:3]:  # Try top 3 enhanced queries
                emit(f"Searching with enhanced query: '{enhanced_query}'", substep=f"Step {idx}", percent=int(100 * (current_step+idx-1)/total_steps), log=f"Enhanced query: {enhanced_query}")
                query_results = self.web_search(enhanced_query, max_results=num_results)
                if query_results:
                    results.extend(query_results)
                    break  # Use first successful query
            
            # Fallback to original query if enhanced queries fail
            if not results:
                emit(f"Enhanced queries failed, using original: '{search_query}'", substep=f"Step {idx}", percent=int(100 * (current_step+idx-1)/total_steps), log=f"Fallback to original query")
                results = self.web_search(search_query, max_results=num_results)
            
            # Score and rank results using enhanced relevance scoring
            if results:
                scored_results = score_search_results(results, search_query, context=all_text)
                # Sort by relevance score (descending)
                results = sorted(scored_results, key=lambda x: x.get('relevance_score', 0), reverse=True)
                emit(f"Ranked {len(results)} results by relevance", substep=f"Step {idx}", percent=int(100 * (current_step+idx-1)/total_steps), log="Applied relevance scoring")
            
            # 1. Strictest: require at least 1 entity AND 2 distinct noun phrases, well-formed
            filtered_results = [r for r in results if is_entity_present((r.get('title','') + ' ' + r.get('snippet','')), ENTITY_KEYWORDS) and multi_phrase_match((r.get('title','') + ' ' + r.get('snippet','')).lower(), PHRASE_KEYWORDS, min_matches=2, stopwords=STOPWORDS) and is_well_formed_result(r)]
            # 2. Fallback: entity present, single-phrase match, well-formed
            if not filtered_results:
                filtered_results = [r for r in results if is_entity_present((r.get('title','') + ' ' + r.get('snippet','')), ENTITY_KEYWORDS) and multi_phrase_match((r.get('title','') + ' ' + r.get('snippet','')).lower(), PHRASE_KEYWORDS, min_matches=1, stopwords=STOPWORDS) and is_well_formed_result(r)]
            # 3. Fallback: entity present, semantic similarity (threshold 0.75), well-formed
            if not filtered_results:
                filtered_results = [r for r in results if is_entity_present((r.get('title','') + ' ' + r.get('snippet','')), ENTITY_KEYWORDS) and is_semantically_similar((r.get('title','') + ' ' + r.get('snippet','')).lower(), step, threshold=0.75) and is_well_formed_result(r)]
            # 4. Fallback: if no entity present at all, allow strict phrase/semantic filtering (for ultra-rare queries)
            if not filtered_results:
                filtered_results = [r for r in results if multi_phrase_match((r.get('title','') + ' ' + r.get('snippet','')).lower(), PHRASE_KEYWORDS, min_matches=2, stopwords=STOPWORDS) and is_well_formed_result(r)]
            if not filtered_results:
                filtered_results = [r for r in results if multi_phrase_match((r.get('title','') + ' ' + r.get('snippet','')).lower(), PHRASE_KEYWORDS, min_matches=1, stopwords=STOPWORDS) and is_well_formed_result(r)]
            if not filtered_results:
                filtered_results = [r for r in results if is_semantically_similar((r.get('title','') + ' ' + r.get('snippet','')).lower(), step, threshold=0.75) and is_well_formed_result(r)]
            # 5. Fallback: focused query from salient phrases
            if not filtered_results:
                salient = extract_salient_phrases(PHRASE_KEYWORDS)
                focused_query = ' '.join(salient) if salient else step
                emit(f"No relevant results for step '{step}'. Retrying with focused query '{focused_query}'...", substep=f"Step {idx}", percent=int(100 * (current_step+idx-1)/total_steps), log="Retrying with focused query.")
                results = self.web_search(focused_query, max_results=num_results)
                filtered_results = [r for r in results if is_entity_present((r.get('title','') + ' ' + r.get('snippet','')), ENTITY_KEYWORDS) and multi_phrase_match((r.get('title','') + ' ' + r.get('snippet','')).lower(), PHRASE_KEYWORDS, min_matches=2, stopwords=STOPWORDS) and is_well_formed_result(r)]
                if not filtered_results:
                    filtered_results = [r for r in results if is_entity_present((r.get('title','') + ' ' + r.get('snippet','')), ENTITY_KEYWORDS) and multi_phrase_match((r.get('title','') + ' ' + r.get('snippet','')).lower(), PHRASE_KEYWORDS, min_matches=1, stopwords=STOPWORDS) and is_well_formed_result(r)]
                if not filtered_results:
                    filtered_results = [r for r in results if is_entity_present((r.get('title','') + ' ' + r.get('snippet','')), ENTITY_KEYWORDS) and is_semantically_similar((r.get('title','') + ' ' + r.get('snippet','')).lower(), step, threshold=0.75) and is_well_formed_result(r)]
                if not filtered_results:
                    filtered_results = [r for r in results if multi_phrase_match((r.get('title','') + ' ' + r.get('snippet','')).lower(), PHRASE_KEYWORDS, min_matches=2, stopwords=STOPWORDS) and is_well_formed_result(r)]
                if not filtered_results:
                    filtered_results = [r for r in results if multi_phrase_match((r.get('title','') + ' ' + r.get('snippet','')).lower(), PHRASE_KEYWORDS, min_matches=1, stopwords=STOPWORDS) and is_well_formed_result(r)]
                if not filtered_results:
                    filtered_results = [r for r in results if is_semantically_similar((r.get('title','') + ' ' + r.get('snippet','')).lower(), step, threshold=0.75) and is_well_formed_result(r)]
            # 6. Fallback: broadened entity matching (fuzzy/substring) if all else fails
            if not filtered_results and ENTITY_KEYWORDS:
                # Use up to two main entities, plus any year range or key topic words
                entity_query = ' '.join(ENTITY_KEYWORDS[:2])
                # Try to extract year range or topic from the step or goal
                import re
                years = re.findall(r'\b(19|20)\d{2}\b', goal + ' ' + step)
                year_range = ''
                if years:
                    year_range = f"{years[0]}-{years[-1]}"
                topic_words = ''
                for word in ['baseball', 'MLB', 'success', 'record', 'win', 'championship']:
                    if word in (goal + ' ' + step).lower():
                        topic_words += ' ' + word
                focused_entity_query = f"{entity_query} {year_range} {topic_words}".strip()
                emit(f"No relevant results for step '{step}'. Retrying with focused entity query '{focused_entity_query}'...", substep=f"Step {idx}", percent=int(100 * (current_step+idx-1)/total_steps), log="Retrying with focused entity query.")
                results = self.web_search(focused_entity_query, max_results=num_results)
                filtered_results = [r for r in results if is_entity_present((r.get('title','') + ' ' + r.get('snippet','')), ENTITY_KEYWORDS) and is_well_formed_result(r)]
            # 7. Fallback: broadened entity matching (fuzzy/substring) if all else fails
            if not filtered_results and ENTITY_KEYWORDS:
                emit(f"No strict entity matches for step '{step}'. Trying broadened entity matching...", substep=f"Step {idx}", percent=int(100 * (current_step+idx-1)/total_steps), log="Trying broadened entity matching.")
                filtered_results = [r for r in results if is_entity_loose((r.get('title','') + ' ' + r.get('snippet','')), ENTITY_KEYWORDS) and is_well_formed_result(r)]
            # 8. If still nothing, skip step
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
            # --- Relevance filtering for summaries ---
            # Helper to check if summary is well-formed English
            import re
            def is_well_formed_english(text):
                # At least 40 chars, contains at least one verb (basic), mostly alphabetic, not code/HTML
                if len(text) < 40:
                    return False
                if re.search(r'<[^>]+>', text):  # HTML tag
                    return False
                if re.search(r'\b(function|var|let|const|def|class|public|private|void|int|float|if|else|elif|return|import)\b', text):
                    return False
                # At least one verb (very basic)
                if not re.search(r'\b(is|are|was|were|has|have|had|does|do|did|can|could|will|would|should|may|might|must|shall|go|make|play|run|see|get|give|take|find|think|know|want|use|show|try|ask|need|feel|be|provide|review|compare|support|feature|include|offer|allow|support|require|contain|allow|enable|enhance|improve|deliver|support|provide|present|appear|seem|look|sound|become|remain|continue|help|allow|let|keep|hold|bring|write|read|move|stand|sit|lie|lead|live|believe|hold|turn|start|begin|stop|create|open|close|build|develop|produce|design|test|check|choose|select|prefer|enjoy|like|love|hate|prefer|recommend|suggest|advise|consider|decide|expect|hope|intend|plan|prefer|promise|refuse|remember|forget|try|want|wish|would)\b', text):
                    return False
                # At least 70% alphabetic
                alpha = sum(c.isalpha() for c in text)
                if alpha / max(1, len(text)) < 0.7:
                    return False
                return True

            # Stricter filter for summaries
            filtered_summaries = [s for s in summaries if is_relevant_summary(s, PHRASE_KEYWORDS) and is_well_formed_english(s)]
            # Fallback 1: single-phrase match, well-formed only
            if not filtered_summaries:
                filtered_summaries = [s for s in summaries if multi_phrase_match(s.lower(), PHRASE_KEYWORDS, min_matches=1, stopwords=STOPWORDS) and is_well_formed_english(s)]
            # Fallback 2: semantic similarity (threshold 0.75, only if embedding model is present)
            if not filtered_summaries:
                try:
                    import importlib.util, os, sys
                    sim_path = os.path.join(os.path.dirname(__file__), 'semantic_similarity.py')
                    spec = importlib.util.spec_from_file_location('semantic_similarity', sim_path)
                    if spec is not None:
                        semantic_mod = importlib.util.module_from_spec(spec)
                        sys.modules['semantic_similarity'] = semantic_mod
                        spec.loader.exec_module(semantic_mod)
                        filtered_summaries = [s for s in summaries if semantic_mod.is_semantically_similar(s.lower(), goal, threshold=0.75) and is_well_formed_english(s)]
                except Exception:
                    pass
            # Do NOT fallback to all summaries; skip step if none are relevant and well-formed
            if not filtered_summaries:
                emit(f"No relevant, well-formed summaries found for step '{step}'. Skipping synthesis for this step.", substep=f"Step {idx}", percent=int(100 * (current_step+idx-1)/total_steps), log="No relevant summaries after all filtering.")
                continue
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
        # --- End refinement loop ---
        web_results_md = step_summaries_md
        summaries_md = step_summaries_md  # Fix: ensure summaries_md is defined for report
        summaries = step_summaries        # Fix: ensure summaries is defined for report
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
        # Summarizing URLs
        summaries = []
        summaries_md = []
        for idx, r in enumerate(results, 1):
            emit(f"Summarizing result {idx}/{len(results)}", substep=f"Summarizing {idx}/{len(results)}", percent=int(100 * (current_step+idx-1)/total_steps), log=f"Summarizing {r['title']}")
            summary = self.fetch_and_summarize_url(r['href'], r.get('snippet', ''), audience=audience, tone=tone, improvement=improvement)
            summaries.append(summary)
            summaries_md.append(f"### {idx}. [{r['title']}]({r['href']})\n{summary}")
        current_step += len(results)
        emit("Summarization complete!", substep="Summarizing", percent=int(100 * current_step/total_steps), log="All web results summarized.")
        # --- General-purpose filtering for summaries ---
        def is_relevant_summary(summary, goal):
            # Simple keyword overlap; can be replaced with semantic similarity for advanced use
            goal_words = set(goal.lower().split())
            summary_words = set(summary.lower().split())
            overlap = goal_words.intersection(summary_words)
            # Filter out summaries with no overlap or that appear to be errors/boilerplate
            error_phrases = [
                "error message", "page not found", "copyright", "terms and conditions", "login to access", "cannot be provided", "generic webpage", "Elsevier", "faq", "frequently asked questions", "no relevant results"
            ]
            if any(phrase in summary.lower() for phrase in error_phrases):
                return False
            return len(overlap) > 0 or goal.lower() in summary.lower()
        filtered_summaries = [s for s in summaries if is_relevant_summary(s, goal)]
        if not filtered_summaries:
            filtered_summaries = summaries  # fallback: use all if all are filtered
        # Synthesis step
        emit("Synthesizing research summary...", substep="Synthesizing", percent=int(100 * (current_step+1)/total_steps), log="Synthesizing report.")
        synthesis = self.synthesize(filtered_summaries, goal, audience=audience, tone=tone, improvement=improvement)
        current_step += 1
        emit("Synthesis complete!", substep="Synthesizing", percent=int(100 * current_step/total_steps), log="Synthesis complete.")
        # --- Post-synthesis topicality check ---
        if goal.lower().split()[0] not in synthesis.lower() and not any(word in synthesis.lower() for word in goal.lower().split()):
            synthesis = f"[Warning] The synthesized answer may not be relevant to your original query: '{goal}'. Please review the web results and consider refining your query for better results.\n\n" + synthesis
        # --- Automatic Reflective Refinement Loop ---
        MAX_REFINE = 3
        for refine_iter in range(MAX_REFINE):
            critique, gaps = self.critique_and_find_gaps(synthesis, goal)
            if not gaps:
                break  # No more gaps found
            emit(f"Refinement iteration {refine_iter+1}: Found gaps, performing additional search...", substep="Refinement", percent=int(100 * current_step/total_steps), log=f"Gaps: {gaps}")
            # For each gap, perform a new web search and summarize
            for gap in gaps:
                gap_results = self.web_search(gap, max_results=2)
                for r in gap_results:
                    gap_summary = self.fetch_and_summarize_url(r['href'], r.get('snippet', ''), audience=audience, tone=tone, improvement=improvement)
                    summaries.append(gap_summary)
        web_results_md = []
        self.sources = []
        for idx, r in enumerate(results, 1):
            web_results_md.append(f"### {idx}. [{r['title']}]({r['href']})\n{r['snippet']}")
            self.sources.append({"title": r.get("title", f"Source {idx}"), "href": r.get("href", ""), "snippet": r.get("snippet", "")})
        # Summarizing URLs
        summaries = []
        summaries_md = []
        for idx, r in enumerate(results, 1):
            emit(f"Summarizing result {idx}/{len(results)}", substep=f"Summarizing {idx}/{len(results)}", percent=int(100 * (current_step+idx-1)/total_steps), log=f"Summarizing {r['title']}")
            summary = self.fetch_and_summarize_url(r['href'], r.get('snippet', ''), audience=audience, tone=tone, improvement=improvement)
            summaries.append(summary)
            summaries_md.append(f"### {idx}. [{r['title']}]({r['href']})\n{summary}")
        current_step += len(results)
        emit("Summarization complete!", substep="Summarizing", percent=int(100 * current_step/total_steps), log="All web results summarized.")
        # --- General-purpose filtering for summaries ---
        def is_relevant_summary(summary, goal):
            # Simple keyword overlap; can be replaced with semantic similarity for advanced use
            goal_words = set(goal.lower().split())
            summary_words = set(summary.lower().split())
            overlap = goal_words.intersection(summary_words)
            # Filter out summaries with no overlap or that appear to be errors/boilerplate
            error_phrases = [
                "error message", "page not found", "copyright", "terms and conditions", "login to access", "cannot be provided", "generic webpage", "Elsevier", "faq", "frequently asked questions", "no relevant results"
            ]
            if any(phrase in summary.lower() for phrase in error_phrases):
                return False
            return len(overlap) > 0 or goal.lower() in summary.lower()
        filtered_summaries = [s for s in summaries if is_relevant_summary(s, goal)]
        if not filtered_summaries:
            filtered_summaries = summaries  # fallback: use all if all are filtered
        # Synthesis step
        emit("Synthesizing research summary...", substep="Synthesizing", percent=int(100 * (current_step+1)/total_steps), log="Synthesizing report.")
        synthesis = self.synthesize(filtered_summaries, goal, audience=audience, tone=tone, improvement=improvement)
        current_step += 1
        emit("Synthesis complete!", substep="Synthesizing", percent=int(100 * current_step/total_steps), log="Synthesis complete.")
        # --- Post-synthesis topicality check ---
        if goal.lower().split()[0] not in synthesis.lower() and not any(word in synthesis.lower() for word in goal.lower().split()):
            synthesis = f"[Warning] The synthesized answer may not be relevant to your original query: '{goal}'. Please review the web results and consider refining your query for better results.\n\n" + synthesis
        # --- Automatic Reflective Refinement Loop ---
        MAX_REFINE = 3
        for refine_iter in range(MAX_REFINE):
            critique, gaps = self.critique_and_find_gaps(synthesis, goal)
            if not gaps:
                break  # No more gaps found
            emit(f"Refinement iteration {refine_iter+1}: Found gaps, performing additional search...", substep="Refinement", percent=int(100 * current_step/total_steps), log=f"Gaps: {gaps}")
            # For each gap, perform a new web search and summarize
            for gap in gaps:
                gap_results = self.web_search(gap, max_results=2)
                for r in gap_results:
                    gap_summary = self.fetch_and_summarize_url(r['href'], r.get('snippet', ''), audience=audience, tone=tone, improvement=improvement)
                    summaries.append(gap_summary)
                    summaries_md.append(f"[Refinement] {gap}: {gap_summary}")
            synthesis = self.synthesize(summaries, goal, audience=audience, tone=tone, improvement=improvement)

        # Write markdown report
        emit("Writing Markdown report...", substep="Writing Report", percent=int(100 * (current_step+1)/total_steps), log="Writing report to disk.")
        from datetime import datetime
        import os
        report_path = self.filename
        if not report_path:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
            safe_goal = ''.join(c for c in goal if c.isalnum() or c in (' ', '_', '-')).rstrip()
            documents_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'documents')
            documents_dir = os.path.abspath(documents_dir)
            os.makedirs(documents_dir, exist_ok=True)
            report_path = os.path.join(documents_dir, f"research_report_{timestamp}.md")
        def strip_pre_banner(text, banner="Shell GPT Research Agent"):
            idx = text.find(banner)
            return text[idx:] if idx != -1 else text
        with open(report_path, "w", encoding="utf-8") as f:
            report_content = f"# Research Report: {goal}\n\n"
            report_content += f"**Audience:** {audience}\n\n"
            report_content += f"**Tone/Style:** {tone}\n\n"
            if improvement:
                report_content += f"**Improvement Goal:** {improvement}\n\n"
            report_content += "## Research Plan\n"
            report_content += f"{steps}\n\n"
            report_content += "## Web Results\n"
            report_content += "\n".join(web_results_md) + "\n\n"
            report_content += "## Summaries\n"
            report_content += "\n".join(summaries_md) + "\n\n"
            report_content += "## Synthesized Research Summary\n"
            report_content += synthesis + "\n\n"
            if self.sources:
                report_content += "\n## Bibliography\n"
                report_content += self.generate_bibliography(self.sources, style=self.citation_style) + "\n"
            content = strip_pre_banner(report_content, banner="Shell GPT Research Agent")
            f.write(content)
        emit("Report written.", substep="Done", percent=100, log=f"Research report written to {report_path}")
        return report_path

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
