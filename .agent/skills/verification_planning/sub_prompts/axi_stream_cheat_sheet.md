# AXI-Stream Protocol Verification Cheat Sheet (Sub-Prompts)

## 0. Signal & Parameter Configurations
| Parameter | Default | Description |
| --- | --- | --- |
| **DATA_WIDTH** | 32/64 | Width of TDATA in bits. Must be a multiple of 8. |
| **HAS_TLAST** | True | Presence of packet boundary marker. |
| **HAS_TKEEP** | True | Presence of null-byte qualifier for packing. |
| **HAS_TSTRB** | False | Presence of data-byte qualifier for sparse streams. |
| **TID_WIDTH** | 0-8 | Width of stream identifier (if interleaving is used). |
| **TDEST_WIDTH** | 0-4 | Width of destination routing identifier. |
| **TUSER_WIDTH** | Var | Width of user-defined sideband signals. |

## 1. General Functional Scenarios
| Category | Scenario | Verification Intent |
| --- | --- | --- |
| **Handshake** | TVALID after TREADY | Verify Receiver's ability to wait for Transmitter stimulus. |
| **Handshake** | TREADY after TVALID | Verify Transmitter's ability to hold data stable until accepted. |
| **Handshake** | Single-cycle Handshake | Verify 0-wait-state transfers (max throughput). |
| **Packets** | Minimal Packet (1 beat) | Ensure packet start/end logic works for single-cycle bursts. |
| **Packets** | Maximum Packet Size | Verify internal counter/buffer overflow handling. |
| **Packets** | Back-to-back Packets | Verify no gaps are required between TLAST=1 and next TLAST=0. |

## 2. Protocol Corner Cases
| Corner Case | Description | Expected Behavior |
| --- | --- | --- |
| **Null Packets** | TVALID=1, TLAST=1, all TKEEP=0 | Receiver should acknowledge the "empty" packet without data consumption. |
| **Sparse Stream** | Randomized TKEEP/TSTRB bits | Verify "holes" in the data stream are correctly ignored by the receiver. |
| **ID Interleaving** | TID changes between beats | Verify stream isolation and context switching logic. |
| **Unaligned Start** | First beat TKEEP != all 1s | Verify support for non-word-aligned packet start offsets. |
| **Mid-Transfer Reset** | Assert Reset while TVALID & TREADY are HIGH | Ensure state machines return to IDLE and no data is "stuck" in FIFOs. |
| **AXI5 Integrity** | Single-bit flip on TDATACHK | Detect parity error and trigger the error reporting mechanism. |
| **Wakeup Latency** | Exit low power via TWAKEUP | Verify that transfers only start AFTER the wakeup handshake completes. |

## 3. Negative Scenarios (Illegal Stimulus)
- **TVALID Drop**: Drop TVALID before TREADY is asserted (violates protocol stability).
- **TLAST Deassertion**: Dropping TLAST during the middle of a multi-beat packet (if protocol requires continuous transfer).
- **Invalid Parity**: Inject incorrect parity on TDATACHK bits to force error detection.
- **Clock Removal**: Stop ACLK during active transfer and verify recovery after clock resumes.
