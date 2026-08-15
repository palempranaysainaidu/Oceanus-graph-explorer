"""
Generate visual architecture diagrams for the Multi-Agent RAG system
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, ConnectionPatch
import numpy as np

def create_architecture_diagram():
    """Create a comprehensive architecture diagram"""
    
    fig, ax = plt.subplots(1, 1, figsize=(16, 12))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 12)
    ax.axis('off')
    
    # Colors
    colors = {
        'user': '#E3F2FD',
        'orchestration': '#FFF3E0', 
        'agents': '#E8F5E8',
        'data': '#F3E5F5',
        'llm': '#FFF8E1',
        'control': '#FFEBEE'
    }
    
    # Title
    ax.text(8, 11.5, 'Cyclic Multi-Agent RAG Architecture', 
            fontsize=20, fontweight='bold', ha='center')
    
    # User Layer
    user_box = FancyBboxPatch((1, 10), 3, 0.8, 
                              boxstyle="round,pad=0.1", 
                              facecolor=colors['user'], 
                              edgecolor='black', linewidth=2)
    ax.add_patch(user_box)
    ax.text(2.5, 10.4, 'User Query', fontsize=12, fontweight='bold', ha='center')
    
    # Orchestration Layer
    orchestration_box = FancyBboxPatch((6, 10), 4, 0.8,
                                       boxstyle="round,pad=0.1",
                                       facecolor=colors['orchestration'],
                                       edgecolor='black', linewidth=2)
    ax.add_patch(orchestration_box)
    ax.text(8, 10.4, 'LangGraph Orchestration', fontsize=12, fontweight='bold', ha='center')
    
    # Response Layer
    response_box = FancyBboxPatch((12, 10), 3, 0.8,
                                  boxstyle="round,pad=0.1",
                                  facecolor=colors['user'],
                                  edgecolor='black', linewidth=2)
    ax.add_patch(response_box)
    ax.text(13.5, 10.4, 'Final Response', fontsize=12, fontweight='bold', ha='center')
    
    # Agent Layer
    agent_y = 8.5
    agents = [
        ('Measurement\nAgent', 1.5, colors['agents']),
        ('Metadata\nAgent', 4, colors['agents']),
        ('Semantic\nAgent', 6.5, colors['agents']),
        ('Analysis\nAgent', 9, colors['control']),
        ('Refinement\nAgent', 11.5, colors['control']),
        ('Coordinator\nAgent', 14, colors['llm'])
    ]
    
    for name, x, color in agents:
        agent_box = FancyBboxPatch((x-0.7, agent_y-0.4), 1.4, 0.8,
                                   boxstyle="round,pad=0.1",
                                   facecolor=color,
                                   edgecolor='black', linewidth=1)
        ax.add_patch(agent_box)
        ax.text(x, agent_y, name, fontsize=10, fontweight='bold', ha='center', va='center')
    
    # Database Layer
    db_y = 6.5
    databases = [
        ('CockroachDB\n(Time Series)', 1.5, colors['data']),
        ('Neo4j\n(Graph)', 4, colors['data']),
        ('Pinecone\n(Vector)', 6.5, colors['data'])
    ]
    
    for name, x, color in databases:
        db_box = FancyBboxPatch((x-0.8, db_y-0.4), 1.6, 0.8,
                                boxstyle="round,pad=0.1",
                                facecolor=color,
                                edgecolor='black', linewidth=1)
        ax.add_patch(db_box)
        ax.text(x, db_y, name, fontsize=10, fontweight='bold', ha='center', va='center')
    
    # LLM Layer
    llm_box = FancyBboxPatch((9, 6.1), 6, 0.8,
                             boxstyle="round,pad=0.1",
                             facecolor=colors['llm'],
                             edgecolor='black', linewidth=2)
    ax.add_patch(llm_box)
    ax.text(12, 6.5, 'Groq LLM (gpt-oss-120b)', fontsize=12, fontweight='bold', ha='center')
    
    # Cycle Control
    cycle_box = FancyBboxPatch((1, 4), 14, 1.5,
                               boxstyle="round,pad=0.1",
                               facecolor=colors['control'],
                               edgecolor='black', linewidth=2)
    ax.add_patch(cycle_box)
    ax.text(8, 5, 'Cyclic Control System', fontsize=14, fontweight='bold', ha='center')
    ax.text(8, 4.5, 'Quality Assessment → Refinement Decision → Parameter Adjustment', 
            fontsize=11, ha='center')
    ax.text(8, 4.2, 'Max 3 Cycles | Quality Threshold: 0.7 | Adaptive Refinement', 
            fontsize=10, ha='center', style='italic')
    
    # State Management
    state_box = FancyBboxPatch((1, 2.5), 14, 1,
                               boxstyle="round,pad=0.1",
                               facecolor='#F5F5F5',
                               edgecolor='black', linewidth=1)
    ax.add_patch(state_box)
    ax.text(8, 3, 'State Management (TypedDict)', fontsize=12, fontweight='bold', ha='center')
    ax.text(8, 2.7, 'Query | Intent | Results | Quality Score | Cycle Count | Refinements', 
            fontsize=10, ha='center')
    
    # Technology Stack
    tech_box = FancyBboxPatch((1, 0.5), 14, 1.5,
                              boxstyle="round,pad=0.1",
                              facecolor='#FAFAFA',
                              edgecolor='black', linewidth=1)
    ax.add_patch(tech_box)
    ax.text(8, 1.7, 'Technology Stack', fontsize=12, fontweight='bold', ha='center')
    ax.text(4, 1.3, 'Framework: FastAPI', fontsize=10, ha='center')
    ax.text(8, 1.3, 'Language: Python 3.12+', fontsize=10, ha='center')
    ax.text(12, 1.3, 'Orchestration: LangGraph', fontsize=10, ha='center')
    ax.text(4, 0.9, 'Databases: Multi-modal', fontsize=10, ha='center')
    ax.text(8, 0.9, 'LLM: Groq API', fontsize=10, ha='center')
    ax.text(12, 0.9, 'Domain: Oceanography', fontsize=10, ha='center')
    
    # Arrows
    # User to Orchestration
    arrow1 = ConnectionPatch((4, 10.4), (6, 10.4), "data", "data",
                            arrowstyle="->", shrinkA=5, shrinkB=5, 
                            mutation_scale=20, fc="black")
    ax.add_patch(arrow1)
    
    # Orchestration to Response
    arrow2 = ConnectionPatch((10, 10.4), (12, 10.4), "data", "data",
                            arrowstyle="->", shrinkA=5, shrinkB=5,
                            mutation_scale=20, fc="black")
    ax.add_patch(arrow2)
    
    # Orchestration to Agents
    for _, x, _ in agents:
        arrow = ConnectionPatch((8, 10), (x, 8.9), "data", "data",
                               arrowstyle="->", shrinkA=5, shrinkB=5,
                               mutation_scale=15, fc="gray", alpha=0.7)
        ax.add_patch(arrow)
    
    # Agents to Databases
    for i in range(3):
        arrow = ConnectionPatch((agents[i][1], 8.1), (databases[i][1], 6.9), "data", "data",
                               arrowstyle="->", shrinkA=5, shrinkB=5,
                               mutation_scale=15, fc="blue", alpha=0.7)
        ax.add_patch(arrow)
    
    # Cycle arrow
    cycle_arrow = patches.FancyArrowPatch((2, 4.8), (14, 4.8),
                                         connectionstyle="arc3,rad=0.3",
                                         arrowstyle="->", mutation_scale=20,
                                         color="red", linewidth=2)
    ax.add_patch(cycle_arrow)
    ax.text(8, 3.8, '← Refinement Cycle →', fontsize=10, ha='center', color='red', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('backend-chatbot-test/architecture_diagram.png', dpi=300, bbox_inches='tight')
    plt.show()

def create_workflow_diagram():
    """Create a detailed workflow diagram"""
    
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # Title
    ax.text(7, 9.5, 'Cyclic Multi-Agent Workflow', 
            fontsize=18, fontweight='bold', ha='center')
    
    # Workflow steps
    steps = [
        ('User Query', 2, 8.5, '#E3F2FD'),
        ('Parse Intent', 2, 7.5, '#FFF3E0'),
        ('Execute Agents', 2, 6.5, '#E8F5E8'),
        ('Analyze Quality', 2, 5.5, '#FFEBEE'),
        ('Quality < 0.7?', 2, 4.5, '#FFF8E1'),
        ('Refine Intent', 5, 3.5, '#FFEBEE'),
        ('Synthesize', 2, 2.5, '#E8F5E8'),
        ('Final Response', 2, 1.5, '#E3F2FD')
    ]
    
    # Draw workflow boxes
    for step, x, y, color in steps:
        if 'Quality' in step and '?' in step:
            # Diamond for decision
            diamond = patches.RegularPolygon((x, y), 4, radius=0.5, 
                                           orientation=np.pi/4,
                                           facecolor=color, 
                                           edgecolor='black')
            ax.add_patch(diamond)
        else:
            # Rectangle for process
            box = FancyBboxPatch((x-0.7, y-0.3), 1.4, 0.6,
                                boxstyle="round,pad=0.1",
                                facecolor=color,
                                edgecolor='black')
            ax.add_patch(box)
        
        ax.text(x, y, step, fontsize=10, fontweight='bold', 
                ha='center', va='center')
    
    # Agent execution detail
    agents_detail = [
        ('Measurement\nAgent', 7, 7),
        ('Metadata\nAgent', 9, 7),
        ('Semantic\nAgent', 11, 7),
        ('Analysis\nAgent', 7, 5.5),
        ('Refinement\nAgent', 9, 5.5),
        ('Coordinator\nAgent', 11, 5.5)
    ]
    
    for agent, x, y in agents_detail:
        box = FancyBboxPatch((x-0.6, y-0.3), 1.2, 0.6,
                            boxstyle="round,pad=0.1",
                            facecolor='#F0F0F0',
                            edgecolor='gray')
        ax.add_patch(box)
        ax.text(x, y, agent, fontsize=9, ha='center', va='center')
    
    # Arrows
    # Main flow
    for i in range(len(steps)-1):
        if i == 4:  # Skip the decision diamond
            continue
        y1 = steps[i][2] - 0.3
        y2 = steps[i+1][2] + 0.3
        if i == 6:  # Skip synthesis to response for now
            continue
        arrow = ConnectionPatch((2, y1), (2, y2), "data", "data",
                               arrowstyle="->", shrinkA=5, shrinkB=5,
                               mutation_scale=20, fc="black")
        ax.add_patch(arrow)
    
    # Decision arrows
    # Yes arrow (to refine)
    arrow_yes = ConnectionPatch((2.5, 4.5), (4.3, 3.5), "data", "data",
                               arrowstyle="->", shrinkA=5, shrinkB=5,
                               mutation_scale=20, fc="red")
    ax.add_patch(arrow_yes)
    ax.text(3.5, 4, 'YES', fontsize=10, color='red', fontweight='bold')
    
    # No arrow (to synthesize)
    arrow_no = ConnectionPatch((2, 4.2), (2, 2.8), "data", "data",
                              arrowstyle="->", shrinkA=5, shrinkB=5,
                              mutation_scale=20, fc="green")
    ax.add_patch(arrow_no)
    ax.text(1.3, 3.5, 'NO', fontsize=10, color='green', fontweight='bold')
    
    # Cycle back arrow
    cycle_back = patches.FancyArrowPatch((5, 3.2), (2, 6.8),
                                        connectionstyle="arc3,rad=0.5",
                                        arrowstyle="->", mutation_scale=20,
                                        color="red", linewidth=2)
    ax.add_patch(cycle_back)
    
    # Final arrow
    arrow_final = ConnectionPatch((2, 2.2), (2, 1.8), "data", "data",
                                 arrowstyle="->", shrinkA=5, shrinkB=5,
                                 mutation_scale=20, fc="black")
    ax.add_patch(arrow_final)
    
    # Cycle counter
    ax.text(10, 2, 'Cycle Limits:\n• Max 3 cycles\n• Quality threshold: 0.7\n• Adaptive refinement', 
            fontsize=10, bbox=dict(boxstyle="round,pad=0.3", facecolor='#FFFACD'))
    
    plt.tight_layout()
    plt.savefig('backend-chatbot-test/workflow_diagram.png', dpi=300, bbox_inches='tight')
    plt.show()

if __name__ == "__main__":
    print("Generating architecture diagrams...")
    create_architecture_diagram()
    create_workflow_diagram()
    print("Diagrams saved as PNG files!")