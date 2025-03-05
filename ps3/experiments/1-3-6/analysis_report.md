# Lamport Clock Analysis Report

## Executive Summary

This report analyzes the behavior of a distributed system using Lamport logical clocks. 
The system consists of three machines communicating via message passing, 
with each machine maintaining its own logical clock according to the Lamport algorithm.

## Clock Rate Comparison

### Machine 0

- Start Time: 2025-03-05 03:32:39
- End Time: 2025-03-05 03:33:38
- Time Span: 59.00 seconds
- Start Clock: 0
- End Clock: 184
- Clock Range: 184
- Clock Rate: 3.12 ticks/second

### Machine 1

- Start Time: 2025-03-05 03:32:39
- End Time: 2025-03-05 03:33:38
- Time Span: 59.00 seconds
- Start Clock: 0
- End Clock: 357
- Clock Range: 357
- Clock Rate: 6.05 ticks/second

### Machine 2

- Start Time: 2025-03-05 03:32:39
- End Time: 2025-03-05 03:33:38
- Time Span: 59.00 seconds
- Start Clock: 0
- End Clock: 359
- Clock Range: 359
- Clock Rate: 6.08 ticks/second

## Event Count Analysis

### Machine 0

- Total Events: 61
- RECEIVE: 59 (96.72%)
- INITIAL: 1 (1.64%)
- INTERNAL: 1 (1.64%)

### Machine 1

- Total Events: 188
- INTERNAL: 94 (50.00%)
- RECEIVE: 57 (30.32%)
- SEND: 36 (19.15%)
- INITIAL: 1 (0.53%)

### Machine 2

- Total Events: 405
- INTERNAL: 210 (51.85%)
- SEND: 168 (41.48%)
- RECEIVE: 26 (6.42%)
- INITIAL: 1 (0.25%)

## Queue Size Analysis

### Machine 0

- Maximum Queue Size: 51
- Minimum Queue Size: 0
- Mean Queue Size: 26.00
- Median Queue Size: 28.0
- Final Queue Size: 50

Average Queue Size by Event Type:
- INITIAL: 0.00
- INTERNAL: 0.00
- RECEIVE: 26.88

### Machine 1

- Maximum Queue Size: 4
- Minimum Queue Size: 0
- Mean Queue Size: 0.16
- Median Queue Size: 0.0
- Final Queue Size: 0

Average Queue Size by Event Type:
- INITIAL: 0.00
- SEND: 0.00
- INTERNAL: 0.00
- RECEIVE: 0.54

### Machine 2

- Maximum Queue Size: 1
- Minimum Queue Size: 0
- Mean Queue Size: 0.01
- Median Queue Size: 0.0
- Final Queue Size: 0

Average Queue Size by Event Type:
- INITIAL: 0.00
- RECEIVE: 0.15
- SEND: 0.01
- INTERNAL: 0.00

## Clock Jump Analysis

### Machine 0

- Total Jumps: 37

Top 5 largest jumps:
- Jump of 14 at 2025-03-05 03:33:27 (143 → 157) during RECEIVE
- Jump of 11 at 2025-03-05 03:33:02 (57 → 68) during RECEIVE
- Jump of 10 at 2025-03-05 03:33:08 (80 → 90) during RECEIVE
- Jump of 9 at 2025-03-05 03:32:59 (45 → 54) during RECEIVE
- Jump of 8 at 2025-03-05 03:33:24 (127 → 135) during RECEIVE

### Machine 1

- Total Jumps: 66

Top 5 largest jumps:
- Jump of 16 at 2025-03-05 03:32:51 (59 → 75) during RECEIVE
- Jump of 13 at 2025-03-05 03:33:06 (146 → 159) during RECEIVE
- Jump of 13 at 2025-03-05 03:33:38 (344 → 357) during RECEIVE
- Jump of 12 at 2025-03-05 03:33:02 (124 → 136) during RECEIVE
- Jump of 12 at 2025-03-05 03:33:27 (276 → 288) during SEND

### Machine 2

- Total Jumps: 91

Top 5 largest jumps:
- Jump of 9 at 2025-03-05 03:33:08 (170 → 179) during SEND
- Jump of 8 at 2025-03-05 03:32:57 (105 → 113) during SEND
- Jump of 8 at 2025-03-05 03:33:34 (326 → 334) during INTERNAL
- Jump of 7 at 2025-03-05 03:32:53 (78 → 85) during RECEIVE
- Jump of 7 at 2025-03-05 03:33:00 (123 → 130) during INTERNAL

## Conclusions

1. **Clock Rate**: Machine 2 had the highest logical clock rate at 6.08 ticks/second.
2. **Event Volume**: Machine 2 processed the most events (405).
3. **Queue Size**: Machine 0 had the largest queue size (51).
5. **Clock Jumps**: A total of 194 significant clock jumps were detected across all machines.

### Observations on Lamport Clock Behavior

- The logical clocks advance at different rates due to the different execution speeds of the machines.
- Message receipt causes clock jumps when the sender's clock is ahead of the receiver's clock.
- The queue sizes fluctuate based on the balance between incoming messages and processing rate.
- Internal events cause the logical clock to advance by exactly 1, while receive events may cause larger jumps.