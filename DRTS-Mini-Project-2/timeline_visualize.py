import matplotlib.pyplot as plt
import numpy as np

def create_credit_chart():
    pcp2_idle = 0.48
    pcp2_send = 0.52
    pcp1_idle = 0.04
    pcp1_send = 0.96
    frame_tx  = 40

    timeline_pcp2 = [(0, 0.0)]
    timeline_pcp1 = [(0, 0.0)]

    # PCP2 frame 0: t=0 to t=40
    pcp2_c = 0.0 - frame_tx * pcp2_send   # -20.8
    pcp1_c = 0.0 + frame_tx * pcp1_idle   # 1.6
    timeline_pcp2.append((40, pcp2_c))
    timeline_pcp1.append((40, pcp1_c))

    # PCP1 transmits: t=40 to t=80
    pcp2_c = pcp2_c + frame_tx * pcp2_idle  # -1.6
    pcp1_c = pcp1_c - frame_tx * pcp1_send  # -36.8
    timeline_pcp2.append((80, pcp2_c))
    timeline_pcp1.append((80, pcp1_c))

    # Both idle until PCP2 recovers to 0
    t_recover = 80 + abs(pcp2_c) / pcp2_idle  # 83.33
    pcp1_c = pcp1_c + (t_recover - 80) * pcp1_idle
    timeline_pcp2.append((t_recover, 0.0))
    timeline_pcp1.append((t_recover, pcp1_c))

    # PCP2 frames 1-5 back to back
    t = t_recover
    pcp2_c = 0.0
    for i in range(5):
        t_end = t + frame_tx
        pcp2_c_new = pcp2_c - frame_tx * pcp2_send
        pcp1_c_new = pcp1_c + frame_tx * pcp1_idle
        timeline_pcp2.append((t_end, pcp2_c_new))
        timeline_pcp1.append((t_end, pcp1_c_new))
        pcp2_c = pcp2_c_new
        pcp1_c = pcp1_c_new
        t = t_end

        if pcp2_c < 0 and i < 4:
            t_recover2 = t + abs(pcp2_c) / pcp2_idle
            pcp1_c = pcp1_c + (t_recover2 - t) * pcp1_idle
            timeline_pcp2.append((t_recover2, 0.0))
            timeline_pcp1.append((t_recover2, pcp1_c))
            pcp2_c = 0.0
            t = t_recover2

    t2, c2 = zip(*timeline_pcp2)
    t1, c1 = zip(*timeline_pcp1)

    fig, ax = plt.subplots(figsize=(10, 4))


    ax.plot(t2, c2, color='#e74c3c', linewidth=2, label='PCP2 (Class A)')
    ax.plot(t1, c1, color='#f39c12', linewidth=2, label='PCP1 (Class B)')
    ax.axhline(y=0, color='black', linestyle='--', linewidth=1.2, alpha=0.7, label='Credit = 0 threshold')
    ax.axvspan(40, 80, alpha=0.1, color='#f39c12', label='PCP1 transmitting')

    # Fix x axis to end at 320us with ticks every 50us
    ax.set_xlim(0, 320)
    ax.set_xticks(range(0, 321, 50))

    ax.set_xlabel('Time (μs)', fontsize=11)
    ax.set_ylabel('Credit (units)', fontsize=11)
    ax.set_title('CBS Credit Evolution — Starvation Test Case',
                 fontsize=11, fontweight='bold')
    ax.legend(fontsize=9, loc='lower right')
    ax.grid(True, linestyle=':', alpha=0.6)

    plt.tight_layout()
    plt.savefig('credit_evolution_starvation.png', dpi=150, bbox_inches='tight')
    plt.show()

if __name__ == "__main__":
    create_credit_chart()