"""
Generate IEEE-quality architecture diagrams for XING paper.
Figures 1-3: Architecture topology, Self-healing DAG, Semantic Memory Fabric.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import os

output_dir = 'figures'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)


def set_style():
    plt.rcParams.update({
        'font.family': 'serif',
        'font.serif': ['Times New Roman'],
        'font.size': 8,
        'axes.titlesize': 9,
        'figure.dpi': 300,
        'savefig.dpi': 300,
    })


def fig1_architecture():
    set_style()
    fig, ax = plt.subplots(figsize=(7.0, 4.5))

    layers = [
        ('Adaptive Application Layer', '#2c3e50', 0.85),
        ('Agentic Orchestration Kernel', '#2980b9', 0.80),
        ('Adaptive Cognitive Routing Engine', '#27ae60', 0.78),
        ('Semantic Memory Fabric', '#8e44ad', 0.76),
        ('Distributed Runtime Infrastructure', '#e67e22', 0.72),
    ]

    y_positions = [4.2, 3.3, 2.4, 1.5, 0.6]
    box_w = 5.5
    box_h = 0.55

    for (name, color, alpha), y in zip(layers, y_positions):
        rect = mpatches.FancyBboxPatch(
            (0.75, y), box_w, box_h,
            boxstyle="round,pad=0.08",
            facecolor=color, edgecolor='white', linewidth=1.5, alpha=alpha
        )
        ax.add_patch(rect)
        ax.text(0.75 + box_w / 2, y + box_h / 2, name,
                ha='center', va='center', fontsize=8.5, fontweight='bold',
                color='white')

    # Arrows between layers
    for i in range(len(y_positions) - 1):
        y_mid = y_positions[i] - 0.1
        ax.annotate('', xy=(3.5, y_positions[i + 1] + box_h),
                    xytext=(3.5, y_positions[i]),
                    arrowprops=dict(arrowstyle='->', color='#555555',
                                    lw=1.5, connectionstyle='arc3,rad=0'))

    # Side annotations
    ax.text(0.2, 2.4, 'Multimodal\nStream', fontsize=7, color='#555555',
            ha='center', va='center', rotation=90)
    ax.text(6.8, 2.4, 'Telemetry\nFeedback', fontsize=7, color='#555555',
            ha='center', va='center', rotation=-90)

    # Edge/Cloud split at bottom
    ax.annotate('', xy=(2.5, 0.3), xytext=(2.5, 0.6),
                arrowprops=dict(arrowstyle='->', color='#e67e22', lw=1))
    ax.annotate('', xy=(4.5, 0.3), xytext=(4.5, 0.6),
                arrowprops=dict(arrowstyle='->', color='#e67e22', lw=1))
    ax.text(2.5, 0.15, 'Edge Nodes\n(SLMs)', fontsize=7, ha='center',
            color='#e67e22', fontweight='bold')
    ax.text(4.5, 0.15, 'Cloud Clusters\n(LLMs)', fontsize=7, ha='center',
            color='#e67e22', fontweight='bold')

    # Routing equation annotation
    ax.text(6.9, 3.6, r'$a^* = \arg\max U(a_j, t_i | \mathbf{C})$',
            fontsize=7, color='#27ae60', ha='right',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8))

    ax.set_xlim(0, 7.5)
    ax.set_ylim(0, 5)
    ax.axis('off')
    ax.set_title('XING Global Runtime Architecture', fontsize=10,
                 fontweight='bold', pad=10)
    plt.tight_layout()
    path = os.path.join(output_dir, 'fig1_architecture.pdf')
    plt.savefig(path, bbox_inches='tight')
    plt.close()
    print(f'[+] {path}')


def fig2_self_healing():
    set_style()
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.0))
    phases = [
        ('t0: Nominal', ['N1', 'N2', 'N3'], [('N1', 'N2'), ('N2', 'N3')],
         None, '#1f77b4'),
        ('t1: Fault', ['N1', 'N2!', 'N3'], [('N1', 'N2!'), ('N2!', 'N3')],
         'N2!', '#d62728'),
        ('t2: Recovered', ['N1', 'N2a', 'N2b', 'N3'],
         [('N1', 'N2a'), ('N2a', 'N2b'), ('N2b', 'N3')], None, '#2ca02c'),
    ]

    for ax, (title, nodes, edges, fault_node, color) in zip(axes, phases):
        pos = {n: (i * 1.2, 0.5) for i, n in enumerate(nodes)}
        for node in nodes:
            is_fault = node == fault_node
            fc = '#d62728' if is_fault else color
            ec = '#8b0000' if is_fault else 'white'
            circle = plt.Circle(pos[node], 0.28, facecolor=fc, edgecolor=ec,
                                linewidth=2 if is_fault else 1)
            ax.add_patch(circle)
            label = node.replace('!', '')
            ax.text(pos[node][0], pos[node][1], label, ha='center',
                    va='center', fontsize=7, fontweight='bold', color='white')
            if is_fault:
                ax.text(pos[node][0], pos[node][1] + 0.45, 'FAIL',
                        ha='center', fontsize=5, color='#d62728',
                        fontweight='bold')

        for src, dst in edges:
            ax.annotate('', xy=pos[dst], xytext=pos[src],
                        arrowprops=dict(arrowstyle='->', color='#555555',
                                        lw=1.2, connectionstyle='arc3,rad=0.1'))

        if title == 't2: Recovered':
            ax.text(1.2 * 3 + 0.8, 0.5,
                    r'$\mathrm{Tr}(\mathbf{A}^m)=0$',
                    fontsize=6, color='#2ca02c', ha='center')

        ax.set_xlim(-0.5, 1.2 * len(nodes) - 0.2)
        ax.set_ylim(-0.2, 1.2)
        ax.set_title(title, fontsize=8, fontweight='bold', pad=5)
        ax.axis('off')

    fig.suptitle('Self-Healing DAG Reconfiguration Lifecycle',
                 fontsize=10, fontweight='bold', y=1.08)
    plt.tight_layout()
    path = os.path.join(output_dir, 'fig2_self_healing.pdf')
    plt.savefig(path, bbox_inches='tight')
    plt.close()
    print(f'[+] {path}')


def fig3_memory_fabric():
    set_style()
    fig, ax = plt.subplots(figsize=(7.0, 3.0))

    # Core nodes
    core_nodes = {
        'C1': (0.5, 2.5),
        'C4': (3.5, 2.5),
        'C6': (2.0, 1.5),
    }
    active_nodes = {
        'C2': (1.5, 3.2),
        'C5': (2.5, 3.2),
    }
    decaying_nodes = {
        'C3': (0.5, 0.8),
        'C7': (3.5, 0.8),
    }

    all_nodes = {**core_nodes, **active_nodes, **decaying_nodes}

    edges = [
        ('C1', 'C2', 0.85, '#1f77b4'),
        ('C1', 'C4', 0.72, '#2ca02c'),
        ('C4', 'C6', 0.65, '#27ae60'),
        ('C2', 'C3', 0.41, '#cccccc'),
        ('C4', 'C5', 0.55, '#ff7f0e'),
        ('C6', 'C7', 0.18, '#dddddd'),
        ('C2', 'C6', 0.50, '#9467bd'),
    ]

    for src, dst, weight, color in edges:
        alpha = max(0.2, weight)
        ax.annotate('', xy=all_nodes[dst], xytext=all_nodes[src],
                    arrowprops=dict(arrowstyle='->', color=color,
                                    lw=0.5 + 2.0 * weight, alpha=alpha,
                                    connectionstyle='arc3,rad=0.15'))

    for node_id, (x, y) in all_nodes.items():
        if node_id in core_nodes:
            fc, ec, size = '#1f77b4', 'white', 0.35
        elif node_id in active_nodes:
            fc, ec, size = '#ff7f0e', 'white', 0.28
        else:
            fc, ec, size = '#cccccc', '#999999', 0.22
        circle = plt.Circle((x, y), size, facecolor=fc, edgecolor=ec,
                            linewidth=1.5, alpha=0.85)
        ax.add_patch(circle)
        ax.text(x, y, node_id, ha='center', va='center', fontsize=7,
                fontweight='bold', color='white')

    labels = {'C1': 'Task Goal', 'C4': 'Procedural\nRule', 'C6': 'Memory\nState',
              'C2': 'Context', 'C5': 'Episodic\nTrace',
              'C3': 'Decayed\nTrace', 'C7': 'Historical\nState'}
    for node_id, (x, y) in all_nodes.items():
        ax.text(x, y - 0.5, labels.get(node_id, ''), ha='center',
                fontsize=5.5, color='#555555')

    # Decay formula
    ax.text(7.0, 2.8, r'$\mathbf{C}(\tau) = \mathbf{C}_0 e^{-\lambda \tau} \sigma(M_{\mathrm{sim}})$',
            fontsize=7, color='#555555', ha='right',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#f5f5f5', alpha=0.8))
    ax.text(7.0, 2.2, r'$\Psi_{t+1} = \Psi_t + \gamma (R - \Psi_t)$',
            fontsize=7, color='#555555', ha='right',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#f5f5f5', alpha=0.8))

    ax.set_xlim(-0.5, 7.5)
    ax.set_ylim(0.2, 4.0)
    ax.axis('off')
    ax.set_title('Semantic Memory Fabric: Attributed Knowledge Graph with Context Decay',
                 fontsize=10, fontweight='bold', pad=8)
    plt.tight_layout()
    path = os.path.join(output_dir, 'fig3_memory_fabric.pdf')
    plt.savefig(path, bbox_inches='tight')
    plt.close()
    print(f'[+] {path}')


if __name__ == '__main__':
    fig1_architecture()
    fig2_self_healing()
    fig3_memory_fabric()
    print('All architecture figures generated.')
