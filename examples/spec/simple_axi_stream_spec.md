# AMBA AXI4-Stream Protocol Specification
## Simplified Reference (Demo Spec for verification_ai_skills)

**Protocol Version:** AXI4-Stream  
**Document Purpose:** Demo specification — shows the kind of input the AI pipeline consumes.

---

## 1. Introduction

The AXI4-Stream protocol is a point-to-point streaming interface designed for high-throughput, low-latency data transfer. It decouples the producer (Master/Transmitter) from the consumer (Slave/Receiver) using a simple handshake mechanism.

The protocol supports:
- Variable-width data payloads (configurable TDATA width)
- Byte-granular validity qualifiers (TKEEP, TSTRB)
- Logical packet framing via TLAST
- Stream routing via TID and TDEST sidebands
- Optional user-defined sideband data (TUSER)

---

## 2. Signal List

| Signal  | Width       | Direction (Master→Slave) | Description |
|---------|-------------|--------------------------|-------------|
| TVALID  | 1           | Master → Slave           | Transfer valid. Master asserts when data on bus is valid. |
| TREADY  | 1           | Slave → Master           | Transfer ready. Slave asserts when it can accept data. |
| TDATA   | DATA_WIDTH  | Master → Slave           | Data payload. Valid only when TVALID and TREADY are both asserted. |
| TSTRB   | DATA_WIDTH/8| Master → Slave           | Byte strobe. A 1 indicates the corresponding TDATA byte is a data byte; a 0 indicates a position byte. |
| TKEEP   | DATA_WIDTH/8| Master → Slave           | Byte qualifier. A 1 indicates the corresponding byte is part of the data stream; a 0 means the byte shall be removed before reaching the data sink. |
| TLAST   | 1           | Master → Slave           | Packet boundary indicator. Asserted on the final beat of a logical packet. |
| TID     | ID_WIDTH    | Master → Slave           | Stream identifier. Distinguishes between multiple logical streams sharing the same interface. |
| TDEST   | DEST_WIDTH  | Master → Slave           | Destination identifier. Used for routing in interconnect fabrics. |
| TUSER   | USER_WIDTH  | Master → Slave           | User-defined sideband data. Not interpreted by the protocol. |

**Note:** DATA_WIDTH must be a power of 2, minimum 8 bits. Default is 32 bits.

---

## 3. Handshake Protocol

### 3.1 TVALID / TREADY Handshake

A transfer occurs on the rising edge of the clock when **both** TVALID and TREADY are asserted simultaneously.

```
       ___     ___     ___     ___     ___     ___
CLK   /   \___/   \___/   \___/   \___/   \___/   \___
       _______________________
TVALID                        \_____
              _________
TREADY _______/         \_____
              ^
              Transfer occurs here (both HIGH)
```

**Rule 3.1.1 — TVALID Stability (SHALL):**  
Once TVALID is asserted, the Master **shall not** deassert TVALID until the transfer completes (i.e., until the rising clock edge where both TVALID and TREADY are HIGH). The values of TDATA, TSTRB, TKEEP, TLAST, TID, TDEST, and TUSER **shall** remain stable for the entire duration that TVALID is asserted.

**Rule 3.1.2 — TREADY Independence:**  
The Slave **may** assert TREADY before, during, or after TVALID is asserted. TREADY is **not** required to wait for TVALID. Deasserting TREADY once asserted is permitted.

**Rule 3.1.3 — No TVALID Dependency:**  
The Master **shall not** wait for TREADY to be asserted before asserting TVALID. A design where TVALID depends on TREADY is a protocol violation.

---

## 4. Data Transfer and Packet Framing

### 4.1 TLAST — Packet Boundary

TLAST marks the last beat of a logical packet. The Master **shall** assert TLAST exactly on the final data beat.

**Rule 4.1.1:** A single-beat packet is legal. The Master **shall** assert TLAST simultaneously with the only data beat.  
**Rule 4.1.2:** TLAST **shall** be stable while TVALID is asserted, following the same stability rules as TDATA.

### 4.2 TKEEP — Byte Qualifiers

TKEEP indicates which bytes in the final beat of a packet carry valid data.

**Rule 4.2.1 — Non-null beats:** For all beats except the last, TKEEP **shall** be all-ones (`'1`). Partial bytes are only legal on the last beat.  
**Rule 4.2.2 — Null termination:** A null packet is defined as a single beat where TKEEP is all-zeros and TLAST is asserted. This signals end-of-stream without any data.  
**Rule 4.2.3 — TSTRB dependency:** A byte position where TKEEP=0 **shall** also have TSTRB=0. Setting TSTRB=1 when TKEEP=0 is an illegal combination and constitutes a protocol violation.

### 4.3 TSTRB — Byte Strobe

TSTRB distinguishes between data bytes (TSTRB=1) and position bytes (TSTRB=0, where the byte slot exists in the stream but carries no meaningful data).

**Rule 4.3.1:** TSTRB[n]=1 requires TKEEP[n]=1. This is a hard dependency; violation is illegal.

---

## 5. Stream Routing Sidebands

### 5.1 TID — Stream Identifier

TID identifies a logical stream when multiple streams share an interface.

**Rule 5.1.1 — TID Stability:** TID **shall** remain stable for every beat of a single logical packet (from first beat to the beat where TLAST is asserted).  
**Rule 5.1.2 — TID Change:** TID **may** change only after the completion of the current packet (after the beat where TLAST and the handshake both occur).

### 5.2 TDEST — Destination

TDEST provides routing information.

**Rule 5.2.1 — TDEST Stability:** Like TID, TDEST **shall** be stable for the entire duration of a packet.

---

## 6. Reset Behavior

**Rule 6.1 — TVALID during Reset:**  
The Master **shall** deassert TVALID during reset and for at least one clock cycle after reset is deasserted.

**Rule 6.2 — TREADY during Reset:**  
The Slave **shall** deassert TREADY during reset. TREADY **may** be asserted on the first cycle after reset.

**Rule 6.3 — No Transfers during Reset:**  
No data transfers **shall** occur while reset is asserted. Any transfer that was in progress when reset is asserted is considered abandoned.

---

## 7. Continuous Streaming

**Rule 7.1:** A Master **may** keep TVALID asserted across multiple consecutive packets (back-to-back transfers) without deasserting between packets. This is referred to as continuous streaming.

**Rule 7.2:** In continuous streaming, a new packet begins on the beat following the TLAST beat of the previous packet. TID and TDEST **may** change between packets in this case.

---

## 8. Performance and Timing

- **Maximum throughput:** Achieved when TVALID and TREADY are both asserted every clock cycle with no stalls.
- **Stall latency:** A Slave may introduce stalls by deasserting TREADY. The number of stall cycles is implementation-defined.
- **Zero-latency forwarding:** The Slave **may** combinatorially derive TREADY from TVALID (same-cycle response), but this can create combinational loops in certain topologies and **shall** be used with care.
