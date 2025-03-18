# Lamport Clock Analysis Report

## Executive Summary

This report analyzes the behavior of a distributed system using Lamport logical clocks. 
The system consists of three machines communicating via message passing, 
with each machine maintaining its own logical clock according to the Lamport algorithm.

## Clock Rate Comparison

### Machine 0

- Start Time: 2025-03-05 04:33:54
- End Time: 2025-03-05 04:34:53
- Time Span: 59.00 seconds
- Start Clock: 0
- End Clock: 355
- Clock Range: 355
- Clock Rate: 6.02 ticks/second

### Machine 1

- Start Time: 2025-03-05 04:33:54
- End Time: 2025-03-05 04:34:53
- Time Span: 59.00 seconds
- Start Clock: 0
- End Clock: 360
- Clock Range: 360
- Clock Rate: 6.10 ticks/second

### Machine 2

- Start Time: 2025-03-05 04:33:54
- End Time: 2025-03-05 04:34:53
- Time Span: 59.00 seconds
- Start Clock: 0
- End Clock: 362
- Clock Range: 362
- Clock Rate: 6.14 ticks/second

## Event Count Analysis

### Machine 0

- Total Events: 254
- INTERNAL: 122 (48.03%)
- RECEIVE: 66 (25.98%)
- SEND: 65 (25.59%)
- INITIAL: 1 (0.39%)

### Machine 1

- Total Events: 323
- INTERNAL: 144 (44.58%)
- RECEIVE: 89 (27.55%)
- SEND: 89 (27.55%)
- INITIAL: 1 (0.31%)

### Machine 2

- Total Events: 392
- INTERNAL: 197 (50.26%)
- SEND: 115 (29.34%)
- RECEIVE: 79 (20.15%)
- INITIAL: 1 (0.26%)

## Queue Size Analysis

### Machine 0

- Maximum Queue Size: 3
- Minimum Queue Size: 0
- Mean Queue Size: 0.11
- Median Queue Size: 0.0
- Final Queue Size: 0

Average Queue Size by Event Type:
- INITIAL: 0.00
- SEND: 0.02
- INTERNAL: 0.00
- RECEIVE: 0.39

### Machine 1

- Maximum Queue Size: 3
- Minimum Queue Size: 0
- Mean Queue Size: 0.14
- Median Queue Size: 0.0
- Final Queue Size: 0

Average Queue Size by Event Type:
- INITIAL: 0.00
- INTERNAL: 0.00
- RECEIVE: 0.47
- SEND: 0.02

### Machine 2

- Maximum Queue Size: 3
- Minimum Queue Size: 0
- Mean Queue Size: 0.05
- Median Queue Size: 0.0
- Final Queue Size: 0

Average Queue Size by Event Type:
- INITIAL: 0.00
- INTERNAL: 0.00
- RECEIVE: 0.20
- SEND: 0.04

## Clock Jump Analysis

### Machine 0

- Total Jumps: 66

Top 5 largest jumps:
- Jump of 16 at 2025-03-05 04:34:39 (254 → 270) during RECEIVE
- Jump of 14 at 2025-03-05 04:34:46 (304 → 318) during INTERNAL
- Jump of 13 at 2025-03-05 04:34:49 (326 → 339) during INTERNAL
- Jump of 11 at 2025-03-05 04:34:47 (308 → 319) during INTERNAL
- Jump of 10 at 2025-03-05 04:33:58 (20 → 30) during RECEIVE

### Machine 1

- Total Jumps: 87

Top 5 largest jumps:
- Jump of 12 at 2025-03-05 04:34:35 (240 → 252) during RECEIVE
- Jump of 10 at 2025-03-05 04:34:36 (243 → 253) during RECEIVE
- Jump of 10 at 2025-03-05 04:34:46 (310 → 320) during INTERNAL
- Jump of 9 at 2025-03-05 04:33:55 (4 → 13) during INTERNAL
- Jump of 8 at 2025-03-05 04:33:56 (6 → 14) during SEND

### Machine 2

- Total Jumps: 103

Top 5 largest jumps:
- Jump of 9 at 2025-03-05 04:34:40 (274 → 283) during RECEIVE
- Jump of 9 at 2025-03-05 04:34:53 (353 → 362) during SEND
- Jump of 8 at 2025-03-05 04:34:06 (70 → 78) during SEND
- Jump of 8 at 2025-03-05 04:34:15 (125 → 133) during INTERNAL
- Jump of 7 at 2025-03-05 04:33:59 (29 → 36) during INTERNAL

## Conclusions

1. **Clock Rate**: Machine 2 had the highest logical clock rate at 6.14 ticks/second.
2. **Event Volume**: Machine 2 processed the most events (392).
3. **Queue Size**: Machine 0 had the largest queue size (3).
5. **Clock Jumps**: A total of 256 significant clock jumps were detected across all machines.

### Observations on Lamport Clock Behavior

- The logical clocks advance at different rates due to the different execution speeds of the machines.
- Message receipt causes clock jumps when the sender's clock is ahead of the receiver's clock.
- The queue sizes fluctuate based on the balance between incoming messages and processing rate.
- Internal events cause the logical clock to advance by exactly 1, while receive events may cause larger jumps.