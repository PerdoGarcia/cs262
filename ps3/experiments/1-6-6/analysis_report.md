# Lamport Clock Analysis Report

## Executive Summary

This report analyzes the behavior of a distributed system using Lamport logical clocks. 
The system consists of three machines communicating via message passing, 
with each machine maintaining its own logical clock according to the Lamport algorithm.

## Clock Rate Comparison

### Machine 0

- Start Time: 2025-03-05 04:28:38
- End Time: 2025-03-05 04:29:37
- Time Span: 59.00 seconds
- Start Clock: 0
- End Clock: 312
- Clock Range: 312
- Clock Rate: 5.29 ticks/second

### Machine 1

- Start Time: 2025-03-05 04:28:38
- End Time: 2025-03-05 04:29:37
- Time Span: 59.00 seconds
- Start Clock: 0
- End Clock: 368
- Clock Range: 368
- Clock Rate: 6.24 ticks/second

### Machine 2

- Start Time: 2025-03-05 04:28:38
- End Time: 2025-03-05 04:29:37
- Time Span: 59.00 seconds
- Start Clock: 0
- End Clock: 367
- Clock Range: 367
- Clock Rate: 6.22 ticks/second

## Event Count Analysis

### Machine 0

- Total Events: 61
- RECEIVE: 59 (96.72%)
- INITIAL: 1 (1.64%)
- INTERNAL: 1 (1.64%)

### Machine 1

- Total Events: 389
- INTERNAL: 236 (60.67%)
- SEND: 112 (28.79%)
- RECEIVE: 40 (10.28%)
- INITIAL: 1 (0.26%)

### Machine 2

- Total Events: 392
- INTERNAL: 210 (53.57%)
- SEND: 111 (28.32%)
- RECEIVE: 70 (17.86%)
- INITIAL: 1 (0.26%)

## Queue Size Analysis

### Machine 0

- Maximum Queue Size: 11
- Minimum Queue Size: 0
- Mean Queue Size: 7.54
- Median Queue Size: 8.0
- Final Queue Size: 11

Average Queue Size by Event Type:
- INITIAL: 0.00
- INTERNAL: 0.00
- RECEIVE: 7.80

### Machine 1

- Maximum Queue Size: 3
- Minimum Queue Size: 0
- Mean Queue Size: 0.02
- Median Queue Size: 0.0
- Final Queue Size: 0

Average Queue Size by Event Type:
- INITIAL: 0.00
- INTERNAL: 0.00
- SEND: 0.00
- RECEIVE: 0.20

### Machine 2

- Maximum Queue Size: 3
- Minimum Queue Size: 0
- Mean Queue Size: 0.07
- Median Queue Size: 0.0
- Final Queue Size: 0

Average Queue Size by Event Type:
- INITIAL: 0.00
- INTERNAL: 0.00
- SEND: 0.03
- RECEIVE: 0.37

## Clock Jump Analysis

### Machine 0

- Total Jumps: 48

Top 5 largest jumps:
- Jump of 18 at 2025-03-05 04:29:21 (196 → 214) during RECEIVE
- Jump of 13 at 2025-03-05 04:29:12 (135 → 148) during RECEIVE
- Jump of 13 at 2025-03-05 04:29:15 (153 → 166) during RECEIVE
- Jump of 13 at 2025-03-05 04:29:30 (259 → 272) during RECEIVE
- Jump of 13 at 2025-03-05 04:29:36 (289 → 302) during RECEIVE

### Machine 1

- Total Jumps: 100

Top 5 largest jumps:
- Jump of 10 at 2025-03-05 04:29:04 (154 → 164) during RECEIVE
- Jump of 9 at 2025-03-05 04:28:58 (118 → 127) during INTERNAL
- Jump of 9 at 2025-03-05 04:29:01 (136 → 145) during INTERNAL
- Jump of 9 at 2025-03-05 04:29:17 (233 → 242) during INTERNAL
- Jump of 9 at 2025-03-05 04:29:24 (275 → 284) during SEND

### Machine 2

- Total Jumps: 105

Top 5 largest jumps:
- Jump of 11 at 2025-03-05 04:29:21 (256 → 267) during INTERNAL
- Jump of 10 at 2025-03-05 04:29:30 (314 → 324) during RECEIVE
- Jump of 9 at 2025-03-05 04:28:42 (19 → 28) during SEND
- Jump of 9 at 2025-03-05 04:29:23 (271 → 280) during INTERNAL
- Jump of 8 at 2025-03-05 04:29:13 (208 → 216) during INTERNAL

## Conclusions

1. **Clock Rate**: Machine 1 had the highest logical clock rate at 6.24 ticks/second.
2. **Event Volume**: Machine 2 processed the most events (392).
3. **Queue Size**: Machine 0 had the largest queue size (11).
5. **Clock Jumps**: A total of 253 significant clock jumps were detected across all machines.

### Observations on Lamport Clock Behavior

- The logical clocks advance at different rates due to the different execution speeds of the machines.
- Message receipt causes clock jumps when the sender's clock is ahead of the receiver's clock.
- The queue sizes fluctuate based on the balance between incoming messages and processing rate.
- Internal events cause the logical clock to advance by exactly 1, while receive events may cause larger jumps.