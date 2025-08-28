import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import colorsys
import os
from matplotlib.colors import to_rgb
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

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

# Define metrics to plot (same for both individual and combined plots)
metrics_to_plot = [
    "Win rate (including ties as .5)",
    "strict all",
    "Retreival Relevance Normalized (Avg / 2) avg over ALL user-provided reference -> any arxiv id found in the report",
    "Document Importance RATIO (avg over median citations per reference div by gt arxiv number)",
    "ARXIV Essential citation coverage avg per file",
    "Citation Precision (0's for Nans)",
    "relaxed recall - divisor all sentences - slide 1  - 0 for nans",
]

# Renaming dictionaries for individual plots
individual_metric_renames = {
    "Citation Precision (0's for Nans)": 'Citation \n Precision',
    "relaxed recall - divisor all sentences - slide 1  - 0 for nans": 'Claim \n Coverage',
    'Retreival Relevance Normalized (Avg / 2) avg over ALL user-provided reference -> any arxiv id found in the report':'Relevance \nRate',
    'Win rate (including ties as .5)':'Organization',
    "strict all":'Nugget \nCoverage',
    "ARXIV Essential citation coverage avg per file" :"Reference \n Coverage",
    "Document Importance RATIO (avg over median citations per reference div by gt arxiv number)":'Document \n Importance',
}

# Renaming dictionaries for combined plots (more compact labels)
combined_metric_renames = {
    "Citation Precision (0's for Nans)": 'Cite-P',
    "relaxed recall - divisor all sentences - slide 1  - 0 for nans": 'Claim Cov \n(w = 1)',
    'Retreival Relevance Normalized (Avg / 2) avg over ALL user-provided reference -> any arxiv id found in the report':'Relevance \nRate',
    'Win rate (including ties as .5)':'Organization',
    "strict all":'Nugget \nCoverage',
    "ARXIV Essential citation coverage avg per file" :"Reference \n Coverage",
    "Document Importance RATIO (avg over median citations per reference div by gt arxiv number)":'Doc \n Importance',
}

# Define the two model groups
model_groups = {
    'llama_only': {
        'exclude': ['Abalation (Llama-4,2,2) - no filter, topk','nan','Ground Truth' ,'lotus gain','o1 + web',
                   'Search AI (GPT-4.1)', 'Search AI (Claude-opus-4)','Search AI (Gemini-2.5-pro)','OpenAI DeepResearch',
                   'DeepScholar-base (GPT4.1)','DeepScholar-base (Llama-4, Gemini-2.5-pro)','DeepScholar-base (GPT4.1 + Claude-opus-4)','DeepScholar-base (GPT4.1 + o3)',
                   'Claude- Parallel','Claude- Tavily','DeepScholar-base (GPT4.1 + o3)','DeepScholar-base (GPT4.1 + Gemini-2.5-pro)',
                   'DeepScholar-base (GPT4.1)', 'DeepScholar-base (GPT4.1 + o3)', 'DeepScholar-base (GPT4.1 + Gemini-2.5-pro)',
                'Llama-4 - Parallel','Llama-4 - Tavily', 'Search AI (o3)','Claude- Tavily', 'Claude- Parallel','Ours (Llama-4, GPT4.1 2,2)'],
        'title': 'Open-source systems',
        'filename': 'open_source_systems'
    },
    'non_llama': {
        'exclude': ['Abalation (Llama-4,2,2) - no filter, topk','nan','Ground Truth' ,'lotus gain','o1 + web',
                   'DeepResearcher (Llama-4-scout)','STORM (Llama-4-scout)','OpenScholar (Llama-4-scout)',
                   'Search AI (Llama-4-Scout)','Search AI (GPT-4.1)',
                   'DeepScholar-base (Llama-4-scout)','DeepScholar-base (GPT4.1)',
                   'Llama-4 - Parallel','Llama-4 - Tavily','Search AI (Llama-4-scout)',
                    'DeepScholar-base (GPT4.1 + o3)', 'DeepScholar-base (GPT4.1 + Gemini-2.5-pro)',
                    'Llama-4 - Parallel','Llama-4 - Tavily', 'Claude- Tavily', 'Claude- Parallel'
],
        'title': 'Closed-source systems',
        'filename': 'closed_source_systems'
    }
}

# Use colorblind-friendly colors
colorblind_friendly_colors = [
    '#1f77b4',  # blue
    '#ff7f0e',  # orange  
    '#2ca02c',  # green
    'red',  # red
    '#9467bd',  # purple
    '#8c564b',  # brown
    '#e377c2',  # pink
    '#7f7f7f',  # gray
    'y',  # olive bcbd22
    '#17becf',  # cyan
    '#ff9896',  # light red
    '#98df8a',  # light green
    '#ffbb78',  # light orange
    '#c5b0d5',  # light purple
    '#c49c94',  # light brown
    '#f7b6d2',  # light pink
]

def get_models_for_group(exclude_list):
    """Get models for a specific group"""
    all_models = df.iloc[1:, 0].tolist()
    # Clean the exclude list to handle whitespace
    exclude_list_clean = [str(item).strip() for item in exclude_list]
    
    # Debug: print what we're working with
    print(f"\nExcluding models: {exclude_list_clean}")
    
    filtered_models = []
    for model in all_models:
        model_clean = str(model).strip()
        if model_clean not in exclude_list_clean:
            filtered_models.append(model_clean)
        else:
            print(f"Excluded: '{model_clean}'")
    
    print(f"Models included: {filtered_models}")
    return filtered_models

def get_model_data(models_to_plot, metrics_to_plot, color_mapping=None):
    """Get data for a specific group of models"""
    model_data = []
    for i, model_name in enumerate(models_to_plot):
        # find the row
        model_row = None
        for idx, row in df.iterrows():
            if str(row.iloc[0]).strip() == model_name:
                model_row = row
                break
        if model_row is None:
            continue

        # extract values
        values = []
        for metric in metrics_to_plot:
            try:
                if metric in df.columns:
                    val = model_row[metric]
                    if pd.isna(val):
                        val = 0
                    else:
                        val_str = str(val).replace('%', '').strip()
                        val = float(val_str)
                        if metric in ["Win rate (including ties as .5)",
                                      "Citation Precision (0's for Nans)",
                                      "relaxed recall - divisor all sentences - slide 1  - 0 for nans"]:
                            val = val / 100
                    # Clip values to maximum of 1.0 for the spider plot
                    val = min(val, 1.0)
                    values.append(val)
                else:
                    values.append(0)
            except Exception as e:
                values.append(0)

        # Use global color mapping if provided, otherwise fall back to index-based coloring
        if color_mapping and model_name in color_mapping:
            color = color_mapping[model_name]
        else:
            color = colorblind_friendly_colors[i % len(colorblind_friendly_colors)]

        model_data.append({
            'name': model_name,
            'values': values,
            'color': color
        })
    
    return model_data

def create_individual_spider_plot(ax, model_data, title, metrics_to_plot, metric_renames):
    """Create a single spider plot for individual plots (with rotation and extended arcs)"""
    if not model_data:
        ax.text(0.5, 0.5, 'No data', ha='center', va='center', transform=ax.transAxes)
        return
    
    labels = [metric_renames.get(metric, metric) for metric in metrics_to_plot]
    angles = np.linspace(0, 2*np.pi, len(labels), endpoint=False).tolist()
    angles += angles[:1]

    idx_citep = metrics_to_plot.index("Citation Precision (0's for Nans)")
    idx_claim = metrics_to_plot.index("relaxed recall - divisor all sentences - slide 1  - 0 for nans")

    # midpoint angle (in radians) between the two axes
    mid_angle = 0.5 * (angles[idx_citep] + angles[idx_claim])

    # offset so that midpoint goes to 270° (south)
    theta_offset = (3*np.pi/2) - mid_angle

    # rotate the entire polar axis frame
    ax.set_theta_offset(theta_offset)
    
    # Helper: rotation tangent to arc, accounting for axis offset; keeps text upright
    def tangent_rotation(angle_rad, ax):
        ang = angle_rad + ax.get_theta_offset()
        deg = np.degrees(ang) % 360
        if 90 < deg < 270:
            deg += 180
        return deg - 90                                 # tangent (subtract 90)

    # TWO-LAYER APPROACH: Outer plot for arcs + Inner plot for data

    # LAYER 1: Create larger outer spider plot for arcs (background)
    ax.set_rmax(1.45)  # Larger outer plot to accommodate arcs
    ax.set_ylim(0, 1.45)
    ax.set_yticks([])  # No ticks for background layer
    ax.set_yticklabels([])
    ax.grid(False)  # No grid for background layer
    ax.spines['polar'].set_visible(False)  # Remove the outer polar boundary

    # Add arc categories in the outer area - disconnected with different colors
    arc_radius = 1.38  # Position arcs clearly outside the inner 1.0 circle
    arc_colors = ['#9ea8b8', '#9e938a', '#aebdb0']  #green brown blue

    # Manually specify arc boundaries with extended coverage
    # Metrics order: [0:Organization, 1:Nugget Coverage, 2:Relevance Rate, 3:Document Importance, 4:Ref Cov., 5:Cite-P, 6:Claim Cov]
    
    gap_size = np.pi/90  # 4 degrees - you can adjust this value

    # Knowledge Synthesis: Organization (0) to Nugget Coverage (1) - extended with gap
    ks_start = angles[0] - np.pi/12 + gap_size   # Start slightly before Organization + gap
    ks_end = angles[1] + np.pi/12 - gap_size     # End slightly after Nugget Coverage - gap

    # Verifiability: Cite-P (5) to Claim Cov (6) - extended more on both sides with gap
    vf_start = angles[5] - np.pi/6 + gap_size    # Extend further between Ref Cov and Cite-P + gap
    vf_end = angles[6] + np.pi/6 - gap_size      # Extend further between Claim Cov and Organization - gap

    # Retrieval Quality: Relevance Rate (2) to Ref Cov (4) - now includes Document Importance (3)
    rq_start = angles[2] - np.pi/6 + gap_size    # Start at Relevance Rate + gap
    rq_end = angles[4] + np.pi/12 - gap_size     # End at Ref Cov - gap
    category_boundaries = [
        (ks_start, ks_end, arc_colors[0], 'Knowledge Synthesis'),
        (vf_start, vf_end, arc_colors[1], 'Verifiability'), 
        (rq_start, rq_end, arc_colors[2], 'Retrieval Quality')
    ]
    
    # Sort boundaries by start angle to ensure proper connection order
    category_boundaries.sort(key=lambda x: x[0])
    
    # Create connected arcs by filling gaps between categories
    all_arc_angles = []
    all_arc_colors = []
    for start_angle, end_angle, color, category_name in category_boundaries:
        # Create arc angles for this category only
        arc_angles = np.linspace(start_angle, end_angle, 100)
        arc_r = np.full_like(arc_angles, arc_radius)
        
        # Plot just this arc segment
        ax.plot(arc_angles, arc_r, 
                color=color, linewidth=8, alpha=0.9, zorder=20)
    # No arrows - clean arc design

    # Add category labels (aligned to arc tangents)
    for start_angle, end_angle, color, category_name in category_boundaries:
        mid_angle = 0.5 * (start_angle + end_angle)
        label_radius = arc_radius + 0.12
        # base tangent rotation
        base_rot = tangent_rotation(mid_angle, ax)

        # special-case flip for Verifiability & Retrieval Quality
        if category_name in ["Verifiability", "Retrieval Quality"]:
            base_rot += 180

        ax.text(mid_angle, label_radius, category_name,
                ha='center', va='center',
                fontsize=40, fontweight='bold', color=color,
                rotation=base_rot,
                rotation_mode='anchor', zorder=21)

    # LAYER 2: Now overlay the main spider plot (foreground) - constrained to 1.0
    # Draw a white circle to mask the inner area and create clean separation
    circle_angles = np.linspace(0, 2*np.pi, 100)
    circle_r = np.full_like(circle_angles, 1.0)
    ax.fill(circle_angles, circle_r, color='white', alpha=0.95, zorder=10)

    # Add the MAIN BLACK CIRCLE at radius 1.0 (the boundary)
    ax.plot(circle_angles, circle_r, color='darkgray', linewidth=1.5, zorder=15)  # Changed from black to darkgray and reduced width from 2 to 1.5

    # Draw inner grid circles (lighter)
    for r in [0.2, 0.4, 0.6, 0.8]:
        inner_circle_r = np.full_like(circle_angles, r)
        ax.plot(circle_angles, inner_circle_r, color='lightgray', linewidth=0.5, alpha=0.7, zorder=11)

    # Add radial grid lines
    for angle in angles[:-1]:  # Don't include the duplicate last angle
        ax.plot([angle, angle], [0, 1.0], color='lightgray', linewidth=0.5, alpha=0.7, zorder=11)

    # Add tick labels for the inner plot - positioned at "Nugget Coverage" axis
    # "Nugget Coverage" is at index 1 in metrics_to_plot (strict all)
    nugget_angle = angles[1]  # Get the angle for "Nugget Coverage" axis
    for i, r in enumerate([0.2, 0.4, 0.6, 0.8]):
        ax.text(nugget_angle, r, f'{r}', ha='center', va='bottom', fontsize=32, zorder=12)  # Much larger font

    # Plot the spider charts in the inner area (foreground layer)
    for model_data_item in model_data:
        values_plot = model_data_item['values'] + model_data_item['values'][:1]
        ax.plot(angles, values_plot, linewidth=3, linestyle='solid',
                color=model_data_item['color'], label=model_data_item['name'], zorder=13)
        ax.fill(angles, values_plot, alpha=0.12, color=model_data_item['color'], zorder=12)

    # Set the metric labels on the inner side of the circle
    ax.set_thetagrids(np.degrees(angles[:-1]), [])  # Remove default labels

    # Add custom metric labels positioned inside the circle - with higher zorder to appear above arcs
    label_radius = 1.11  # Position labels further outside the main circle
    for i, (angle, label) in enumerate(zip(angles[:-1], labels)):
        ax.text(angle, label_radius, label,
                ha='center', va='center', fontsize=34, fontweight='normal',
                zorder=25)  # Much higher zorder to appear above arcs

def create_combined_spider_plot(ax, model_data, title, metrics_to_plot, metric_renames):
    """Create a single spider plot for combined plots (without rotation, connected arcs)"""
    if not model_data:
        ax.text(0.5, 0.5, 'No data', ha='center', va='center', transform=ax.transAxes)
        return
    
    labels = [metric_renames.get(metric, metric) for metric in metrics_to_plot]
    angles = np.linspace(0, 2*np.pi, len(labels), endpoint=False).tolist()
    angles += angles[:1]

    # TWO-LAYER APPROACH: Outer plot for arcs + Inner plot for data

    # LAYER 1: Create larger outer spider plot for arcs (background)
    ax.set_rmax(1.3)  # Larger outer plot to accommodate arcs
    ax.set_ylim(0, 1.3)
    ax.set_yticks([])  # No ticks for background layer
    ax.set_yticklabels([])
    ax.grid(False)  # No grid for background layer
    ax.spines['polar'].set_visible(False)  # Remove the outer polar boundary

    # Add arc categories in the outer area - using different gray tones
    arc_radius = 1.25  # Position arcs clearly outside the inner 1.0 circle
    arc_colors = ['#2d2d2d', '#555555', '#808080']  # Very dark gray, Medium dark gray, Medium gray

    # Manually specify arc boundaries with extended coverage for Verifiability
    # Metrics order: [0:Organization, 1:Nugget Coverage, 2:Relevance Rate, 3:Document Importance, 4:Ref Cov., 5:Cite-P, 6:Claim Cov]
    
    # Knowledge Synthesis: Organization (0) to Nugget Coverage (1)
    ks_start = angles[0]  # Start at Organization
    ks_end = angles[1]    # End at Nugget Coverage
    
    # Verifiability: Cite-P (5) to Claim Cov (6) - extend half way on both sides
    vf_start = angles[5] - np.pi/7  # Half way between Ref Cov and Cite-P
    vf_end = angles[6] + np.pi/7    # Half way between Claim Cov and Organization
    
    # Retrieval Quality: Relevance Rate (2) to Ref Cov (4) - now includes Document Importance (3)
    rq_start = angles[2] - np.pi/7 # Start at Relevance Rate
    rq_end = angles[4]    # End at Ref Cov
    
    category_boundaries = [
        (ks_start, ks_end, arc_colors[0], 'Knowledge Synthesis'),
        (vf_start, vf_end, arc_colors[1], 'Verifiability'), 
        (rq_start, rq_end, arc_colors[2], 'Retrieval Quality')
    ]
    
    # Sort boundaries by start angle to ensure proper connection order
    category_boundaries.sort(key=lambda x: x[0])
    
    # Create connected arcs by filling gaps between categories
    all_arc_angles = []
    all_arc_colors = []
    
    for i, (start_angle, end_angle, color, category_name) in enumerate(category_boundaries):
        # Create arc segment for this category
        arc_angles = np.linspace(start_angle, end_angle, 100)
        all_arc_angles.extend(arc_angles)
        all_arc_colors.extend([color] * len(arc_angles))
        
        # Connect to next category if not the last one
        if i < len(category_boundaries) - 1:
            next_start = category_boundaries[i + 1][0]
            # Create connecting segment
            if next_start > end_angle:
                # Normal case: next category starts after this one ends
                connect_angles = np.linspace(end_angle, next_start, 50)
                all_arc_angles.extend(connect_angles)
                all_arc_colors.extend([color] * len(connect_angles))  # Use same color for connection
            else:
                # Handle wrap-around case
                connect_angles1 = np.linspace(end_angle, 2*np.pi, 25)
                connect_angles2 = np.linspace(0, next_start, 25)
                all_arc_angles.extend(connect_angles1)
                all_arc_angles.extend(connect_angles2)
                all_arc_colors.extend([color] * len(connect_angles1))
                all_arc_colors.extend([color] * len(connect_angles2))
    
    # Connect last category back to first if needed
    if len(category_boundaries) > 1:
        last_end = category_boundaries[-1][1]
        first_start = category_boundaries[0][0]
        if first_start > last_end:
            connect_angles = np.linspace(last_end, first_start, 50)
            all_arc_angles.extend(connect_angles)
            all_arc_colors.extend([arc_colors[0]] * len(connect_angles))
        else:
            connect_angles1 = np.linspace(last_end, 2*np.pi, 25)
            connect_angles2 = np.linspace(0, first_start, 25)
            all_arc_angles.extend(connect_angles1)
            all_arc_angles.extend(connect_angles2)
            all_arc_colors.extend([arc_colors[0]] * len(connect_angles1))
            all_arc_colors.extend([arc_colors[0]] * len(connect_angles2))

    # Plot the connected colored arc segments
    arc_r = np.full_like(all_arc_angles, arc_radius)
    
    # Plot each colored segment separately to ensure colors show properly
    current_color = all_arc_colors[0]
    start_idx = 0
    
    for i in range(1, len(all_arc_angles)):
        if all_arc_colors[i] != current_color or i == len(all_arc_angles) - 1:
            # Plot the segment with current color
            segment_angles = all_arc_angles[start_idx:i+1]
            segment_r = np.full_like(segment_angles, arc_radius)
            ax.plot(segment_angles, segment_r, 
                    color=current_color, linewidth=8, alpha=0.9, zorder=20)
            
            # Update for next segment
            if i < len(all_arc_angles) - 1:
                current_color = all_arc_colors[i]
                start_idx = i

    # Add category labels
    for i, (start_angle, end_angle, color, category_name) in enumerate(category_boundaries):
        mid_angle = (start_angle + end_angle) / 2
        label_radius = arc_radius + 0.10  # Move labels further outside the arcs (was 0.06)

        # Add text with rotation logic
        rotation_angle = np.degrees(mid_angle)
        if mid_angle > np.pi/2 and mid_angle < 3*np.pi/2:
            rotation_angle = rotation_angle + 180

        # Special rotation for "Retrieval Quality" - rotate 180 degrees
        if category_name == "Retrieval Quality":
            rotation_angle = rotation_angle + 180
            
        # Special rotation for "Verifiability" - rotate 180 degrees
        if category_name == "Verifiability":
            rotation_angle = rotation_angle + 180

        ax.text(mid_angle, label_radius, category_name,
                ha='center', va='center', fontsize=32, fontweight='bold',
                color=color,
                rotation=rotation_angle - 90, zorder=21)

    # LAYER 2: Now overlay the main spider plot (foreground) - constrained to 1.0
    # Draw a white circle to mask the inner area and create clean separation
    circle_angles = np.linspace(0, 2*np.pi, 100)
    circle_r = np.full_like(circle_angles, 1.0)
    ax.fill(circle_angles, circle_r, color='white', alpha=0.95, zorder=10)

    # Add the MAIN BLACK CIRCLE at radius 1.0 (the boundary)
    ax.plot(circle_angles, circle_r, color='darkgray', linewidth=1.5, zorder=15)  # Changed from black to darkgray and reduced width from 2 to 1.5

    # Draw inner grid circles (lighter)
    for r in [0.2, 0.4, 0.6, 0.8]:
        inner_circle_r = np.full_like(circle_angles, r)
        ax.plot(circle_angles, inner_circle_r, color='lightgray', linewidth=0.5, alpha=0.7, zorder=11)

    # Add radial grid lines
    for angle in angles[:-1]:  # Don't include the duplicate last angle
        ax.plot([angle, angle], [0, 1.0], color='lightgray', linewidth=0.5, alpha=0.7, zorder=11)

    # Add tick labels for the inner plot - positioned at "Reference Coverage" axis
    # "Reference Coverage" is at index 4 in metrics_to_plot (ARXIV Essential citation coverage)
    ref_cov_angle = angles[4]  # Get the angle for "Reference Coverage" axis
    for i, r in enumerate([0.2, 0.4, 0.6, 0.8]):
        ax.text(ref_cov_angle, r, f'{r}', ha='center', va='bottom', fontsize=24, zorder=12)  # Much larger font

    # Plot the spider charts in the inner area (foreground layer)
    for model_data_item in model_data:
        values_plot = model_data_item['values'] + model_data_item['values'][:1]
        ax.plot(angles, values_plot, linewidth=3, linestyle='solid',
                color=model_data_item['color'], label=model_data_item['name'], zorder=13)
        ax.fill(angles, values_plot, alpha=0.12, color=model_data_item['color'], zorder=12)

    # Set the metric labels on the inner side of the circle
    ax.set_thetagrids(np.degrees(angles[:-1]), [])  # Remove default labels

    # Add custom metric labels positioned inside the circle - with higher zorder to appear above arcs
    label_radius = 1.11  # Position labels further outside the main circle
    for i, (angle, label) in enumerate(zip(angles[:-1], labels)):
        ax.text(angle, label_radius, label,
                ha='center', va='center', fontsize=26, fontweight='normal',
                zorder=25)  # Much higher zorder to appear above arcs

# Create global color mapping for consistency across all plots
all_models_set = set()
for group_name, group_config in model_groups.items():
    models = get_models_for_group(group_config['exclude'])
    all_models_set.update(models)

# Create custom ordered list for legend
legend_order = [
    'Search AI (Llama-4-Scout)',
    'Search AI (Claude)',
    'Search AI (Gemini)',
    'OpenAI DeepResearch',
    'STORM (Llama-4)',
    'OpenScholar (Llama-4)',
    'DeepScholar (Llama-4)',
    'DeepScholar (GPT4.1 + Gemini)',
    'DeepResearcher (Llama-4)',
    'DeepScholar (GPT4.1 + Claude)',
    'DeepScholar (GPT4.1 + o3)'
]

# Filter to only include models that actually exist in our data
sorted_models = [model for model in legend_order if model in all_models_set]

# Add any remaining models that weren't in our custom order
remaining_models = [model for model in all_models_set if model not in legend_order]
sorted_models.extend(sorted(remaining_models))

# Create global color mapping - this ensures consistent colors across all plots
global_color_map = {}
for i, model_name in enumerate(sorted_models):
    global_color_map[model_name] = colorblind_friendly_colors[i % len(colorblind_friendly_colors)]

def print_models_in_group(group_name, group_config):
    """Print which models are included in a specific group"""
    print(f"\n{'='*50}")
    print(f"PLOT: {group_config['title']}")
    print(f"{'='*50}")
    
    models = get_models_for_group(group_config['exclude'])
    print(f"Total models in this plot: {len(models)}")
    print(f"Models: {models}")
    print(f"{'='*50}\n")

def generate_individual_plots():
    """Generate individual spider plots"""
    print("\n" + "="*80)
    print("GENERATING INDIVIDUAL PLOTS")
    print("="*80)
    
    # Create output directory if it doesn't exist
    output_dir = 'eval/plots/spiderplot_final'
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate individual plots
    for group_name, group_config in model_groups.items():
        print_models_in_group(group_name, group_config)
        
        # Create a new figure for each plot
        fig, ax = plt.subplots(figsize=(16, 16), subplot_kw=dict(projection='polar'))
        
        # Get models and data for this group
        models = get_models_for_group(group_config['exclude'])
        model_data = get_model_data(models, metrics_to_plot, global_color_map)
        
        # Create the spider plot
        create_individual_spider_plot(ax, model_data, group_config['title'], metrics_to_plot, individual_metric_renames)
        
        # Adjust layout
        plt.tight_layout()
        
        # Save the individual plot
        filename = f"indi_spider_plot_{group_config['filename']}.pdf"
        filepath = os.path.join(output_dir, filename)
        plt.savefig(filepath, format='pdf', bbox_inches='tight', dpi=300)
        print(f"Saved individual plot as: {filepath}")
        
        # Show the plot
        plt.show()
        
        # Close the figure to free memory
        plt.close()
    
    print("\nAll individual plots have been saved!")

def generate_combined_plot():
    """Generate combined spider plot with legend"""
    print("\n" + "="*80)
    print("GENERATING COMBINED PLOT WITH LEGEND")
    print("="*80)
    
    # Create output directory if it doesn't exist
    output_dir = 'eval/plots/spiderplot_final'
    os.makedirs(output_dir, exist_ok=True)
    
    # Create the combined figure - much bigger
    fig = plt.figure(figsize=(48, 40))

    # Create a grid for the spider plots - 2 plots layout with minimal spacing
    # Use 2 columns for side-by-side layout
    gs = fig.add_gridspec(2, 2, height_ratios=[0.2, 1], width_ratios=[1, 1], 
                          hspace=0.05, wspace=0.05)

    # Create the shared legend at the top
    legend_ax = fig.add_subplot(gs[0, :])
    legend_ax.axis('off')

        # Define subgroups with their indices (updated for 2-plot layout)
    subgroups = [

                {'indices': [ 7,8,9, 0], 'title': 'Search AI Systems'},
        {'indices': [6,5,2,], 'title': 'Academic Systems'},  
                {'indices': [4,10,11,3], 'title': 'DeepScholar Variants'},
        {'indices': [1], 'title': 'Commercial System'}]


    # Create grouped legend - centered with gaps
    y_positions = [0.9, 0.7, 0.5, 0.3]  # Vertical positions for groups with much bigger gaps

    for group_idx, group_info in enumerate(subgroups):
        y_pos = y_positions[group_idx]
        
        # Create legend handles for this group
        group_handles = []
        group_labels = []
        
        for idx in group_info['indices']:
            if idx < len(sorted_models):
                model_name = sorted_models[idx]
                color = global_color_map[model_name]
                handle = Line2D([0], [0], color=color, linewidth=6, label=model_name)  # Thicker lines
                group_handles.append(handle)
                group_labels.append(model_name)
        
        # Create legend for this group with box - centered
        if group_handles:
            # Calculate number of columns based on group size
            ncols = min(len(group_handles), 4)
            
            group_legend = legend_ax.legend(group_handles, group_labels,
                                          loc='center', frameon=True, fontsize=38,  # Much larger font
                                          bbox_to_anchor=(0.5, y_pos-0.1),  # Center horizontally
                                          ncol=ncols, fancybox=False, shadow=False,
                                          facecolor='white', edgecolor='black')  # White background
            
            # Add the legend to the axis (matplotlib can handle multiple legends)
            legend_ax.add_artist(group_legend)

    # Create the two spider plots
    plot_positions = [
        (1, 0, 'llama_only'),    # Second row, left position
        (1, 1, 'non_llama'),     # Second row, right position
    ]

    # Print models for each group before creating plots
    for group_name, group_config in model_groups.items():
        print_models_in_group(group_name, group_config)

    for i, (row, col, group_name) in enumerate(plot_positions):
        # Handle single column positions
        ax = fig.add_subplot(gs[row, col], projection='polar')
        
        group_config = model_groups[group_name]
        models = get_models_for_group(group_config['exclude'])
        model_data = get_model_data(models, metrics_to_plot, global_color_map)
        create_combined_spider_plot(ax, model_data, group_config['title'], metrics_to_plot, combined_metric_renames)
        
        # Add title below the plot with (a), (b) labels
        plot_letter = ['(a)', '(b)'][i]
        ax.text(0.5, -0.12, f"{plot_letter} {group_config['title']}", 
                ha='center', va='center', fontsize=32, fontweight='bold',
                transform=ax.transAxes)

    plt.tight_layout()
    plt.subplots_adjust(top=0.95, bottom=0.02, left=0.05, right=0.95)

    # Save the combined plot
    filename = "spider_plot_combined_with_legend.pdf"
    filepath = os.path.join(output_dir, filename)
    plt.savefig(filepath, format='pdf', bbox_inches='tight', dpi=300)
    print(f"\nSaved combined plot as: {filepath}")
    plt.show()

def main():
    """Main function to generate both individual and combined plots"""
    print("Spider Plot Generator - Unified Script (2 Plots)")
    print("=" * 50)
    
    # Generate individual plots
    generate_individual_plots()
    
    # Generate combined plot
    generate_combined_plot()
    
    print("\n" + "="*80)
    print("ALL PLOTS GENERATED SUCCESSFULLY!")
    print("="*80)

if __name__ == "__main__":
    main()
