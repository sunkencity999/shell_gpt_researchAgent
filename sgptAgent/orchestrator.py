
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
        summaries = []
        for query in queries:
            results = self.web_search(query)
            for result in results:
                summary = self.fetch_and_summarize_url(result['href'], result.get('snippet', ''))
                summaries.append(summary)
        return summaries

class ReportGeneratorAgent(ResearchAgent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def run(self, goal: str, summaries: list, **kwargs) -> str:
        synthesis = self.synthesize(summaries, goal, **kwargs)
        return self.write_report(synthesis, [], goal, **kwargs)

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
        summaries = self.data_collector.run(queries, **kwargs)

        emit("Generating report...", substep="Report Generation", percent=80)
        report_path = self.report_generator.run(goal, summaries, **kwargs)
        
        emit("Research complete!", substep="Complete", percent=100)
        return report_path, 0, 0, 0
