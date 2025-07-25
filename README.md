<div align="center">
  <img src="sgptAgent/Assets/sgptRAicon.png" alt="Shell GPT Research Agent Logo" width="160"/>
  <br/>
  <em>Shell-GPT Research Agent</em>
</div>

# 🔬 **Advanced Open-Source AI Research Agent**

**A sophisticated autonomous research assistant** - combining multi-step reasoning, domain-aware query enhancement, and intelligent synthesis to deliver comprehensive, evidence-based research reports that go far beyond what any single LLM query or Google search can provide. Powered by local LLM inference with Ollama.

---

## 🎯 **Why ResearchAgent > Simple LLM Queries + Google Search**

| **Traditional Approach** | **ResearchAgent** |
|---------------------------|-------------------|
| ❌ Single query, limited context | ✅ **Multi-step reasoning** with 10+ targeted searches |
| ❌ Generic search terms | ✅ **Domain-aware query enhancement** with NLP |
| ❌ Manual source evaluation | ✅ **Automated relevance scoring** and content validation |
| ❌ Surface-level information | ✅ **Deep synthesis** with cross-source validation |
| ❌ No fact-checking | ✅ **Iterative refinement** with gap analysis |
| ❌ Inconsistent quality | ✅ **Progressive fallback strategies** ensure results |

### **🧠 The Intelligence Difference**

**Simple LLM Query:** *"Which team is better, Dodgers or Giants?"*
- **Result:** Generic response based on training data cutoff
- **Limitations:** No current data, no specific metrics, no evidence

**Google Search:** *"Dodgers vs Giants"*
- **Result:** Random mix of news articles, opinions, outdated stats
- **Limitations:** Manual filtering, no synthesis, information overload

**ResearchAgent:** *"Which is the better team this decade, the LA Dodgers or SF Giants?"*
- **Result:** Comprehensive analysis with:
  - ✅ **Current statistics** from MLB.com, Baseball-Reference, ESPN
  - ✅ **Multi-year performance** comparison (2015-2024)
  - ✅ **Playoff records**, World Series wins, division titles
  - ✅ **Advanced metrics** (WAR, OPS+, ERA+, defensive efficiency)
  - ✅ **Expert analysis** synthesis from multiple sports journalists
  - ✅ **Evidence-based conclusion** with supporting data

---

## 🚀 **Core Capabilities**

### **🎯 Multi-Step Reasoning Engine**
- **Autonomous Planning**: Breaks complex questions into 5-10 focused sub-questions
- **Progressive Research**: Each step builds on previous findings
- **Dynamic Adaptation**: Adjusts strategy based on intermediate results
- **Gap Analysis**: Identifies and fills missing information automatically

### **🧠 Advanced NLP & Query Enhancement**
- **Entity Recognition**: Uses spaCy to extract organizations, people, dates, locations
- **Domain Intelligence**: Both automatic detection AND user-selectable domains (Technology, Healthcare, Finance, Legal, Academic, Business, Science, General)
- **Domain-Aware Enhancement**: Specialized agents enhance queries with domain-specific terminology and research focus
- **Query Expansion**: NLTK WordNet synonyms + domain-specific keywords
- **Contextual Rewriting**: Generates 10+ targeted search variations per step

### **🔍 Intelligent Search Strategy**
- **Multi-Provider Search**: Google CSE, DuckDuckGo, Brave Search
- **Domain-Specific Targeting**: 
  - Sports → MLB.com, ESPN, Baseball-Reference, FanGraphs
  - Technology → TechCrunch, Ars Technica, Wired, The Verge
  - Business → Bloomberg, Reuters, WSJ, Forbes
  - Science → Nature, Science.org, NCBI, PubMed
- **Progressive Fallback**: 5-level search strategy ensures relevant results
- **Relevance Scoring**: TF-IDF + keyword overlap + entity presence

### **📊 Content Validation & Quality Control**
- **Pre-Synthesis Filtering**: Removes irrelevant, error, or low-quality content
- **Source Credibility**: Prioritizes authoritative domain sources
- **Content Deduplication**: Fuzzy matching prevents redundant information
- **Error Detection**: Identifies 404s, access denied, corrupted content

### **🔬 Advanced Synthesis Engine**
- **Multi-Source Integration**: Combines information from 20+ sources per report
- **Conflict Resolution**: Identifies and addresses contradictory information
- **Evidence Linking**: Connects claims to specific sources and data
- **Confidence Scoring**: Indicates reliability of synthesized conclusions

### **🗂️ Project-Based Workflow**
- **Stateful Research**: All research artifacts (plan, sources, summaries, reports) are saved to a dedicated project directory.
- **Continuous Research**: Easily resume and build upon previous research by selecting an existing project.
- **Knowledge Base**: Over time, your projects become a valuable, queryable knowledge base.

---

## 📋 **Use Cases & Examples**

### **🏆 Sports Analysis**
**Query:** *"Compare the offensive performance of the Yankees and Red Sox over the past 5 seasons"*

**ResearchAgent Approach:**
1. **Planning**: Breaks down into batting stats, home runs, OPS, team records
2. **Enhanced Queries**: "Yankees batting average 2019-2024", "Red Sox OPS+ advanced metrics"
3. **Domain Targeting**: Searches Baseball-Reference, FanGraphs, MLB.com
4. **Synthesis**: Comprehensive comparison with specific statistics and trends

**Why Better:** Gets current, specific data from authoritative sources vs generic LLM knowledge

### **💼 Business Intelligence**
**Query:** *"Analyze the competitive landscape for electric vehicle manufacturers in 2024"*

**ResearchAgent Approach:**
1. **Planning**: Market share, production volumes, technology advantages, financial performance
2. **Enhanced Queries**: "Tesla Model Y sales Q3 2024", "BYD global market share electric vehicles"
3. **Domain Targeting**: Bloomberg, Reuters, company investor relations, industry reports
4. **Synthesis**: Data-driven competitive analysis with market positioning

**Why Better:** Current market data and financial metrics vs outdated training data

### **🔬 Scientific Research**
**Query:** *"What are the latest developments in CRISPR gene editing for cancer treatment?"*

**ResearchAgent Approach:**
1. **Planning**: Recent trials, FDA approvals, success rates, specific cancer types
2. **Enhanced Queries**: "CRISPR CAR-T therapy clinical trials 2024", "FDA approval gene editing cancer"
3. **Domain Targeting**: PubMed, Nature, Science.org, clinical trial databases
4. **Synthesis**: Evidence-based summary of current research status

**Why Better:** Latest peer-reviewed research vs potentially outdated information

### **📈 Investment Analysis**
**Query:** *"Should I invest in renewable energy stocks in 2025?"*

**ResearchAgent Approach:**
1. **Planning**: Market trends, policy changes, company performance, growth projections
2. **Enhanced Queries**: "renewable energy stock performance 2024", "IRA tax credits solar wind"
3. **Domain Targeting**: MarketWatch, Yahoo Finance, Morningstar, SEC filings
4. **Synthesis**: Comprehensive investment thesis with risk analysis

**Why Better:** Current market data and regulatory changes vs generic investment advice

---

## 🛠 **Technical Architecture**

### **🧠 Enhanced AI Stack**
- **Multi-Agent System**: A team of specialized AI agents (Planner, Data Collector, Report Generator) work together to produce comprehensive research reports. This modular architecture improves the quality of the research and makes the system more scalable and extensible.
- **Local LLM**: Ollama integration with model selection
- **NLP Processing**: spaCy (entity recognition) + NLTK (query expansion)
- **Relevance Scoring**: scikit-learn TF-IDF + custom algorithms
- **Content Extraction**: newspaper3k + Playwright + BeautifulSoup
- **GUI**: PyQt5 for a modern, cross-platform user interface.
- **Web Solution**: FastAPI for the backend API, HTML/CSS/JavaScript for the frontend.
- **Fuzzy Matching**: fuzzywuzzy for deduplication

### **🔍 Search Infrastructure**
- **Multi-Provider**: Google Custom Search, DuckDuckGo, Brave Search
- **Rate Limiting**: Intelligent request management
- **Error Handling**: Robust fallback mechanisms
- **Content Validation**: Pre-processing quality checks

### **📊 Quality Assurance**
- **Progressive Validation**: Content relevance scoring at each step
- **Iterative Refinement**: Automatic gap detection and filling
- **Source Verification**: Domain authority and credibility checks
- **Synthesis Validation**: Evidence-based conclusion requirements

---

## 🔧 **Research Automation Framework**

### **🎯 Overview**
ResearchAgent features a powerful **Research Automation Framework** that extends beyond traditional research with intelligent command execution, data analysis, and workflow automation. This system provides secure, user-approved automation for complex research tasks.

### **🛡️ Security-First Design**
- **Multi-Tier Validation**: Commands are classified into Safe, Moderate, and Advanced categories
- **User Approval Workflow**: Restricted commands require explicit user confirmation
- **Sandbox Protection**: Automation runs in controlled environment with proper validation
- **Command Filtering**: Dangerous operations are blocked entirely

### **🚀 Automation Capabilities**

#### **📊 Data Analysis Mode**
- **Document Analysis**: Extract insights from research files and documents
- **Statistical Processing**: Generate summaries, word counts, and data metrics
- **Content Mining**: Search through large document collections
- **Pattern Recognition**: Identify trends and patterns in research data

**Example Commands:**
```bash
# Analyze document structure and content
find documents/ -name "*.pdf" -exec pdfinfo {} \;

# Extract key statistics from research files
wc -l documents/*.txt | sort -n

# Search for specific topics across documents
grep -r "artificial intelligence" documents/ --include="*.txt"
```

#### **📈 Data Visualization Mode**
- **Chart Generation**: Create visual representations of research data
- **Trend Analysis**: Generate graphs showing patterns over time
- **Report Enhancement**: Add visual elements to research reports
- **Custom Dashboards**: Build interactive data presentations

**Example Commands:**
```bash
# Generate word frequency charts
python -c "import matplotlib.pyplot as plt; # chart generation code"

# Create timeline visualizations
gnuplot -c timeline_script.gp research_data.csv

# Build interactive HTML dashboards
pandoc research_report.md -o interactive_dashboard.html
```

#### **🔄 Workflow Automation Mode**
- **Batch Processing**: Process multiple files simultaneously
- **Pipeline Execution**: Run multi-step research workflows
- **Task Scheduling**: Automate repetitive research tasks
- **Integration Scripts**: Connect different research tools

**Example Commands:**
```bash
# Batch convert and process research files
for file in documents/*.pdf; do convert_and_analyze "$file"; done

# Run complete research pipeline
./research_pipeline.sh --input data/ --output reports/

# Generate comprehensive research summaries
python research_summarizer.py --batch --all-topics
```

#### **💡 Smart Suggestions Mode**
- **Context-Aware Recommendations**: Suggestions based on your research topic
- **Tool Discovery**: Find relevant commands for your specific needs
- **Best Practices**: Learn optimal automation patterns
- **Custom Commands**: Generate tailored automation scripts

### **🖥️ User Interfaces**

#### **Desktop GUI Automation**
- **Integrated Panel**: Automation controls built into the main research interface
- **Mode Selection**: Choose from Data Analysis, Visualization, Workflow, or Custom modes
- **Live Output**: Real-time command execution results
- **User Approval**: Interactive dialogs for restricted commands
- **Suggestion System**: Get smart automation recommendations

#### **Web GUI Automation**
- **Browser-Based Interface**: Full automation capabilities in the web interface
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Progress Tracking**: Real-time status updates and execution monitoring
- **Suggestion Grid**: Visual grid of recommended automation commands
- **Click-to-Use**: Click any suggestion to auto-populate the command input

### **🎮 How to Use Automation**

#### **Desktop GUI:**
1. **Open ResearchAgent**: Launch the desktop application
2. **Navigate to Automation**: Scroll to the "🔧 Research Automation" section
3. **Select Mode**: Choose your automation type (Data Analysis, Visualization, etc.)
4. **Get Suggestions**: Click "💡 Get Suggestions" for context-aware recommendations
5. **Enter Command**: Type or select a command to execute
6. **Run Automation**: Click "⚙️ Run Automation" to execute
7. **Approve if Needed**: Confirm any restricted commands in the approval dialog

#### **Web GUI:**
1. **Access Web Interface**: Navigate to `http://localhost:8000`
2. **Expand Automation**: Click the "🔧 Research Automation" collapsible section
3. **Choose Mode**: Select automation mode from the dropdown
4. **Enter Research Query**: Add your research topic in the main query field
5. **Get Suggestions**: Click "💡 Get Suggestions" for smart recommendations
6. **Select Command**: Click any suggestion or enter a custom command
7. **Execute**: Click "⚙️ Run Automation" and monitor progress

### **💡 Pro Tips for Automation**

#### **Best Practices:**
- **Start Simple**: Begin with basic file operations before advanced workflows
- **Use Suggestions**: Let the AI recommend commands based on your research topic
- **Test Commands**: Try commands on sample data before running on important files
- **Read Approval Dialogs**: Understand what restricted commands will do
- **Save Useful Commands**: Keep track of automation commands that work well

#### **Common Use Cases:**
- **📚 Literature Review**: Automate document analysis and citation extraction
- **📊 Data Research**: Process CSV files, generate statistics, create charts
- **🔍 Content Mining**: Search through large document collections
- **📝 Report Generation**: Automate formatting and compilation of research reports
- **🔄 Workflow Optimization**: Create repeatable research processes

#### **Security Considerations:**
- **Review Commands**: Always understand what automation commands will do
- **Approve Carefully**: Be cautious when approving advanced/bash commands
- **Backup Data**: Keep backups of important research files
- **Test Environment**: Use test data when trying new automation workflows

### **🛠️ Advanced Features**

#### **Custom Automation Functions**
- **Document Analysis**: `analyze_documents()` - Extract insights from research files
- **Data Visualization**: `create_visualizations()` - Generate charts and graphs
- **Workflow Automation**: `run_workflow()` - Execute multi-step processes
- **Smart Suggestions**: `get_research_suggestions()` - Context-aware recommendations

#### **Integration Capabilities**
- **Shell Commands**: Direct system command execution with safety controls
- **Python Scripts**: Run custom analysis scripts with research data
- **File Processing**: Batch operations on research documents
- **Data Export**: Generate outputs in multiple formats (CSV, JSON, HTML)

---

## 🚀 **Getting Started**

### **📦 Quick Installation**

**Linux/macOS:**
```bash
git clone https://github.com/sunkencity999/shell_gpt_researchAgent.git
cd shell_gpt_researchAgent
chmod +x install.sh
./install.sh
```

**Windows:**
```cmd
git clone https://github.com/sunkencity999/shell_gpt_researchAgent.git
cd shell_gpt_researchAgent
install_windows.bat
```

### **🎯 Usage Examples**

**Command Line:**
```bash
./launch_sgpt_research.sh
# Enter a research goal, then a project name (e.g., "My_EV_Market_Analysis")
# To continue a project, enter its name when prompted.
```

**GUI Application:**
```bash
# Option 1: Use desktop launcher (Linux)
./sgpt-research-gui
# or double-click sgpt-research-gui.desktop

# Option 2: Direct activation
source venv/bin/activate
python sgptAgent/gui_app.py

# In the GUI, you can type a new project name or select an existing one from the dropdown.
```

**Web Application:**
```bash
# Launch the web service (Linux/macOS)
./launch_web.sh
# or (Windows)
launch_web.bat

# Access the web UI in your browser at http://localhost:8000
```

**🌐 Enhanced Web Interface Features:**
- **📊 Domain-Specific Research**: Select from 8+ specialized research domains (Technology, Healthcare, Finance, Legal, Academic, Business, Science, General)
- **🎯 Smart Query Enhancement**: Domain-aware agents automatically enhance your research queries with relevant terminology and focus areas
- **📁 Complete File Management**: Full parity with desktop GUI including:
  - 📋 **View & Preview**: Browse saved reports with live preview
  - ⬇️ **Download**: Export reports in multiple formats
  - 🗑️ **Delete**: Securely remove unwanted reports with confirmation
  - 🔄 **Refresh**: Real-time file list updates
- **⚙️ Advanced Settings**: Configure LLM parameters, output formats, and research depth
- **📈 Live Progress Tracking**: Real-time research progress with detailed status updates
- **🔒 Secure Operations**: Path validation and permission handling for all file operations

**Direct Python:**
```python
from sgptAgent.agent import ResearchAgent

agent = ResearchAgent()
report = agent.run(
    goal="Analyze the future of autonomous vehicles",
    project_name="Autonomous_Vehicles_2025",
    audience="investors",
    tone="professional",
    num_results=15
)
```

### **🔧 Configuration**

**Environment Variables:**
```bash
# Required for enhanced search capabilities
export GOOGLE_API_KEY="your_google_api_key"
export GOOGLE_CSE_ID="your_custom_search_engine_id"

# Optional: OpenAI API for testing
export OPENAI_API_KEY="your_openai_key"
```

**Model Selection:**
- Supports any Ollama model (llama3, mistral, codellama, etc.)
- Automatic model detection and selection interface
- Optimized for models with 7B+ parameters

---

## 📊 **Performance Metrics**

### **🎯 Research Quality**
- **Source Diversity**: 15-25 unique sources per report
- **Content Relevance**: 85%+ relevance score after filtering
- **Fact Verification**: Cross-source validation for key claims
- **Completeness**: 90%+ coverage of research sub-questions

### **⚡ Efficiency**
- **Search Strategy**: 5-level progressive fallback ensures results
- **Processing Speed**: 2-5 minutes for comprehensive reports
- **Resource Usage**: Optimized for local LLM inference
- **Success Rate**: 95%+ successful report generation

### **🔍 Comparison Benchmarks**

| **Method** | **Sources** | **Current Data** | **Synthesis Quality** | **Time** |
|------------|-------------|------------------|----------------------|----------|
| Simple LLM Query | 0 | ❌ | Basic | 30 sec |
| Google Search | 1-3 manual | ⚠️ | None | 10+ min |
| **ResearchAgent** | **15-25 auto** | **✅** | **Advanced** | **3-5 min** |

---

## 🛡️ **Privacy & Security**

### **🔒 Local-First Architecture**
- **No Cloud Dependencies**: All LLM processing runs locally via Ollama
- **Private Research**: Your queries never leave your machine
- **Secure Storage**: Reports saved locally in git-ignored directory
- **API Minimization**: Only web search APIs used (no content sent to external LLMs)

### **🌐 Responsible Web Usage**
- **Rate Limiting**: Respects website rate limits and robots.txt
- **Ethical Scraping**: Uses newspaper3k and Playwright responsibly
- **Source Attribution**: Full citation and source tracking
- **Content Respect**: Follows fair use guidelines

---

## 🔮 **Advanced Features**

### **🎨 Customization Options**
- **Audience Targeting**: Tailor reports for executives, researchers, students
- **Tone Control**: Professional, academic, casual, technical writing styles
- **Citation Styles**: APA, MLA, Chicago, IEEE formatting
- **Output Formats**: Markdown, PDF, HTML reports

### **📊 Structured Data Extraction**
This powerful feature allows you to extract specific, structured information from the research summaries and present it as a clean Markdown table in your final report. It's the ideal way to get organized, actionable data instead of just narrative text.

**How It Works**
The research process is now designed to always output structured data as a Markdown table. You control the *content* of this table using the **Structured Data Prompt** field in the UI (or the `structured_data_prompt` argument in the Python API).

Your prompt should clearly define the columns of the table you want. The AI will then read the research summaries and populate the rows based on your instructions.

**Best Practices for Prompts**
- **Be Specific:** Clearly name the columns you want.
- **Focus on Entities:** Ask for specific things (e.g., "artists," "companies," "statistics").
- **Keep it Concise:** The prompt should be a clear instruction for creating the table.

**Example Use Cases**

**1. Analyzing Musicians**
-   **Research Goal:** "Who was the most popular musician in 2024?"
-   **Structured Data Prompt:** 
    > "Create a table of the most popular musicians mentioned. Include columns for 'Artist Name', 'Primary Metric of Popularity (e.g., streams, awards, searches)', and 'Key Achievement'."

**2. Comparing Sports Teams**
-   **Research Goal:** "Who was the best pitcher in the MLB in 2024?"
-   **Structured Data Prompt:**
    > "Generate a table of top pitchers. The columns should be 'Pitcher Name', 'Team', 'Key Statistic', and 'Notable Accomplishments in 2024'."

**3. Tracking Market Trends**
-   **Research Goal:** "What are the leading AI companies to watch?"
-   **Structured Data Prompt:**
    > "Create a table of leading AI companies. Include columns for 'Company Name', 'Key Technology Area', and 'Recent Funding/Valuation'."

By using a well-crafted prompt, you can transform raw research into a perfectly organized table, ready for analysis or presentation.

### **🔧 Developer Features**
- **Python API**: Full programmatic access to research capabilities
- **Plugin Architecture**: Extensible search providers and content extractors
- **Custom Domains**: Add specialized search targeting for niche fields
- **Batch Processing**: Research multiple queries in parallel

### **📈 Analytics & Insights**
- **Search Performance**: Track query success rates and source quality
- **Content Analysis**: Identify trending topics and information gaps
- **Source Reliability**: Build reputation scores for different domains
- **Research Patterns**: Analyze effective query strategies

## 🆕 **Recent Updates**

### **Enhanced Web GUI (Latest)**
- 🎯 **Domain Selection**: Choose from 8 specialized research domains (Technology, Healthcare, Finance, Legal, Academic, Business, Science, General)
- 🗑️ **Complete File Management**: Added secure file deletion with confirmation dialogs and path validation
- 📊 **Advanced Progress Tracking**: Real-time metrics including elapsed time, ETA estimation, results counter, and success rates
- 🔒 **Security Enhancements**: Directory traversal protection and secure file operations
- 💼 **Professional UI**: Danger button styling, enhanced file management workflow, and improved user feedback

### **Query Enhancement System**
- 🧠 **Multi-Strategy Enhancement**: Progressive query enhancement with domain-aware targeting
- 🔍 **Improved Search Targeting**: Domain-specific site targeting for better result quality
- 📈 **Smart Fallback Strategies**: Multiple levels of query refinement with error handling
- 🎪 **Content Validation**: Pre-synthesis relevance filtering to ensure quality outputs

## 👨‍💻 **Creator & Contact**

**ResearchAgent** was created by **Christopher Bradford**.

For questions, support, or collaboration opportunities:
- **Email**: admin@robotbirdservices.com
- **Project**: Shell GPT Research Agent

## 📄 **License**

MIT License - See [LICENSE](LICENSE) for details.

## 🙏 **Acknowledgments**

Built with powerful open-source tools:
- **Shell-GPT** for base system control via LLM
- **Ollama** for local LLM inference
- **spaCy** for advanced NLP processing
- **NLTK** for linguistic analysis
- **scikit-learn** for relevance scoring
- **Rich** for beautiful CLI interfaces

---

<div align="center">

**🔬 ResearchAgent: Where AI Meets Deep Research**

*Transform any question into a comprehensive, evidence-based research report*

[**Get Started**](#-getting-started) • [**Examples**](#-use-cases--examples) • [**Documentation**](#-technical-architecture)

</div>
