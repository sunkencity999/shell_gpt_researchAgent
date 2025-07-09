document.addEventListener('DOMContentLoaded', () => {
    const queryInput = document.getElementById('query-input');
    const audienceInput = document.getElementById('audience-input');
    const toneInput = document.getElementById('tone-input');
    const improvementInput = document.getElementById('improvement-input');
    const projectNameSelect = document.getElementById('project-name-select');
    const newProjectRow = document.getElementById('new-project-row');
    const newProjectNameInput = document.getElementById('new-project-name-input');
    const modelSelect = document.getElementById('model-select');
    const resultsSpin = document.getElementById('results-spin');
    const localDocsPathInput = document.getElementById('local-docs-path-input');
    const useLocalDocsCheckbox = document.getElementById('use-local-docs-checkbox');
    const localDocsPathContainer = document.getElementById('local-docs-path-container');
    const tempSpin = document.getElementById('temp-spin');
    const maxTokensSpin = document.getElementById('max-tokens-spin');
    const systemPromptInput = document.getElementById('system-prompt-input');
    const ctxWindowSpin = document.getElementById('ctx-window-spin');
    const fileInput = document.getElementById('file-input');
    const citationSelect = document.getElementById('citation-select');
    const clearBtn = document.getElementById('clear-btn');
    const runBtn = document.getElementById('run-btn');
    const outputBox = document.getElementById('output-box');
    const progressLabel = document.getElementById('progress-label');
    const progressSubstep = document.getElementById('progress-substep');
    const progressBarFill = document.getElementById('progress-bar-fill');
    const progressBarText = document.getElementById('progress-bar-text');
    const timeLabel = document.getElementById('time-label');
    const etaLabel = document.getElementById('eta-label');
    const resultsLabel = document.getElementById('results-label');
    const successLabel = document.getElementById('success-label');
    const progressLog = document.getElementById('progress-log');
    const reportFilter = document.getElementById('report-filter');
    const reportList = document.getElementById('report-list');
    const openReportBtn = document.getElementById('open-report-btn');
    const downloadReportBtn = document.getElementById('download-report-btn');
    const refreshReportsBtn = document.getElementById('refresh-reports-btn');
    const reportPreview = document.getElementById('report-preview');
    const collapsibleHeader = document.querySelector('.collapsible-header');
    const collapsibleContent = document.querySelector('.collapsible-content');

    let researchTaskId = null;
    let progressInterval = null;
    let startTime = null;

    // Collapsible section logic
    if (collapsibleHeader) {
        collapsibleHeader.addEventListener('click', () => {
            collapsibleContent.classList.toggle('expanded');
            collapsibleHeader.classList.toggle('expanded');
        });
    }

    // Fetch models on load
    const fetchModels = async () => {
        try {
            const response = await fetch('/api/models');
            const data = await response.json();
            modelSelect.innerHTML = '';
            data.models.forEach(model => {
                const option = document.createElement('option');
                option.value = model;
                option.textContent = model;
                modelSelect.appendChild(option);
            });
        } catch (error) {
            console.error('Error fetching models:', error);
            alert('Failed to load models. Please check the server.');
        }
    };

    const fetchProjects = async () => {
        try {
            const response = await fetch('/api/projects');
            const data = await response.json();
            // Clear existing options except the first "None" option
            const selectedValue = projectNameSelect.value;
            projectNameSelect.innerHTML = '<option value="">None</option><option value="__new__">Add New Project...</option>';
            data.projects.forEach(project => {
                const option = document.createElement('option');
                option.value = project;
                option.textContent = project;
                projectNameSelect.appendChild(option);
            });
            projectNameSelect.value = selectedValue;
        } catch (error) {
            console.error('Error fetching projects:', error);
        }
    };

    projectNameSelect.addEventListener('change', () => {
        if (projectNameSelect.value === '__new__') {
            newProjectRow.style.display = 'flex';
        } else {
            newProjectRow.style.display = 'none';
        }
    });

    // Clear fields
    clearBtn.addEventListener('click', () => {
        queryInput.value = '';
        audienceInput.value = '';
        toneInput.value = '';
        improvementInput.value = '';
        projectNameSelect.value = '';
        newProjectRow.style.display = 'none';
        newProjectNameInput.value = '';
        resultsSpin.value = 10;
        useLocalDocsCheckbox.checked = false;
        localDocsPathContainer.style.display = 'none';
        localDocsPathInput.disabled = true;
        tempSpin.value = 0.7;
        maxTokensSpin.value = 2048;
        systemPromptInput.value = '';
        ctxWindowSpin.value = 2048;
        fileInput.value = 'research_report.txt';
        citationSelect.value = 'APA';
        outputBox.value = '';
        progressLabel.textContent = '';
        progressSubstep.textContent = '';
        progressBarFill.style.width = '0%';
        progressBarText.textContent = '0%';
        timeLabel.textContent = '⏱️ Elapsed: 0:00';
        etaLabel.textContent = '🎯 ETA: --:--';
        resultsLabel.textContent = '📊 Results: 0';
        successLabel.textContent = '✅ Success: 0%';
        progressLog.innerHTML = '';
        runBtn.disabled = false;
        if (progressInterval) {
            clearInterval(progressInterval);
            progressInterval = null;
        }
        startTime = null;
    });

    useLocalDocsCheckbox.addEventListener('change', () => {
        if (useLocalDocsCheckbox.checked) {
            localDocsPathContainer.style.display = 'flex';
            localDocsPathInput.disabled = false;
        } else {
            localDocsPathContainer.style.display = 'none';
            localDocsPathInput.disabled = true;
        }
    });

    const analyzeImagesBtn = document.getElementById('analyze-images-btn');

    analyzeImagesBtn.addEventListener('click', async () => {
        const url = prompt("Enter the URL of the page to analyze for images:");
        if (!url) return;

        runBtn.disabled = true;
        outputBox.value = '';
        progressLog.innerHTML = '';
        progressLabel.textContent = 'Analyzing images...';
        progressSubstep.textContent = '';
        progressBarFill.style.width = '0%';
        progressBarText.textContent = '0%';
        timeLabel.textContent = '⏱️ Elapsed: 0:00';
        etaLabel.textContent = '🎯 ETA: Calculating...';
        resultsLabel.textContent = '📊 Results: 0';
        successLabel.textContent = '✅ Success: 0%';

        const researchData = {
            query: url, // Using query to pass the URL
            mode: 'vision',
            project_name: projectNameSelect.value || 'vision_analysis',
            documents_base_dir: '{{ documents_dir }}'
        };

        try {
            const response = await fetch('/api/research', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(researchData)
            });
            const data = await response.json();
            if (data.task_id) {
                researchTaskId = data.task_id;
                startTime = new Date();
                progressInterval = setInterval(pollResearchStatus, 1000);
            } else {
                alert('Failed to start image analysis.');
                runBtn.disabled = false;
            }
        } catch (error) {
            console.error('Error starting image analysis:', error);
            alert('An error occurred while starting image analysis.');
            runBtn.disabled = false;
        }
    });

    // Start research
    runBtn.addEventListener('click', async () => {
        const query = queryInput.value.trim();
        if (!query) {
            alert('Please enter a research query.');
            return;
        }

        runBtn.disabled = true;
        outputBox.value = '';
        progressLog.innerHTML = '';
        progressLabel.textContent = 'Initializing research...';
        progressSubstep.textContent = '';
        progressBarFill.style.width = '0%';
        progressBarText.textContent = '0%';
        timeLabel.textContent = '⏱️ Elapsed: 0:00';
        etaLabel.textContent = '🎯 ETA: Calculating...';
        resultsLabel.textContent = '📊 Results: 0';
        successLabel.textContent = '✅ Success: 0%';

        let projectName = projectNameSelect.value;
        if (projectName === '__new__') {
            projectName = newProjectNameInput.value.trim();
            if (!projectName) {
                alert('Please enter a new project name.');
                runBtn.disabled = false;
                return;
            }
        }

        const researchData = {
            query: query,
            audience: audienceInput.value.trim(),
            tone: toneInput.value.trim(),
            improvement: improvementInput.value.trim(),
            project_name: projectName || null,
            model: modelSelect.value,
            num_results: parseInt(resultsSpin.value),
            temperature: parseFloat(tempSpin.value),
            max_tokens: parseInt(maxTokensSpin.value),
            system_prompt: systemPromptInput.value.trim(),
            ctx_window: parseInt(ctxWindowSpin.value),
            citation_style: citationSelect.value,
            filename: fileInput.value.trim() || 'research_report.txt',
            local_docs_path: useLocalDocsCheckbox.checked ? localDocsPathInput.value.trim() : null
        };

        try {
            const response = await fetch('/api/research', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(researchData)
            });
            const data = await response.json();
            if (data.task_id) {
                researchTaskId = data.task_id;
                startTime = new Date();
                progressInterval = setInterval(pollResearchStatus, 1000);
            } else {
                alert('Failed to start research.');
                runBtn.disabled = false;
            }
        } catch (error) {
            console.error('Error starting research:', error);
            alert('An error occurred while starting research.');
            runBtn.disabled = false;
        }
    });

    // Poll research status
    const pollResearchStatus = async () => {
        if (!researchTaskId) return;

        try {
            const response = await fetch(`/api/research/status/${researchTaskId}`);
            const data = await response.json();

            progressLabel.textContent = data.log.length > 0 ? data.log[data.log.length - 1].desc || '' : '';
            progressSubstep.textContent = data.log.length > 0 ? data.log[data.log.length - 1].substep || '' : '';
            progressBarFill.style.width = `${data.progress}%`;
            progressBarText.textContent = `${data.progress}%`;

            // Update log
            const currentLogContent = progressLog.innerHTML;
            data.log.forEach(logEntry => {
                const logLine = `<p><strong>${new Date(logEntry.timestamp).toLocaleTimeString()}</strong>: ${logEntry.log || logEntry.desc}</p>`;
                if (!currentLogContent.includes(logLine)) { // Avoid duplicate log entries
                    progressLog.innerHTML += logLine;
                    progressLog.scrollTop = progressLog.scrollHeight; // Scroll to bottom
                }
            });

            // Update metrics
            if (startTime) {
                const elapsedSeconds = (new Date() - startTime) / 1000;
                const minutes = Math.floor(elapsedSeconds / 60);
                const seconds = Math.floor(elapsedSeconds % 60).toString().padStart(2, '0');
                timeLabel.textContent = `⏱️ Elapsed: ${minutes}:${seconds}`;

                if (data.progress > 0 && data.progress < 100) {
                    const estimatedTotalSeconds = (elapsedSeconds / data.progress) * 100;
                    const remainingSeconds = estimatedTotalSeconds - elapsedSeconds;
                    const etaMinutes = Math.floor(remainingSeconds / 60);
                    const etaSeconds = Math.floor(remainingSeconds % 60).toString().padStart(2, '0');
                    etaLabel.textContent = `🎯 ETA: ${etaMinutes}:${etaSeconds}`;
                } else if (data.progress === 100) {
                    etaLabel.textContent = '🎯 Completed!';
                }
            }

            // Placeholder for actual results/success metrics from backend
            // You'd need to add these to your FastAPI response for /api/research/status/{task_id}
            resultsLabel.textContent = `📊 Results: ${data.total_results_found || 0}`;
            successLabel.textContent = `✅ Success: ${data.successful_queries && data.total_queries ? ((data.successful_queries / data.total_queries) * 100).toFixed(0) : 0}%`;

            if (data.status === 'completed') {
                clearInterval(progressInterval);
                progressInterval = null;
                outputBox.value = data.result || 'Research completed.';
                progressLabel.textContent = '✅ Research completed successfully!';
                runBtn.disabled = false;
                fetchReports(); // Refresh report list
            } else if (data.status === 'failed') {
                clearInterval(progressInterval);
                progressInterval = null;
                outputBox.value = `Research failed: ${data.error || 'Unknown error.'}\n\nLog:\n${data.log.map(entry => entry.log || entry.desc).join('\n')}`;
                progressLabel.textContent = '❌ Research failed';
                runBtn.disabled = false;
            }
        } catch (error) {
            console.error('Error polling research status:', error);
            clearInterval(progressInterval);
            progressInterval = null;
            runBtn.disabled = false;
            alert('An error occurred while fetching research status.');
        }
    };

    // Fetch and display reports
    const fetchReports = async (path = '.') => {
        try {
            const response = await fetch(`/api/reports?path=${encodeURIComponent(path)}`);
            const data = await response.json();
            reportList.innerHTML = '';

            // Add a ".." (go back) item if not in the root directory
            if (path !== '.') {
                const parentPath = path.substring(0, path.lastIndexOf('/') || '.');
                const li = document.createElement('li');
                li.textContent = '../';
                li.dataset.path = parentPath;
                li.dataset.type = 'folder';
                li.classList.add('folder');
                li.addEventListener('click', () => fetchReports(parentPath));
                reportList.appendChild(li);
            }

            data.reports.forEach(report => {
                const li = document.createElement('li');
                li.textContent = report.name;
                li.dataset.path = report.path;
                li.dataset.type = report.type;

                if (report.type === 'folder') {
                    li.classList.add('folder');
                    li.addEventListener('click', () => fetchReports(report.path));
                } else {
                    li.classList.add('file');
                    li.addEventListener('click', () => {
                        Array.from(reportList.children).forEach(item => item.classList.remove('selected'));
                        li.classList.add('selected');
                        loadReportPreview(report.path);
                    });
                }
                reportList.appendChild(li);
            });
        } catch (error) {
            console.error('Error fetching reports:', error);
        }
    };

    const loadReportPreview = async (reportPath) => {
        try {
            const encodedPath = encodeURIComponent(reportPath);
            const response = await fetch(`/api/reports/${encodedPath}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const htmlContent = await response.text();
            reportPreview.srcdoc = htmlContent;
        } catch (error) {
            console.error('Error loading report preview:', error);
            reportPreview.srcdoc = `[Error loading report: ${error.message}]`;
        }
    };

    // Filter reports
    reportFilter.addEventListener('keyup', () => {
        const filterText = reportFilter.value.toLowerCase();
        Array.from(reportList.children).forEach(item => {
            const text = item.textContent.toLowerCase();
            item.style.display = text.includes(filterText) ? 'block' : 'none';
        });
    });

    // Open selected report in main output
    openReportBtn.addEventListener('click', async () => {
        const selectedItem = reportList.querySelector('li.selected');
        if (selectedItem) {
            const reportPath = selectedItem.dataset.path;
            try {
                const encodedPath = encodeURIComponent(reportPath);
                const response = await fetch(`/api/reports/${encodedPath}`);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const htmlContent = await response.text();
                // This will put the HTML content directly into the textarea.
                // If you want to display rendered HTML, you'd need a different element (e.g., a div) and innerHTML.
                outputBox.value = htmlContent.replace(/<[^>]*>?/gm, ''); // Strip HTML tags for textarea
            } catch (error) {
                console.error('Error opening report:', error);
                alert(`Could not open report: ${error.message}`);
            }
        } else {
            alert('Please select a report to open.');
        }
    });

    downloadReportBtn.addEventListener('click', () => {
        const selectedItem = reportList.querySelector('li.selected');
        if (selectedItem) {
            const reportPath = selectedItem.dataset.path;
            const encodedPath = encodeURIComponent(reportPath);
            window.location.href = `/api/download/${encodedPath}`;
        } else {
            alert('Please select a report to download.');
        }
    });

    // Initial fetches
    fetchModels();
    fetchProjects();
    fetchReports();
});