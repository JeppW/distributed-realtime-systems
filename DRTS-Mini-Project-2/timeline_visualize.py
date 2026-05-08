import matplotlib.pyplot as plt

def create_gantt_chart():
    # Set up the figure with two subplots (one above the other)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    fig.canvas.manager.set_window_title('TSN Scheduling: SP vs CBS')
    
    # Y-axis configuration
    y_ticks = [15, 25, 35]
    y_labels = ['P0 (Best Effort)', 'P1 (Medium)', 'P2 (High)']
    
    # Colors for each priority
    colors = {'P2': '#e74c3c', 'P1': '#f39c12', 'P0': '#3498db'}
    
    # ==========================================
    # Plot 1: Strict Priority (SP) - Starvation
    # ==========================================
    ax1.set_title('Strict Priority (SP) - P0 is Starved', fontsize=12, fontweight='bold')
    
    # Under SP, P2 and P1 dominate the bandwidth. P0 never gets a chance.
    # Data format: [(start_time, duration), ...]
    sp_p2_blocks = [(0, 15), (30, 15), (60, 15)]
    sp_p1_blocks = [(15, 15), (45, 15), (75, 15)]
    sp_p0_blocks = [] # Empty! Starved.
    
    ax1.broken_barh(sp_p2_blocks, (30, 9), facecolors=colors['P2'], edgecolor='black')
    ax1.broken_barh(sp_p1_blocks, (20, 9), facecolors=colors['P1'], edgecolor='black')
    ax1.broken_barh(sp_p0_blocks, (10, 9), facecolors=colors['P0'], edgecolor='black')
    
    # ==========================================
    # Plot 2: Credit-Based Shaper (CBS)
    # ==========================================
    ax2.set_title('Credit-Based Shaper (CBS) - Bandwidth is Shared', fontsize=12, fontweight='bold')
    
    # Under CBS, P2 and P1 run out of credit, forcing pauses where P0 can transmit.
    cbs_p2_blocks = [(0, 10), (30, 10), (60, 10)]
    cbs_p1_blocks = [(10, 10), (40, 10), (70, 10)]
    cbs_p0_blocks = [(20, 10), (50, 10), (80, 10)] # P0 gets slices of time!
    
    ax2.broken_barh(cbs_p2_blocks, (30, 9), facecolors=colors['P2'], edgecolor='black')
    ax2.broken_barh(cbs_p1_blocks, (20, 9), facecolors=colors['P1'], edgecolor='black')
    ax2.broken_barh(cbs_p0_blocks, (10, 9), facecolors=colors['P0'], edgecolor='black')

    # ==========================================
    # Formatting and Styling
    # ==========================================
    for ax in [ax1, ax2]:
        ax.set_ylim(5, 45)
        ax.set_xlim(0, 90)
        ax.set_yticks(y_ticks)
        ax.set_yticklabels(y_labels)
        ax.grid(True, axis='x', linestyle='--', alpha=0.7)
        ax.set_ylabel('Queue Priority')

    ax2.set_xlabel('Time (Synthetic Units)')
    
    # Add a custom legend
    import matplotlib.patches as mpatches
    legend_patches = [
        mpatches.Patch(color=colors['P2'], label='Priority 2 (High)'),
        mpatches.Patch(color=colors['P1'], label='Priority 1 (Medium)'),
        mpatches.Patch(color=colors['P0'], label='Priority 0 (Best Effort)')
    ]
    fig.legend(handles=legend_patches, loc='upper right', bbox_to_anchor=(0.95, 0.95))

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    create_gantt_chart()