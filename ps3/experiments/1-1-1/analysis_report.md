# Lamport Clock Analysis Report

## Executive Summary

This report analyzes the behavior of a distributed system using Lamport logical clocks. 
The system consists of three machines communicating via message passing, 
with each machine maintaining its own logical clock according to the Lamport algorithm.

## Clock Rate Comparison

### Machine 0

- Start Time: 2025-03-05 04:12:57
- End Time: 2025-03-05 04:13:56
- Time Span: 59.00 seconds
- Start Clock: 0
- End Clock: 59
- Clock Range: 59
- Clock Rate: 1.00 ticks/second

### Machine 1

- Start Time: 2025-03-05 04:12:57
- End Time: 2025-03-05 04:13:56
- Time Span: 59.00 seconds
- Start Clock: 0
- End Clock: 60
- Clock Range: 60
- Clock Rate: 1.02 ticks/second

### Machine 2

- Start Time: 2025-03-05 04:12:57
- End Time: 2025-03-05 04:13:56
- Time Span: 59.00 seconds
- Start Clock: 0
- End Clock: 59
- Clock Range: 59
- Clock Rate: 1.00 ticks/second

## Event Count Analysis

### Machine 0

- Total Events: 72
- INTERNAL: 31 (43.06%)
- SEND: 29 (40.28%)
- RECEIVE: 11 (15.28%)
- INITIAL: 1 (1.39%)

### Machine 1

- Total Events: 64
- INTERNAL: 28 (43.75%)
- RECEIVE: 19 (29.69%)
- SEND: 16 (25.00%)
- INITIAL: 1 (1.56%)

### Machine 2

- Total Events: 64
- RECEIVE: 24 (37.50%)
- INTERNAL: 23 (35.94%)
- SEND: 16 (25.00%)
- INITIAL: 1 (1.56%)

## Queue Size Analysis

### Machine 0

- Maximum Queue Size: 1
- Minimum Queue Size: 0
- Mean Queue Size: 0.01
- Median Queue Size: 0.0
- Final Queue Size: 0

Average Queue Size by Event Type:
- INITIAL: 0.00
- INTERNAL: 0.00
- RECEIVE: 0.09
- SEND: 0.00

### Machine 1

- Maximum Queue Size: 1
- Minimum Queue Size: 0
- Mean Queue Size: 0.02
- Median Queue Size: 0.0
- Final Queue Size: 0

Average Queue Size by Event Type:
- INITIAL: 0.00
- SEND: 0.00
- INTERNAL: 0.00
- RECEIVE: 0.05

### Machine 2

- Maximum Queue Size: 2
- Minimum Queue Size: 0
- Mean Queue Size: 0.22
- Median Queue Size: 0.0
- Final Queue Size: 0

Average Queue Size by Event Type:
- INITIAL: 0.00
- INTERNAL: 0.00
- SEND: 0.00
- RECEIVE: 0.58

## Clock Jump Analysis

### Machine 0

- Total Jumps: 10

Top 5 largest jumps:
- Jump of 2 at 2025-03-05 04:12:59 (1 → 3) during RECEIVE
- Jump of 2 at 2025-03-05 04:13:02 (4 → 6) during RECEIVE
- Jump of 2 at 2025-03-05 04:13:11 (13 → 15) during RECEIVE
- Jump of 2 at 2025-03-05 04:13:25 (27 → 29) during RECEIVE
- Jump of 2 at 2025-03-05 04:13:31 (33 → 35) during RECEIVE

### Machine 1

- Total Jumps: 13

Top 5 largest jumps:
- Jump of 2 at 2025-03-05 04:13:02 (4 → 6) during RECEIVE
- Jump of 2 at 2025-03-05 04:13:05 (7 → 9) during RECEIVE
- Jump of 2 at 2025-03-05 04:13:08 (10 → 12) during RECEIVE
- Jump of 2 at 2025-03-05 04:13:10 (12 → 14) during RECEIVE
- Jump of 2 at 2025-03-05 04:13:15 (17 → 19) during RECEIVE

### Machine 2

- Total Jumps: 11

Top 5 largest jumps:
- Jump of 2 at 2025-03-05 04:13:05 (7 → 9) during RECEIVE
- Jump of 2 at 2025-03-05 04:13:11 (13 → 15) during RECEIVE
- Jump of 2 at 2025-03-05 04:13:13 (15 → 17) during RECEIVE
- Jump of 2 at 2025-03-05 04:13:26 (28 → 30) during RECEIVE
- Jump of 2 at 2025-03-05 04:13:36 (38 → 40) during RECEIVE

## Conclusions

1. **Clock Rate**: Machine 1 had the highest logical clock rate at 1.02 ticks/second.
2. **Event Volume**: Machine 0 processed the most events (72).
3. **Queue Size**: Machine 2 had the largest queue size (2).
5. **Clock Jumps**: A total of 34 significant clock jumps were detected across all machines.

### Observations on Lamport Clock Behavior

- The logical clocks advance at different rates due to the different execution speeds of the machines.
- Message receipt causes clock jumps when the sender's clock is ahead of the receiver's clock.
- The queue sizes fluctuate based on the balance between incoming messages and processing rate.
- Internal events cause the logical clock to advance by exactly 1, while receive events may cause larger jumps.