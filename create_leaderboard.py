import pandas as pd
import numpy as np
import os
from datetime import datetime

def load_data():
    """Load data from Google Sheets"""
    # Use Sheet ID and GID from the URL
    sheet_id = "16vmSDBJ4ylWLWAgJJ8cRg0waVmQYO4miLA5jRT3aIGE"
    gid = "122040106"  # updated GID
    
    # Construct the export URL
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    
    # Read the CSV into a DataFrame, using the second row as the header
    df = pd.read_csv(csv_url, header=1)
    
    # Clean whitespace in all metric names
    df.iloc[:, 0] = df.iloc[:, 0].astype(str).str.strip()
    df.columns = df.columns.str.strip()
    
    return df



def process_data(df):
    """Process and clean the data for leaderboard"""
    # Filter out 'nan' systems
    df_clean = df[df['System Name'] != 'nan'].copy()
    
    # Define the 7 metrics from spider plot
    metrics = [
        "Win rate (including ties as .5)",
        "strict all", 
        "Retreival Relevance Normalized (Avg / 2) avg over ALL user-provided reference -> any arxiv id found in the report",
        "Document Importance RATIO (avg over median citations per reference div by gt arxiv number)",
        "ARXIV Essential citation coverage avg per file",
        "Citation Precision (0's for Nans)", 
        "relaxed recall - divisor all sentences - slide 1  - 0 for nans"
    ]
    
    # Create clean metric names for display
    metric_display_names = {
        "Win rate (including ties as .5)": "Org.",
        "strict all": "Nugget<br>Cov.",
        "Retreival Relevance Normalized (Avg / 2) avg over ALL user-provided reference -> any arxiv id found in the report": "Rel.<br>Rate.",
        "Document Importance RATIO (avg over median citations per reference div by gt arxiv number)": "Doc.<br>Imp.",
        "ARXIV Essential citation coverage avg per file": "Ref.<br>Cov.",
        "Citation Precision (0's for Nans)": "Cite-P", 
        "relaxed recall - divisor all sentences - slide 1  - 0 for nans": "Claim<br>Cov."
    }
    
    # Select required columns (including the open/close column from the sheet)
    leaderboard_data = df_clean[['System Name', 'lm', 'open/close'] + metrics].copy()
    
    # Rename the open/close column to System Type for consistency
    leaderboard_data = leaderboard_data.rename(columns={'open/close': 'System Type'})
    
    # Process metric values
    for metric in metrics:
        if metric in leaderboard_data.columns:
            # Convert to numeric, handling percentages and NaN
            leaderboard_data[metric] = pd.to_numeric(leaderboard_data[metric].astype(str).str.replace('%', ''), errors='coerce')
            
            # Convert percentage metrics to decimal
            if metric in ["Win rate (including ties as .5)", "Citation Precision (0's for Nans)", 
                         "relaxed recall - divisor all sentences - slide 1  - 0 for nans"]:
                leaderboard_data[metric] = leaderboard_data[metric] / 100
            
            # Fill NaN with 0
            leaderboard_data[metric] = leaderboard_data[metric].fillna(0)
            
            # Clip values to maximum of 1.0
            leaderboard_data[metric] = leaderboard_data[metric].clip(upper=1.0)
    
    # Rename columns for display
    leaderboard_data = leaderboard_data.rename(columns=metric_display_names)
    
    # Sort by Organization first, then by Document Importance if tied
    metric_columns = list(metric_display_names.values())
    leaderboard_data = leaderboard_data.sort_values([metric_columns[0], metric_columns[3]], ascending=[False, False])
    
    return leaderboard_data, metric_columns

def create_html_leaderboard(data, metric_columns):
    """Create HTML leaderboard"""
    
    # Get timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DeepScholar-Bench Leaderboard</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 3rem;
            font-weight: 700;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        }}
        
        .header p {{
            font-size: 1.2rem;
            opacity: 0.9;
            margin-bottom: 20px;
        }}
        
        .timestamp {{
            font-size: 0.9rem;
            opacity: 0.8;
        }}
        
        .table-container {{
            overflow-x: auto;
            padding: 30px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
        }}
        
        th {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-weight: 300;
            text-align: center;
            padding: 8px 4px;
            font-size: 0.95rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            position: sticky;
            top: 0;
            z-index: 10;
        }}
        
        .category-header {{
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%) !important;
            color: white;
            font-weight: 700;
            text-align: center;
            font-size: 0.9rem;
            padding: 12px 8px;
        }}
        
        td {{
            padding: 18px 15px;
            text-align: center;
            border-bottom: 1px solid #f0f0f0;
            font-size: 0.9rem;
        }}
        
        tr:hover {{
            background-color: #f8f9ff;
            transform: scale(1.00);
            transition: all 0.2s ease;
        }}
        

        
        .system-name {{
            font-weight: 600;
            color: #1e3c72;
            text-align: left;
            max-width: 200px;
            word-wrap: break-word;
        }}
        
        .lm {{
            font-weight: 500;
            color: #764ba2;
            background: #f0f0ff;
            padding: 6px 12px;
            border-radius: 20px;
            display: inline-block;
            font-size: 0.85rem;
        }}
        
        .metric-score {{
            font-weight: 600;
        }}
        
        .score-excellent {{
            color: #27ae60;
        }}
        
        .score-good {{
            color: #f39c12;
        }}
        
        .score-fair {{
            color: #e74c3c;
        }}
        

        
        .footer {{
            background: #f8f9fa;
            padding: 20px 40px;
            text-align: center;
            color: #666;
            border-top: 1px solid #e9ecef;
        }}
        
        .metric-info {{
            background: #f8f9ff;
            margin: 20px 30px;
            padding: 20px;
            border-radius: 12px;
            border-left: 5px solid #667eea;
        }}
        
        .metric-info h3 {{
            color: #1e3c72;
            margin-bottom: 10px;
        }}
        
        .metric-info p {{
            color: #666;
            line-height: 1.6;
        }}
        
        @media (max-width: 768px) {{
            body {{
                padding: 10px;
            }}
            
            .container {{
                border-radius: 15px;
            }}
            
            .header {{
                padding: 25px 20px;
            }}
            
            .header h1 {{
                font-size: 1.8rem;
            }}
            
            .header p {{
                font-size: 1rem;
            }}
            
            .table-container {{
                padding: 15px 10px;
                overflow-x: auto;
            }}
            
            table {{
                min-width: 800px;
                font-size: 0.75rem;
            }}
            
            th, td {{
                padding: 10px 6px;
                font-size: 0.75rem;
            }}
            
            .system-name {{
                max-width: 120px;
                font-size: 0.8rem;
            }}
            
            .category-header {{
                font-size: 0.8rem;
                padding: 8px 4px;
            }}
            
            .radar-charts-section {{
                margin: 20px 15px;
                padding: 15px;
            }}
            
            .radar-charts-section h3 {{
                font-size: 1.3rem;
            }}
            
            .radar-charts-section .flex {{
                flex-direction: column;
                gap: 20px;
            }}
            
            #systemCheckboxes {{
                min-width: 100%;
                max-width: 100%;
            }}
            
            #radarChart {{
                width: 100% !important;
                height: 500px !important;
                max-width: 100% !important;
            }}
            
            .metric-info {{
                margin: 20px 15px;
                padding: 15px;
            }}
            
            .metric-info h3 {{
                font-size: 1.3rem;
            }}
            
            .contact-section {{
                margin: 20px 15px;
                padding: 15px;
            }}
            
            .contact-section h3 {{
                font-size: 1.3rem;
            }}
        }}
        
        @media (max-width: 480px) {{
            body {{
                padding: 5px;
            }}
            
            .header {{
                padding: 20px 15px;
            }}
            
            .header h1 {{
                font-size: 1.5rem;
            }}
            
            .header p {{
                font-size: 0.9rem;
            }}
            
            .table-container {{
                padding: 10px 5px;
            }}
            
            table {{
                min-width: 700px;
                font-size: 0.7rem;
            }}
            
            th, td {{
                padding: 8px 4px;
                font-size: 0.7rem;
            }}
            
            .system-name {{
                max-width: 100px;
                font-size: 0.75rem;
            }}
            
            #radarChart {{
                height: 450px !important;
            }}
            
            .filter-container {{
                margin: 15px 10px;
                padding: 15px;
            }}
            
            .filter-container .flex {{
                flex-direction: column;
                gap: 15px;
            }}
            
            .filter-container select, .filter-container button {{
                width: 100%;
                min-width: auto;
            }}
        }}
        
        .sort-btn {{
            background: none;
            border: none;
            color: white;
            cursor: pointer;
            padding: 5px;
            border-radius: 3px;
            transition: background 0.2s;
        }}
        
        .sort-btn:hover {{
            background: rgba(255, 255, 255, 0.2);
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏆 DeepScholar-Bench Leaderboard</h1>
            <p>Comprehensive Leaderboard for Research AI Systems</p>
            <div class="timestamp">Last updated: {timestamp}</div>
            <div style="margin-top: 10px;">
                <a href="https://github.com/guestrin-lab/deepscholar-bench" target="_blank" style="color: #ffeb3b; text-decoration: none; font-weight: bold;">GitHub Repository</a>
                &nbsp;|&nbsp;
                <a href="https://arxiv.org/abs/2508.20033" target="_blank" style="color: #ffeb3b; text-decoration: none; font-weight: bold;">Research Paper</a>
                &nbsp;|&nbsp;
                <a href="deep-scholar.vercel.app" target="_blank" style="color: #ffeb3b; text-decoration: none; font-weight: bold;">DeepResearch Preview</a>

          
          
            </div>
            <div style="margin-top: 20px;">
                <a href="#contact" style="color: #ffeb3b; text-decoration: none; font-weight: bold;">Submit Your Solution</a>
            </div>
        </div>
        
        <div class="metric-info">
            <h3>🌐🔍 About DeepScholar-Bench</h3>
            <p>
                <strong>DeepScholar-Bench</strong> provides a live benchmark for evaluating generative research synthesis systems. 
                Its benchmark dataset is generated based on recent ArXiv papers, requiring systems to generate a related work sections by retrieving, 
                synthesizing, and citing sources from the web. The benchmark provides holistic evaluation across three 
                critical capabilities of generative research synthesis: knowledge synthesis, retrieval quality and verifiability.
            </p>
        </div>
        

        
        <div class="filter-container" style="background: #f8f9ff; margin: 20px 30px; padding: 20px; border-radius: 12px; border-left: 5px solid #667eea;">
            <div style="display: flex; flex-wrap: wrap; gap: 20px; align-items: center; justify-content: space-between;">
                <div style="display: flex; flex-wrap: wrap; gap: 20px; align-items: center;">
                    <div style="display: flex; flex-wrap: wrap; gap: 10px; align-items: center;">
                        <label style="font-weight: 600; color: #1e3c72; margin-right: 10px;">Language Model:</label>
                        <select id="lmFilter" onchange="applyFilters()" style="padding: 8px 12px; border: 2px solid #667eea; border-radius: 6px; background: white; font-size: 14px; min-width: 180px;">
                            <option value="all">All Models</option>
                        </select>
                    </div>
                    <div style="display: flex; flex-wrap: wrap; gap: 10px; align-items: center;">
                        <label style="font-weight: 600; color: #1e3c72; margin-right: 10px;">System Type:</label>
                        <select id="typeFilter" onchange="applyFilters()" style="padding: 8px 12px; border: 2px solid #667eea; border-radius: 6px; background: white; font-size: 14px; min-width: 180px;">
                            <option value="all">All Types</option>
                                                    <option value="Open">Open</option>
                        <option value="Closed">Closed</option>
                        </select>
                    </div>
                </div>
                <div style="display: flex; align-items: center; gap: 15px;">
                    <button onclick="clearAllFilters()" style="padding: 8px 16px; background: #667eea; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: 600;">Clear All Filters</button>
                    <span id="filterStatus" style="color: #666; font-style: italic;"></span>
                </div>
            </div>
        </div>
        

"""
    


    # Add table structure
    html_content += """
    <div class='table-container'>
        <table id='leaderboard'>
            <thead>
                <tr>
                    <th rowspan="2" onclick='sortTable(0)'>System Name <span class='sort-btn'>↕</span></th>
                    <th colspan="2" class="category-header">🧠 Knowledge Synthesis</th>
                    <th colspan="3" class="category-header">🔍 Retrieval Quality</th>
                    <th colspan="2" class="category-header">✅ Verifiability</th>
                </tr>
                <tr>
                    <th onclick='sortTable(1)' style='font-size: 0.85rem;'>Organization <span class='sort-btn'>↕</span></th>
                    <th onclick='sortTable(2)' style='font-size: 0.85rem;'>Nugget<br>Coverage <span class='sort-btn'>↕</span></th>
                    <th onclick='sortTable(3)' style='font-size: 0.85rem;'>Relevance<br>Rate <span class='sort-btn'>↕</span></th>
                    <th onclick='sortTable(4)' style='font-size: 0.85rem;'>Document<br>Importance <span class='sort-btn'>↕</span></th>
                    <th onclick='sortTable(5)' style='font-size: 0.85rem;'>Reference<br>Coverage <span class='sort-btn'>↕</span></th>
                    <th onclick='sortTable(6)' style='font-size: 0.85rem;'>Citation<br>Precision <span class='sort-btn'>↕</span></th>
                    <th onclick='sortTable(7)' style='font-size: 0.85rem;'>Claim<br>Coverage <span class='sort-btn'>↕</span></th>
                </tr>
            </thead>
            <tbody>
    """

    # Add JavaScript for dropdowns
    html_content += """
    <script>
        function toggleDropdown(id) {
            const element = document.getElementById(id);
            if (element.style.display === 'none') {
                element.style.display = 'block';
            } else {
                element.style.display = 'none';
            }
        }
    </script>
    """
    
    # Add table rows
    for idx, row in data.iterrows():
        # Format System Type and Language Model as tags
        system_type = row['System Type']
        lm = row['lm'] if pd.notna(row['lm']) else 'N/A'
        
        if system_type == 'Open':
            type_style = 'background: #d4edda; color: #155724; padding: 2px 6px; border-radius: 12px; font-size: 0.75rem; font-weight: 600;'
            system_type_display = 'Open'
        elif system_type == 'Closed':
            type_style = 'background: #f8d7da; color: #721c24; padding: 2px 6px; border-radius: 12px; font-size: 0.75rem; font-weight: 600;'
            system_type_display = 'Closed'
        else:
            type_style = 'background: #fff3cd; color: #856404; padding: 2px 6px; border-radius: 12px; font-size: 0.75rem; font-weight: 600;'
            system_type_display = 'Unknown'

        lm_style = 'background: #f0f0ff; color: #764ba2; padding: 2px 6px; border-radius: 12px; font-size: 0.75rem; font-weight: 600;'

        html_content += f"""
                    <tr>
                        <td class="system-name">{row['System Name']}<br/>
                            <span style="{type_style}">{system_type_display}</span>
                            <span style="{lm_style}">{lm}</span>
                        </td>
"""
        
        # Add metric scores with color coding
        for metric in metric_columns:
            score = row[metric]
            score_class = ""
            if score >= 0.7:
                score_class = "score-excellent"
                score_style = "color: #27ae60; font-weight: 600;"
            elif score >= 0.5:
                score_class = "score-good"
                score_style = "color: #f39c12; font-weight: 600;"
            else:
                score_class = "score-fair"
                score_style = "color: #e74c3c; font-weight: 600;"
            
            html_content += f'<td class="metric-score" style="background: white;"><span style="{score_style}">{score:.3f}</span></td>\n'
        
        html_content += "                    </tr>\n"
    
    html_content += """
                </tbody>
            </table>
        </div>
        
        <!-- Interactive Radar Charts Section -->
        <div class="radar-charts-section" style="margin: 40px 30px; padding: 20px; background: #f8f9ff; border-radius: 12px; border-left: 5px solid #667eea;">
            <h3 style="color: #1e3c72; margin-bottom: 15px;">📊 Interactive Radar Charts</h3>
            <p style="margin-bottom: 20px;">Check/uncheck systems to compare their performance across all metrics:</p>
            
            <div class="flex" style="display: flex; gap: 30px; align-items: flex-start;">
                <!-- System Checkboxes Panel -->
                <div style="min-width: 200px; max-width: 250px;">
                    <div style="margin-bottom: 15px;">
                        <button onclick="selectAllSystems()" style="padding: 6px 12px; background: #27ae60; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px; margin-right: 8px;">Select All</button>
                        <button onclick="clearAllSystems()" style="padding: 6px 12px; background: #e74c3c; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">Clear All</button>
                    </div>
                    <div id="systemCheckboxes" style="max-height: 400px; overflow-y: auto; border: 1px solid #ddd; border-radius: 6px; padding: 12px; background: white;">
                        <!-- Checkboxes will be populated here -->
                    </div>
                </div>
                
                <!-- Radar Chart -->
                <div style="flex: 1; display: flex; justify-content: center;">
                    <canvas id="radarChart" width="600" height="600" style="max-width: 100%; height: auto;"></canvas>
                </div>
            </div>
            
        </div>

        <!-- Evaluation Metrics Section -->
        <div class="metric-info" style="margin: 40px 30px; padding: 20px; background: #f8f9ff; border-radius: 12px; border-left: 5px solid #667eea;">
            <h3 style="color: #1e3c72; margin-bottom: 15px;">📊 Evaluation Metrics</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-top: 15px;">
                <div>
                    <h4 style="color: #1e3c72; margin-bottom: 10px;">🧠 Knowledge Synthesis</h4>
                    <ul style="margin: 0; padding-left: 20px; line-height: 1.6;">
                        <li><strong>Organization</strong> - Measures how well the system organizes and structures the related work section</li>
                        <li><strong>Nugget Coverage</strong> - Evaluates the comprehensiveness of key insights and findings covered</li>
                    </ul>
                </div>
                <div>
                    <h4 style="color: #1e3c72; margin-bottom: 10px;">🔍 Retrieval Quality</h4>
                    <ul style="margin: 0; padding-left: 20px; line-height: 1.6;">
                        <li><strong>Relevance Rate</strong> - Assesses how relevant the retrieved references are to the query</li>
                        <li><strong>Document Importance</strong> - Measures the significance and impact of cited documents</li>
                        <li><strong>Reference Coverage</strong> - Evaluates the breadth of reference sources included</li>
                    </ul>
                </div>
                <div>
                    <h4 style="color: #1e3c72; margin-bottom: 10px;">✅ Verifiability</h4>
                    <ul style="margin: 0; padding-left: 20px; line-height: 1.6;">
                        <li><strong>Citation Precision</strong> - Measures the accuracy and correctness of citations</li>
                        <li><strong>Claim Coverage</strong> - Evaluates how well claims are supported by evidence</li>
                    </ul>
                </div>
            </div>
        </div>

        <!-- Contact Form Section -->
        <div id="contact" class="contact-section" style="margin: 40px 30px; padding: 20px; background: #f8f9ff; border-radius: 12px; border-left: 5px solid #667eea;">
            <h3 style="color: #1e3c72; margin-bottom: 15px;">📬 Submit Your Solution</h3>
            <p>If you'd like to submit your solution to the DeepScholar-Bench leaderboard, please contact us:</p>
            
            <div style="margin-top: 20px; text-align: center;">
                <a href="mailto:negara@berkeley.edu?subject=DeepScholar-Bench Submission&body=Hello,%0D%0A%0D%0AI would like to submit my solution to the DeepScholar-Bench leaderboard.%0D%0A%0D%0APlease find my submission details below:%0D%0A%0D%0A[Your message here]%0D%0A%0D%0ABest regards," 
                   style="background: #667eea; color: white; padding: 15px 30px; border: none; border-radius: 8px; cursor: pointer; font-weight: 600; text-decoration: none; display: inline-block; font-size: 16px;">
                    📧 Email negara@berkeley.edu
                </a>
                
                <p style="margin-top: 15px; color: #666; font-size: 0.9rem;">
                    Click the button above to open your email client with a pre-filled message template.
                </p>
            </div>
        </div>
        
        <div class="footer">
            <p>🌐🔍 DeepScholar-Bench: A comprehensive benchmark for evaluating research AI systems across multiple dimensions of quality and accuracy.</p>
        </div>
    </div>
    
    <!-- Chart.js Library -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    
    <script>
        let sortDirection = {};
        let allRows = []; // Store all original rows for filtering
        let currentFilter = 'all';
        let radarChart = null; // Global variable for radar chart
        let leaderboardData = []; // Store the leaderboard data for radar charts
        
        // Initialize the page
        document.addEventListener('DOMContentLoaded', function() {
            // Store all original rows
            const tbody = document.getElementById('leaderboard').getElementsByTagName('tbody')[0];
            allRows = Array.from(tbody.getElementsByTagName('tr'));
            
            // Populate language model filter options
            populateLMFilter();
            
            // Apply color coding to metrics
            applyMetricColorCoding();
            
            // Initialize radar chart
            initializeRadarChart();
            
            // Populate system selector
            populateSystemSelector();
        });
        
        function applyMetricColorCoding() {
            // Metric columns: 1=Organization, 2=Nugget Coverage, 3=Relevance Rate, 
            // 4=Document Importance, 5=Reference Coverage, 6=Citation Precision, 7=Claim Coverage
            const metricColumns = [1, 2, 3, 4, 5, 6, 7];
            
            metricColumns.forEach(columnIndex => {
                // Get all values for this column
                const values = [];
                allRows.forEach(row => {
                    const cell = row.cells[columnIndex];
                    if (cell) {
                        const value = parseFloat(cell.textContent.trim());
                        if (!isNaN(value)) {
                            values.push({ value: value, cell: cell });
                        }
                    }
                });
                
                // Sort by value (descending for ranking)
                values.sort((a, b) => b.value - a.value);
                
                // Apply colors
                values.forEach((item, index) => {
                    let textColor;
                    
                    if (index < 3) {
                        // Top 3: Green
                        textColor = '#27ae60';
                    } else if (index >= values.length - 3) {
                        // Bottom 3: Red
                        textColor = '#e74c3c';
                    } else {
                        // Others: Orange
                        textColor = '#f39c12';
                    }
                    
                    // Only color the number text, keep cell background white
                    item.cell.innerHTML = `<span style="color: ${textColor}; font-weight: 600;">${item.value.toFixed(3)}</span>`;
                    item.cell.style.backgroundColor = 'white';
                });
            });
        }
        
        function populateLMFilter() {
            const lmSet = new Set();
            allRows.forEach(row => {
                const systemNameCell = row.cells[0]; // System Name column contains LM info
                if (systemNameCell) {
                    // Look for LM span tags within the system name cell
                    const lmSpans = systemNameCell.querySelectorAll('span[style*="background: #f0f0ff"]');
                    lmSpans.forEach(span => {
                        const lmText = span.textContent.trim();
                        if (lmText && lmText !== 'N/A') {
                            // Handle comma-separated models
                            const models = lmText.split(',').map(m => m.trim());
                            models.forEach(model => {
                                if (model) lmSet.add(model);
                            });
                        }
                    });
                }
            });
            
            const lmFilter = document.getElementById('lmFilter');
            const sortedLMs = Array.from(lmSet).sort();
            
            sortedLMs.forEach(lm => {
                const option = document.createElement('option');
                option.value = lm;
                option.textContent = lm;
                lmFilter.appendChild(option);
            });
        }
        
        function applyFilters() {
            const selectedLM = document.getElementById('lmFilter').value;
            const selectedType = document.getElementById('typeFilter').value;
            const tbody = document.getElementById('leaderboard').getElementsByTagName('tbody')[0];
            const filterStatus = document.getElementById('filterStatus');
            
            // Clear current table
            tbody.innerHTML = '';
            
            let filteredRows = allRows;
            let filterMessages = [];
            
            // Apply language model filter
            if (selectedLM !== 'all') {
                filteredRows = filteredRows.filter(row => {
                    const systemNameCell = row.cells[0]; // System Name column contains LM info
                    if (systemNameCell) {
                        // Look for LM span tags within the system name cell
                        const lmSpans = systemNameCell.querySelectorAll('span[style*="background: #f0f0ff"]');
                        for (let span of lmSpans) {
                            const lmText = span.textContent.trim();
                            if (lmText && lmText.includes(selectedLM)) {
                                return true;
                            }
                        }
                    }
                    return false;
                });
                filterMessages.push(`Model: ${selectedLM}`);
            }
            
            // Apply system type filter
            if (selectedType !== 'all') {
                filteredRows = filteredRows.filter(row => {
                    const systemNameCell = row.cells[0]; // System Name column contains type info
                    if (systemNameCell) {
                        // Look for type span tags within the system name cell
                        const typeSpans = systemNameCell.querySelectorAll('span[style*="background: #f8d7da"], span[style*="background: #d4edda"]');
                        for (let span of typeSpans) {
                            const typeText = span.textContent.trim();
                            if (typeText && typeText.includes(selectedType)) {
                                return true;
                            }
                        }
                    }
                    return false;
                });
                filterMessages.push(`Type: ${selectedType}`);
            }
            
            // Update filter status
            if (filterMessages.length > 0) {
                filterStatus.textContent = `Showing ${filteredRows.length} systems (${filterMessages.join(', ')})`;
            } else {
                filterStatus.textContent = '';
            }
            
            // Add filtered rows back to table (no ranking)
            filteredRows.forEach((row, index) => {
                tbody.appendChild(row);
            });
            
            // Reapply color coding for the filtered results
            applyMetricColorCodingToVisibleRows();
        }
        
        function applyMetricColorCodingToVisibleRows() {
            // Apply color coding only to currently visible rows
            const tbody = document.getElementById('leaderboard').getElementsByTagName('tbody')[0];
            const visibleRows = Array.from(tbody.getElementsByTagName('tr'));
            
            // Metric columns: 1=Organization, 2=Nugget Coverage, 3=Relevance Rate, 
            // 4=Document Importance, 5=Reference Coverage, 6=Citation Precision, 7=Claim Coverage
            const metricColumns = [1, 2, 3, 4, 5, 6, 7];
            
            metricColumns.forEach(columnIndex => {
                // Get all values for this column from visible rows
                const values = [];
                visibleRows.forEach(row => {
                    const cell = row.cells[columnIndex];
                    if (cell) {
                        const value = parseFloat(cell.textContent.trim());
                        if (!isNaN(value)) {
                            values.push({ value: value, cell: cell });
                        }
                    }
                });
                
                // Sort by value (descending for ranking)
                values.sort((a, b) => b.value - a.value);
                
                // Apply colors
                values.forEach((item, index) => {
                    let textColor;
                    
                    if (index < 3) {
                        // Top 3: Green
                        textColor = '#27ae60';
                    } else if (index >= values.length - 3) {
                        // Bottom 3: Red
                        textColor = '#e74c3c';
                    } else {
                        // Others: Orange
                        textColor = '#f39c12';
                    }
                    
                    // Only color the number text, keep cell background white
                    item.cell.innerHTML = `<span style="color: ${textColor}; font-weight: 600;">${item.value.toFixed(3)}</span>`;
                    item.cell.style.backgroundColor = 'white';
                });
            });
        }
        
        function clearAllFilters() {
            document.getElementById('lmFilter').value = 'all';
            document.getElementById('typeFilter').value = 'all';
            applyFilters();
        }
        
        function updateSortIndicators(activeColumnIndex, ascending) {
            // Reset all sort indicators
            const headers = document.querySelectorAll('th .sort-btn');
            headers.forEach((btn, index) => {
                if (index === activeColumnIndex) {
                    // Show active sort direction
                    btn.textContent = ascending ? '↑' : '↓';
                    btn.style.color = '#fff';
                    btn.style.fontWeight = 'bold';
                } else {
                    // Show neutral state
                    btn.textContent = '↕';
                    btn.style.color = '#fff';
                    btn.style.fontWeight = 'normal';
                }
            });
        }
        
        function sortTable(columnIndex) {
            const table = document.getElementById('leaderboard');
            const tbody = table.getElementsByTagName('tbody')[0];
            const rows = Array.from(tbody.getElementsByTagName('tr'));
            
            // Toggle sort direction
            sortDirection[columnIndex] = !sortDirection[columnIndex];
            const ascending = sortDirection[columnIndex];
            
            // Update sort indicators
            updateSortIndicators(columnIndex, ascending);
            
            rows.sort((a, b) => {
                let aValue = a.cells[columnIndex].textContent.trim();
                let bValue = b.cells[columnIndex].textContent.trim();
                
                
                
                // Try to parse as numbers
                const aNum = parseFloat(aValue);
                const bNum = parseFloat(bValue);
                
                if (!isNaN(aNum) && !isNaN(bNum)) {
                    return ascending ? aNum - bNum : bNum - aNum;
                } else {
                    return ascending ? aValue.localeCompare(bValue) : bValue.localeCompare(aValue);
                }
            });
            
            // Clear tbody and add sorted rows
            tbody.innerHTML = '';
            rows.forEach((row, index) => {
                tbody.appendChild(row);
            });
            
            // Reapply color coding after sorting
            applyMetricColorCodingToVisibleRows();
        }
        
        // Radar Chart Functions
        function initializeRadarChart() {
            const ctx = document.getElementById('radarChart').getContext('2d');
            const labels = ['Organization', 'Nugget\\nCoverage', 'Relevance\\nRate', 'Document\\nImportance', 'Reference\\nCoverage', 'Citation\\nPrecision', 'Claim\\nCoverage'];
            radarChart = new Chart(ctx, {
                type: 'radar',
                data: { labels: labels, datasets: [] },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        r: {
                            beginAtZero: true,
                            max: 1,
                            ticks: { stepSize: 0.2, color: '#666', font: { size: 12 } },
                            grid: { color: 'rgba(0, 0, 0, 0.1)' },
                            pointLabels: { font: { size: 14, weight: 'bold' }, color: '#1e3c72' }
                        }
                    },
                    plugins: {
                        legend: { position: 'top', labels: { usePointStyle: true, padding: 20, font: { size: 14 } } },
                        tooltip: { callbacks: { label: function(context) { return context.dataset.label + ': ' + context.parsed.r.toFixed(3); } } }
                    },
                    layout: {
                        padding: {
                            top: 20,
                            bottom: 20
                        }
                    }
                }
            });
        }
        
        function populateSystemSelector() {
            const checkboxContainer = document.getElementById('systemCheckboxes');
            const tbody = document.getElementById('leaderboard').getElementsByTagName('tbody')[0];
            const rows = Array.from(tbody.getElementsByTagName('tr'));
            checkboxContainer.innerHTML = '';
            
            rows.forEach((row, index) => {
                const systemNameCell = row.cells[0];
                if (systemNameCell) {
                    const systemName = systemNameCell.textContent.split('\\n')[0].trim();
                    
                    // Create checkbox container
                    const checkboxDiv = document.createElement('div');
                    checkboxDiv.style.cssText = 'display: flex; align-items: center; margin-bottom: 8px; padding: 6px; border-radius: 4px; transition: background-color 0.2s;';
                    checkboxDiv.onmouseover = function() { this.style.backgroundColor = '#f8f9ff'; };
                    checkboxDiv.onmouseout = function() { this.style.backgroundColor = 'transparent'; };
                    
                    // Create checkbox
                    const checkbox = document.createElement('input');
                    checkbox.type = 'checkbox';
                    checkbox.id = 'system_' + index;
                    checkbox.value = index;
                    checkbox.style.cssText = 'margin-right: 10px; transform: scale(1.2);';
                    checkbox.onchange = function() { updateRadarChart(); };
                    
                    // Check by default for OpenAI DeepResearch, Search AI (Claude-opus-4), and Search AI (Llama-4-Scout)
                    if (systemName.includes('OpenAI DeepResearch') || systemName.includes('Search AI (Claude-opus-4)') || systemName.includes('Search AI (Llama-4-Scout)')) {
                        checkbox.checked = true;
                    }
                    
                    // Create label
                    const label = document.createElement('label');
                    label.htmlFor = 'system_' + index;
                    label.textContent = systemName;
                    label.style.cssText = 'cursor: pointer; font-size: 13px; color: #333; flex: 1; user-select: none;';
                    
                    // Add to container
                    checkboxDiv.appendChild(checkbox);
                    checkboxDiv.appendChild(label);
                    checkboxContainer.appendChild(checkboxDiv);
                }
            });
            
            leaderboardData = rows.map((row, index) => {
                const systemNameCell = row.cells[0];
                const systemName = systemNameCell.textContent.split('\\n')[0].trim();
                const metrics = [];
                for (let i = 1; i <= 7; i++) {
                    const cell = row.cells[i];
                    if (cell) {
                        const value = parseFloat(cell.textContent.trim());
                        metrics.push(isNaN(value) ? 0 : value);
                    }
                }
                return { index: index, name: systemName, metrics: metrics };
            });
            
            // Update the radar chart with default selections
            updateRadarChart();
        }
        
        function updateRadarChart() {
            const checkboxes = document.querySelectorAll('#systemCheckboxes input[type="checkbox"]:checked');
            const selectedIndices = Array.from(checkboxes).map(checkbox => parseInt(checkbox.value));
            
            if (selectedIndices.length === 0) {
                // Clear the chart if no systems are selected
                radarChart.data.datasets = [];
                radarChart.update();
                return;
            }
            
            radarChart.data.datasets = [];
            selectedIndices.forEach((index, colorIndex) => {
                const systemData = leaderboardData[index];
                if (systemData) {
                    const color = getSystemColor(colorIndex);
                    radarChart.data.datasets.push({
                        label: systemData.name,
                        data: systemData.metrics,
                        borderColor: color,
                        backgroundColor: color + '20',
                        borderWidth: 3,
                        pointBackgroundColor: color,
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2,
                        pointRadius: 6,
                        fill: true
                    });
                }
            });
            radarChart.update();
        }
        
        function clearAllSystems() {
            const checkboxes = document.querySelectorAll('#systemCheckboxes input[type="checkbox"]');
            checkboxes.forEach(checkbox => {
                checkbox.checked = false;
            });
            updateRadarChart();
        }
        
        function selectAllSystems() {
            const checkboxes = document.querySelectorAll('#systemCheckboxes input[type="checkbox"]');
            checkboxes.forEach(checkbox => {
                checkbox.checked = true;
            });
            updateRadarChart();
        }
        
        function getSystemColor(index) {
            const colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf', '#ff9896', '#98df8a', '#ffbb78', '#c5b0d5', '#c49c94'];
            return colors[index % colors.length];
        }
    </script>
</body>
</html>
"""
    
    return html_content

def main():
    """Main function to generate the leaderboard"""
    print("🚀 Creating DeepScholar-Bench Leaderboard...")
    
    # Load and process data
    df = load_data()
    leaderboard_data, metric_columns = process_data(df)
    
    print(f"✅ Processed {len(leaderboard_data)} systems")
    print(f"📊 Included metrics: {', '.join(metric_columns)}")
    
    # Create HTML leaderboard
    html_content = create_html_leaderboard(leaderboard_data, metric_columns)
    
    # Create output directory
    output_dir = 'leaderboard'
    os.makedirs(output_dir, exist_ok=True)
    
    # Save HTML file
    html_file = os.path.join(output_dir, 'deepscholar_bench_leaderboard.html')
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"🎉 Leaderboard saved to: {html_file}")
    
    # Also save CSV for reference
    csv_file = os.path.join(output_dir, 'leaderboard_data.csv')
    leaderboard_data.to_csv(csv_file, index=False)
    print(f"📋 CSV data saved to: {csv_file}")
    
    # Print top 5 systems
    print("\n🏆 Top 5 Systems:")
    print("=" * 80)
    top_5 = leaderboard_data.head()
    for idx, row in top_5.iterrows():
        print(f"{idx+1:2d}. {row['System Name']:<30} ({row['lm']}) - Org: {row[metric_columns[0]]:.3f}")
    
    return html_file, csv_file

if __name__ == "__main__":
    main()
