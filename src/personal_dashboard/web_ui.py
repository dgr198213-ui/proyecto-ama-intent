"""
Web Dashboard for Personal Development Tools
Simple FastAPI-based interface
"""

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json
from pathlib import Path
from datetime import datetime

app = FastAPI(title="AMA-Intent Personal Dashboard")

# Mount static files
static_dir = Path("static")
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Templates
templates_dir = Path("templates")
templates_dir.mkdir(exist_ok=True)
templates = Jinja2Templates(directory=templates_dir)

# Data directory
data_dir = Path("data/personal")
data_dir.mkdir(parents=True, exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Main dashboard page"""
    # Load overview data
    overview = {
        "projects": [],
        "code_analyses": [],
        "content_ideas": [],
        "last_updated": datetime.now().isoformat()
    }
    
    # Try to load existing data
    projects_file = data_dir / "projects.json"
    if projects_file.exists():
        with open(projects_file, 'r') as f:
            overview["projects"] = json.load(f)
    
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "overview": overview}
    )

@app.get("/api/overview")
async def get_overview():
    """API endpoint for dashboard overview"""
    overview = {
        "total_projects": 0,
        "active_projects": 0,
        "recent_activity": [],
        "quick_stats": {},
        "timestamp": datetime.now().isoformat()
    }
    
    # Load and calculate stats
    projects_file = data_dir / "projects.json"
    if projects_file.exists():
        with open(projects_file, 'r') as f:
            projects = json.load(f)
            overview["total_projects"] = len(projects)
            overview["active_projects"] = len([p for p in projects if p.get("status") != "completed"])
    
    return JSONResponse(overview)

@app.get("/debug", response_class=HTMLResponse)
async def debug_assistant(request: Request):
    """Debug assistant interface"""
    return templates.TemplateResponse("debug.html", {"request": request})

@app.post("/api/debug/analyze")
async def analyze_error(error_traceback: str = Form(...), code_snippet: str = Form("")):
    """API endpoint for error analysis"""
    # This would integrate with the DebugAssistant class
    analysis_result = {
        "error_type": "Example Error",
        "solutions": [
            "Check the syntax on line 42",
            "Verify variable names are correct",
            "Ensure all required modules are imported"
        ],
        "confidence": 0.85,
        "timestamp": datetime.now().isoformat()
    }
    
    return JSONResponse(analysis_result)

@app.get("/projects", response_class=HTMLResponse)
async def projects_view(request: Request):
    """Projects management interface"""
    projects = []
    projects_file = data_dir / "projects.json"
    if projects_file.exists():
        with open(projects_file, 'r') as f:
            projects = json.load(f)
    
    return templates.TemplateResponse("projects.html", {
        "request": request,
        "projects": projects
    })

@app.get("/content", response_class=HTMLResponse)
async def content_creator(request: Request):
    """Content creator interface"""
    return templates.TemplateResponse("content.html", {"request": request})

# Create basic HTML templates
templates_dir.mkdir(exist_ok=True)

# Main dashboard template
dashboard_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AMA-Intent Personal Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body class="bg-gray-50 text-gray-800">
    <div class="min-h-screen">
        <!-- Header -->
        <header class="bg-white shadow-sm border-b">
            <div class="container mx-auto px-4 py-4">
                <div class="flex justify-between items-center">
                    <div class="flex items-center space-x-3">
                        <div class="bg-blue-100 p-2 rounded-lg">
                            <i class="fas fa-brain text-blue-600 text-xl"></i>
                        </div>
                        <div>
                            <h1 class="text-2xl font-bold text-gray-900">AMA-Intent Personal Dashboard</h1>
                            <p class="text-gray-600 text-sm">Your AI-powered development companion</p>
                        </div>
                    </div>
                    <div class="text-sm text-gray-500">
                        Last updated: <span id="last-updated">{{ overview.last_updated[:16] }}</span>
                    </div>
                </div>
            </div>
        </header>

        <!-- Main Content -->
        <main class="container mx-auto px-4 py-8">
            <!-- Stats Overview -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div class="bg-white rounded-xl shadow p-6">
                    <div class="flex items-center justify-between">
                        <div>
                            <p class="text-gray-500 text-sm">Projects</p>
                            <p class="text-3xl font-bold text-gray-900" id="project-count">{{ overview.projects|length }}</p>
                        </div>
                        <div class="bg-blue-100 p-3 rounded-full">
                            <i class="fas fa-project-diagram text-blue-600 text-xl"></i>
                        </div>
                    </div>
                    <div class="mt-4">
                        <a href="/projects" class="text-blue-600 hover:text-blue-800 text-sm font-medium">
                            Manage Projects →
                        </a>
                    </div>
                </div>

                <div class="bg-white rounded-xl shadow p-6">
                    <div class="flex items-center justify-between">
                        <div>
                            <p class="text-gray-500 text-sm">Debug Assistant</p>
                            <p class="text-3xl font-bold text-gray-900">Ready</p>
                        </div>
                        <div class="bg-green-100 p-3 rounded-full">
                            <i class="fas fa-bug text-green-600 text-xl"></i>
                        </div>
                    </div>
                    <div class="mt-4">
                        <a href="/debug" class="text-blue-600 hover:text-blue-800 text-sm font-medium">
                            Debug Code →
                        </a>
                    </div>
                </div>

                <div class="bg-white rounded-xl shadow p-6">
                    <div class="flex items-center justify-between">
                        <div>
                            <p class="text-gray-500 text-sm">Content Creator</p>
                            <p class="text-3xl font-bold text-gray-900">Ready</p>
                        </div>
                        <div class="bg-purple-100 p-3 rounded-full">
                            <i class="fas fa-pen-nib text-purple-600 text-xl"></i>
                        </div>
                    </div>
                    <div class="mt-4">
                        <a href="/content" class="text-blue-600 hover:text-blue-800 text-sm font-medium">
                            Create Content →
                        </a>
                    </div>
                </div>
            </div>

            <!-- Quick Actions -->
            <div class="mb-8">
                <h2 class="text-xl font-bold text-gray-900 mb-4">Quick Actions</h2>
                <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <a href="/debug" class="bg-white rounded-lg shadow p-4 hover:shadow-md transition-shadow text-center">
                        <i class="fas fa-search text-blue-500 text-2xl mb-2"></i>
                        <p class="font-medium">Debug Code</p>
                    </a>
                    <a href="/projects?action=new" class="bg-white rounded-lg shadow p-4 hover:shadow-md transition-shadow text-center">
                        <i class="fas fa-plus text-green-500 text-2xl mb-2"></i>
                        <p class="font-medium">New Project</p>
                    </a>
                    <a href="/content" class="bg-white rounded-lg shadow p-4 hover:shadow-md transition-shadow text-center">
                        <i class="fas fa-edit text-purple-500 text-2xl mb-2"></i>
                        <p class="font-medium">Write Blog Post</p>
                    </a>
                    <a href="#" onclick="runCodeAnalysis()" class="bg-white rounded-lg shadow p-4 hover:shadow-md transition-shadow text-center">
                        <i class="fas fa-code text-orange-500 text-2xl mb-2"></i>
                        <p class="font-medium">Analyze Code</p>
                    </a>
                </div>
            </div>

            <!-- Recent Activity -->
            <div class="bg-white rounded-xl shadow p-6">
                <div class="flex justify-between items-center mb-4">
                    <h2 class="text-xl font-bold text-gray-900">Recent Activity</h2>
                    <button onclick="refreshData()" class="text-blue-600 hover:text-blue-800">
                        <i class="fas fa-sync-alt"></i> Refresh
                    </button>
                </div>
                <div id="recent-activity" class="text-gray-600">
                    <p class="text-center py-8">No recent activity. Start by creating a project or debugging some code!</p>
                </div>
            </div>
        </main>

        <!-- Footer -->
        <footer class="bg-white border-t mt-12">
            <div class="container mx-auto px-4 py-6">
                <div class="flex justify-between items-center">
                    <div class="text-gray-600 text-sm">
                        AMA-Intent v2.0 • Personal Edition
                    </div>
                    <div class="text-gray-600 text-sm">
                        <a href="#" class="hover:text-blue-600 mr-4">GitHub</a>
                        <a href="#" class="hover:text-blue-600">Documentation</a>
                    </div>
                </div>
            </div>
        </footer>
    </div>

    <script>
        async function refreshData() {
            const response = await fetch('/api/overview');
            const data = await response.json();
            
            // Update project count
            document.getElementById('project-count').textContent = data.total_projects;
            
            // Update last updated
            const now = new Date().toISOString().slice(0, 16).replace('T', ' ');
            document.getElementById('last-updated').textContent = now;
            
            // Show notification
            showNotification('Data refreshed successfully');
        }
        
        async function runCodeAnalysis() {
            showNotification('Opening code analysis tool...');
            // This would open a modal or navigate to debug page
            window.location.href = '/debug';
        }
        
        function showNotification(message) {
            // Simple notification
            alert(message); // Replace with better notification system
        }
        
        // Refresh data on page load
        document.addEventListener('DOMContentLoaded', refreshData);
    </script>
</body>
</html>
'''

# Save the template
(templates_dir / "dashboard.html").write_text(dashboard_html)

# Debug assistant template
debug_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Debug Assistant - AMA-Intent</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body class="bg-gray-50 text-gray-800">
    <div class="min-h-screen">
        <!-- Header -->
        <header class="bg-white shadow-sm border-b">
            <div class="container mx-auto px-4 py-4">
                <div class="flex justify-between items-center">
                    <div class="flex items-center space-x-3">
                        <a href="/" class="text-blue-600 hover:text-blue-800">
                            <i class="fas fa-arrow-left"></i>
                        </a>
                        <div class="bg-red-100 p-2 rounded-lg">
                            <i class="fas fa-bug text-red-600 text-xl"></i>
                        </div>
                        <div>
                            <h1 class="text-2xl font-bold text-gray-900">Debug Assistant</h1>
                            <p class="text-gray-600 text-sm">Analyze and fix code errors</p>
                        </div>
                    </div>
                </div>
            </div>
        </header>

        <!-- Main Content -->
        <main class="container mx-auto px-4 py-8">
            <div class="max-w-4xl mx-auto">
                <!-- Error Input -->
                <div class="bg-white rounded-xl shadow p-6 mb-6">
                    <h2 class="text-xl font-bold text-gray-900 mb-4">Paste Error or Code</h2>
                    <form id="debug-form" method="POST" action="/api/debug/analyze">
                        <div class="mb-4">
                            <label class="block text-gray-700 text-sm font-medium mb-2">
                                Error Traceback (Python/JavaScript)
                            </label>
                            <textarea 
                                id="error-traceback" 
                                name="error_traceback"
                                rows="8"
                                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
                                placeholder="Paste your error traceback here..."
                            ></textarea>
                        </div>
                        
                        <div class="mb-6">
                            <label class="block text-gray-700 text-sm font-medium mb-2">
                                Related Code (Optional)
                            </label>
                            <textarea 
                                id="code-snippet" 
                                name="code_snippet"
                                rows="6"
                                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
                                placeholder="Paste related code for better analysis..."
                            ></textarea>
                        </div>
                        
                        <div class="flex justify-between">
                            <button
                                type="button"
                                onclick="analyzeError()"
                                class="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-6 rounded-lg transition-colors"
                            >
                                <i class="fas fa-search mr-2"></i> Analyze Error
                            </button>
                            
                            <button
                                type="button"
                                onclick="clearForm()"
                                class="bg-gray-200 hover:bg-gray-300 text-gray-800 font-medium py-2 px-6 rounded-lg transition-colors"
                            >
                                Clear
                            </button>
                        </div>
                    </form>
                </div>

                <!-- Results -->
                <div id="results" class="hidden bg-white rounded-xl shadow p-6">
                    <h2 class="text-xl font-bold text-gray-900 mb-4">Analysis Results</h2>
                    <div id="results-content">
                        <!-- Results will be displayed here -->
                    </div>
                </div>

                <!-- Examples -->
                <div class="bg-white rounded-xl shadow p-6 mt-6">
                    <h2 class="text-xl font-bold text-gray-900 mb-4">Example Errors</h2>
                    <div class="space-y-4">
                        <div class="border-l-4 border-blue-500 pl-4 py-2">
                            <p class="font-medium text-gray-900">ModuleNotFoundError</p>
                            <p class="text-gray-600 text-sm font-mono mt-1">
                                ModuleNotFoundError: No module named 'requests'
                            </p>
                            <button onclick="loadExample(1)" class="text-blue-600 text-sm mt-2 hover:text-blue-800">
                                Try this example
                            </button>
                        </div>
                        
                        <div class="border-l-4 border-red-500 pl-4 py-2">
                            <p class="font-medium text-gray-900">SyntaxError</p>
                            <p class="text-gray-600 text-sm font-mono mt-1">
                                SyntaxError: invalid syntax (test.py, line 3)
                            </p>
                            <button onclick="loadExample(2)" class="text-blue-600 text-sm mt-2 hover:text-blue-800">
                                Try this example
                            </button>
                        </div>
                        
                        <div class="border-l-4 border-yellow-500 pl-4 py-2">
                            <p class="font-medium text-gray-900">TypeError</p>
                            <p class="text-gray-600 text-sm font-mono mt-1">
                                TypeError: can only concatenate str (not "int") to str
                            </p>
                            <button onclick="loadExample(3)" class="text-blue-600 text-sm mt-2 hover:text-blue-800">
                                Try this example
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </main>
    </div>

    <script>
        const examples = {
            1: "ModuleNotFoundError: No module named 'requests'\nTraceback (most recent call last):\n  File \"test.py\", line 1, in <module>\n    import requests\nModuleNotFoundError: No module named 'requests'",
            2: "File \"test.py\", line 3\n    print('Hello World'\n         ^\nSyntaxError: invalid syntax",
            3: "Traceback (most recent call last):\n  File \"test.py\", line 2, in <module>\n    result = 'Number: ' + 42\nTypeError: can only concatenate str (not \"int\") to str"
        };
        
        function loadExample(exampleId) {
            document.getElementById('error-traceback').value = examples[exampleId] || '';
            document.getElementById('code-snippet').value = '';
        }
        
        function clearForm() {
            document.getElementById('error-traceback').value = '';
            document.getElementById('code-snippet').value = '';
            document.getElementById('results').classList.add('hidden');
        }
        
        async function analyzeError() {
            const errorText = document.getElementById('error-traceback').value;
            const codeText = document.getElementById('code-snippet').value;
            
            if (!errorText.trim()) {
                alert('Please paste an error traceback to analyze');
                return;
            }
            
            // Show loading
            document.getElementById('results').classList.remove('hidden');
            document.getElementById('results-content').innerHTML = `
                <div class="text-center py-8">
                    <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                    <p class="mt-4 text-gray-600">Analyzing error...</p>
                </div>
            `;
            
            try {
                const formData = new FormData();
                formData.append('error_traceback', errorText);
                formData.append('code_snippet', codeText);
                
                const response = await fetch('/api/debug/analyze', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                // Display results
                let resultsHTML = `
                    <div class="mb-6 p-4 bg-blue-50 rounded-lg">
                        <div class="flex items-center">
                            <div class="bg-blue-100 p-2 rounded-full mr-3">
                                <i class="fas fa-info-circle text-blue-600"></i>
                            </div>
                            <div>
                                <p class="font-medium text-gray-900">${result.error_type}</p>
                                <p class="text-gray-600 text-sm">Confidence: ${(result.confidence * 100).toFixed(1)}%</p>
                            </div>
                        </div>
                    </div>
                    
                    <h3 class="text-lg font-bold text-gray-900 mb-3">Suggested Solutions</h3>
                    <div class="space-y-3 mb-6">
                `;
                
                result.solutions.forEach((solution, index) => {
                    resultsHTML += `
                        <div class="flex items-start">
                            <div class="bg-green-100 text-green-800 text-xs font-medium px-2 py-1 rounded mr-3 mt-1">${index + 1}</div>
                            <p class="text-gray-700">${solution}</p>
                        </div>
                    `;
                });
                
                resultsHTML += `
                    </div>
                    
                    <div class="border-t pt-4">
                        <h3 class="text-lg font-bold text-gray-900 mb-3">Quick Fix</h3>
                        <div class="bg-gray-50 p-4 rounded-lg font-mono text-sm">
                            ${result.quick_fix || 'No quick fix available'}
                        </div>
                    </div>
                `;
                
                document.getElementById('results-content').innerHTML = resultsHTML;
                
            } catch (error) {
                document.getElementById('results-content').innerHTML = `
                    <div class="bg-red-50 border border-red-200 rounded-lg p-4">
                        <div class="flex items-center">
                            <div class="bg-red-100 p-2 rounded-full mr-3">
                                <i class="fas fa-exclamation-triangle text-red-600"></i>
                            </div>
                            <div>
                                <p class="font-medium text-red-800">Analysis Failed</p>
                                <p class="text-red-600 text-sm">${error.message}</p>
                            </div>
                        </div>
                    </div>
                `;
            }
        }
    </script>
</body>
</html>
'''

# Save debug template
(templates_dir / "debug.html").write_text(debug_html)

# Simple projects template
projects_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Projects - AMA-Intent</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body class="bg-gray-50 text-gray-800">
    <div class="min-h-screen">
        <header class="bg-white shadow-sm border-b">
            <div class="container mx-auto px-4 py-4">
                <div class="flex justify-between items-center">
                    <div class="flex items-center space-x-3">
                        <a href="/" class="text-blue-600 hover:text-blue-800">
                            <i class="fas fa-arrow-left"></i>
                        </a>
                        <div class="bg-green-100 p-2 rounded-lg">
                            <i class="fas fa-project-diagram text-green-600 text-xl"></i>
                        </div>
                        <div>
                            <h1 class="text-2xl font-bold text-gray-900">Project Manager</h1>
                            <p class="text-gray-600 text-sm">Manage your personal projects</p>
                        </div>
                    </div>
                    <a href="/projects?action=new" class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium">
                        <i class="fas fa-plus mr-2"></i> New Project
                    </a>
                </div>
            </div>
        </header>

        <main class="container mx-auto px-4 py-8">
            <div class="mb-6">
                <div class="flex justify-between items-center mb-4">
                    <h2 class="text-xl font-bold text-gray-900">Your Projects</h2>
                    <div class="text-gray-600 text-sm">
                        {{ projects|length }} project(s)
                    </div>
                </div>
                
                {% if projects %}
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {% for project in projects %}
                    <div class="bg-white rounded-xl shadow p-6 hover:shadow-lg transition-shadow">
                        <div class="flex justify-between items-start mb-4">
                            <div>
                                <h3 class="font-bold text-gray-900 text-lg">{{ project.name }}</h3>
                                <span class="text-sm px-2 py-1 rounded-full 
                                    {% if project.status == 'completed' %}bg-green-100 text-green-800
                                    {% elif project.status == 'active' %}bg-blue-100 text-blue-800
                                    {% else %}bg-gray-100 text-gray-800{% endif %}">
                                    {{ project.status|default('planning') }}
                                </span>
                            </div>
                            <div class="text-gray-400">
                                <i class="fas fa-ellipsis-v"></i>
                            </div>
                        </div>
                        
                        <p class="text-gray-600 text-sm mb-4">{{ project.description|default('No description')|truncate(100) }}</p>
                        
                        <div class="mb-4">
                            <div class="flex justify-between text-sm text-gray-500 mb-1">
                                <span>Progress</span>
                                <span>{{ project.progress|default(0) }}%</span>
                            </div>
                            <div class="h-2 bg-gray-200 rounded-full overflow-hidden">
                                <div class="h-full bg-blue-500 rounded-full" style="width: {{ project.progress|default(0) }}%"></div>
                            </div>
                        </div>
                        
                        <div class="flex justify-between text-sm text-gray-600">
                            <div>
                                <i class="fas fa-tasks mr-1"></i>
                                {{ project.tasks|length|default(0) }} tasks
                            </div>
                            <div>
                                <i class="far fa-calendar mr-1"></i>
                                {{ project.created[:10] if project.created else 'N/A' }}
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                </div>
                {% else %}
                <div class="bg-white rounded-xl shadow p-12 text-center">
                    <div class="text-gray-400 mb-4">
                        <i class="fas fa-project-diagram text-6xl"></i>
                    </div>
                    <h3 class="text-xl font-bold text-gray-900 mb-2">No Projects Yet</h3>
                    <p class="text-gray-600 mb-6">Start by creating your first personal project</p>
                    <a href="/projects?action=new" class="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium inline-block">
                        <i class="fas fa-plus mr-2"></i> Create First Project
                    </a>
                </div>
                {% endif %}
            </div>
            
            <!-- GitHub Integration -->
            <div class="bg-white rounded-xl shadow p-6">
                <div class="flex items-center mb-4">
                    <div class="bg-gray-100 p-2 rounded-lg mr-3">
                        <i class="fab fa-github text-gray-800 text-xl"></i>
                    </div>
                    <div>
                        <h2 class="text-xl font-bold text-gray-900">GitHub Integration</h2>
                        <p class="text-gray-600 text-sm">Connect your projects with GitHub</p>
                    </div>
                </div>
                
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div class="border rounded-lg p-4 text-center">
                        <i class="fab fa-github text-2xl mb-2 text-gray-700"></i>
                        <p class="font-medium">Sync Projects</p>
                        <p class="text-gray-600 text-sm">Sync with GitHub repositories</p>
                    </div>
                    
                    <div class="border rounded-lg p-4 text-center">
                        <i class="fas fa-ticket-alt text-2xl mb-2 text-gray-700"></i>
                        <p class="font-medium">Create Issues</p>
                        <p class="text-gray-600 text-sm">Convert tasks to GitHub issues</p>
                    </div>
                    
                    <div class="border rounded-lg p-4 text-center">
                        <i class="fas fa-code-branch text-2xl mb-2 text-gray-700"></i>
                        <p class="font-medium">Track Progress</p>
                        <p class="text-gray-600 text-sm">Monitor commits and PRs</p>
                    </div>
                </div>
                
                <div class="mt-6">
                    <button onclick="connectGitHub()" class="bg-gray-800 hover:bg-black text-white px-4 py-2 rounded-lg font-medium">
                        <i class="fab fa-github mr-2"></i> Connect GitHub Account
                    </button>
                </div>
            </div>
        </main>
    </div>
    
    <script>
        function connectGitHub() {
            alert('GitHub integration would connect here. In a real implementation, this would open OAuth flow.');
        }
    </script>
</body>
</html>
'''

# Save projects template
(templates_dir / "projects.html").write_text(projects_html)