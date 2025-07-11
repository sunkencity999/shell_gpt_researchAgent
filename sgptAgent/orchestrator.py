
from sgptAgent.agent import ResearchAgent
from sgptAgent.config import cfg
import os

class PlannerAgent(ResearchAgent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def run(self, goal: str, **kwargs) -> list:
        return await self.plan(goal, **kwargs)

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
                    image_analyses = []
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

    async def run(self, goal: str, results: list, **kwargs) -> str:
        summaries = [result["summary"] for result in results]
        web_results_md = []
        for result in results:
            web_results_md.append(f"### [{result['title']}]({result['href']})\n{result['snippet']}")
            if result.get("images"):
                web_results_md.append("\n**Image Analysis:**")
                for image in result["images"]:
                    web_results_md.append(f"- Image: {image['image_path']}")
                    web_results_md.append(f"  - Analysis: {image['analysis']}")

        synthesis = await self.synthesize(summaries, goal, **kwargs)
        reasoning = await self.generate_reasoning(synthesis, summaries, goal, **kwargs)
        self.sources = results # Set the sources for the report

        structured_data = None
        if kwargs.get("structured_data_prompt"):
            # Copy kwargs to avoid modifying the original dict, which might be used elsewhere.
            llm_kwargs = kwargs.copy()
            prompt_text = llm_kwargs.pop("structured_data_prompt", None)
            llm_kwargs.pop("progress_callback", None)  # Avoid passing non-serializable functions
            structured_data = await self.extract_structured_data(summaries, structured_data_prompt=prompt_text, goal=goal, **llm_kwargs)

        # Explicitly pass arguments to avoid TypeError
        return self.write_report(
            synthesis=synthesis, 
            reasoning=reasoning, 
            web_results_md=web_results_md, 
            goal=goal, 
            structured_data=structured_data, 
            audience=kwargs.get("audience"),
            tone=kwargs.get("tone"),
            improvement=kwargs.get("improvement"),
            citation_style=kwargs.get("citation_style"),
            filename=kwargs.get("filename"),
            project_name=kwargs.get("project_name"),
            documents_base_dir=kwargs.get("documents_base_dir")
        )

    async def generate_reasoning(self, synthesis: str, summaries: list, goal: str, **kwargs) -> str:
        llm_kwargs = kwargs.copy()
        llm_kwargs.pop("progress_callback", None)
        combined_summaries = "\n\n".join(summaries)
        prompt = f'''You are a research analyst. Your task is to explain the reasoning behind a given conclusion based on a set of summaries.
Focus on connecting the key points in the summaries to the final answer, explaining *how* the evidence supports the conclusion.

**Research Goal:**
"""
{goal}
"""

**Conclusion:**
"""
{synthesis}
"""

**Evidence (Summaries):**
"""
{combined_summaries}
"""

**Reasoning:**
(Explain the *why* behind the conclusion, citing the evidence from the summaries.)
'''
        return await self.llm.chat(self.model, prompt, **llm_kwargs)

    async def extract_structured_data(self, summaries: list, structured_data_prompt: str, goal: str, **kwargs) -> str:
        llm_kwargs = kwargs.copy()
        llm_kwargs.pop("progress_callback", None)
        combined_summaries = "\n\n".join(summaries)
        prompt = f'''You are a data extraction tool. Your task is to extract information from the provided text based on the user's request and return it as a Markdown table.
Do not include any explanations, apologies, or conversational text. Only output the raw Markdown table.

**Research Goal:** "{goal}"

**User Request:** "{structured_data_prompt}"

**Text to Extract From:**
---
{combined_summaries}
---

**Markdown Table Output:**
| Header 1 | Header 2 | Header 3 |
|---|---|---|
| Data 1 | Data 2 | Data 3 |

(Your Markdown table output should follow this format)
'''
        return await self.llm.chat(self.model, prompt, **llm_kwargs)

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

            response = requests.get(url, timeout=30)
            soup = BeautifulSoup(response.content, "html.parser")
            images = soup.find_all("img")
            page_domain = urlparse(url).netloc

            if not images:
                return image_analyses

            base_dir = documents_base_dir if documents_base_dir else os.getcwd()
            if project_name:
                project_dir = os.path.join(base_dir, project_name)
            else:
                project_dir = base_dir
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
                    # Check if the image is from the same domain
                    if urlparse(img_url).netloc != page_domain:
                        return None
                    try:
                        img_response = requests.get(img_url, stream=True, timeout=15)
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

            for i, img in enumerate(images[:5]): # Limit to first 5 images
                result = await process_single_image(i, img)
                if result:
                    image_analyses.append(result)

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
        plan = await self.planner.run(goal, **kwargs)
        
        emit("Collecting data...", substep="Data Collection", percent=30)
        # The plan is a string of bullet points, so we need to parse it into a list of strings
        queries = [line.strip('-*• ') for line in plan.split('\n') if line.strip('-*• ')]
        results, total_results_found, successful_queries, total_queries = await self.data_collector.run(queries, multimodal_agent=self.multimodal_agent, vision_agent=self.vision_agent, **kwargs)

        emit("Generating report...", substep="Report Generation", percent=80)
        report_path = await self.report_generator.run(goal, results, **kwargs)
        
        emit("Research complete!", substep="Complete", percent=100)
        return report_path, total_results_found, successful_queries, total_queries
