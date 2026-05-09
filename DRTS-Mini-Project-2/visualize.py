import os
import json
import argparse
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch


def parse_args():
    parser = argparse.ArgumentParser(description="Visualize TSN Network Topology.")
    parser.add_argument("--TestCase", type=str, default="test_case_starvation",
                        help="Name of the test case folder inside TestCases/")
    parser.add_argument("--save", action="store_true",
                        help="Save the figure as a PNG instead of showing it")
    return parser.parse_args()


def load_json(filepath):
    with open(filepath, 'r') as f:
        return json.load(f)


def infer_left_to_right_order(topology):
    """
    Figures out the left-to-right node order by finding the
    source node (no incoming links) and following the chain.
    Only considers one direction of bidirectional links.
    """
    nodes = ([n['id'] for n in topology.get('end_systems', [])] +
             [n['id'] for n in topology.get('switches', [])])

    # Build adjacency ignoring reverse links (keep only unique src->dst pairs)
    links = topology.get('links', [])
    seen_pairs = set()
    edges = []
    for link in links:
        src, dst = link['source'], link['destination']
        pair = tuple(sorted([src, dst]))
        if pair not in seen_pairs:
            seen_pairs.add(pair)
            edges.append((src, dst))

    # Find node with no incoming edges = leftmost
    incoming = {n: 0 for n in nodes}
    for src, dst in edges:
        incoming[dst] = incoming.get(dst, 0) + 1

    start = min(incoming, key=incoming.get)

    # Follow the chain from start
    order = [start]
    visited = {start}
    adj = {src: dst for src, dst in edges}
    adj_rev = {dst: src for src, dst in edges}

    current = start
    while True:
        next_node = adj.get(current)
        if next_node and next_node not in visited:
            order.append(next_node)
            visited.add(next_node)
            current = next_node
        else:
            break

    # Add any remaining nodes not in chain
    for n in nodes:
        if n not in visited:
            order.append(n)

    return order


def assign_positions(topology):
    order = infer_left_to_right_order(topology)
    positions = {}
    n = len(order)
    for i, node_id in enumerate(order):
        x = i * (6.0 / max(n - 1, 1)) - 3.0
        positions[node_id] = (x, 0.0)
    return positions


def draw_node(ax, x, y, label, node_type):
    color = '#90EE90' if node_type == 'ES' else '#87CEEB'
    box = mpatches.FancyBboxPatch(
        (x - 0.35, y - 0.18), 0.70, 0.36,
        boxstyle="round,pad=0.02",
        linewidth=2,
        edgecolor='black',
        facecolor=color,
        zorder=5
    )
    ax.add_patch(box)
    ax.text(x, y, label, ha='center', va='center',
            fontsize=12, fontweight='bold', zorder=6)


def draw_link(ax, x1, y1, x2, y2, bw, delay, offset=0.05):
    """Draw a single directed arrow with label."""
    ax.annotate(
        "",
        xy=(x2, y2 + offset),
        xytext=(x1, y1 + offset),
        arrowprops=dict(
            arrowstyle="-|>",
            color='#333333',
            lw=1.8,
            mutation_scale=18,
            shrinkA=28,
            shrinkB=28,
        ),
        zorder=3
    )
    mx = (x1 + x2) / 2
    my = (y1 + y2) / 2 + offset + 0.10
    ax.text(mx, my, f"{bw} Mbps  |  {delay} μs",
            ha='center', va='center', fontsize=9,
            bbox=dict(facecolor='white', edgecolor='none', alpha=0.85, pad=2),
            zorder=7)


def visualize_topology(test_case_name, save=False):
    directory = os.path.join("TestCases", test_case_name)
    topo_path = os.path.join(directory, 'topology.json')

    if not os.path.exists(topo_path):
        print(f"Error: Could not find {topo_path}")
        return

    data     = load_json(topo_path)
    topology = data['topology']
    pos      = assign_positions(topology)

    fig, ax = plt.subplots(figsize=(14, 4))
    ax.set_xlim(-4.0, 4.0)
    ax.set_ylim(-1.2, 1.2)
    ax.axis('off')
    plt.title(f"TSN Network Topology — {test_case_name}",
              fontsize=14, fontweight='bold', pad=12)

    # Draw nodes
    for node_id, (x, y) in pos.items():
        node_type = 'ES' if node_id.startswith('ES') else 'SW'
        draw_node(ax, x, y, node_id, node_type)

    # Group bidirectional link pairs
    link_pairs = {}
    for link in topology.get('links', []):
        src, dst = link['source'], link['destination']
        key = tuple(sorted([src, dst]))
        link_pairs.setdefault(key, []).append(link)

    for key, links in link_pairs.items():
        offsets = [0.08, -0.08] if len(links) == 2 else [0.0]
        for i, link in enumerate(links):
            src, dst = link['source'], link['destination']
            if src not in pos or dst not in pos:
                continue
            x1, y1 = pos[src]
            x2, y2 = pos[dst]
            bw    = link.get('bandwidth_mbps', topology.get('default_bandwidth_mbps', 100))
            delay = round(link.get('delay', 0), 3)
            draw_link(ax, x1, y1, x2, y2, bw, delay, offset=offsets[i])

    # Legend
    legend_handles = [
        mpatches.Patch(facecolor='#90EE90', edgecolor='black', label='End System (ES)'),
        mpatches.Patch(facecolor='#87CEEB', edgecolor='black', label='Switch (SW)'),
    ]
    ax.legend(handles=legend_handles, loc='lower right', fontsize=10)

    plt.tight_layout()

    if save:
        out_path = f"topology_{test_case_name}.png"
        plt.savefig(out_path, dpi=150, bbox_inches='tight')
        print(f"Saved to {out_path}")
    else:
        plt.show()


def main():
    args = parse_args()
    visualize_topology(args.TestCase, save=args.save)


if __name__ == "__main__":
    main()