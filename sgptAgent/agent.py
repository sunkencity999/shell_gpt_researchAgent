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

from dotenv import load_dotenv
load_dotenv()

class ResearchAgent:
    def __init__(self, model=None, temperature=0.7, max_tokens=1024, system_prompt="", ctx_window=2048):
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
            f"{context}\nBreak down the following research goal into step-by-step actions:\n{goal}\nRespond with a bullet list."
        )
        steps = self.llm.generate(
            prompt, model=self.model,
            temperature=self.temperature, max_tokens=self.max_tokens,
            system_prompt=self.system_prompt, context_window=self.ctx_window
        )
        self.memory.append({"goal": goal, "plan": steps, "audience": audience, "tone": tone, "improvement": improvement})
        return steps

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

    def synthesize(self, summaries: list, goal: str, audience: str = "", tone: str = "", improvement: str = "") -> str:
        context = ""
        if audience:
            context += f"Intended audience: {audience}. "
        if tone:
            context += f"Preferred tone/style: {tone}. "
        if improvement:
            context += f"Special instructions: {improvement}. "
        prompt = (
            f"{context}\nYou are an expert research assistant. Your task is to extract, merge, and cross-reference the actual factual information, data, and findings from the following summaries.\n"
            "Do NOT review, critique, or comment on the writing style, structure, or quality of the summaries.\n"
            "Instead, synthesize the core facts, insights, and evidence presented across all summaries into a single, unified, and information-rich research report.\n"
            "- Identify and merge overlapping facts or data points.\n"
            "- Cross-reference and reconcile any differing details.\n"
            "- Present the synthesized findings as if you had direct access to all the original source material.\n"
            "- Focus on delivering new, integrated knowledge and clarity, not meta-analysis.\n"
            "If technical topics are present, explain them clearly for the intended audience.\n"
            f"Research goal: {goal}\n\n"
            "Summaries:\n" + "\n---\n".join(summaries)
        )
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
            num_results=10, temperature=0.7, max_tokens=1024, system_prompt="", ctx_window=2048, citation_style="APA", filename=None):
        self.filename = filename
        # Update instance parameters for this run
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
        self.sources = []  # Track sources for bibliography
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console,
            transient=True,
        ) as progress:
            # Planning step
            plan_task = progress.add_task("Planning research steps...", total=1)
            steps = self.plan(goal, audience=audience, tone=tone, improvement=improvement)
            progress.update(plan_task, advance=1, description="Planning complete!")
            progress.refresh()

            # Web search step
            search_task = progress.add_task("Searching the web...", total=1)
            results = self.web_search(goal, max_results=num_results)
            progress.update(search_task, advance=1, description=f"Found {len(results)} web results.")
            progress.refresh()

            if len(results) < num_results:
                console.print(f"[yellow][WARNING] Only {len(results)} results found (requested {num_results}). Research may be less comprehensive.")
            console.print(f"\n[bold]Top {len(results)} Web Results:[/bold]")
            web_results_md = []
            self.sources = []
            for idx, r in enumerate(results, 1):
                console.print(f"{idx}. [link={r['href']}] {r['title']} [/link]\n   {r['snippet']}")
                web_results_md.append(f"### {idx}. [{r['title']}]({r['href']})\n{r['snippet']}")
                self.sources.append({"title": r.get("title", f"Source {idx}"), "href": r.get("href", ""), "snippet": r.get("snippet", "")})

            # Summarizing URLs with progress
            summarize_task = progress.add_task("Summarizing web results...", total=len(results))
            summaries = []
            summaries_md = []
            for idx, r in enumerate(results, 1):
                progress.update(summarize_task, description=f"Summarizing result {idx}/{len(results)}: {r['title']}")
                summary = self.fetch_and_summarize_url(r['href'], r.get('snippet', ''), audience=audience, tone=tone, improvement=improvement)
                summaries.append(summary)
                summaries_md.append(f"### {idx}. [{r['title']}]({r['href']})\n{summary}")
                progress.advance(summarize_task)
            progress.update(summarize_task, description="Summarization complete!")
            progress.refresh()

            # Synthesis step
            synth_task = progress.add_task("Synthesizing research summary...", total=1)
            synthesis = self.synthesize(summaries, goal, audience=audience, tone=tone, improvement=improvement)
            progress.update(synth_task, advance=1, description="Synthesis complete!")
            progress.refresh()

            # Write markdown report with timestamp
            report_task = progress.add_task("Writing Markdown report...", total=1)
            from datetime import datetime
            import os
            # Use provided filename if given, else auto-generate
            report_path = self.filename
            if not report_path:
                timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
                safe_goal = ''.join(c for c in goal if c.isalnum() or c in (' ', '_', '-')).rstrip()
                documents_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'documents')
                documents_dir = os.path.abspath(documents_dir)
                os.makedirs(documents_dir, exist_ok=True)
                report_path = os.path.join(documents_dir, f"research_report_{timestamp}.md")
            # Remove any text before the Shell GPT Research Agent banner (for dual CLI coexistence)
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
                report_content += f"{synthesis}\n"
                # Bibliography section
                if self.sources:
                    report_content += "\n## Bibliography\n"
                    report_content += self.generate_bibliography(self.sources, style=self.citation_style) + "\n"
                # Strip any stray output before the banner
                report_content = strip_pre_banner(report_content, banner="Shell GPT Research Agent")
                f.write(report_content)
            progress.update(report_task, advance=1, description="Report written!")
            progress.refresh()

        console.print(f"\n[green][Research report written to {report_path}]")
        return steps

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
