Starvation demonstration test case - 3 streams showing CBS bandwidth protection.

Topology: ES0 ──(100 Mbps)──> ES1 (direct link, single shared port)

Streams (all traverse the same port):
  Stream 0 (PCP 2): 1100 bytes, period 100 µs
    -> TX time = 88 µs → 88% utilization
  
  Stream 1 (PCP 2): 650 bytes, period 250 µs  
    -> TX time = 52 µs → 20.8% utilization
  
  Stream 2 (PCP 1): 250 bytes, period 1000 µs
    -> TX time = 20 µs → 2% utilization
    
  Total utilization: 110.8% (overload - NOT schedulable without CBS)
  PCP 2 utilization: 108.8% (causes STARVATION in SP mode)

CBS configuration (config.json):
  PCP 2: idleSlope=0.88, sendSlope=0.12 → max 88% bandwidth
  PCP 1: idleSlope=0.12, sendSlope=0.88 → guaranteed 12% bandwidth

Why CBS helps:
  - In SP mode: PCP 2 demands 108.8% bandwidth → Stream 2 STARVES
  - In CBS mode: PCP 2 is rate-limited to 88%, leaving 12% for Stream 2 (enough for 2%)
  - CBS prevents high-priority traffic from monopolizing the link

Expected result:
  SP:  Stream 2 = STARVED (never gets service)
  CBS: Stream 2 = finite delay (protected by bandwidth reservation)
