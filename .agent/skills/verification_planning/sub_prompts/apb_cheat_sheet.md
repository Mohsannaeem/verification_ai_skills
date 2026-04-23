# AMBA APB Protocol Verification Cheat Sheet (Sub-Prompts)

## 0. Signal & Parameter Configurations
| Parameter | Default | Description |
| --- | --- | --- |
| **DATA_WIDTH** | 32 | Width of PWDATA and PRDATA in bits (typically 32, optionally 8/16). |
| **ADDR_WIDTH** | 32 | Width of PADDR in bits. |
| **HAS_APB3** | True | Presence of PREADY (Wait states) and PSLVERR (Error reporting). |
| **HAS_APB4** | False | Presence of PPROT (Protection limits) and PSTRB (Write strobes). |
| **HAS_APB5** | False | Presence of PWAKEUP (Low power trigger) and PUSER (Sideband signaling). |
| **HAS_PARITY**| False | Presence of parity check signals (APB5 safety extension). |

## 1. General Functional Scenarios
| Category | Scenario | Verification Intent |
| --- | --- | --- |
| **State Machine** | IDLE $\to$ SETUP $\to$ ACCESS $\to$ IDLE | Ensure baseline standard transfer phase transitions without dropping logic. |
| **State Machine** | IDLE $\to$ SETUP $\to$ ACCESS $\to$ SETUP | Verify back-to-back transfer efficiency with no intermediate IDLE cycles. |
| **Handshake** | Zero Wait-State Transfer | Verify slave correctly asserts PREADY=1 immediately on the first ACCESS cycle. |
| **Handshake** | Extended Wait-State Transfer | Verify master holds PADDR, PWRITE, PSEL, PWDATA, PPROT stable during extended PREADY=0 periods. |
| **Read/Write** | Mixed Read/Write sequence | Verify sequence logic clearing PWDATA and enabling PRDATA accurately across toggling PWRITE states. |

## 2. Protocol Corner Cases
| Corner Case | Description | Expected Behavior |
| --- | --- | --- |
| **Error Termination** | PSLVERR = 1 and PREADY = 1 | Verify Slave correctly reports target error upon active transfer termination. |
| **Sparse Writes (APB4)** | Randomizing PSTRB bits | Verify Slave accurately masks specific data bytes and discards inactive lanes. |
| **Protection Denial (APB4)**| Asserting PPROT[1] (Non-Secure) | Attempt access to secure slave banks to invoke expected PSLVERR protection faults. |
| **Wakeup Latency (APB5)** | Toggling PWAKEUP from IDLE | Verify clock-enable and delayed SETUP assertion until PWAKEUP sequence clears. |
| **Read Strobe Mask (APB4)**| PWRITE=0 and PSTRB != 0 | Ensure PSTRB is explicitly forced LOW during all read transactions. |
| **Address Unaligned Access**| PADDR points off 32-bit boundary | Validate slave behavior (assert PSLVERR or execute aligned fallback). |

## 3. Negative Scenarios (Illegal Stimulus)
- **PENABLE Premature Assertion**: Drive PENABLE=1 directly from IDLE without navigating through the SETUP phase. (Violates 2-phase APB clocking).
- **SETUP Glitch Withdrawal**: Assert PSEL=1, but de-assert it on the very next cycle without driving PENABLE=1.
- **Payload Instability**: Mutate PADDR or PWDATA randomly while PENABLE=1 but PREADY is stuck LOW (stalling).
- **Reset during ACCESS**: Pull PRESETn LOW mid-transfer and verify clean truncation without residual pipeline pollution.
- **Parity Corruption (APB5)**: Inject single-bit faults on data or control parity arrays to forcefully trigger standard parity alarms.
