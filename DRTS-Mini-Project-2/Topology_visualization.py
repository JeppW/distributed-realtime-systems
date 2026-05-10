import os
import json
import argparse
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


def parse_args():
    parser = argparse.ArgumentParser(description="Visualize TSN Network Topology.")
    parser.add_argument("--TestCase", type=str, default="test_case_1")
    parser.add_argument("--save", action="store_true")
    return parser.parse_args()


def load_json(filepath):
    with open(filepath, 'r') as f:
        return json.load(f)


def get_positions(topology):
    switches    = [n['id'] for n in topology.get('switches', [])]
    end_systems = [n['id'] for n in topology.get('end_systems', [])]
    links       = topology.get('links', [])

    adj = {n: set() for n in switches + end_systems}
    seen = set()
    for link in links:
        src, dst = link['source'], link['destination']
        key = tuple(sorted([src, dst]))
        if key not in seen:
            seen.add(key)
            adj[src].add(dst)
            adj[dst].add(src)

    if len(switches) == 0:
        es = end_systems
        return {es[0]: (-1.5, 0.0), es[1]: (1.5, 0.0)}

    es_connections = {}
    for es in end_systems:
        for neighbor in adj[es]:
            if neighbor in switches:
                es_connections[es] = neighbor

    if len(switches) == 1:
        sw = switches[0]
        return {
            end_systems[0]: (-3.0, 0.0),
            sw:              (0.0, 0.0),
            end_systems[1]: ( 3.0, 0.0),
        }

    if len(switches) == 2:
        sw0, sw1 = switches[0], switches[1]

        es_to_sw = {}
        for es in end_systems:
            for sw in switches:
                if sw in adj[es]:
                    es_to_sw[es] = sw

        connected_switches = list(es_to_sw.values())

        # Both ES connect to same switch → Y shape
        if len(set(connected_switches)) == 1:
            hub_sw   = connected_switches[0]
            other_sw = sw0 if hub_sw == sw1 else sw1
            return {
                end_systems[0]: (-2.5,  0.7),
                end_systems[1]: (-2.5, -0.7),
                hub_sw:         ( 0.0,  0.0),
                other_sw:       ( 2.5,  0.0),
            }

        # ES on opposite ends → straight line
        sw_sw_pair = None
        for link in links:
            if link['source'] in switches and link['destination'] in switches:
                sw_sw_pair = (link['source'], link['destination'])
                break

        if sw_sw_pair:
            left_sw, right_sw = sw_sw_pair
        else:
            left_sw, right_sw = switches[0], switches[1]

        left_es  = next((es for es in end_systems if es_to_sw.get(es) == left_sw), None)
        right_es = next((es for es in end_systems if es_to_sw.get(es) == right_sw), None)

        if not left_es or not right_es:
            all_nodes = end_systems + switches
            return {n: (i * 2.0 - 3.0, 0.0) for i, n in enumerate(all_nodes)}

        return {
            left_es:  (-3.0, 0.0),
            left_sw:  (-1.0, 0.0),
            right_sw: ( 1.0, 0.0),
            right_es: ( 3.0, 0.0),
        }

    all_nodes = end_systems + switches
    return {n: (i * 2.0 - 3.0, 0.0) for i, n in enumerate(all_nodes)}


def draw_node(ax, x, y, label, node_type):
    color = '#90EE90' if node_type == 'ES' else '#87CEEB'
    box = mpatches.FancyBboxPatch(
        (x - 0.30, y - 0.18), 0.60, 0.36,
        boxstyle="round,pad=0.02",
        linewidth=2, edgecolor='black', facecolor=color, zorder=5
    )
    ax.add_patch(box)
    ax.text(x, y, label, ha='center', va='center',
            fontsize=11, fontweight='bold', zorder=6)


def draw_arrow(ax, x1, y1, x2, y2, v_offset, label, label_side=1):
    """Draw arrow with vertical offset. label_side: +1 above, -1 below."""
    ax.annotate(
        "", xy=(x2, y2 + v_offset), xytext=(x1, y1 + v_offset),
        arrowprops=dict(
            arrowstyle="-|>", color='#333333',
            lw=1.8, mutation_scale=16,
            shrinkA=25, shrinkB=25,
        ), zorder=3
    )
    mx = (x1 + x2) / 2
    my = (y1 + y2) / 2 + v_offset + label_side * 0.14
    ax.text(mx, my, label, ha='center', va='center', fontsize=8,
            bbox=dict(facecolor='white', edgecolor='none', alpha=0.9, pad=2),
            zorder=7)


def visualize_topology(test_case_name, save=False):
    directory = os.path.join("TestCases", test_case_name)
    topo_path = os.path.join(directory, 'topology.json')

    if not os.path.exists(topo_path):
        print(f"Error: Could not find {topo_path}")
        return

    data     = load_json(topo_path)
    topology = data['topology']
    pos      = get_positions(topology)

    fig, ax = plt.subplots(figsize=(14, 5))
    ax.set_aspect('equal')
    ax.axis('off')

    xs = [p[0] for p in pos.values()]
    ys = [p[1] for p in pos.values()]
    ax.set_xlim(min(xs) - 1.2, max(xs) + 1.2)
    ax.set_ylim(min(ys) - 1.2, max(ys) + 1.2)

    plt.title(f"TSN Network Topology — {test_case_name}",
              fontsize=14, fontweight='bold', pad=12)

    for node_id, (x, y) in pos.items():
        node_type = 'ES' if node_id.startswith('ES') else 'SW'
        draw_node(ax, x, y, node_id, node_type)

    # Group bidirectional pairs
    link_pairs = {}
    for link in topology.get('links', []):
        key = tuple(sorted([link['source'], link['destination']]))
        link_pairs.setdefault(key, []).append(link)

    for key, links in link_pairs.items():
        # Use larger offsets for Y-shape topology to avoid label overlap
        if len(links) == 2:
            offsets     = [ 0.13, -0.13]
            label_sides = [    1,     -1]
        else:
            offsets     = [0.0]
            label_sides = [  1]

        for i, link in enumerate(links):
            src, dst = link['source'], link['destination']
            if src not in pos or dst not in pos:
                continue
            x1, y1 = pos[src]
            x2, y2 = pos[dst]
            bw    = link.get('bandwidth_mbps', topology.get('default_bandwidth_mbps', 100))
            delay = round(link.get('delay', 0), 3)
            draw_arrow(ax, x1, y1, x2, y2,
                       offsets[i],
                       f"{bw} Mbps | {delay} μs",
                       label_sides[i])

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