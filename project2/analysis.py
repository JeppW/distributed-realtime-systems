import json
import os
import math

DIRECTORY = "test_case_1"

def load_json(filename):
    with open(os.path.join(DIRECTORY, filename), 'r') as f:
        return json.load(f)

def tx_time(size_bytes, bw_mbps):
    """Calculates transmission time in microseconds."""
    return (size_bytes * 8.0) / bw_mbps

def get_link_bw(src, dst, topology):
    """Finds the specific bandwidth for a link, falling back to default."""
    default_bw = topology.get('default_bandwidth_mbps', 100)
    for link in topology.get('links', []):
        if (link.get('source') == src and link.get('destination') == dst) or \
           (link.get('source') == dst and link.get('destination') == src):
            return link.get('bandwidth_mbps', default_bw)
    return default_bw

# =========================================================
# 1. STRICT PRIORITY (SP) LINK CALCULATOR
# =========================================================
def calculate_sp_link_wcrt(stream, competitors, bw_mbps):
    # Base transmission time
    C_i = tx_time(stream['size'], bw_mbps)

    # LPI: Max transmission time of strictly lower priority streams
    lower = [tx_time(c['size'], bw_mbps) for c in competitors if c['PCP'] < stream['PCP']]
    LPI = max(lower) if lower else 0.0

    # SPI: Sum of transmission times for same priority frames (FIFO)
    same = [tx_time(c['size'], bw_mbps) for c in competitors if c['PCP'] == stream['PCP'] and c['id'] != stream['id']]
    SPI = sum(same)

    # HPI: Iterative RTA for higher priority streams preempting the queue
    higher = [c for c in competitors if c['PCP'] > stream['PCP']]
    HPI = 0.0
    w = LPI + SPI 
    
    while True:
        # How many higher priority frames arrive during the waiting window 'w'?
        HPI_new = sum(math.ceil((w + 1e-6) / h['period']) * tx_time(h['size'], bw_mbps) for h in higher)
        w_new = LPI + SPI + HPI_new
        
        if w_new == w or w_new > stream['period']:
            HPI = HPI_new
            break
        w = w_new

    # WCRT = SPI + HPI + LPI + C_i
    return SPI + HPI + LPI + C_i

# =========================================================
# 2. CREDIT BASED SHAPER (CBS) LINK CALCULATOR
# =========================================================
def calculate_cbs_link_wcrt(stream, competitors, bw_mbps, alpha_idle=0.5, alpha_send=0.5):
    # Base transmission time
    C_i = tx_time(stream['size'], bw_mbps)

    # LPI: Max transmission time of strictly lower priority streams
    lower = [tx_time(c['size'], bw_mbps) for c in competitors if c['PCP'] < stream['PCP']]
    LPI = max(lower) if lower else 0.0

    # SPI: Sum of same-priority tx times + credit recovery time
    same = [tx_time(c['size'], bw_mbps) for c in competitors if c['PCP'] == stream['PCP'] and c['id'] != stream['id']]
    SPI = sum(c * (1 + (alpha_send / alpha_idle)) for c in same)

    # HPI: Class A is 0. Class B accumulates Class A's credit during LPI block.
    higher = [tx_time(c['size'], bw_mbps) for c in competitors if c['PCP'] > stream['PCP']]
    HPI = 0.0
    if stream['PCP'] == 1 and higher: # Target is Class B and Class A exists
        HPI = LPI * (alpha_idle / alpha_send) + max(higher)

    # WCRT = SPI + HPI + LPI + C_i
    return SPI + HPI + LPI + C_i

# =========================================================
# 3. MAIN EXECUTION
# =========================================================
def analyze_network():
    topology = load_json('topology.json')['topology']
    streams = {s['id']: s for s in load_json('streams.json')['streams']}
    routes = load_json('routes.json')['routes']
    
    # Map streams to specific edges
    link_occupants = {} 
    stream_paths = {}   
    
    for route in routes:
        s_id = route['flow_id']
        nodes = [hop['node'] for hop in route['paths'][0]]
        edges = list(zip(nodes[:-1], nodes[1:]))
        stream_paths[s_id] = edges
        
        for edge in edges:
            link_occupants.setdefault(edge, []).append(s_id)

    results = {}

    for s_id, stream in streams.items():
        if stream['PCP'] == 0: 
            continue # Skip Best Effort
            
        e2e_cbs, e2e_sp = 0.0, 0.0
        
        # Calculate WCRT compositionally across the path
        for src, dst in stream_paths[s_id]:
            edge = (src, dst)
            competitors = [streams[c] for c in link_occupants[edge]]
            link_bw = get_link_bw(src, dst, topology)
            
            e2e_sp += calculate_sp_link_wcrt(stream, competitors, link_bw)
            e2e_cbs += calculate_cbs_link_wcrt(stream, competitors, link_bw)
            
        results[s_id] = {'SP': round(e2e_sp, 2), 'CBS': round(e2e_cbs, 2)}
        
    # Output formatting
    print(f"{'Stream ID':<10} | {'SP WCRT':<10} | {'CBS WCRT':<10}")
    print("-" * 38)
    for s_id, vals in sorted(results.items()):
        print(f"{s_id:<10} | {str(vals['SP']).replace('.', ','):<10} | {str(vals['CBS']).replace('.', ','):<10}")

if __name__ == "__main__":
    analyze_network()