from sgpt.llm_functions.ollama import OllamaClient
from sgpt.config import cfg
from sgpt.web_search import search_web_with_fallback, fetch_url_text
from dotenv import load_dotenv
load_dotenv()

class ResearchAgent:
    def __init__(self, model=None):
        self.model = model or cfg.get("DEFAULT_MODEL")
        # Remove 'ollama/' prefix if present
        if self.model.startswith('ollama/'):
            self.model = self.model.split('/', 1)[1]
        self.llm = OllamaClient()
        self.memory = []  # Simple in-memory history for now

    def plan(self, goal: str) -> list:
        """Use the LLM to break down the research goal into steps."""
        prompt = f"Break down the following research goal into step-by-step actions:\n{goal}\nRespond with a bullet list."
        steps = self.llm.generate(prompt, model=self.model)
        self.memory.append({"goal": goal, "plan": steps})
        return steps

    def web_search(self, query: str, max_results: int = 3) -> list:
        """Perform a real web search (with fallback) and return results."""
        return search_web_with_fallback(query, max_results=max_results)

    def fetch_and_summarize_url(self, url: str, snippet: str = "") -> str:
        """Fetch URL content and summarize it with the LLM. Returns summary or error message."""
        text = fetch_url_text(url, snippet)
        print(f"[DEBUG] Extracted text length: {len(text)} for {url}")
        print(f"[DEBUG] Extracted text preview: {text[:300].replace(chr(10),' ')}")
        if not text or len(text.strip()) < 100:
            return f"[Fetch failed: insufficient content from {url}]"
        prompt = (
            "Write a detailed, multi-paragraph summary of the following web page content. "
            "Make it suitable for a research report. Include all key findings, context, and implications.\n\n"
            f"Content:\n{text}"
        )
        print(f"[DEBUG] Prompt length: {len(prompt)}")
        print(f"[DEBUG] Prompt preview: {prompt[:500].replace(chr(10),' ')}")
        try:
            summary = self.llm.generate(prompt, model=self.model)
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

    def synthesize(self, summaries: list, goal: str) -> str:
        prompt = (
            "You are an expert research assistant. Synthesize the following summaries from multiple sources "
            "into a single, comprehensive, verbose research report. Address the research goal explicitly.\n\n"
            f"Research goal: {goal}\n\n"
            "Summaries:\n" + "\n---\n".join(summaries)
        )
        return self.llm.generate(prompt, model=self.model)

    def run(self, goal: str):
        print(f"Goal: {goal}\n")
        steps = self.plan(goal)
        print("Plan:\n", steps)
        results = self.web_search(goal, max_results=10)
        if len(results) < 10:
            print(f"[WARNING] Only {len(results)} results found (requested 10). Research may be less comprehensive.")
        print(f"\nTop {len(results)} Web Results:")
        web_results_md = []
        for idx, r in enumerate(results, 1):
            print(f"{idx}. {r['title']}\n   {r['href']}\n   {r['snippet']}\n")
            web_results_md.append(f"### {idx}. [{r['title']}]({r['href']})\n{r['snippet']}")
        # Summarize all results, ensure summary is non-empty
        summaries = []
        summaries_md = []
        for idx, r in enumerate(results, 1):
            if r['href']:
                print(f"\nSummary of result {idx}:")
                summary = self.fetch_and_summarize_url(r['href'], r.get('snippet', ''))
                print(f"[LLM summary output for result {idx}]:\n{summary}\n---")
                if not summary or summary.strip() == '' or summary.startswith('[Fetch failed') or summary.startswith('[Error'):
                    print(f"[WARNING] No summary generated for result {idx} ({r['href']}). Skipping.")
                    # Optionally retry once
                    retry_summary = self.fetch_and_summarize_url(r['href'], r.get('snippet', ''))
                    if retry_summary and retry_summary.strip() != '' and not retry_summary.startswith('[Fetch failed') and not retry_summary.startswith('[Error'):
                        print(f"[LLM summary output on retry for result {idx}]:\n{retry_summary}\n---")
                        print(retry_summary)
                        summaries.append(retry_summary)
                        summaries_md.append(f"#### Summary of result {idx}\n{retry_summary}")
                    else:
                        print(f"[WARNING] Retry also failed for result {idx}.")
                else:
                    print(summary)
                    summaries.append(summary)
                    summaries_md.append(f"#### Summary of result {idx}\n{summary}")
            else:
                print(f"\nNo URL to summarize for result {idx}.")
        print(f"\n{len(summaries)} out of {len(results)} results were successfully summarized and will be used for synthesis.")
        # Synthesize all summaries into a final answer
        synthesis = ""
        if summaries:
            print("\nSYNTHESIZED RESEARCH SUMMARY:")
            synthesis = self.synthesize(summaries, goal)
            print(synthesis)
        else:
            print("\nNo valid summaries to synthesize.")
        # Write markdown report with timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
        safe_goal = ''.join(c for c in goal if c.isalnum() or c in (' ', '_', '-')).rstrip()
        report_path = f"research_report_{timestamp}.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(f"# Research Report: {goal}\n\n")
            f.write("## Research Plan\n")
            f.write(f"{steps}\n\n")
            f.write("## Web Results\n")
            f.write("\n".join(web_results_md) + "\n\n")
            f.write("## Summaries\n")
            f.write("\n".join(summaries_md) + "\n\n")
            f.write("## Synthesized Research Summary\n")
            f.write(f"{synthesis}\n")
        print(f"\n[Research report written to {report_path}]")
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
