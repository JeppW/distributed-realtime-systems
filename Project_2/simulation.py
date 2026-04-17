import json
import os
import heapq

# Set this to the directory containing your JSON files
DIRECTORY = "test_case_2"

# =========================================================
# 1. EVENT PRIORITIES (Fixes simultaneous event bugs)
# =========================================================
# If multiple events happen at the exact same microsecond, 
# they MUST be processed in this order to accurately model reality.
PRIO_GENERATE = 0      # 1st: Generate new frames
PRIO_ARRIVE = 1        # 2nd: Frames arrive at queues
PRIO_TX_END = 2        # 3rd: Links free up
PRIO_CREDIT_ZERO = 3   # 4th: Credits recover to 0

# =========================================================
# 2. UTILITY & DATA LOADING
# =========================================================
def load_json(filename):
    """Safely load a JSON file from the target directory."""
    path = os.path.join(DIRECTORY, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Could not find {filename} in {DIRECTORY}")
    with open(path, 'r') as f:
        return json.load(f)

# =========================================================
# 3. SIMULATION ENTITIES
# =========================================================
class Frame:
    """Represents a single instance of a stream traversing the network."""
    def __init__(self, stream_id, pcp, size_bytes, gen_time, path):
        self.stream_id = stream_id
        self.pcp = pcp
        self.size = size_bytes
        self.gen_time = gen_time
        self.path = path
        self.hop_index = 0

class Port:
    """Represents a switch or end-system output port with CBS/SP queues."""
    def __init__(self, port_id, bandwidth_mbps, delay, cbs_slopes):
        self.id = port_id
        self.bandwidth = bandwidth_mbps
        self.delay = delay
        
        # Priority queues: 2 (AVB A), 1 (AVB B), 0 (Best Effort)
        self.queues = {2: [], 1: [], 0: []}
        
        # Transmission state
        self.is_transmitting = False
        self.tx_pcp = None
        
        # CBS properties loaded dynamically from config
        self.credits = {2: 0.0, 1: 0.0}
        self.slopes = cbs_slopes
        self.last_update_time = 0.0

    def update_credits(self, current_time):
        """Updates the credit buckets based on elapsed time and current state."""
        dt = current_time - self.last_update_time
        if dt <= 0:
            return

        for p in [2, 1]:
            is_tx = (self.is_transmitting and self.tx_pcp == p)
            is_waiting = len(self.queues[p]) > 0

            if is_tx:
                # Transmitting: decrease credit
                self.credits[p] -= self.slopes[p]['send'] * dt
            elif is_waiting:
                # Not transmitting but frames waiting: accumulate credit
                self.credits[p] += self.slopes[p]['idle'] * dt
            else:
                # Idle: Queue empty, not transmitting
                if self.credits[p] > 0:
                    self.credits[p] = 0.0 # Positive credit resets instantly
                elif self.credits[p] < 0:
                    # Negative credit recovers slowly to 0
                    self.credits[p] = min(0.0, self.credits[p] + self.slopes[p]['idle'] * dt) 
                    
        self.last_update_time = current_time

# =========================================================
# 4. DISCRETE-EVENT SIMULATOR CORE
# =========================================================
class Simulator:
    def __init__(self, mode, topology_links, streams, cbs_slopes):
        self.mode = mode # 'SP' or 'CBS'
        self.current_time = 0.0
        
        # Min-heap for events: (time, priority, counter, type, payload)
        self.events = []
        self.event_counter = 0 
        
        # Build network ports
        self.ports = {}
        for link in topology_links:
            pid = (link['source'], link['sourcePort'])
            bw = link.get('bandwidth_mbps', 100)
            delay = link.get('delay', 0.0)
            self.ports[pid] = Port(pid, bw, delay, cbs_slopes)
            
        self.streams = streams
        # Store end-to-end delays for every frame
        self.observed_delays = {s['id']: [] for s in streams}

    def schedule(self, time, event_prio, event_type, payload):
        """Schedules an event on the timeline."""
        heapq.heappush(self.events, (time, event_prio, self.event_counter, event_type, payload))
        self.event_counter += 1

    def run(self, max_time):
        """Main simulation loop."""
        # Seed initial generation events at t=0
        for stream in self.streams:
            self.schedule(0.0, PRIO_GENERATE, 'GENERATE', {'stream': stream, 'gen_time': 0.0})

        while self.events:
            event_time, event_prio, _, event_type, payload = heapq.heappop(self.events)
            
            if event_time > max_time:
                break
                
            self.current_time = event_time
            
            # Event Router
            if event_type == 'GENERATE':
                self.handle_generate(payload)
            elif event_type == 'ARRIVE':
                self.handle_arrive(payload)
            elif event_type == 'TX_END':
                self.handle_tx_end(payload)
            elif event_type == 'CREDIT_ZERO':
                self.handle_credit_zero(payload)
                
        # Calculate WCD. -1.0 implies starvation (no frames finished)
        return {s_id: max(delays) if delays else -1.0 for s_id, delays in self.observed_delays.items()}

    # --- EVENT HANDLERS ---
    
    def handle_generate(self, payload):
        stream = payload['stream']
        gen_time = payload['gen_time']
        frame = Frame(stream['id'], stream['PCP'], stream['size'], gen_time, stream['path'])
        
        # Schedule the next frame generation for this stream
        next_gen = gen_time + stream['period']
        self.schedule(next_gen, PRIO_GENERATE, 'GENERATE', {'stream': stream, 'gen_time': next_gen})
        
        # Arrive at the source's output port instantly
        self.schedule(gen_time, PRIO_ARRIVE, 'ARRIVE', {'frame': frame, 'port_id': frame.path[0]})

    def handle_arrive(self, payload):
        frame = payload['frame']
        port_id = payload['port_id']

        # If at destination, record delay and terminate frame
        if frame.hop_index == len(frame.path) - 1:
            delay = self.current_time - frame.gen_time
            self.observed_delays[frame.stream_id].append(delay)
            return

        port = self.ports[port_id]
        port.update_credits(self.current_time)
        port.queues[frame.pcp].append(frame)
        self.trigger_port(port)

    def handle_tx_end(self, payload):
        frame = payload['frame']
        port = self.ports[payload['port_id']]

        port.update_credits(self.current_time)
        port.is_transmitting = False
        port.tx_pcp = None

        # Forward frame to the next hop with link propagation delay
        frame.hop_index += 1
        next_port_id = frame.path[frame.hop_index]
        arrival_time = self.current_time + port.delay
        
        self.schedule(arrival_time, PRIO_ARRIVE, 'ARRIVE', {'frame': frame, 'port_id': next_port_id})
        
        # Check if the port can transmit the next frame
        self.trigger_port(port)

    def handle_credit_zero(self, payload):
        """Wakes up the port when a blocked queue's credit recovers to 0."""
        port = self.ports[payload['port_id']]
        self.trigger_port(port)

    # --- CORE SCHEDULING LOGIC ---

    def trigger_port(self, port):
        """Evaluates the port's queues and decides what to transmit."""
        if port.is_transmitting:
            return

        port.update_credits(self.current_time)
        selected_frame = None
        
        if self.mode == 'SP':
            # Strict Priority: Pure FIFO based on PCP
            for pcp in [2, 1, 0]:
                if port.queues[pcp]:
                    selected_frame = port.queues[pcp].pop(0)
                    break
                    
        elif self.mode == 'CBS':
            # Credit-Based Shaper: Respect >= 0 credit bound (using -1e-9 for float precision)
            if port.queues[2] and port.credits[2] >= -1e-9:
                selected_frame = port.queues[2].pop(0)
            elif port.queues[1] and port.credits[1] >= -1e-9:
                selected_frame = port.queues[1].pop(0)
            elif port.queues[0]:
                selected_frame = port.queues[0].pop(0)

            # If no frame was selected, but frames are waiting, we are credit-blocked.
            # Schedule a wake-up event for when the highest priority blocked queue recovers.
            if not selected_frame:
                for p in [2, 1]:
                    if port.queues[p] and port.credits[p] < 0:
                        time_to_zero = -port.credits[p] / port.slopes[p]['idle']
                        wake_time = self.current_time + time_to_zero
                        self.schedule(wake_time, PRIO_CREDIT_ZERO, 'CREDIT_ZERO', {'port_id': port.id})
                        break # Only wake up for the highest priority one

        # If we selected a frame, start transmission
        if selected_frame:
            port.is_transmitting = True
            port.tx_pcp = selected_frame.pcp
            
            tx_time = (selected_frame.size * 8.0) / port.bandwidth
            self.schedule(self.current_time + tx_time, PRIO_TX_END, 'TX_END', {
                'frame': selected_frame,
                'port_id': port.id
            })

# =========================================================
# 5. MAIN EXECUTION & DATA PARSING
# =========================================================
def main():
    print("Loading network configuration...")
    
    # 1. Load Data
    topology = load_json('topology.json')['topology']
    raw_streams = load_json('streams.json')['streams']
    routes = load_json('routes.json')['routes']
    
    # Check for config.json, otherwise fallback to defaults
    try:
        config = load_json('config.json')
        # Convert JSON string keys ("2", "1") to integers
        cbs_slopes = {int(k): v for k, v in config['cbs_slopes'].items()}
    except FileNotFoundError:
        print("Warning: config.json not found. Defaulting to 0.5 slopes.")
        cbs_slopes = {2: {'idle': 0.5, 'send': 0.5}, 1: {'idle': 0.5, 'send': 0.5}}

    # 2. Parse routes mapping
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

    # 4. Run Simulations
    # 100,000 us (100 ms) allows multi-period overlap for worst-case analysis
    MAX_SIM_TIME = 100000.0  
    
    print("\nRunning Strict Priority (SP) Simulation...")
    sim_sp = Simulator('SP', topology['links'], streams, cbs_slopes)
    sp_results = sim_sp.run(MAX_SIM_TIME)

    print("Running Credit Based Shaper (CBS) Simulation...")
    sim_cbs = Simulator('CBS', topology['links'], streams, cbs_slopes)
    cbs_results = sim_cbs.run(MAX_SIM_TIME)

    # 5. Formatted Output Console Print
    print("\n================================================================================")
    print("                      TSN SIMULATION MAXIMUM DELAY RESULTS                      ")
    print("================================================================================")
    print(f"{'Stream':<8} | {'Size(B)':<8} | {'PCP':<4} | {'Period(us)':<12} | {'SP WCD (us)':<12} | {'CBS WCD (us)':<12}")
    print("-" * 80)
    
    for s in streams:
        if s['PCP'] == 0: 
            continue # Skip best effort in reporting if desired
            
        s_id = s['id']
        
        # Format output. Catch the -1.0 flag which indicates starvation.
        sp_str = f"{sp_results[s_id]:.2f}" if sp_results[s_id] != -1.0 else "STARVED"
        cbs_str = f"{cbs_results[s_id]:.2f}" if cbs_results[s_id] != -1.0 else "STARVED"
        
        print(f"{s_id:<8} | {s['size']:<8} | {s['PCP']:<4} | {s['period']:<12} | {sp_str:<12} | {cbs_str:<12}")
        
    print("================================================================================\n")

if __name__ == "__main__":
    main()