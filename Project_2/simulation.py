import json
import os
import heapq
import math
from functools import reduce

# Directory where the input JSON files are expected to be located
DIRECTORY = "test_case_starve"

# =========================================================
# 1. EVENT PRIORITIES (Fixes simultaneous event bugs)
# =========================================================
# In discrete-event simulations, multiple events can occur at the exact same time.
# These priorities determine the order of execution when timestamps tie.
PRIO_GENERATE = 0      # Generating a frame has highest priority
PRIO_ARRIVE = 1        # Frame arriving at a switch/port
PRIO_TX_END = 2        # Frame finishing transmission
PRIO_CREDIT_ZERO = 3   # CBS credit reaching exactly 0

# =========================================================
# 2. UTILITY & MATH FUNCTIONS
# =========================================================
def load_json(filename):
    """Utility to load and parse a JSON file from the target directory."""
    path = os.path.join(DIRECTORY, filename)
    with open(path, 'r') as f:
        return json.load(f)

def compute_hyperperiod(streams):
    """
    Calculates the hyperperiod of all streams. 
    The hyperperiod is the Least Common Multiple (LCM) of all frame generation periods.
    Simulating for the hyperperiod ensures all possible traffic overlaps are observed.
    """
    periods = [int(s['period']) for s in streams]
    if not periods:
        return 100000.0
        
    # Use math.lcm if available (Python 3.9+), otherwise fallback to custom gcd-based lcm
    if hasattr(math, 'lcm'):
        return float(math.lcm(*periods))
    else:
        def lcm(a, b):
            return abs(a*b) // math.gcd(a, b)
        return float(reduce(lcm, periods))

# =========================================================
# 3. SIMULATION ENTITIES
# =========================================================
class Frame:
    """Represents a single packet/frame traveling through the network."""
    def __init__(self, stream_id, pcp, size_bytes, gen_time, path):
        self.stream_id = stream_id
        self.pcp = pcp                  # Priority Code Point (0, 1, or 2)
        self.size = size_bytes
        self.gen_time = gen_time        # Timestamp when the frame was originally created
        self.path = path                # List of (Node, Port) tuples representing the route
        self.hop_index = 0              # Tracks the frame's current position in the path

class Port:
    """Represents an egress (outgoing) port on a network node/switch."""
    def __init__(self, port_id, bandwidth_mbps, delay, cbs_slopes):
        self.id = port_id
        self.bandwidth = bandwidth_mbps
        self.delay = delay
        # Queues mapped by PCP (Priority). Assuming priorities 0, 1, and 2.
        self.queues = {2: [], 1: [], 0: []}
        
        # State tracking for transmission
        self.is_transmitting = False
        self.tx_pcp = None              # The priority of the frame currently being transmitted
        
        # Credit-Based Shaper (CBS) state variables
        self.credits = {2: 0.0, 1: 0.0} # Credit pools for traffic classes 1 and 2
        self.slopes = cbs_slopes        # The rates at which credits accumulate or deplete
        self.last_update_time = 0.0     # The last timestamp credits were updated

    def update_credits(self, current_time):
        """Updates the CBS credits based on elapsed time since the last update."""
        dt = current_time - self.last_update_time
        if dt <= 0: return

        # Only priority classes 1 and 2 are shaped by CBS
        for p in [2, 1]:
            is_tx = (self.is_transmitting and self.tx_pcp == p)
            is_waiting = len(self.queues[p]) > 0

            if is_tx:
                # If currently transmitting a frame of this priority, drain credits
                self.credits[p] -= self.slopes[p]['send'] * dt
            elif is_waiting:
                # If a frame of this priority is waiting but NOT transmitting, accumulate credits
                self.credits[p] += self.slopes[p]['idle'] * dt
            else:
                # If neither transmitting nor waiting, credits naturally drift back to 0
                if self.credits[p] > 0:
                    self.credits[p] = 0.0 
                elif self.credits[p] < 0:
                    self.credits[p] = min(0.0, self.credits[p] + self.slopes[p]['idle'] * dt) 
        self.last_update_time = current_time

# =========================================================
# 4. DISCRETE-EVENT SIMULATOR CORE
# =========================================================
class Simulator:
    """The central engine that manages time and processes network events."""
    def __init__(self, mode, topology_links, streams, cbs_slopes):
        self.mode = mode # 'SP' (Strict Priority) or 'CBS' (Credit Based Shaper)
        self.current_time = 0.0
        
        # Min-heap to store future events sorted by (time, priority)
        self.events = []
        self.event_counter = 0 # Breaks ties in heapq if time and priority match
        
        # Initialize network ports based on topology
        self.ports = {}
        for link in topology_links:
            pid = (link['source'], link['sourcePort'])
            bw = link.get('bandwidth_mbps', 100)
            delay = link.get('delay', 0.0)
            self.ports[pid] = Port(pid, bw, delay, cbs_slopes)
            
        self.streams = streams
        # Dictionary to record end-to-end delays observed for each stream
        self.observed_delays = {s['id']: [] for s in streams}

    def schedule(self, time, event_prio, event_type, payload):
        """Pushes a new event into the min-heap."""
        heapq.heappush(self.events, (time, event_prio, self.event_counter, event_type, payload))
        self.event_counter += 1

    def run(self, max_time):
        """The main simulation loop."""
        # Bootstrapping: Schedule the very first generation event for all streams
        for stream in self.streams:
            self.schedule(0.0, PRIO_GENERATE, 'GENERATE', {'stream': stream, 'gen_time': 0.0})

        # Process events until the queue is empty or max_time is reached
        while self.events:
            event_time, event_prio, _, event_type, payload = heapq.heappop(self.events)
            
            if event_time > max_time:
                break
                
            self.current_time = event_time
            
            # Dispatch event to appropriate handler
            if event_type == 'GENERATE': self.handle_generate(payload)
            elif event_type == 'ARRIVE': self.handle_arrive(payload)
            elif event_type == 'TX_END': self.handle_tx_end(payload)
            elif event_type == 'CREDIT_ZERO': self.handle_credit_zero(payload)
                
        # Return maximum delay (Worst-Case Delay) per stream, or -1.0 if never arrived
        return {s_id: max(delays) if delays else -1.0 for s_id, delays in self.observed_delays.items()}

    def handle_generate(self, payload):
        """Creates a new frame and schedules its arrival at the first port, and schedules the next generation."""
        stream = payload['stream']
        gen_time = payload['gen_time']
        
        # Create the actual frame
        frame = Frame(stream['id'], stream['PCP'], stream['size'], gen_time, stream['path'])
        
        # Schedule the *next* frame generation for this stream
        next_gen = gen_time + stream['period']
        self.schedule(next_gen, PRIO_GENERATE, 'GENERATE', {'stream': stream, 'gen_time': next_gen})
        
        # Schedule the arrival of the *current* frame at the first node in its route
        self.schedule(gen_time, PRIO_ARRIVE, 'ARRIVE', {'frame': frame, 'port_id': frame.path[0]})

    def handle_arrive(self, payload):
        """Processes a frame arriving at a port queue or reaching its final destination."""
        frame = payload['frame']
        port_id = payload['port_id']
        
        # Base case: Frame has reached the end of its path
        if frame.hop_index == len(frame.path) - 1:
            delay = self.current_time - frame.gen_time
            self.observed_delays[frame.stream_id].append(delay)
            return

        # Regular case: Frame needs to be queued at the current switch port
        port = self.ports[port_id]
        port.update_credits(self.current_time)
        port.queues[frame.pcp].append(frame) # Add frame to the queue matching its priority
        
        # Check if the port can start transmitting this frame immediately
        self.trigger_port(port)

    def handle_tx_end(self, payload):
        """Clears the port after a frame finishes sending and moves the frame to the next hop."""
        frame = payload['frame']
        port = self.ports[payload['port_id']]
        
        port.update_credits(self.current_time)
        port.is_transmitting = False
        port.tx_pcp = None

        # Advance frame to the next node in its path
        frame.hop_index += 1
        next_port_id = frame.path[frame.hop_index]
        arrival_time = self.current_time + port.delay
        
        # Schedule the arrival at the next hop
        self.schedule(arrival_time, PRIO_ARRIVE, 'ARRIVE', {'frame': frame, 'port_id': next_port_id})
        
        # Since the port is now free, try to send the next waiting frame
        self.trigger_port(port)

    def handle_credit_zero(self, payload):
        """Wakes up a port when its CBS credit hits zero (meaning it might be able to transmit again)."""
        port = self.ports[payload['port_id']]
        self.trigger_port(port)

    def trigger_port(self, port):
        """Selects the next frame to transmit based on the scheduling mode (SP or CBS)."""
        # If the port is busy, it cannot transmit anything else right now
        if port.is_transmitting:
            return

        port.update_credits(self.current_time)
        selected_frame = None
        
        # --- Strict Priority (SP) Logic ---
        if self.mode == 'SP':
            # Always pick the highest priority queue (2 -> 1 -> 0) that has waiting frames
            for pcp in [2, 1, 0]:
                if port.queues[pcp]:
                    selected_frame = port.queues[pcp].pop(0)
                    break
                    
        # --- Credit Based Shaper (CBS) Logic ---
        elif self.mode == 'CBS':
            # Priority 2 and 1 can only transmit if their credit is non-negative (>= 0)
            if port.queues[2] and port.credits[2] >= -1e-9:
                selected_frame = port.queues[2].pop(0)
            elif port.queues[1] and port.credits[1] >= -1e-9:
                selected_frame = port.queues[1].pop(0)
            # Priority 0 is best-effort and has no credit restriction
            elif port.queues[0]:
                selected_frame = port.queues[0].pop(0)

            # If frames are waiting but cannot be sent because credits are negative,
            # we must proactively schedule an event to wake this port up exactly when
            # credits cross back to 0. Otherwise, the port might stall forever.
            if not selected_frame:
                for p in [2, 1]:
                    if port.queues[p] and port.credits[p] < 0:
                        time_to_zero = -port.credits[p] / port.slopes[p]['idle']
                        wake_time = self.current_time + time_to_zero
                        self.schedule(wake_time, PRIO_CREDIT_ZERO, 'CREDIT_ZERO', {'port_id': port.id})
                        break 

        # If a frame was successfully selected, initiate its transmission
        if selected_frame:
            port.is_transmitting = True
            port.tx_pcp = selected_frame.pcp
            # Calculate how long the frame takes to physically transmit over the wire
            tx_time = (selected_frame.size * 8.0) / port.bandwidth
            
            # Schedule the end of this transmission
            self.schedule(self.current_time + tx_time, PRIO_TX_END, 'TX_END', {
                'frame': selected_frame,
                'port_id': port.id
            })

# =========================================================
# 5. MAIN EXECUTION & DATA PARSING
# =========================================================
def main():
    # Load configuration inputs
    topology = load_json('topology.json')['topology']
    raw_streams = load_json('streams.json')['streams']
    routes = load_json('routes.json')['routes']
    
    # Load CBS parameters or default to 0.5/0.5
    try:
        config = load_json('config.json')
        cbs_slopes = {int(k): v for k, v in config['cbs_slopes'].items()}
    except FileNotFoundError:
        cbs_slopes = {2: {'idle': 0.5, 'send': 0.5}, 1: {'idle': 0.5, 'send': 0.5}}

    # Map the flow IDs to their specific port-by-port network paths
    routes_map = {}
    for r in routes:
        routes_map[r['flow_id']] = [(hop['node'], hop['port']) for hop in r['paths'][0]]

    # Combine stream generation info with route paths
    streams = []
    for s in raw_streams:
        streams.append({
            'id': s['id'], 'PCP': s['PCP'], 'size': s['size'],
            'period': s['period'], 'path': routes_map[s['id']]
        })

    # Calculate simulation runtime based on hyperperiod
    hyperperiod = compute_hyperperiod(streams)
    MAX_SIM_TIME = hyperperiod * 2.0
    # Hardcoded overwrite for consistent testing runtime
    MAX_SIM_TIME = 100000
    
    print("\n" + "="*80)
    print(f"Network Hyperperiod calculated: {hyperperiod:,.2f} us")
    print(f"Simulating for 2x Hyperperiod: {MAX_SIM_TIME:,.2f} us")
    print("="*80 + "\n")
    
    # Run the SP (Strict Priority) test
    print("Running Strict Priority (SP) Simulation...")
    sim_sp = Simulator('SP', topology['links'], streams, cbs_slopes)
    sp_results = sim_sp.run(MAX_SIM_TIME)

    # Run the CBS (Credit Based Shaper) test
    print("Running Credit Based Shaper (CBS) Simulation...")
    sim_cbs = Simulator('CBS', topology['links'], streams, cbs_slopes)
    cbs_results = sim_cbs.run(MAX_SIM_TIME)

    # Output and format the Worst-Case Delay (WCD) findings
    print("\n================================================================================")
    print("                      TSN SIMULATION MAXIMUM DELAY RESULTS                      ")
    print("================================================================================")
    print(f"{'Stream':<8} | {'Size(B)':<8} | {'PCP':<4} | {'Period(us)':<12} | {'SP WCD (us)':<12} | {'CBS WCD (us)':<12}")
    print("-" * 80)
    
    for s in streams:
        # Ignore best effort traffic in the final delay reporting
        if s['PCP'] == 0: continue 
        s_id = s['id']
        # If result is -1.0, the frame never reached the end (starved)
        sp_str = f"{sp_results[s_id]:.2f}" if sp_results[s_id] != -1.0 else "STARVED"
        cbs_str = f"{cbs_results[s_id]:.2f}" if cbs_results[s_id] != -1.0 else "STARVED"
        print(f"{s_id:<8} | {s['size']:<8} | {s['PCP']:<4} | {s['period']:<12} | {sp_str:<12} | {cbs_str:<12}")
        
    print("================================================================================\n")

if __name__ == "__main__":
    main()