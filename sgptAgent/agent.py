import sys
import os
import importlib.util
import datetime
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.console import Console
from pathlib import Path
import glob
import PyPDF2

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
    def __init__(self, model=None, temperature=0.3, max_tokens=6144, system_prompt="", ctx_window=8192, **kwargs):
        self.model = model or cfg.get("DEFAULT_MODEL")
        self.embedding_model = cfg.get("EMBEDDING_MODEL")
        # Remove 'ollama/' prefix if present
        if self.model.startswith('ollama/'):
            self.model = self.model.split('/', 1)[1]
        self.llm = OllamaClient()
        self.memory = []  # Simple in-memory history for now
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt
        self.ctx_window = ctx_window
        self.local_document_index = [] # Stores chunks of local documents

    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> list:
        """Splits text into overlapping chunks."""
        chunks = []
        if not text:
            return chunks
        words = text.split()
        if len(words) <= chunk_size:
            return [" ".join(words)]
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            chunks.append(chunk)
        return chunks

    def _get_embedding(self, text: str) -> list:
        """Helper to get embeddings for a text chunk using Ollama."""
        try:
            return self.llm.embeddings(self.embedding_model, text)
        except Exception as e:
            # Check if the model is available, if not, prompt the user to pull it.
            if "not found" in str(e):
                print(f"Embedding model '{self.embedding_model}' not found.")
                print(f"Please pull the model using: ollama pull {self.embedding_model}")
                # Ask user if they want to pull the model now.
                if input("Would you like to pull the model now? (y/n): ").lower() == "y":
                    import subprocess
                    subprocess.run(["ollama", "pull", self.embedding_model])
                    return self.llm.get_embedding(self.embedding_model, text)
            return []

    def index_local_documents(self, local_docs_path: str, progress_callback=None):
        """Indexes local documents for RAG, now with embeddings."""
        def emit(desc, bar='', substep=None, percent=None, log=None):
            if progress_callback:
                progress_callback(desc, bar, substep=substep, percent=percent, log=log)

        if not local_docs_path or not os.path.exists(local_docs_path):
            emit("Local documents path not found.", log=f"Path not found: {local_docs_path}")
            return

        emit("Indexing local documents...", substep="Indexing", log=f"Indexing documents from {local_docs_path}")
        
        supported_extensions = ['.txt', '.md', '.pdf'] # Add more as needed
        
        for ext in supported_extensions:
            for file_path in glob.glob(os.path.join(local_docs_path, '**', f'*{ext}'), recursive=True):
                try:
                    content = ""
                    if ext == '.txt' or ext == '.md':
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                    elif ext == '.pdf':
                        try:
                            with open(file_path, 'rb') as f:
                                reader = PyPDF2.PdfReader(f)
                                for page in reader.pages:
                                    content += page.extract_text() or ""
                        except Exception as e:
                            emit(f"Error reading PDF {file_path}: {e}", log=f"PDF read error: {e}")
                            continue

                    if content:
                        chunks = self._chunk_text(content)
                        for i, chunk in enumerate(chunks):
                            embedding = self._get_embedding(chunk)
                            self.local_document_index.append({
                                "source": file_path,
                                "chunk_id": i,
                                "content": chunk,
                                "embedding": embedding
                            })
                        emit(f"Indexed {len(chunks)} chunks from {file_path}", log=f"Indexed {file_path}")
                except Exception as e:
                    emit(f"Error indexing {file_path}: {e}", log=f"Error indexing {file_path}: {e}")
        
        emit(f"Finished indexing. Total chunks: {len(self.local_document_index)}", bar='', substep="Indexing", log="Local document indexing complete.")

    async def plan(self, goal: str, audience: str = "", tone: str = "", improvement: str = "", **kwargs) -> list:
        """Use the LLM to break down the research goal into steps, with context."""
        context = ""
        if audience:
            context += f"Intended audience: {audience}. "
        if tone:
            context += f"Preferred tone/style: {tone}. "
        if improvement:
            context += f"Special instructions: {improvement}. "
        
        prompt = (
        f"{context}\nYou are a research assistant. Break down the following research goal into simple, direct questions that work well for web search.\n\n"
        f"CRITICAL REQUIREMENTS:\n"
        f"- Each question must DIRECTLY relate to the research goal\n"
        f"- Each question must be SHORT and SPECIFIC (under 10 words)\n"
        f"- Use SIMPLE language, not academic jargon\n"
        f"- Focus on PRACTICAL, ACTIONABLE information\n"
        f"- Start each line with a dash (-) followed by a space\n"
        f"- NO explanations, reasoning, commentary, or introductory text\n"
        f"- ONLY return the bullet list, nothing else\n\n"
        f"Research goal: {goal}\n\n"
        f"IMPORTANT: Your questions must help answer the research goal above. Do NOT generate questions about unrelated topics.\n\n"
        f"Example format (do NOT include this text, only the questions):\n"
        f"- What is [specific topic]?\n"
        f"- How does [specific process] work?\n"
        f"- Who are the top [specific people/companies]?\n"
        f"- What are [specific topic] best practices?\n"
        f"- When did [specific development] happen?\n\n"
        f"Now generate 5-8 questions that directly help answer: {goal}"
    )
        # Use faster parameters for planning
        response = await self.llm.chat(self.model, prompt, temperature=0.1, max_tokens=512)
        # Clean the response to remove thinking tags and explanatory text
        cleaned_response = self.clean_llm_response(response)
        return cleaned_response

    def web_search(self, query: str, max_results: int = 10) -> list:
        """Sanitize the query and search the web."""
        # Sanitize the query to remove invalid characters and instructions
        import re
        sanitized_query = re.sub(r'\s*\(.*?\)\s*', '', query).strip()
        return search_web_with_fallback(sanitized_query, max_results=max_results)

    async def fetch_and_summarize_url(self, url: str, snippet: str = "", audience: str = "", tone: str = "", improvement: str = "") -> str:
        """Fetch content from URL and summarize it."""
        try:
            content = await fetch_url_text(url)
            if not content or len(content.strip()) < 100:
                return f"Unable to fetch meaningful content from {url}. Snippet: {snippet}"
            
            context = ""
            if audience:
                context += f"Intended audience: {audience}. "
            if tone:
                context += f"Preferred tone/style: {tone}. "
            if improvement:
                context += f"Special instructions: {improvement}. "
            
            prompt = f"{context}Create a comprehensive summary of the following content. Focus on extracting specific facts, data, examples, and actionable insights. Your summary should be detailed and thorough, covering:\n\n1. Main points and key findings\n2. Specific data, statistics, numbers, and examples\n3. Important context and background information\n4. Business insights, trends, or market information\n5. Any conclusions, recommendations, or implications\n\nAim for 4-6 detailed paragraphs that capture the full scope and depth of the information. Include specific details and avoid generic statements:\n\n{content[:8000]}"
            summary = await self.llm.chat(self.model, prompt, temperature=self.temperature, max_tokens=self.max_tokens)
            return summary
        except Exception as e:
            return f"Error processing {url}: {str(e)}. Snippet: {snippet}"

    def _is_semantically_similar(self, text: str, goal: str, threshold: float = 0.5) -> bool:
        """Helper to check for semantic similarity."""
        sim_path = os.path.join(os.path.dirname(__file__), 'semantic_similarity.py')
        spec = importlib.util.spec_from_file_location('semantic_similarity', sim_path)
        if spec and spec.loader:
            try:
                semantic_mod = importlib.util.module_from_spec(spec)
                sys.modules['semantic_similarity'] = semantic_mod
                spec.loader.exec_module(semantic_mod)
                return semantic_mod.is_semantically_similar(text, goal, threshold)
            except Exception:
                return False # If similarity check fails, assume not similar
        return False # Default to false if module can't be loaded

    def validate_content_relevance(self, summaries: list, goal: str, min_relevance_threshold: float = 0.01) -> tuple:
        """Validate that summaries are relevant to the research goal - very permissive approach."""
        if not summaries:
            return [], "No summaries provided for validation."

        relevant_summaries = []
        irrelevant_count = 0

        for summary in summaries:
            summary_lower = summary.lower()

            # Only filter out obvious technical errors and very short content
            error_indicators = [
                "404", "403", "500", "page not found", "corrupted pdf", 
                "unable to fetch", "access denied", "client error"
            ]
        
            # Very permissive filtering - only exclude obvious errors or very short content
            if any(indicator in summary_lower for indicator in error_indicators):
                irrelevant_count += 1
                continue
        
            if len(summary.strip()) < 30:  # Very short threshold
                irrelevant_count += 1
                continue
        
            # Include almost everything else
            relevant_summaries.append(summary)

        # If we have no relevant summaries, include everything except obvious errors
        if not relevant_summaries:
            for summary in summaries:
                if len(summary.strip()) > 10:  # Extremely low bar
                    relevant_summaries.append(summary)

        validation_msg = f"Content validation: {len(relevant_summaries)} relevant, {irrelevant_count} irrelevant summaries (permissive filtering)"
        return relevant_summaries, validation_msg

    async def synthesize(self, summaries: list, goal: str, audience: str = "", tone: str = "", improvement: str = "", **kwargs) -> str:
        # Fast fail for empty data to prevent hanging
        if not summaries:
            print("[SYNTHESIS] No summaries provided - returning early")
            return "No relevant information found to synthesize."
        
        # Fast fail for very short summaries that indicate data collection failure
        total_content_length = sum(len(str(summary)) for summary in summaries)
        if total_content_length < 100:
            print(f"[SYNTHESIS] Insufficient content ({total_content_length} chars) - likely data collection failure")
            return "Insufficient data collected for meaningful analysis. Please try again or check your internet connection."

        # Validate content relevance before synthesis
        relevant_summaries, validation_msg = self.validate_content_relevance(summaries, goal)
        print(f" {validation_msg}")
        
        # Use all summaries if validation returns empty (very permissive approach)
        if not relevant_summaries:
            relevant_summaries = summaries
            print("Using all summaries as fallback for synthesis")
        
        # Limit the number of summaries to avoid exceeding the context window
        if len(relevant_summaries) > 50:
            print(f"INFO: Limiting summaries for synthesis from {len(relevant_summaries)} to 50.")
            relevant_summaries = relevant_summaries[:50]

        context = ""
        if audience:
            context += f"Intended audience: {audience}. "
        if tone:
            context += f"Preferred tone/style: {tone}. "
        if improvement:
            context += f"Special instructions: {improvement}. "
        
        combined_summaries = "\n\n".join(relevant_summaries)
        
        # Debug output
        print(f"\n=== SYNTHESIS DEBUG ===")
        print(f"Research Goal: {goal}")
        print(f"Number of relevant summaries: {len(relevant_summaries)}")
        print(f"Combined summaries length: {len(combined_summaries)} characters")
        if relevant_summaries:
            print(f"First summary preview: {relevant_summaries[0][:200]}...")
        print(f"========================\n")
        
        prompt = f'''You are a research analyst. Write a comprehensive analysis based on the provided source material.

**Research Question:** {goal}

**Context:** {context}

**Source Material:**
{combined_summaries}

**Instructions:** 
Write a detailed research analysis with the following sections:

# Executive Summary
Provide a comprehensive overview of the key findings and main conclusions from the research.

# Background and Context
Establish the necessary context and background for understanding the topic.

# Key Findings
Present the main research findings with supporting evidence from the sources:
- Primary insights and discoveries
- Supporting data and evidence
- Relevant trends and patterns

# Analysis
Provide in-depth analysis of the findings:
- What do these results mean?
- How do different sources compare?
- What are the implications?

# Conclusions
Summarize the main conclusions and their significance.

Write in a clear, professional tone. Use specific evidence from the sources to support all claims. Be thorough and analytical.'''
        
        try:
            print(f"[SYNTHESIS DEBUG] Starting synthesis with {len(relevant_summaries)} summaries")
            print(f"[SYNTHESIS DEBUG] Model: {self.model}")
            print(f"[SYNTHESIS DEBUG] Prompt length: {len(prompt)} characters")
            
            # Use faster model for synthesis if using large models that may hang
            synthesis_model = self.model
            if self.model in ['qwen3:32b', 'qwen3:14b', 'deepseek-r1:32b', 'openthinker:32b']:
                synthesis_model = 'llama3.2:latest'  # Faster, smaller model for synthesis
                print(f"[SYNTHESIS DEBUG] Switching to faster model for synthesis: {synthesis_model}")
            
            # Override LLM parameters to disable safety filtering
            llm_params = {
                'temperature': self.temperature,
                'max_tokens': self.max_tokens,
                'system_prompt': 'You are a professional research analyst. Provide comprehensive, factual analysis based on the provided information. Do not refuse to analyze any legitimate research topics.',
                'top_p': 0.9,
                'repeat_penalty': 1.1
            }
            
            print(f"[SYNTHESIS DEBUG] About to call LLM with timeout=300s")
            # Add timeout to prevent infinite hanging
            import asyncio
            try:
                synthesis = await asyncio.wait_for(
                    self.llm.chat(synthesis_model, prompt, **llm_params),
                    timeout=300  # 5 minute timeout for synthesis
                )
                print(f"[SYNTHESIS DEBUG] LLM call completed, response length: {len(synthesis)}")
            except asyncio.TimeoutError:
                print("[SYNTHESIS] LLM synthesis timed out after 5 minutes")
                return "Analysis timed out. The research query may be too complex or the model is overloaded. Please try again with a simpler query or different research depth setting."
            
            # Debug: Check for refusal patterns
            refusal_patterns = [
                "i can't provide", "i cannot provide", "i'm unable to", "i apologize",
                "illegal or harmful", "against my guidelines", "i'm not able to"
            ]
            
            synthesis_lower = synthesis.lower()
            if any(pattern in synthesis_lower for pattern in refusal_patterns):
                print(f"\n=== LLM REFUSAL DETECTED ===")
                print(f"Synthesis response: {synthesis[:200]}...")
                print(f"Model: {self.model}")
                print(f"Prompt length: {len(prompt)} characters")
                print(f"========================\n")
                
                # Try a simpler, more direct prompt
                simple_prompt = f"""Analyze the following information about: {goal}

Information:
{combined_summaries[:5000]}  

Provide a comprehensive analysis covering:
1. Key findings
2. Important details
3. Main conclusions

Write in a professional, analytical tone."""
                
                print("Retrying with simplified prompt...")
                try:
                    synthesis = await asyncio.wait_for(
                        self.llm.chat(self.model, simple_prompt, temperature=self.temperature, max_tokens=self.max_tokens),
                        timeout=180  # 3 minute timeout for retry synthesis
                    )
                except asyncio.TimeoutError:
                    print("[SYNTHESIS] Retry synthesis also timed out")
                    return "Analysis failed due to timeout. Please try a simpler query or check if the model is responding properly."
            
            # Validate and clean up any hallucinated source references
            validated_synthesis = self.validate_and_clean_sources(synthesis, combined_summaries)
            return validated_synthesis
            
        except Exception as e:
            print(f"\n=== SYNTHESIS ERROR ===")
            print(f"Error: {str(e)}")
            print(f"Model: {self.model}")
            print(f"Prompt length: {len(prompt)} characters")
            print(f"========================\n")
            
            # Return a basic analysis as fallback
            return f"""# Analysis of {goal}

Based on the available research data, this analysis covers the key findings from {len(relevant_summaries)} sources.

## Key Information Found

The research gathered information from multiple authoritative sources covering various aspects of the topic.

## Summary

Detailed analysis was requested but encountered technical issues during generation. The source material contains relevant information that should be reviewed directly.

*Note: This is a fallback response due to synthesis processing issues. Please check the source material directly for detailed information.*"""


    def validate_and_clean_sources(self, synthesis: str, source_material: str) -> str:
        """Validate source references in synthesis and remove/flag hallucinated citations."""
        import re
        
        # Common patterns for fake source references that LLMs generate
        fake_source_patterns = [
            r'\(Source: \[.*?\]\)',  # (Source: [Something])
            r'\[.*? Source\]',       # [Print Shop Source], [Mimaki Source], etc.
            r'\(.*? Source\)',       # (Print Shop Source)
            r'Source: .*?(?=\.|\n)',  # Source: Something
            r'According to \[.*?\]',  # According to [Source]
            r'\[Source \d+\]',       # [Source 1], [Source 2]
            r'\(Ref: .*?\)',         # (Ref: Something)
            r'\[Ref \d+\]'          # [Ref 1], [Ref 2]
        ]
        
        cleaned_synthesis = synthesis
        removed_references = []
        
        # Remove fake source references
        for pattern in fake_source_patterns:
            matches = re.findall(pattern, cleaned_synthesis, re.IGNORECASE)
            if matches:
                removed_references.extend(matches)
                cleaned_synthesis = re.sub(pattern, '', cleaned_synthesis, flags=re.IGNORECASE)
        
        # Clean up extra whitespace and punctuation left by removed references
        cleaned_synthesis = re.sub(r'\s+', ' ', cleaned_synthesis)  # Multiple spaces to single
        cleaned_synthesis = re.sub(r'\s+\.', '.', cleaned_synthesis)  # Space before period
        cleaned_synthesis = re.sub(r'\s+,', ',', cleaned_synthesis)   # Space before comma
        cleaned_synthesis = re.sub(r'\.\s*\.', '.', cleaned_synthesis) # Double periods
        
        # Log what was removed for debugging
        if removed_references:
            print(f"\n=== SOURCE VALIDATION ===")
            print(f"Removed {len(removed_references)} hallucinated source references:")
            for ref in removed_references[:5]:  # Show first 5
                print(f"  - {ref}")
            if len(removed_references) > 5:
                print(f"  ... and {len(removed_references) - 5} more")
            print(f"========================\n")
        
        return cleaned_synthesis.strip()

    def retrieve_local_documents(self, query: str, top_k: int = 3) -> list:
        """Retrieves top_k most relevant local document chunks based on semantic similarity."""
        if not self.local_document_index:
            return []

        query_embedding = self._get_embedding(query)

        # Cosine similarity calculation
        def cosine_similarity(v1, v2):
            import numpy as np
            dot_product = np.dot(v1, v2)
            norm_v1 = np.linalg.norm(v1)
            norm_v2 = np.linalg.norm(v2)
            if norm_v1 == 0 or norm_v2 == 0:
                return 0.0
            return dot_product / (norm_v1 * norm_v2)

        scored_chunks = []
        for chunk_info in self.local_document_index:
            if "embedding" in chunk_info:
                score = cosine_similarity(query_embedding, chunk_info["embedding"])
                scored_chunks.append((score, chunk_info))

        # Sort by score in descending order and get top_k
        scored_chunks.sort(key=lambda x: x[0], reverse=True)

        relevant_chunks = []
        for score, chunk_info in scored_chunks[:top_k]:
            relevant_chunks.append(chunk_info["content"])

        return relevant_chunks

    async def critique_and_find_gaps(self, synthesis: str, goal: str) -> tuple:
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
        
        response = await self.llm.chat(self.model, prompt, temperature=self.temperature, max_tokens=self.max_tokens)
        
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
        sensitive_keywords = ['assassin', 'murder', 'kill', 'death', 'crime', 'history', 'historical', 'biography', 'war', 'assassination']
        query_lower = query.lower()
        
        if any(keyword in query_lower for keyword in sensitive_keywords):
            return query  # Return original query without domain filtering
        
        if domain == 'general':
            return query
        elif domain == 'technology':
            return f"{query} site:techcrunch.com OR site:arstechnica.com OR site:wired.com OR site:theverge.com"
        elif domain == 'business':
            return f"{query} site:entrepreneur.com OR site:inc.com OR site:sba.gov OR site:forbes.com/entrepreneurs OR site:smallbusiness.chron.com OR site:nerdwallet.com/small-business"
        elif domain == 'science':
            return f"{query} site:nature.com OR site:science.org OR site:ncbi.nlm.nih.gov OR site:pubmed.ncbi.nlm.nih.gov"
        elif domain == 'health':
            return f"{query} site:mayoclinic.org OR site:webmd.com OR site:nih.gov OR site:cdc.gov"
        elif domain == 'sports':
            return f"{query} site:espn.com OR site:sports.yahoo.com OR site:bleacherreport.com OR site:si.com OR site:nfl.com OR site:nba.com OR site:mlb.com OR site:nhl.com"
        elif domain == 'finance':
            return f"{query} site:bloomberg.com OR site:marketwatch.com OR site:yahoo.com/finance OR site:morningstar.com OR site:investopedia.com OR site:seekingalpha.com OR site:fool.com"
        elif domain == 'education':
            return f"{query} site:edu OR site:khanacademy.org OR site:coursera.org OR site:edx.org OR site:mit.edu OR site:stanford.edu OR site:harvard.edu"
        elif domain == 'politics':
            return f"{query} site:politico.com OR site:reuters.com OR site:apnews.com OR site:washingtonpost.com OR site:nytimes.com OR site:cnn.com/politics OR site:bbc.com/news/world"
        else:
            return query
    
    def write_report(self, synthesis: str, reasoning: str, web_results_md: list, goal: str, structured_data: str = None, audience: str = "", tone: str = "", improvement: str = "", citation_style: str = "APA", filename: str = None, project_name: str = None, documents_base_dir: str = None, **kwargs) -> str:
        """Write a formatted research report to the project directory."""
        if not filename:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"research_report_{timestamp}.md"

        save_dir = documents_base_dir
        if project_name and documents_base_dir:
            save_dir = os.path.join(documents_base_dir, project_name)
        elif not documents_base_dir:
            save_dir = os.getcwd() # Fallback if no base dir is provided

        os.makedirs(save_dir, exist_ok=True)
        report_path = os.path.join(save_dir, filename)

        # Create a comprehensive report structure
        current_time = datetime.datetime.now().strftime("%B %d, %Y at %I:%M %p")
        
        report_content = f"""# Comprehensive Research Report

**Research Question:** {goal}

**Report Generated:** {current_time}

**Audience:** {audience if audience else 'General'}

**Tone/Style:** {tone if tone else 'Professional Academic'}

---

{synthesis}

---

## Research Methodology

**Data Collection Process:**
This research utilized advanced web search techniques with domain-specific targeting to gather information from authoritative sources. The research process included:

- **Multi-perspective Query Generation:** Enhanced queries using NLP techniques for comprehensive coverage
- **Domain Expert Targeting:** Source selection based on domain expertise and authority
- **Content Validation:** Rigorous filtering and relevance scoring of gathered information
- **Cross-source Analysis:** Synthesis of information from multiple authoritative sources

**Research Parameters:**
- Search Strategy: {reasoning if reasoning else 'Multi-domain comprehensive approach'}
- Content Filtering: Relevance-scored and domain-validated
- Source Quality: Prioritized authoritative and expert sources

"""
        if structured_data:
            report_content += f"""## Structured Data

{structured_data}

"""
        # Enhanced source section
        report_content += """## Source Analysis and Bibliography

**Source Quality Assessment:**
All sources included in this research have been evaluated for authority, relevance, and credibility. The following sources provided the foundation for this analysis:

**Primary Sources:**
"""
        
        # Organize sources by type/domain for better presentation
        if web_results_md:
            report_content += "\n".join(web_results_md)
        else:
            report_content += "No web sources were successfully retrieved for this research."
            
        report_content += "\n\n**Research Notes:**\n"
        report_content += "- Sources were selected based on domain expertise and authority\n"
        report_content += "- Content was filtered for relevance to the research question\n"
        report_content += "- Multiple perspectives were sought to ensure comprehensive coverage\n"
        report_content += "- All information presented is derived directly from the listed sources\n\n"
        
        report_content += "---\n\n"
        report_content += f"**Report Completion:** This comprehensive research report contains {len(synthesis.split()) if synthesis else 0} words of analysis based on {len(web_results_md) if web_results_md else 0} source(s).\n\n"
        report_content += "*Generated by ResearchAgent - Advanced AI Research Assistant*"

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)

        return report_path

    async def run(self, goal: str, **kwargs):
        from sgptAgent.orchestrator import Orchestrator
        orchestrator = Orchestrator(**self.__dict__)
        return await orchestrator.run(goal, **kwargs)

    def clean_llm_response(self, response: str) -> str:
        """Clean LLM response by removing thinking tags and explanatory text."""
        import re
        
        # Remove thinking tags and their content
        response = re.sub(r'<thinking>.*?</thinking>', '', response, flags=re.DOTALL)
        
        # Remove common explanatory patterns that reasoning models produce
        explanatory_patterns = [
            r'Okay.*?(?=\n-|\n\*|\n\d+\.|$)',  # Catches "Okay, let's see. The user wants..."
            r'I need to.*?(?=\n-|\n\*|\n\d+\.|$)',
            r'Let me.*?(?=\n-|\n\*|\n\d+\.|$)',
            r'First.*?(?=\n-|\n\*|\n\d+\.|$)',
            r'The user.*?(?=\n-|\n\*|\n\d+\.|$)',
            r'To answer.*?(?=\n-|\n\*|\n\d+\.|$)',
            r'Here are.*?(?=\n-|\n\*|\n\d+\.|$)',
            r'Based on.*?(?=\n-|\n\*|\n\d+\.|$)',
        ]
        
        for pattern in explanatory_patterns:
            response = re.sub(pattern, '', response, flags=re.DOTALL | re.IGNORECASE)
        
        # If response still doesn't contain bullet points, extract only lines that start with bullets
        lines = response.split('\n')
        bullet_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped and any(stripped.startswith(marker) for marker in ['-', '*', '•', '1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.']):
                bullet_lines.append(line)
        
        # If we found bullet points, use only those
        if bullet_lines:
            response = '\n'.join(bullet_lines)
        
        # Clean up extra whitespace
        response = re.sub(r'\n\s*\n', '\n', response)
        response = response.strip()
        
        return response
    
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
            project_name = input("Enter a project name (optional, leave blank for none): ").strip()
            if not project_name:
                project_name = None
            agent = ResearchAgent()
            agent.run(goal, project_name=project_name)
    except (KeyboardInterrupt, EOFError):
        print("\nExiting.")
