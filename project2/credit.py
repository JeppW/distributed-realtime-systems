import matplotlib.pyplot as plt

def visualize_cbs_concept():
    """Generates a timeline graph of a Credit-Based Shaper (CBS) queue."""
    
    # 1. Define the Time and Credit coordinates based on standard IEEE 802.1Qav behavior
    # Scenario: A high-priority frame arrives, but a Best Effort frame is already transmitting.
    
    times = [0, 2, 8, 12, 16, 20]
    
    # Credit values at those specific times
    # t=0 to t=2: Queue is empty, credit is 0.
    # t=2: Frame arrives, but port is blocked. Credit builds at 'idleSlope'.
    # t=8: Port becomes free. Credit has reached a peak. Transmission starts, credit drops at 'sendSlope'.
    # t=12: Frame finishes transmitting. Credit is now negative.
    # t=12 to t=16: Queue is empty. Credit recovers back to 0 at 'idleSlope'.
    credits = [0, 0, 12, -4, 0, 0] 

    # 2. Set up the plot
    plt.figure(figsize=(12, 6))
    
    # Draw the main Credit line
    plt.plot(times, credits, marker='o', markersize=8, linestyle='-', color='#d62728', linewidth=3, label="CBS Credit Level")
    
    # Draw the zero-credit baseline
    plt.axhline(0, color='black', linewidth=1.5, linestyle='--')

    # 3. Highlight the different phases of the CBS cycle
    # Phase A: Waiting (Interference)
    plt.axvspan(2, 8, color='#ff9999', alpha=0.3, label='Frame Waiting (Credit builds at idleSlope)')
    
    # Phase B: Transmitting
    plt.axvspan(8, 12, color='#99ff99', alpha=0.3, label='Transmitting (Credit drops at sendSlope)')
    
    # Phase C: Recovery
    plt.axvspan(12, 16, color='#ffff99', alpha=0.3, label='Recovery (Credit rebuilds to 0)')

    # 4. Add educational annotations
    plt.annotate('Frame Arrives\n(Port Busy)', xy=(2, 0), xytext=(0, 4),
                 arrowprops=dict(facecolor='black', shrink=0.05, width=1.5, headwidth=6))
    
    plt.annotate('Port Free\n(Starts Sending)', xy=(8, 12), xytext=(5, 14),
                 arrowprops=dict(facecolor='black', shrink=0.05, width=1.5, headwidth=6))
    
    plt.annotate('Finished Sending\n(Credit < 0)', xy=(12, -4), xytext=(13, -7),
                 arrowprops=dict(facecolor='black', shrink=0.05, width=1.5, headwidth=6))

    # 5. Formatting
    plt.title("Credit-Based Shaper (CBS) Behavior Over Time", fontsize=16, fontweight='bold')
    plt.xlabel("Time (microseconds)", fontsize=12)
    plt.ylabel("Accumulated Credit (bits)", fontsize=12)
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.legend(loc='upper right', fontsize=10)
    plt.tight_layout()
    
    plt.show()

if __name__ == "__main__":
    visualize_cbs_concept()