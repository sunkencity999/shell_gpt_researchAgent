
from sgptAgent.agent import ResearchAgent
from sgptAgent.config import cfg
import os

class PlannerAgent(ResearchAgent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def run(self, goal: str, **kwargs) -> list:
        return self.plan(goal, **kwargs)

class DataCollectorAgent(ResearchAgent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def run(self, queries: list, multimodal_agent, vision_agent, **kwargs) -> tuple:
        results = []
        total_results_found = 0
        successful_queries = 0
        total_queries = len(queries)

        for query in queries:
            search_results = self.web_search(query)
            if search_results:
                successful_queries += 1
                total_results_found += len(search_results)
                for result in search_results:
                    summary = await self.fetch_and_summarize_url(result['href'], result.get('snippet', ''))
                    image_analyses = await vision_agent._process_images(result['href'], kwargs.get("project_name"), kwargs.get("documents_base_dir"), multimodal_agent)
                    results.append({
                        "title": result.get("title"),
                        "href": result.get("href"),
                        "snippet": result.get("snippet"),
                        "summary": summary,
                        "images": image_analyses
                    })
        return results, total_results_found, successful_queries, total_queries

class ReportGeneratorAgent(ResearchAgent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def run(self, goal: str, results: list, **kwargs) -> str:
        summaries = [result["summary"] for result in results]
        web_results_md = []
        for result in results:
            web_results_md.append(f"### [{result['title']}]({result['href']})\n{result['snippet']}")
            if result.get("images"):
                web_results_md.append("\n**Image Analysis:**")
                for image in result["images"]:
                    web_results_md.append(f"- Image: {image['image_path']}")
                    web_results_md.append(f"  - Analysis: {image['analysis']}")

        synthesis = self.synthesize(summaries, goal, **kwargs)
        self.sources = results # Set the sources for the report
        return self.write_report(synthesis, web_results_md, goal, **kwargs)

class VisionAgent(ResearchAgent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.multimodal_model = cfg.get("MULTIMODAL_MODEL")

    def run(self, url: str, project_name: str, documents_base_dir: str) -> list:
        return self._process_images(url, project_name, documents_base_dir, self)

    async def _process_images(self, url: str, project_name: str, documents_base_dir: str, multimodal_agent) -> list:
        image_analyses = []
        try:
            from bs4 import BeautifulSoup
            import requests
            from urllib.parse import urljoin, urlparse
            import base64
            import asyncio

            response = requests.get(url)
            soup = BeautifulSoup(response.content, "html.parser")
            images = soup.find_all("img")

            if not images:
                return image_analyses

            project_dir = os.path.join(documents_base_dir, project_name)
            images_dir = os.path.join(project_dir, "images")
            os.makedirs(images_dir, exist_ok=True)

            async def process_single_image(i, img):
                img_url = img.get("src")
                if not img_url:
                    return None

                if img_url.startswith("data:image"):
                    try:
                        header, encoded = img_url.split(",", 1)
                        ext = header.split("/")[1].split(";")[0]
                        # Add padding if missing, which is a common issue with web-sourced base64
                        padding = '=' * (-len(encoded) % 4)
                        img_data = base64.b64decode(encoded + padding)
                        if len(img_data) < 10000: # Filter out small images
                            return None
                        img_name = f"image_{i}.{ext}"
                        img_path = os.path.join(images_dir, img_name)
                        with open(img_path, "wb") as f:
                            f.write(img_data)
                    except Exception as e:
                        print(f"Error processing data URI image: {e}")
                        return None
                else:
                    img_url = urljoin(url, img_url)
                    try:
                        img_response = requests.get(img_url, stream=True)
                        img_response.raise_for_status()
                        # Check content length to filter small images
                        if int(img_response.headers.get('content-length', 0)) < 10000:
                            return None
                        img_data = img_response.content
                        img_name = os.path.basename(urlparse(img_url).path)
                        if not img_name:
                            _, ext = os.path.splitext(img_url)
                            if ext.lower() not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                                ext = '.jpg'
                            img_name = f"image_{i}{ext}"
                        img_path = os.path.join(images_dir, img_name)
                        with open(img_path, "wb") as f:
                            f.write(img_data)
                    except Exception as e:
                        print(f"Error downloading image {img_url}: {e}")
                        return None

                try:
                    analysis = multimodal_agent.run(img_path)
                    return {"image_path": img_path, "analysis": analysis}
                except Exception as e:
                    print(f"Error analyzing image {img_path}: {e}")
                    return None

            tasks = [process_single_image(i, img) for i, img in enumerate(images[:5])] # Limit to first 5 images
            results = await asyncio.gather(*tasks)
            image_analyses = [res for res in results if res is not None]

        except Exception as e:
            print(f"Error processing images for {url}: {e}")

        return image_analyses

class MultimodalAgent(ResearchAgent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.multimodal_model = cfg.get("MULTIMODAL_MODEL")

    def run(self, image_path: str) -> str:
        return self.llm.chat_with_image(self.multimodal_model, "Describe this image in detail.", image_path)

class Orchestrator:
    def __init__(self, **kwargs):
        self.planner = PlannerAgent(**kwargs)
        self.data_collector = DataCollectorAgent(**kwargs)
        self.report_generator = ReportGeneratorAgent(**kwargs)
        self.vision_agent = VisionAgent(**kwargs)
        self.multimodal_agent = MultimodalAgent(**kwargs)

    async def run(self, goal: str, **kwargs):
        mode = kwargs.get("mode", "research")
        if mode == "vision":
            return self.vision_agent.run(goal, **kwargs)

        progress_callback = kwargs.get('progress_callback')

        def emit(desc, substep=None, percent=None, log=None):
            if progress_callback:
                progress_callback(desc, '', substep, percent, log)

        emit("Planning...", substep="Planning", percent=10)
        plan = self.planner.run(goal, **kwargs)
        
        emit("Collecting data...", substep="Data Collection", percent=30)
        # The plan is a string of bullet points, so we need to parse it into a list of strings
        queries = [line.strip('-*• ') for line in plan.split('\n') if line.strip('-*• ')]
        results, total_results_found, successful_queries, total_queries = await self.data_collector.run(queries, multimodal_agent=self.multimodal_agent, vision_agent=self.vision_agent, **kwargs)

        emit("Generating report...", substep="Report Generation", percent=80)
        report_path = self.report_generator.run(goal, results, **kwargs)
        
        emit("Research complete!", substep="Complete", percent=100)
        return report_path, total_results_found, successful_queries, total_queries
