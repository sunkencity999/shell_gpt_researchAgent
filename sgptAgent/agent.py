import sys
import os
import importlib.util
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
    def __init__(self, model=None, temperature=0.7, max_tokens=2048, system_prompt="", ctx_window=2048, **kwargs):
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
        response = await self.llm.chat(self.model, prompt, temperature=self.temperature, max_tokens=self.max_tokens)
        return response

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
            
            prompt = f"{context}Summarize the following content in 2-3 sentences, focusing on the key information:\n\n{content[:2000]}"
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

    def validate_content_relevance(self, summaries: list, goal: str, min_relevance_threshold: float = 0.1) -> tuple:
        """Validate that summaries are relevant to the research goal before synthesis, using a hybrid approach."""
        if not summaries:
            return [], "No summaries provided for validation."

        relevant_summaries = []
        irrelevant_count = 0

        # Extract key terms from the research goal
        goal_lower = goal.lower()
        # Be more inclusive with keywords
        goal_keywords = set(word.strip('.,!?()[]{}":;') for word in goal_lower.split()
                           if len(word) > 2 and word not in ['the', 'and', 'or', 'but', 'for', 'with', 'this', 'that', 'what', 'how', 'who', 'is', 'a', 'in', 'to', 'of'])

        for summary in summaries:
            summary_lower = summary.lower()

            # 1. Check for explicit error indicators or irrelevant topics
            error_indicators = [
                "error message", "page not found", "copyright", "terms and conditions",
                "login to access", "cannot be provided", "generic webpage", "corrupted pdf",
                "unable to fetch", "access denied", "404", "403", "500", "client error",
                "i apologize", "i'm unable", "i cannot", "not related to", "appears to be",
                "stardew valley", "daily harvest", "u.s. bureau of labor statistics"
            ]
            if any(indicator in summary_lower for indicator in error_indicators):
                irrelevant_count += 1
                continue

            # 2. Calculate keyword overlap score
            summary_words = set(word.strip('.,!?()[]{}":;') for word in summary_lower.split())
            overlap = len(goal_keywords.intersection(summary_words))
            relevance_score = overlap / len(goal_keywords) if goal_keywords else 0

            # 3. Check for semantic similarity
            is_similar = self._is_semantically_similar(summary_lower, goal_lower, threshold=0.45)

            # 4. Determine relevance
            if relevance_score >= min_relevance_threshold or is_similar:
                relevant_summaries.append(summary)
            else:
                irrelevant_count += 1

        # If no summaries are relevant, be less strict and try again
        if not relevant_summaries and summaries:
            for summary in summaries:
                 # Check again with a lower semantic threshold
                 if self._is_semantically_similar(summary.lower(), goal.lower(), threshold=0.35):
                     relevant_summaries.append(summary)
            if relevant_summaries:
                irrelevant_count = len(summaries) - len(relevant_summaries)


        validation_msg = f"Content validation: {len(relevant_summaries)} relevant, {irrelevant_count} irrelevant summaries"
        return relevant_summaries, validation_msg

    async def synthesize(self, summaries: list, goal: str, audience: str = "", tone: str = "", improvement: str = "", **kwargs) -> str:
        """Synthesize multiple summaries into a coherent answer with content validation."""
        if not summaries:
            return "No relevant information found to synthesize."
        
        # Validate content relevance before synthesis
        relevant_summaries, validation_msg = self.validate_content_relevance(summaries, goal)
        print(f" {validation_msg}")
        
        if not relevant_summaries:
            return f"""I apologize, but I was unable to find relevant information to answer your research question: "{goal}"\n\nThe search results contained content that was not related to your specific question. This could be due to:\n1. Limited availability of specific data on this topic\n2. Search queries not targeting the right sources\n3. The information you're looking for may require access to specialized databases\n\n**Suggestions:**\n- Try rephrasing your research question with more specific terms\n- Consider breaking down your question into smaller, more focused parts\n- Look for official sources, academic papers, or industry-specific databases\n- Try using more specific keywords related to your topic\n\n**Alternative approach:** You might want to search for more specific aspects of your topic or try different keyword combinations to get more targeted results."""
        
        # Limit the number of summaries to avoid exceeding the context window
        if len(relevant_summaries) > 30:
            print(f"INFO: Limiting summaries for synthesis from {len(relevant_summaries)} to 30.")
            relevant_summaries = relevant_summaries[:30]

        context = ""
        if audience:
            context += f"Intended audience: {audience}. "
        if tone:
            context += f"Preferred tone/style: {tone}. "
        if improvement:
            context += f"Special instructions: {improvement}. "
        
        combined_summaries = "\n\n".join(relevant_summaries)
        
        prompt = f'''**Your Task:** Answer the following research goal **using only the provided summaries**. Your answer must be a direct and concise synthesis of the information. Do not add any information that is not present in the summaries.

**Research Goal:**
{goal}

**Summaries:**
---
{combined_summaries}
---

**Answer:**
'''
        
        synthesis = await self.llm.chat(self.model, prompt, temperature=self.temperature, max_tokens=self.max_tokens)
        return synthesis

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
    
    def write_report(self, synthesis: str, reasoning: str, web_results_md: list, goal: str, structured_data: str = None, audience: str = "", tone: str = "", improvement: str = "", citation_style: str = "APA", filename: str = None, project_name: str = None, documents_base_dir: str = None, **kwargs) -> str:
        """Write a formatted research report to the project directory."""
        if not filename:
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"research_report_{timestamp}.md"

        save_dir = documents_base_dir
        if project_name and documents_base_dir:
            save_dir = os.path.join(documents_base_dir, project_name)
        elif not documents_base_dir:
            save_dir = os.getcwd() # Fallback if no base dir is provided

        os.makedirs(save_dir, exist_ok=True)
        report_path = os.path.join(save_dir, filename)

        report_content = f"""# Research Report: {goal}

## Synthesis

{synthesis}

### Reasoning

{reasoning}

"""
        if structured_data:
            report_content += f"""## Structured Data

{structured_data}

"""
        report_content += "## Sources\n\n"
        report_content += "\n".join(web_results_md)

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)

        return report_path

    async def run(self, goal: str, **kwargs):
        from sgptAgent.orchestrator import Orchestrator
        orchestrator = Orchestrator(**self.__dict__)
        return await orchestrator.run(goal, **kwargs)

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
