# AMBA AHB Protocol Verification Cheat Sheet (Sub-Prompts)

## 0. Signal & Parameter Configurations
| Parameter | Default | Description |
| --- | --- | --- |
| **DATA_WIDTH** | 32 | Width of HWDATA and HRDATA (typically 32, optionally 64/128/256). |
| **ADDR_WIDTH** | 32 | Width of HADDR (typically 32, optionally scaled to 64). |
| **HAS_MULTIPLE_MASTERS**| False | Enables explicit arbitration signals (HMASTER, HBUSREQ, HGRANT). |
| **HAS_AHB5** | False | Enables AHB5 secure extensions (HEXCL for atomicity, advanced HPROT). |
| **HAS_SPLIT_RETRY** | False | Enables advanced slave responses (SPLIT/RETRY) requiring master rearbitration. |

## 1. General Functional Scenarios
| Category | Scenario | Verification Intent |
| --- | --- | --- |
| **Basic Transfers** | Single NONSEQ Transfers | Verify functional correctness for isolated read and write operations. |
| **Pipelining** | Back-to-Back (Data + Address overlap) | Ensure the Master successfully launches the Address phase of N+1 while the Data phase of N is still executing. |
| **Burst Types** | WRAP4 / WRAP8 / WRAP16 | Verify the Address wraps cleanly across fixed boundary alignments during continuous bursts. |
| **Burst Types** | INCR (Undefined Length) | Verify infinite incrementing sequences tracking correctly without premature termination. |
| **Wait States** | HREADY / HREADYOUT = 0 | Validate that Master securely holds HADDR, HTRANS, HWDATA, and HWRITE stable across extended wait states. |

## 2. Protocol Corner Cases
| Corner Case | Description | Expected Behavior |
| --- | --- | --- |
| **Error Handling** | HRESP = ERROR | Protocol explicitly requires a two-cycle ERROR response (Wait state + Error cycle). Verify Master aborts subsequent beats in the burst. |
| **Atomic Operations (AHB5)** | EXOKAY Response on HEXCL | Ensure semaphore protection operates effectively using generic Exclusive Read/Write locks. |
| **Endianness (AHB5)** | Mixed-Endian Operations | Check behavior of master writing byte-invariant transfers. |
| **TrustZone Protection**| HPROT[1] Secure Violations | Attempt to run NONSEQ transactions dynamically to a Secure-mapped slave memory to intercept PSLVERR. |
| **Burst Abort** | Transition HTRANS to IDLE mid-burst | Verify Slave drops expected payload and recovers smoothly without stalling logic. |
| **Wait State Extremes** | Max Wait States during Data Phase | Evaluate master retention capacity over deep stalls (e.g. 50+ clock cycles). |

## 3. Negative Scenarios (Illegal Stimulus)
- **Address Phase Mutability**: Forcing HADDR or HWRITE to change states while HREADY is LOW. (Creates an illegal protocol violation).
- **Invalid HTRANS Sequencer**: Forcing HTRANS=SEQ immediately following an HTRANS=IDLE cycle abruptly.
- **Single-Cycle Error Fault**: Slave attempting to assert HRESP=ERROR in just a single clock cycle without fulfilling the required two-cycle mechanism.
- **Dangling Write Payload**: Failing to provide aligned HWDATA directly into the pipeline stage tracking the target Address phase. 
- **Unsupported Wrapping**: Issuing a WRAP burst on a non-aligned memory boundary, crashing the index calculator.
