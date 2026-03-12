import json
import os

# --- CONFIGURATION ---
DIRECTORY = "test_case_3" # Update this to your folder name

def load_json(filename):
    path = os.path.join(DIRECTORY, filename)
    with open(path, 'r') as f:
        return json.load(f)

def calculate_analysis():
    # 1. Load data
    topology_data = load_json('topology.json')['topology']
    streams_data = load_json('streams.json')['streams']
    routes_data = load_json('routes.json')['routes']

    # Use the default bandwidth for all calculations to match reference results
    base_bw = topology_data.get('default_bandwidth_mbps', 100) 
    
    # 2. Map Streams
    streams = {s['id']: s for s in streams_data}
    
    # 3. Map traffic to links (Determine competitors per link)
    link_occupants = {} # (src, dst) -> list of stream_ids
    stream_paths = {}    # stream_id -> list of (src, dst)
    
    for route in routes_data:
        s_id = route['flow_id']
        path_nodes = [hop['node'] for hop in route['paths'][0]]
        edges = []
        for i in range(len(path_nodes) - 1):
            edge = (path_nodes[i], path_nodes[i+1])
            edges.append(edge)
            if edge not in link_occupants:
                link_occupants[edge] = []
            link_occupants[edge].append(s_id)
        stream_paths[s_id] = edges

    # 4. Analysis Parameters (alpha_ratio = 1.0 for 0.5/0.5 slopes)
    alpha_ratio = 1.0 

    results = {}

    for s_id, stream in streams.items():
        # Only analyze AVB Classes (PCP 1 and 2)
        if stream['PCP'] == 0:
            continue
            
        e2e_wcrt = 0.0
        # compositional analysis: sum WCRT of each link in the path
        for edge in stream_paths[s_id]:
            
            # Helper to calculate transmission time at 100Mbps
            def tx_time(bytes_val):
                return (bytes_val * 8.0) / base_bw

            Ci = tx_time(stream['size'])
            
            # Get all streams sharing this specific egress port
            on_link = link_occupants.get(edge, [])
            
            # --- SPI: Same Priority Interference ---
            # Sum of (Cj * 2) for all other streams of the same priority on this link
            spi_streams = [c for c in on_link if streams[c]['PCP'] == stream['PCP'] and c != s_id]
            spi = sum(tx_time(streams[c]['size']) * (1 + alpha_ratio) for c in spi_streams)
            
            # --- LPI: Lower Priority Interference ---
            # Max transmission time of any stream with strictly lower PCP on this link
            lower_streams = [c for c in on_link if streams[c]['PCP'] < stream['PCP']]
            lpi = max([tx_time(streams[c]['size']) for c in lower_streams]) if lower_streams else 0
            
            # --- HPI: Higher Priority Interference ---
            hpi = 0
            if stream['PCP'] == 1: # Class B
                # Interference from Class A (PCP 2)
                higher_streams = [c for c in on_link if streams[c]['PCP'] > stream['PCP']]
                if higher_streams:
                    max_high_Ci = max([tx_time(streams[c]['size']) for c in higher_streams])
                    # Formula: BlockingDuration * (alpha_idle/alpha_send) + max(C_high)
                    # With 0.5/0.5 slopes, this is LPI + max(C_high)
                    hpi = lpi + max_high_Ci
            
            # Total WCRT for this specific hop
            link_wcrt = Ci + spi + hpi + lpi
            e2e_wcrt += link_wcrt
            
        results[s_id] = round(e2e_wcrt, 2)

    # 5. Output Results
    print(f"{'ID':<5} | {'WCRT'}")
    print("-" * 15)
    for s_id in sorted(results.keys()):
        # Formatting to match CSV style (using comma as decimal separator)
        formatted_val = str(results[s_id]).replace('.', ',')
        print(f"{s_id:<5} | {formatted_val}")

if __name__ == "__main__":
    calculate_analysis()