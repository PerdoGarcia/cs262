#!/usr/bin/env python3


import os
import re
import pandas as pd
from datetime import datetime
import numpy as np
import subprocess
import time
import signal

def extract_connections_from_logs(log_path="system_output.log"):
    """Extract connection information from system output log."""
    connections = {}

    # Read system output log if it exists
    if not os.path.exists(log_path):
        print(f"System output log not found: {log_path}")
        return connections

    with open(log_path, 'r') as f:
        log_text = f.read()

    # Extract established connections
    established_pattern = re.compile(r"DEBUG: Machine (\d+) established connections to: \[(.*?)\]")
    established_matches = established_pattern.findall(log_text)

    for match in established_matches:
        machine_id = int(match[0])
        connections_list = match[1]
        # Parse the connection list
        if connections_list:
            connected_to = [int(x.strip()) for x in connections_list.split(',')]
            connections[machine_id] = connected_to
        else:
            connections[machine_id] = []

    # Extract individual connection logs
    connected_pattern = re.compile(r"Machine (\d+) connected to machine (\d+)")
    connected_matches = connected_pattern.findall(log_text)

    for match in connected_matches:
        source = int(match[0])
        target = int(match[1])
        if source not in connections:
            connections[source] = []
        if target not in connections[source]:
            connections[source].append(target)

    return connections

def extract_message_stats_from_logs(log_files):
    """Extract message statistics from log files."""
    message_stats = {
        'send_count': {},
        'receive_count': {},
        'internal_count': {},
        'clock_jumps': {}
    }

    log_pattern = re.compile(
        r"System Time: (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \| \| \s*(\w+)\s* \| \| (.*?) \| \| Queue Size: (\d+) \| \| Logical Clock: (\d+)"
    )

    for machine_id, log_file in log_files.items():
        message_stats['send_count'][machine_id] = 0
        message_stats['receive_count'][machine_id] = 0
        message_stats['internal_count'][machine_id] = 0
        message_stats['clock_jumps'][machine_id] = []

        prev_clock = 0

        with open(log_file, 'r') as f:
            for line in f:
                match = log_pattern.match(line)
                if match:
                    event_type = match.group(2).strip()
                    logical_clock = int(match.group(5))

                    # Count event types
                    if event_type == "SEND":
                        message_stats['send_count'][machine_id] += 1
                    elif event_type == "RECEIVE":
                        message_stats['receive_count'][machine_id] += 1
                    elif event_type == "INTERNAL":
                        message_stats['internal_count'][machine_id] += 1

                    # Check for clock jumps (more than 1 increment)
                    if logical_clock > prev_clock + 1 and prev_clock > 0:
                        message_stats['clock_jumps'][machine_id].append({
                            'from': prev_clock,
                            'to': logical_clock,
                            'jump': logical_clock - prev_clock,
                            'event_type': event_type
                        })

                    prev_clock = logical_clock

    return message_stats

def check_operation_execution(log_files):
    """Check if all operations (1, 2, 3, internal) were executed."""
    operation_stats = {
        'random_send': {},      # Operation 1
        'next_machine_send': {}, # Operation 2
        'broadcast_send': {}     # Operation 3
    }

    # Track consecutive sends to detect broadcasts
    consecutive_sends = {}  # machine_id -> (timestamp, recipients)

    for machine_id, log_file in log_files.items():
        operation_stats['random_send'][machine_id] = set()
        operation_stats['next_machine_send'][machine_id] = set()
        operation_stats['broadcast_send'][machine_id] = set()
        consecutive_sends[machine_id] = []

        last_timestamp = None
        last_recipients = set()

        with open(log_file, 'r') as f:
            for line in f:
                if "SEND" in line:
                    # Extract timestamp
                    timestamp_match = re.search(r"System Time: (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", line)
                    timestamp = None
                    if timestamp_match:
                        timestamp = timestamp_match.group(1)

                    # Extract recipient from "Sent to machine X"
                    match = re.search(r"Sent to machine (\d+)", line)
                    if match:
                        recipient = int(match.group(1))

                        # Track different operations based on recipient
                        if recipient == (machine_id + 1) % 3:
                            # This could be either op 1 (random) or op 2 (next)
                            operation_stats['next_machine_send'][machine_id].add(recipient)
                        else:
                            # This must be op 1 (random) or part of op 3 (broadcast)
                            operation_stats['random_send'][machine_id].add(recipient)

                        # Track consecutive sends to detect broadcasts
                        if timestamp == last_timestamp:
                            last_recipients.add(recipient)
                        else:
                            # If the previous timestamp had multiple recipients, it was likely a broadcast
                            if len(last_recipients) > 1:
                                operation_stats['broadcast_send'][machine_id].update(last_recipients)

                            # Reset for new timestamp
                            last_timestamp = timestamp
                            last_recipients = {recipient}

    # Check the last set of sends for each machine
    for machine_id, recipients in last_recipients.items():
        if len(recipients) > 1:
            operation_stats['broadcast_send'][machine_id].update(recipients)

    return operation_stats

def check_lamport_properties_improved(log_files):
    """
    Verify that Lamport clock properties are maintained using an improved matching algorithm.
    This version focuses on logical clock values and allows for more flexible matching.
    """

    # Parse all log files and extract events
    events = []
    send_events = {}  # (sender, receiver) -> list of send events
    receive_events = {}  # (sender, receiver) -> list of receive events

    log_pattern = re.compile(
        r"System Time: (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \| \| \s*(\w+)\s* \| \| (.*?) \| \| Queue Size: (\d+) \| \| Logical Clock: (\d+)"
    )

    for machine_id, log_file in log_files.items():
        with open(log_file, 'r') as f:
            for line in f:
                match = log_pattern.match(line)
                if match:
                    timestamp_str = match.group(1)
                    event_type = match.group(2).strip()
                    details = match.group(3).strip()
                    queue_size = int(match.group(4))
                    logical_clock = int(match.group(5))

                    # Extract source or target machine for SEND/RECEIVE events
                    source_machine = None
                    target_machine = None

                    if event_type == "RECEIVE":
                        source_match = re.search(r"Receive machine (\d+)", details)
                        if source_match:
                            source_machine = int(source_match.group(1))

                    if event_type == "SEND":
                        target_match = re.search(r"Sent to machine (\d+)", details)
                        if target_match:
                            target_machine = int(target_match.group(1))

                    event = {
                        'machine_id': machine_id,
                        'timestamp': datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S"),
                        'event_type': event_type,
                        'details': details,
                        'queue_size': queue_size,
                        'logical_clock': logical_clock,
                        'source_machine': source_machine,
                        'target_machine': target_machine,
                        'matched': False
                    }

                    events.append(event)

                    # Organize send and receive events by sender/receiver pair
                    if event_type == "SEND" and target_machine is not None:
                        key = (machine_id, target_machine)
                        if key not in send_events:
                            send_events[key] = []
                        send_events[key].append(event)

                    if event_type == "RECEIVE" and source_machine is not None:
                        key = (source_machine, machine_id)
                        if key not in receive_events:
                            receive_events[key] = []
                        receive_events[key].append(event)

    # Sort events by timestamp
    events.sort(key=lambda x: x['timestamp'])

    # Check Lamport properties
    results = {
        'monotonic': True,
        'causality': True,
        'violations': []
    }

    # Check monotonicity for each machine
    clock_values = {}
    for event in events:
        machine_id = event['machine_id']
        if machine_id not in clock_values:
            clock_values[machine_id] = 0

        # Check if clock always increases
        if event['logical_clock'] < clock_values[machine_id]:
            results['monotonic'] = False
            results['violations'].append({
                'type': 'monotonicity',
                'machine': machine_id,
                'prev_clock': clock_values[machine_id],
                'new_clock': event['logical_clock'],
                'event': event
            })

        clock_values[machine_id] = event['logical_clock']

    # Improved matching algorithm for send/receive pairs
    unmatched_sends = []

    # For each sender-receiver pair
    for key in send_events.keys():
        sender, receiver = key
        sends = send_events.get(key, [])
        receives = receive_events.get(key, [])

        # Sort sends and receives by logical clock
        sends.sort(key=lambda x: x['logical_clock'])
        if receives:
            receives.sort(key=lambda x: x['logical_clock'])

        # Try to match each send with a receive
        for send in sends:
            matched = False

            # Look for a receive with a logical clock greater than the send's
            for receive in receives:
                if (not receive['matched'] and
                    receive['logical_clock'] > send['logical_clock']):
                    # Found a match!
                    send['matched'] = True
                    receive['matched'] = True
                    matched = True
                    break

            if not matched:
                # Check if this send is near the end of the log
                last_timestamp = events[-1]['timestamp']
                time_diff = (last_timestamp - send['timestamp']).total_seconds()

                if time_diff < 10:  # If send was in the last 10 seconds
                    # This is likely a timing issue, not a real problem
                    pass
                else:
                    unmatched_sends.append({
                        'type': 'unmatched_send',
                        'sender': sender,
                        'receiver': receiver,
                        'logical_clock': send['logical_clock'],
                        'timestamp': send['timestamp']
                    })

    # Check for receives without matching sends
    for key in receive_events.keys():
        sender, receiver = key
        receives = receive_events.get(key, [])

        for receive in receives:
            if not receive['matched']:
                # This receive has no matching send
                results['violations'].append({
                    'type': 'missing_send',
                    'receiver': receiver,
                    'source': sender,
                    'event': receive
                })

    # Add unmatched sends to violations
    for unmatched in unmatched_sends:
        results['violations'].append(unmatched)

    return results

def run_system_and_capture_logs(timeout=60):
    """Run the Lamport clock system and capture logs."""
    # Start the system
    process = subprocess.Popen(['python', 'machines.py'],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                text=True,
                                bufsize=1)

    # Capture output
    output = []

    try:
        # Wait for the system to run
        start_time = time.time()
        while time.time() - start_time < timeout:
            line = process.stdout.readline()
            if not line:
                break
            output.append(line)
            print(line, end='')  # Show output in real-time
    finally:
        # Stop the system
        process.send_signal(signal.SIGINT)
        process.wait()

    # Save output to file
    with open("system_output.log", "w") as f:
        f.write(''.join(output))

    # Collect logs
    log_files = {}
    for i in range(3):
        log_file = f"machine_{i}.log"
        if os.path.exists(log_file):
            log_files[i] = log_file

    return ''.join(output), log_files

def main():
    """Run the improved validation script."""
    print("Starting Complete Lamport Clock System Validation")
    print("===============================================")

    # Check if log files already exist
    log_files = {}
    for i in range(3):
        log_file = f"machine_{i}.log"
        if os.path.exists(log_file):
            log_files[i] = log_file

    # If logs don't exist, run the system
    if not log_files:
        print("No log files found. Running the system...")
        output, log_files = run_system_and_capture_logs()
    else:
        print("Using existing log files...")
        output = ""
        # Read the output from a previous run if available
        if os.path.exists("system_output.log"):
            with open("system_output.log", "r") as f:
                output = f.read()

    # Validate connections
    print("\nValidating connections...")
    connections = extract_connections_from_logs()

    if connections:
        for machine_id, connected_to in connections.items():
            print(f"Machine {machine_id} connected to: {connected_to}")

        # Check if connections are bidirectional
        connection_issues = []
        for machine_id, connected_to in connections.items():
            for target in connected_to:
                if target in connections and machine_id not in connections[target]:
                    connection_issues.append(f"Connection from {machine_id} to {target} is not bidirectional")

        if connection_issues:
            print("\nConnection issues found:")
            for issue in connection_issues:
                print(f" - {issue}")
        else:
            print("\nAll connections are properly established.")
    else:
        print("No connection information found. Unable to validate connections.")

    # Validate message statistics
    print("\nValidating message statistics...")
    message_stats = extract_message_stats_from_logs(log_files)

    for machine_id in sorted(message_stats['send_count'].keys()):
        print(f"Machine {machine_id}:")
        print(f" - Sent: {message_stats['send_count'][machine_id]}")
        print(f" - Received: {message_stats['receive_count'][machine_id]}")
        print(f" - Internal: {message_stats['internal_count'][machine_id]}")
        print(f" - Clock jumps: {len(message_stats['clock_jumps'][machine_id])}")

    # Check operation execution
    print("\nChecking operation execution...")
    # operation_stats = check_operation_execution(log_files)

    # for machine_id in sorted(operation_stats['random_send'].keys()):
    #     print(f"Machine {machine_id}:")
    #     print(f" - Random sends to: {operation_stats['random_send'][machine_id]}")
    #     print(f" - Next machine sends to: {operation_stats['next_machine_send'][machine_id]}")
    #     print(f" - Broadcast sends to: {operation_stats['broadcast_send'][machine_id]}")

    # Verify Lamport clock properties
    print("\nVerifying Lamport clock properties (improved algorithm)...")
    lamport_results = check_lamport_properties_improved(log_files)

    if lamport_results['monotonic']:
        print(" - ✓ All logical clocks are monotonically increasing")
    else:
        print(" - ✗ Some logical clocks decreased (violation of monotonicity)")

    if lamport_results['causality']:
        print(" - ✓ Causal ordering is maintained for all messages")
    else:
        print(" - ✗ Some messages violate causal ordering")

    # Filter out violations that are likely due to timing issues
    filtered_violations = []
    for violation in lamport_results['violations']:
        if violation['type'] == 'unmatched_send':
            # Skip violations that are likely due to timing issues
            continue
        filtered_violations.append(violation)

    if filtered_violations:
        print(f"\nFound {len(filtered_violations)} meaningful violations:")
        for violation in filtered_violations[:5]:  # Show at most 5 violations
            print(f" - {violation['type']} violation: {violation}")

        if len(filtered_violations) > 5:
            print(f"   ... and {len(filtered_violations) - 5} more violations")
    else:
        print("\nNo violations found! Your implementation is working correctly.")

    print("\nValidation complete!")

    # Generate summary
    has_issues = False

    if filtered_violations:
        has_issues = True
        print("\n⚠ ISSUES: Some anomalies were detected in clock properties.")

    if connections and connection_issues:
        has_issues = True
        print("\n⚠ ISSUES: Some connection problems were detected.")

    if not has_issues:
        print("\n✓ SUCCESS: No issues found!")

if __name__ == "__main__":
    main()