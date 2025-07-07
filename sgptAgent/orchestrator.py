
from sgptAgent.agent import ResearchAgent

class PlannerAgent(ResearchAgent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def run(self, goal: str, **kwargs) -> list:
        return self.plan(goal, **kwargs)

class DataCollectorAgent(ResearchAgent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def run(self, queries: list, **kwargs) -> list:
        results = []
        for query in queries:
            search_results = self.web_search(query)
            for result in search_results:
                summary = self.fetch_and_summarize_url(result['href'], result.get('snippet', ''))
                results.append({
                    "title": result.get("title"),
                    "href": result.get("href"),
                    "snippet": result.get("snippet"),
                    "summary": summary
                })
        return results

class ReportGeneratorAgent(ResearchAgent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def run(self, goal: str, results: list, **kwargs) -> str:
        summaries = [result["summary"] for result in results]
        web_results_md = [f"### [{result['title']}]({result['href']})\n{result['snippet']}" for result in results]
        synthesis = self.synthesize(summaries, goal, **kwargs)
        self.sources = results # Set the sources for the report
        return self.write_report(synthesis, web_results_md, goal, **kwargs)

class Orchestrator:
    def __init__(self, **kwargs):
        self.planner = PlannerAgent(**kwargs)
        self.data_collector = DataCollectorAgent(**kwargs)
        self.report_generator = ReportGeneratorAgent(**kwargs)

    def run(self, goal: str, **kwargs):
        progress_callback = kwargs.get('progress_callback')

        def emit(desc, substep=None, percent=None, log=None):
            if progress_callback:
                progress_callback(desc, '', substep, percent, log)

        emit("Planning...", substep="Planning", percent=10)
        plan = self.planner.run(goal, **kwargs)
        
        emit("Collecting data...", substep="Data Collection", percent=30)
        # The plan is a string of bullet points, so we need to parse it into a list of strings
        queries = [line.strip('-*• ') for line in plan.split('\n') if line.strip('-*• ')]
        results = self.data_collector.run(queries, **kwargs)

        emit("Generating report...", substep="Report Generation", percent=80)
        report_path = self.report_generator.run(goal, results, **kwargs)
        
        emit("Research complete!", substep="Complete", percent=100)
        return report_path, 0, 0, 0
