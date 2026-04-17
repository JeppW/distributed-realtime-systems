import json
import os
import heapq

DIRECTORY = "test_case_starve2" # Update this path if your JSON files are elsewhere

def load_json(filename):
    with open(os.path.join(DIRECTORY, filename), 'r') as f:
        return json.load(f)

# =========================================================
# 1. SIMULATION ENTITIES
# =========================================================

PRIO_GENERATE = 0
PRIO_ARRIVE = 1
PRIO_TX_END = 2

class Frame:
    def __init__(self, stream_id, pcp, size_bytes, gen_time, path):
        self.stream_id = stream_id
        self.pcp = pcp
        self.size = size_bytes
        self.gen_time = gen_time
        self.path = path
        self.hop_index = 0

class Port:
    def __init__(self, port_id, bandwidth_mbps, delay):
        self.id = port_id
        self.bandwidth = bandwidth_mbps
        self.delay = delay
        
        # Priority queues: 2 (AVB A), 1 (AVB B), 0 (Best Effort)
        self.queues = {2: [], 1: [], 0: []}
        
        # State
        self.is_transmitting = False
        self.tx_pcp = None
        
        # CBS properties (idleSlope and sendingSlope = 0.5 as per README)
        self.credits = {2: 0.0, 1: 0.0}
        self.idle_slope = 0.5
        self.sending_slope = 0.5
        self.last_update_time = 0.0

    def update_credits(self, current_time):
        dt = current_time - self.last_update_time
        if dt <= 0:
            return

        for p in [2, 1]:
            is_tx = (self.is_transmitting and self.tx_pcp == p)
            is_waiting = len(self.queues[p]) > 0

            if is_tx:
                # Transmitting: decrease credit
                self.credits[p] -= self.sending_slope * dt
            elif is_waiting:
                # Not transmitting but frames waiting: accumulate credit
                self.credits[p] += self.idle_slope * dt
            else:
                # Idle: Queue empty, not transmitting
                if self.credits[p] > 0:
                    self.credits[p] = 0.0 # Positive credit resets instantly
                elif self.credits[p] < 0:
                    self.credits[p] = min(0.0, self.credits[p] + self.idle_slope * dt) # Recovers to 0
                    
        self.last_update_time = current_time

# =========================================================
# 2. DISCRETE-EVENT SIMULATOR CORE
# =========================================================
class Simulator:
    def __init__(self, mode, topology_links, streams):
        self.mode = mode 
        self.current_time = 0.0
        self.events = []
        self.event_counter = 0 
        
        self.ports = {}
        for link in topology_links:
            pid = (link['source'], link['sourcePort'])
            self.ports[pid] = Port(pid, link.get('bandwidth_mbps', 100), link.get('delay', 0.0))
            
        self.streams = streams
        self.observed_delays = {s['id']: [] for s in streams}

    # NEW: Added event_prio to guarantee mathematical ordering of simultaneous events
    def schedule(self, time, event_prio, event_type, payload):
        heapq.heappush(self.events, (time, event_prio, self.event_counter, event_type, payload))
        self.event_counter += 1

    def run(self, max_time):
        for stream in self.streams:
            self.schedule(0.0, PRIO_GENERATE, 'GENERATE', {'stream': stream, 'gen_time': 0.0})

        while self.events:
            event_time, event_prio, _, event_type, payload = heapq.heappop(self.events)
            
            if event_time > max_time:
                break
                
            self.current_time = event_time
            
            if event_type == 'GENERATE':
                self.handle_generate(payload)
            elif event_type == 'ARRIVE':
                self.handle_arrive(payload)
            elif event_type == 'TX_END':
                self.handle_tx_end(payload)
                
        return {s_id: max(delays) if delays else -1.0 for s_id, delays in self.observed_delays.items()}

    def handle_generate(self, payload):
        stream = payload['stream']
        gen_time = payload['gen_time']
        frame = Frame(stream['id'], stream['PCP'], stream['size'], gen_time, stream['path'])
        
        next_gen = gen_time + stream['period']
        self.schedule(next_gen, PRIO_GENERATE, 'GENERATE', {'stream': stream, 'gen_time': next_gen})
        self.schedule(gen_time, PRIO_ARRIVE, 'ARRIVE', {'frame': frame, 'port_id': frame.path[0]})

    def handle_arrive(self, payload):
        frame = payload['frame']
        port_id = payload['port_id']

        if frame.hop_index == len(frame.path) - 1:
            delay = self.current_time - frame.gen_time
            self.observed_delays[frame.stream_id].append(delay)
            return

        port = self.ports[port_id]
        port.update_credits(self.current_time)
        port.queues[frame.pcp].append(frame)
        self.trigger_port(port)

    def trigger_port(self, port):
        if port.is_transmitting:
            return

        port.update_credits(self.current_time)
        selected_frame = None
        
        if self.mode == 'SP':
            for pcp in [2, 1, 0]:
                if port.queues[pcp]:
                    selected_frame = port.queues[pcp].pop(0)
                    break
        elif self.mode == 'CBS':
            if port.queues[2] and port.credits[2] >= 0:
                selected_frame = port.queues[2].pop(0)
            elif port.queues[1] and port.credits[1] >= 0:
                selected_frame = port.queues[1].pop(0)
            elif port.queues[0]:
                selected_frame = port.queues[0].pop(0)

        if selected_frame:
            port.is_transmitting = True
            port.tx_pcp = selected_frame.pcp
            tx_time = (selected_frame.size * 8.0) / port.bandwidth
            self.schedule(self.current_time + tx_time, PRIO_TX_END, 'TX_END', {
                'frame': selected_frame,
                'port_id': port.id
            })

    def handle_tx_end(self, payload):
        frame = payload['frame']
        port = self.ports[payload['port_id']]

        port.update_credits(self.current_time)
        port.is_transmitting = False
        port.tx_pcp = None

        frame.hop_index += 1
        next_port_id = frame.path[frame.hop_index]
        arrival_time = self.current_time + port.delay
        
        self.schedule(arrival_time, PRIO_ARRIVE, 'ARRIVE', {'frame': frame, 'port_id': next_port_id})
        self.trigger_port(port)

# =========================================================
# 3. MAIN EXECUTION & DATA PARSING
# =========================================================
def main():
    # 1. Load data
    topology = load_json('topology.json')['topology']
    raw_streams = load_json('streams.json')['streams']
    routes = load_json('routes.json')['routes']

    # 2. Parse routes to a dictionary for easy mapping
    routes_map = {}
    for r in routes:
        path = [(hop['node'], hop['port']) for hop in r['paths'][0]]
        routes_map[r['flow_id']] = path

    # 3. Compile Streams
    streams = []
    for s in raw_streams:
        streams.append({
            'id': s['id'],
            'PCP': s['PCP'],
            'size': s['size'],
            'period': s['period'],
            'path': routes_map[s['id']]
        })

    # 4. Run simulations
    MAX_SIM_TIME = 100000.0  # Run for 100ms to allow traffic to stack up and hit worst-case
    print("Running SP Simulation...")
    sim_sp = Simulator('SP', topology['links'], streams)
    sp_results = sim_sp.run(MAX_SIM_TIME)

    print("Running CBS Simulation...")
    sim_cbs = Simulator('CBS', topology['links'], streams)
    cbs_results = sim_cbs.run(MAX_SIM_TIME)

    print(f"{'Stream ID':<10} | {'Size (B)':<10} | {'PCP':<5} | {'Period (us)':<12} | {'SP WCD (us)':<12} | {'CBS WCD (us)':<12}")
    print("-" * 80)
    
    for s in streams:
        if s['PCP'] == 0: continue # Optional: skip best effort
        
        s_id = s['id']
        sp_str = f"{sp_results[s_id]:.2f}"
        cbs_str = f"{cbs_results[s_id]:.2f}"
        
        print(f"{s_id:<10} | {s['size']:<10} | {s['PCP']:<5} | {s['period']:<12} | {sp_str:<12} | {cbs_str:<12}")
        

if __name__ == "__main__":
    main()