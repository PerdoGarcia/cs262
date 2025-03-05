# Lamport Clock Analysis Report

## Executive Summary

This report analyzes the behavior of a distributed system using Lamport logical clocks. 
The system consists of three machines communicating via message passing, 
with each machine maintaining its own logical clock according to the Lamport algorithm.

## Clock Rate Comparison

### Machine 0

- Start Time: 2025-03-05 04:05:12
- End Time: 2025-03-05 04:06:12
- Time Span: 60.00 seconds
- Start Clock: 0
- End Clock: 281
- Clock Range: 281
- Clock Rate: 4.68 ticks/second

### Machine 1

- Start Time: 2025-03-05 04:05:12
- End Time: 2025-03-05 04:06:12
- Time Span: 60.00 seconds
- Start Clock: 0
- End Clock: 299
- Clock Range: 299
- Clock Rate: 4.98 ticks/second

### Machine 2

- Start Time: 2025-03-05 04:05:12
- End Time: 2025-03-05 04:06:12
- Time Span: 60.00 seconds
- Start Clock: 0
- End Clock: 296
- Clock Range: 296
- Clock Rate: 4.93 ticks/second

## Event Count Analysis

### Machine 0

- Total Events: 129
- INTERNAL: 71 (55.04%)
- SEND: 36 (27.91%)
- RECEIVE: 21 (16.28%)
- INITIAL: 1 (0.78%)

### Machine 1

- Total Events: 326
- INTERNAL: 190 (58.28%)
- SEND: 98 (30.06%)
- RECEIVE: 37 (11.35%)
- INITIAL: 1 (0.31%)

### Machine 2

- Total Events: 190
- INTERNAL: 79 (41.58%)
- RECEIVE: 74 (38.95%)
- SEND: 36 (18.95%)
- INITIAL: 1 (0.53%)

## Queue Size Analysis

### Machine 0

- Maximum Queue Size: 1
- Minimum Queue Size: 0
- Mean Queue Size: 0.02
- Median Queue Size: 0.0
- Final Queue Size: 0

Average Queue Size by Event Type:
- INITIAL: 0.00
- INTERNAL: 0.00
- RECEIVE: 0.10
- SEND: 0.00

### Machine 1

- Maximum Queue Size: 1
- Minimum Queue Size: 0
- Mean Queue Size: 0.02
- Median Queue Size: 0.0
- Final Queue Size: 0

Average Queue Size by Event Type:
- INITIAL: 0.00
- INTERNAL: 0.00
- RECEIVE: 0.11
- SEND: 0.02

### Machine 2

- Maximum Queue Size: 3
- Minimum Queue Size: 0
- Mean Queue Size: 0.22
- Median Queue Size: 0.0
- Final Queue Size: 1

Average Queue Size by Event Type:
- INITIAL: 0.00
- SEND: 0.08
- INTERNAL: 0.00
- RECEIVE: 0.53

## Clock Jump Analysis

### Machine 0

- Total Jumps: 34

Top 5 largest jumps:
- Jump of 44 at 2025-03-05 04:05:36 (67 → 111) during RECEIVE
- Jump of 24 at 2025-03-05 04:05:55 (177 → 201) during RECEIVE
- Jump of 21 at 2025-03-05 04:05:43 (124 → 145) during RECEIVE
- Jump of 19 at 2025-03-05 04:06:00 (210 → 229) during RECEIVE
- Jump of 15 at 2025-03-05 04:05:18 (17 → 32) during RECEIVE

### Machine 1

- Total Jumps: 74

Top 5 largest jumps:
- Jump of 8 at 2025-03-05 04:05:36 (111 → 119) during INTERNAL
- Jump of 8 at 2025-03-05 04:05:51 (186 → 194) during INTERNAL
- Jump of 8 at 2025-03-05 04:05:59 (226 → 234) during SEND
- Jump of 7 at 2025-03-05 04:06:10 (281 → 288) during INTERNAL
- Jump of 6 at 2025-03-05 04:05:22 (44 → 50) during RECEIVE

### Machine 2

- Total Jumps: 61

Top 5 largest jumps:
- Jump of 15 at 2025-03-05 04:05:26 (48 → 63) during INTERNAL
- Jump of 11 at 2025-03-05 04:05:55 (200 → 211) during RECEIVE
- Jump of 10 at 2025-03-05 04:06:04 (245 → 255) during RECEIVE
- Jump of 9 at 2025-03-05 04:05:50 (177 → 186) during RECEIVE
- Jump of 8 at 2025-03-05 04:05:35 (102 → 110) during RECEIVE

## Conclusions

1. **Clock Rate**: Machine 1 had the highest logical clock rate at 4.98 ticks/second.
2. **Event Volume**: Machine 1 processed the most events (326).
3. **Queue Size**: Machine 2 had the largest queue size (3).
5. **Clock Jumps**: A total of 169 significant clock jumps were detected across all machines.

### Observations on Lamport Clock Behavior

- The logical clocks advance at different rates due to the different execution speeds of the machines.
- Message receipt causes clock jumps when the sender's clock is ahead of the receiver's clock.
- The queue sizes fluctuate based on the balance between incoming messages and processing rate.
- Internal events cause the logical clock to advance by exactly 1, while receive events may cause larger jumps.