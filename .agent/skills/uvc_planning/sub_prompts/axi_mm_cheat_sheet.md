# AMBA AXI Memory Mapped Protocol Verification Cheat Sheet (Sub-Prompts)

## 0. Signal & Parameter Configurations
| Parameter | Default | Description |
| --- | --- | --- |
| **DATA_WIDTH** | 32/64/128 | Width of WDATA and RDATA channels explicitly. |
| **ADDR_WIDTH** | 32/64 | Width of AWADDR and ARADDR addresses explicitly. |
| **ID_WIDTH** | 4 | Width of AxID, WID (AXI3 only), BID, and RID. |
| **HAS_AXI3** | False | Enables WID for write interleaving and exact locked transfers (AxLOCK). |
| **HAS_AXI4** | True | Extends burst limits to 256, disables WID (fixed write tracking), adds QoS. |
| **HAS_AXI5** | False | Enables Atomic operations (AWATOP), data poisoning, and interface parity checks. |

## 1. General Functional Scenarios
| Category | Scenario | Verification Intent |
| --- | --- | --- |
| **Channel Handshakes** | B-Channel Response delays | Verify Master can cleanly consume late returning BVALID signals independently of ongoing Address phases. |
| **Burst Boundary** | Unaligned Start | Perform transfers utilizing explicit WSTRB masking indicating unaligned first-beat accesses. |
| **Burst Types** | FIXED/INCR/WRAP limits | Validating all permutations of AxBURST against extreme max ranges (e.g. 256 beats for AXI4). |
| **Out-of-Order Data** | Read Data re-ordering | Send interleaved RID responses and verify the Master correctly sorts/resolves payload dependencies. |
| **Outstanding Transactions**| Arbiter Max Depth | Flood the interconnect with maximum pending requests to test the depth limits of AWREADY/ARREADY stalls. |

## 2. Protocol Corner Cases
| Corner Case | Description | Expected Behavior |
| --- | --- | --- |
| **4KB Boundary Violation** | INCR burst targets 4K wrap | Standard AXI logic STRICTLY prohibits crossing an isolated 4KB grid. Monitor must flag an illegal sequence gracefully. |
| **Write Interleaving (AXI3)**| Concurrent AxID WDATA | Master alternates WDATA beats explicitly tagging disparate WID payloads (Interconnect demuxing check). |
| **Quality of Service (AXI4)**| AxQOS priority sweeping | Launch identical ID sequences differing only via AxQOS settings; verify exact arbitration granting behaviors. |
| **Atomic Transactions (AXI5)**| AWATOP operations | Execute Load/Store/Compare swap requests to verify slave correctly intercepts R/W locks independently. |
| **Data Poisoning (AXI5)** | Toggling Poison bits | Slave forces Data Poisoning bits; ensure protocol routes to an immediate graceful Error recovery cycle. |
| **Exclusive Access** | AxLOCK Semaphore race | Two masters attempt concurrent EXOKAY transactions toward identical generic addresses (only first completes). |

## 3. Negative Scenarios (Illegal Stimulus)
- **Handshake Violations**: Forcibly de-asserting AWVALID or ARVALID before encountering the corresponding READY HIGH cycle (explicit standard violation).
- **ID Ambiguity (AXI4+)**: Initiating distinct transaction structures concurrently with exactly identical AxIDs across disparate ports.
- **Orphaned Write Data**: Pumping WVALID sequence phases arbitrarily without ever establishing the associated AWVALID sequence logic (dangling queues).
- **Illegal Strobe Constraints**: Toggling WSTRB arrays uniformly active during read-driven phases (logic cross-talk check).
- **Incomplete Bursts**: Halting WDATA sequence abruptly generating fewer beats than promised in AWLEN (Wait state pipeline corruption check).
