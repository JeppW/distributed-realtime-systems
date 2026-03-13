import os
import json
import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

TEST_CASE_DIR = "test_case_1" # Or "test_case_1", "test_case_2", etc.


def load_json(filepath):
    """Utility function to load JSON data from a file."""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Could not find {filepath}.")
        return None

def build_tsn_graph(topology_data, streams_data, routes_data):
    G = nx.DiGraph()
    topo = topology_data.get('topology', {})
    
    # 1. Add Nodes
    for es in topo.get('end_systems', []):
        G.add_node(es['id'], node_type='ES', label=f"End System\n{es['id']}")
    for sw in topo.get('switches', []):
        G.add_node(sw['id'], node_type='SW', label=f"Switch\n{sw['id']}")

    # 2. Add Physical Links
    for link in topo.get('links', []):
        G.add_edge(link['source'], link['destination'], 
                   link_id=link['id'], 
                   bw=link['bandwidth_mbps'],
                   queues={2: [], 1: [], 0: []})

    # 3. Map Streams to Queues
    stream_info = {s['id']: s for s in streams_data.get('streams', [])}

    for route in routes_data.get('routes', []):
        flow_id = route['flow_id']
        paths = route.get('paths', [])
        if not paths: continue
            
        node_sequence = [hop['node'] for hop in paths[0]]
        pcp = stream_info[flow_id]['PCP'] if flow_id in stream_info else 0
        queue_idx = pcp if pcp in [0, 1, 2] else 0

        for i in range(len(node_sequence) - 1):
            u, v = node_sequence[i], node_sequence[i+1]
            if G.has_edge(u, v):
                G[u][v]['queues'][queue_idx].append(f"F{flow_id}")

    return G

def draw_queue_boxes(ax, x, y, queues, link_id, bw, source, dest):
    """Draws a stacked queue structure at exact coordinates."""
    box_width = 0.12
    box_height = 0.04
    
    q_colors = {2: '#ff9999', 1: '#ffff99', 0: '#e6e6e6'}
    q_labels = {2: 'Q2', 1: 'Q1', 0: 'Q0'}

    title_text = f"{link_id} ({bw}Mbps)\n{source} -> {dest}"
    ax.text(x, y + (box_height * 2.5), title_text, ha='center', va='center', 
            fontsize=8, fontweight='bold', bbox=dict(facecolor='white', edgecolor='gray', boxstyle='round,pad=0.2'), zorder=10)

    for i, pcp in enumerate([2, 1, 0]):
        y_offset = y + (1 - i) * box_height
        rect = patches.Rectangle((x - box_width/2, y_offset - box_height/2), 
                                 box_width, box_height, 
                                 linewidth=1, edgecolor='black', facecolor=q_colors[pcp], zorder=4)
        ax.add_patch(rect)
        
        streams = queues[pcp]
        content = ", ".join(streams) if streams else "idle"
        display_text = f"{q_labels[pcp]}: [{content}]"
        
        ax.text(x, y_offset, display_text, ha='center', va='center', fontsize=7, zorder=10)

def visualize_network_with_queues(G, test_case_name):
    fig, ax = plt.subplots(figsize=(18, 12))
    pos = nx.spring_layout(G, seed=42, k=2.5)
    
    es_nodes = [n for n, d in G.nodes(data=True) if d.get('node_type') == 'ES']
    sw_nodes = [n for n, d in G.nodes(data=True) if d.get('node_type') == 'SW']

    # INCREASED node_size to comfortably fit the text
    es_col = nx.draw_networkx_nodes(G, pos, nodelist=es_nodes, node_color='lightgreen', node_shape='o', node_size=4500, edgecolors='black')
    if es_col: es_col.set_zorder(5)
    
    sw_col = nx.draw_networkx_nodes(G, pos, nodelist=sw_nodes, node_color='skyblue', node_shape='s', node_size=4500, edgecolors='black')
    if sw_col: sw_col.set_zorder(5)
    
    # REDUCED font_size slightly to ensure it stays within borders
    node_labels = {n: d['label'] for n, d in G.nodes(data=True)}
    drawn_labels = nx.draw_networkx_labels(G, pos, labels=node_labels, font_size=9, font_weight='bold')
    for _, text_obj in drawn_labels.items():
        text_obj.set_zorder(15)

    # Set to keep track of which idle edges we've already drawn
    drawn_idle_edges = set()

    for u, v, data in G.edges(data=True):
        u_pos, v_pos = pos[u], pos[v]
        dx, dy = v_pos[0] - u_pos[0], v_pos[1] - u_pos[1]
        dist = np.hypot(dx, dy)
        if dist == 0: continue
            
        ox, oy = -dy/dist, dx/dist
        
        mid_x = u_pos[0] + 0.35 * dx + 0.15 * ox
        mid_y = u_pos[1] + 0.35 * dy + 0.15 * oy
        
        has_traffic = any(len(flows) > 0 for flows in data['queues'].values())
        
        if has_traffic:
            arr_in = patches.FancyArrowPatch(tuple(u_pos), (mid_x, mid_y), 
                                             arrowstyle='-|>', mutation_scale=15, 
                                             shrinkA=30, shrinkB=30, color='#333333', linewidth=1.5, zorder=2)
            arr_out = patches.FancyArrowPatch((mid_x, mid_y), tuple(v_pos), 
                                              arrowstyle='-|>', mutation_scale=20, 
                                              shrinkA=30, shrinkB=30, color='#333333', linewidth=1.5, zorder=2)
            ax.add_patch(arr_in)
            ax.add_patch(arr_out)
            
            draw_queue_boxes(ax, mid_x, mid_y, data['queues'], data['link_id'], data['bw'], u, v)
        else:
            # Check if the reverse direction is carrying traffic
            reverse_has_traffic = G.has_edge(v, u) and any(len(flows) > 0 for flows in G[v][u]['queues'].values())
            
            # Draw the idle link ONLY IF the reverse path doesn't have traffic AND we haven't drawn it yet
            if not reverse_has_traffic and (v, u) not in drawn_idle_edges:
                drawn_idle_edges.add((u, v))
                
                # Check if it's bidirectional so we can use a double-sided arrow
                is_bidirectional = G.has_edge(v, u)
                arrow_style = '<|-|>' if is_bidirectional else '-|>'
                
                # Removed 'connectionstyle' to make it a clean straight line rather than an arc
                arr_idle = patches.FancyArrowPatch(tuple(u_pos), tuple(v_pos), 
                                                   arrowstyle=arrow_style, mutation_scale=15, 
                                                   shrinkA=30, shrinkB=30, color='lightgray', 
                                                   linestyle='--', linewidth=1.5, zorder=1)
                ax.add_patch(arr_idle)

    legend_elements = [
        patches.Patch(color='lightgreen', label='End System (ES)'),
        patches.Patch(color='skyblue', label='Switch (SW)'),
        patches.Patch(color='#ff9999', label='Queue 2 (PCP 2)'),
        patches.Patch(color='#ffff99', label='Queue 1 (PCP 1)'),
        patches.Patch(color='#e6e6e6', label='Queue 0 (Best Effort)'),
        plt.Line2D([0], [0], color='lightgray', linestyle='--', linewidth=2, label='Idle Link')
    ]
    ax.legend(handles=legend_elements, loc='upper left', fontsize=11, title="Network Architecture")

    plt.title(f"TSN Egress Port Queue Visualization - {test_case_name}", fontsize=18, fontweight='bold')
    plt.axis('off')
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    print(f"Loading files from directory: {TEST_CASE_DIR}")

    topo_path = os.path.join(TEST_CASE_DIR, 'topology.json')
    streams_path = os.path.join(TEST_CASE_DIR, 'streams.json')
    routes_path = os.path.join(TEST_CASE_DIR, 'routes.json')
    
    topology_data = load_json(topo_path)
    streams_data = load_json(streams_path)
    routes_data = load_json(routes_path)

    if topology_data and streams_data and routes_data:
        tsn_graph = build_tsn_graph(topology_data, streams_data, routes_data)
        visualize_network_with_queues(tsn_graph, TEST_CASE_DIR)