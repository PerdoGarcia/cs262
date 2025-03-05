#!/usr/bin/env python3
"""
Lamport Clock Analysis Tool - Interactive script for analyzing Lamport clock logs.
This tool works directly with the output from the distributed system simulation.
"""

import os
import sys
import argparse
from datetime import datetime
import shutil

# Import the analyzer
from clock_analyzer import LamportClockAnalyzer

def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """Print a header for the tool."""
    print("\n" + "="*80)
    print(" "*30 + "LAMPORT CLOCK ANALYZER")
    print("="*80 + "\n")

def print_menu():
    """Print the main menu options."""
    print("\nPlease select an option:")
    print("1. Analyze log files")
    print("2. Compare logical clock rates")
    print("3. Analyze queue sizes")
    print("4. Find clock jumps")
    print("5. Analyze event distribution")
    # print("6. Analyze message patterns")
    print("7. Generate comprehensive report with visualizations")
    print("8. Run quick analysis (all metrics, no visualizations)")
    print("9. Exit")
    print("\nEnter your choice (1-9): ", end="")

def get_log_files():
    """Get log file paths from user."""
    log_files = {}

    print("\nEnter the path to each machine's log file (leave blank to use default names):")

    for i in range(3):
        default_name = f"machine_{i}.log"

        if os.path.exists(default_name):
            print(f"Found default log file: {default_name}")
            use_default = input(f"Use this file for Machine {i}? (Y/n): ").strip().lower()

            if use_default == "" or use_default == "y":
                log_files[i] = default_name
                continue

        while True:
            file_path = input(f"Machine {i} log file path (default: {default_name}): ").strip()

            if not file_path:
                file_path = default_name

            if os.path.exists(file_path):
                log_files[i] = file_path
                break
            else:
                print(f"Error: File '{file_path}' not found.")
                retry = input("Try again? (Y/n): ").strip().lower()
                if retry == "n":
                    break

    return log_files

def analyze_logs(analyzer):
    """Parse logs and display basic statistics."""
    clear_screen()
    print_header()
    print("Analyzing log files...\n")

    analyzer.parse_logs()

    print("\nAnalysis complete!")
    print("\nBasic statistics:")

    for machine_id, log_df in analyzer.logs.items():
        if log_df.empty:
            print(f"Machine {machine_id}: No data available")
            continue

        print(f"\nMachine {machine_id}:")
        print(f"  - Total events: {len(log_df)}")
        print(f"  - Time span: {(log_df['timestamp'].max() - log_df['timestamp'].min()).total_seconds():.2f} seconds")
        print(f"  - Logical clock range: {log_df['logical_clock'].min()} to {log_df['logical_clock'].max()}")

        # Event type breakdown
        event_counts = log_df['event_type'].value_counts()
        print("  - Event breakdown:")
        for event_type, count in event_counts.items():
            print(f"    - {event_type}: {count} ({count/len(log_df)*100:.1f}%)")

    input("\nPress Enter to continue...")

def compare_clock_rates(analyzer):
    """Compare logical clock rates between machines."""
    clear_screen()
    print_header()
    print("Comparing logical clock rates...\n")

    clock_rates = analyzer.compare_clock_rates()

    print("\nClock Rate Comparison:")
    for machine_id, stats in clock_rates.items():
        print(f"\nMachine {machine_id}:")
        print(f"  - Start Time: {stats['start_time']}")
        print(f"  - End Time: {stats['end_time']}")
        print(f"  - Time Span: {stats['time_span_seconds']:.2f} seconds")
        print(f"  - Start Clock: {stats['start_clock']}")
        print(f"  - End Clock: {stats['end_clock']}")
        print(f"  - Clock Range: {stats['clock_range']}")
        print(f"  - Clock Rate: {stats['clock_rate']:.2f} ticks/second")

    # Find machine with the fastest clock rate
    fastest_machine = max(clock_rates.items(), key=lambda x: x[1]['clock_rate'])[0]
    print(f"\nMachine {fastest_machine} had the fastest logical clock rate.")

    # Ask if user wants to see visualized comparison
    visualize = input("\nWould you like to see a visualization of the clock progression? (y/N): ").strip().lower()
    if visualize == 'y':
        print("\nGenerating visualization...")
        analyzer.plot_logical_clocks()

    input("\nPress Enter to continue...")

def analyze_queue_sizes(analyzer):
    """Analyze queue sizes over time for each machine."""
    clear_screen()
    print_header()
    print("Analyzing queue sizes...\n")

    queue_stats = analyzer.analyze_queue_sizes()

    print("\nQueue Size Analysis:")
    for machine_id, stats in queue_stats.items():
        print(f"\nMachine {machine_id}:")
        print(f"  - Maximum Queue Size: {stats['max']}")
        print(f"  - Minimum Queue Size: {stats['min']}")
        print(f"  - Mean Queue Size: {stats['mean']:.2f}")
        print(f"  - Median Queue Size: {stats['median']}")
        print(f"  - Final Queue Size: {stats['end_value']}")

        print("\n  Average Queue Size by Event Type:")
        for event, avg in stats['by_event_type'].items():
            print(f"  - {event}: {avg:.2f}")

    # Find machine with the largest queue
    largest_queue_machine = max(queue_stats.items(), key=lambda x: x[1]['max'])[0]
    print(f"\nMachine {largest_queue_machine} had the largest queue size ({queue_stats[largest_queue_machine]['max']}).")

    # Ask if user wants to see visualized comparison
    visualize = input("\nWould you like to see a visualization of the queue sizes over time? (y/N): ").strip().lower()
    if visualize == 'y':
        print("\nGenerating visualization...")
        analyzer.plot_queue_sizes()

    input("\nPress Enter to continue...")

def find_clock_jumps(analyzer):
    """Find jumps in logical clocks across machines."""
    clear_screen()
    print_header()
    print("Finding clock jumps...\n")

    threshold = input("Enter minimum jump threshold (default: 1): ").strip()
    threshold = int(threshold) if threshold and threshold.isdigit() else 1

    clock_jumps = analyzer.find_clock_jumps(threshold=threshold)

    print(f"\nClock Jump Analysis (threshold = {threshold}):")
    for machine_id, jumps in clock_jumps.items():
        print(f"\nMachine {machine_id}:")
        if jumps:
            print(f"  - Total Jumps: {len(jumps)}")

            # Calculate statistics
            jump_sizes = [jump['jump'] for jump in jumps]
            avg_jump = sum(jump_sizes) / len(jump_sizes)
            max_jump = max(jump_sizes)

            print(f"  - Average Jump Size: {avg_jump:.2f}")
            print(f"  - Maximum Jump Size: {max_jump}")

            print("\n  Top 5 largest jumps:")
            for jump in sorted(jumps, key=lambda x: x['jump'], reverse=True)[:5]:
                print(f"  - Jump of {jump['jump']} at {jump['to_time']} ({jump['from_clock']} → {jump['to_clock']}) during {jump['event_type']}")
        else:
            print("  No significant clock jumps detected.")

    # Ask if user wants to see visualized comparison
    visualize = input("\nWould you like to see a histogram of clock jumps? (y/N): ").strip().lower()
    if visualize == 'y':
        print("\nGenerating visualization...")
        analyzer.plot_clock_jump_histogram()

    input("\nPress Enter to continue...")

def analyze_event_distribution(analyzer):
    """Analyze the distribution of event types across machines."""
    clear_screen()
    print_header()
    print("Analyzing event distribution...\n")

    event_counts = analyzer.get_event_counts()

    print("\nEvent Distribution Analysis:")
    for machine_id, counts in event_counts.items():
        print(f"\nMachine {machine_id}:")
        print(f"  - Total Events: {counts['total']}")

        # Sort events by count
        sorted_events = sorted(counts['counts'].items(), key=lambda x: x[1], reverse=True)

        for event, count in sorted_events:
            print(f"  - {event}: {count} ({counts['percentages'][event]:.2f}%)")

    # Calculate overall event distribution
    overall_counts = {}
    for machine in event_counts.values():
        for event, count in machine['counts'].items():
            if event not in overall_counts:
                overall_counts[event] = 0
            overall_counts[event] += count

    total_events = sum(overall_counts.values())

    print("\nOverall Event Distribution:")
    for event, count in sorted(overall_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {event}: {count} ({count/total_events*100:.2f}%)")

    # Ask if user wants to see visualized comparison
    visualize = input("\nWould you like to see a visualization of the event distribution? (y/N): ").strip().lower()
    if visualize == 'y':
        print("\nGenerating visualization...")
        analyzer.plot_event_distribution()

    input("\nPress Enter to continue...")

# def analyze_message_patterns(analyzer):
#     """Analyze message patterns between machines."""
#     clear_screen()
#     print_header()
#     print("Analyzing message patterns...\n")

#     patterns = analyzer.analyze_message_patterns()
#     message_matrix = patterns["message_matrix"]

#     print("\nMessage Pattern Analysis:")

#     # Print message matrix
#     print("\nMessage Count Matrix (From → To):")
#     print("    | M0  | M1  | M2  |")
#     print("----|-----|-----|-----|")
#     for i in range(3):
#         row = f"M{i} |"
#         for j in range(3):
#             row += f" {int(message_matrix[i][j]):3d} |"
#         print(row)

#     # Calculate totals
#     print("\nTotal Messages:")
#     for i in range(3):
#         sent = sum(message_matrix[i])
#         received = sum(message_matrix[:, i])
#         print(f"- Machine {i}: Sent {int(sent)} messages, Received {int(received)} messages")

#     # Calculate percentages
#     total_messages = message_matrix.sum()
#     if total_messages > 0:
#         print("\nMessage Distribution:")
#         for i in range(3):
#             for j in range(3):
#                 if i != j and message_matrix[i][j] > 0:
#                     percentage = (message_matrix[i][j] / total_messages) * 100
#                     print(f"- {percentage:.1f}% of messages were sent from Machine {i} to Machine {j}")

#     # Ask if user wants to see visualized comparison
#     visualize = input("\nWould you like to see a visualization of the message flow? (y/N): ").strip().lower()
#     if visualize == 'y':
#         print("\nGenerating visualization...")
#         analyzer.plot_message_flow()

#     input("\nPress Enter to continue...")

def generate_report(analyzer):
    """Generate a comprehensive report with visualizations."""
    clear_screen()
    print_header()
    print("Generating comprehensive report...\n")

    output_dir = input("Enter output directory (default: 'analysis_results'): ").strip()
    if not output_dir:
        output_dir = "analysis_results"

    print(f"\nGenerating report in '{output_dir}'...")
    report_path = analyzer.generate_full_report(output_dir)

    print(f"\nReport generation complete!")
    print(f"Report saved to: {report_path}")
    print(f"Visualizations saved to: {output_dir}")

    # Check if we can open the report
    open_report = input("\nWould you like to open the report now? (y/N): ").strip().lower()
    if open_report == 'y':
        try:
            if sys.platform == 'win32':
                os.startfile(report_path)
            elif sys.platform == 'darwin':  # macOS
                os.system(f'open "{report_path}"')
            else:  # Linux
                os.system(f'xdg-open "{report_path}"')
            print("\nOpened report in default application.")
        except Exception as e:
            print(f"\nError opening report: {e}")
            print(f"Please open the file manually: {report_path}")

    input("\nPress Enter to continue...")

def run_quick_analysis(analyzer):
    """Run a quick analysis showing all metrics without visualizations."""
    clear_screen()
    print_header()
    print("Running quick analysis...\n")

    # Parse logs if needed
    if not analyzer.logs:
        print("Parsing log files...")
        analyzer.parse_logs()

    # Get all metrics
    clock_rates = analyzer.compare_clock_rates()
    event_counts = analyzer.get_event_counts()
    queue_stats = analyzer.analyze_queue_sizes()
    clock_jumps = analyzer.find_clock_jumps(threshold=1)
    # message_patterns = analyzer.analyze_message_patterns()

    # Display clock rates
    print("\n=== CLOCK RATE COMPARISON ===")
    for machine_id, stats in clock_rates.items():
        print(f"\nMachine {machine_id}:")
        print(f"  Clock Rate: {stats['clock_rate']:.2f} ticks/second")
        print(f"  Clock Range: {stats['start_clock']} → {stats['end_clock']} ({stats['clock_range']} ticks)")
        print(f"  Time Span: {stats['time_span_seconds']:.2f} seconds")

    # Display event counts
    print("\n=== EVENT DISTRIBUTION ===")
    for machine_id, counts in event_counts.items():
        print(f"\nMachine {machine_id} ({counts['total']} events):")
        for event, count in sorted(counts['counts'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {event}: {count} ({counts['percentages'][event]:.1f}%)")

    # Display queue stats
    print("\n=== QUEUE SIZE ANALYSIS ===")
    for machine_id, stats in queue_stats.items():
        print(f"\nMachine {machine_id}:")
        print(f"  Max: {stats['max']}, Min: {stats['min']}, Avg: {stats['mean']:.2f}, Final: {stats['end_value']}")

    # Display clock jumps
    print("\n=== CLOCK JUMP ANALYSIS ===")
    for machine_id, jumps in clock_jumps.items():
        if jumps:
            print(f"\nMachine {machine_id}: {len(jumps)} jumps")
            jump_sizes = [jump['jump'] for jump in jumps]
            print(f"  Avg Jump: {sum(jump_sizes)/len(jump_sizes):.2f}, Max Jump: {max(jump_sizes)}")
        else:
            print(f"\nMachine {machine_id}: No significant jumps")

    # Display message patterns
    print("\n=== MESSAGE PATTERN ANALYSIS ===")
    message_matrix = message_patterns["message_matrix"]
    for i in range(3):
        sent = sum(message_matrix[i])
        received = sum(message_matrix[:, i])
        print(f"Machine {i}: Sent {int(sent)}, Received {int(received)}")

    # Display conclusions
    print("\n=== CONCLUSIONS ===")

    # Find machine with highest clock rate
    max_rate_machine = max(clock_rates.items(), key=lambda x: x[1]['clock_rate'])[0]
    max_rate = clock_rates[max_rate_machine]['clock_rate']
    print(f"- Machine {max_rate_machine} had the highest logical clock rate ({max_rate:.2f} ticks/second)")

    # Find machine with most events
    most_events_machine = max(event_counts.items(), key=lambda x: x[1]['total'])[0]
    most_events = event_counts[most_events_machine]['total']
    print(f"- Machine {most_events_machine} processed the most events ({most_events})")

    # Find machine with largest queue
    largest_queue_machine = max(queue_stats.items(), key=lambda x: x[1]['max'])[0]
    largest_queue = queue_stats[largest_queue_machine]['max']
    print(f"- Machine {largest_queue_machine} had the largest queue size ({largest_queue})")

    input("\nPress Enter to continue...")

def main():
    """Main function to run the interactive analysis tool."""
    parser = argparse.ArgumentParser(description="Lamport Clock Analysis Tool")
    parser.add_argument("--quick", action="store_true", help="Run quick analysis and exit")
    parser.add_argument("--report", action="store_true", help="Generate full report and exit")
    parser.add_argument("--output", type=str, default="analysis_results", help="Output directory for report")
    args = parser.parse_args()

    # Initialize the analyzer
    if os.path.exists("machine_0.log") and os.path.exists("machine_1.log") and os.path.exists("machine_2.log"):
        analyzer = LamportClockAnalyzer({
            0: "machine_0.log",
            1: "machine_1.log",
            2: "machine_2.log"
        })
        analyzer.parse_logs()
    else:
        analyzer = LamportClockAnalyzer()

    # Check for command line arguments
    if args.quick:
        run_quick_analysis(analyzer)
        return
    elif args.report:
        print("Generating report...")
        analyzer.generate_full_report(args.output)
        print(f"Report generated in {args.output}")
        return

    # Interactive mode
    while True:
        clear_screen()
        print_header()

        # Check if we have logs loaded
        if not analyzer.logs:
            print("No log files have been analyzed yet.")
            print("You'll need to provide log file paths in the next step.\n")
        else:
            print("Log files loaded:")
            for machine_id, file_path in analyzer.log_files.items():
                print(f"- Machine {machine_id}: {file_path}")
            print()

        print_menu()

        choice = input().strip()

        if choice == "1":
            # Get log files if not already loaded
            if not analyzer.log_files:
                log_files = get_log_files()
                for machine_id, file_path in log_files.items():
                    analyzer.add_log_file(machine_id, file_path)

            analyze_logs(analyzer)

        elif choice == "2":
            if not analyzer.logs:
                log_files = get_log_files()
                for machine_id, file_path in log_files.items():
                    analyzer.add_log_file(machine_id, file_path)
                analyzer.parse_logs()

            compare_clock_rates(analyzer)

        elif choice == "3":
            if not analyzer.logs:
                log_files = get_log_files()
                for machine_id, file_path in log_files.items():
                    analyzer.add_log_file(machine_id, file_path)
                analyzer.parse_logs()

            analyze_queue_sizes(analyzer)

        elif choice == "4":
            if not analyzer.logs:
                log_files = get_log_files()
                for machine_id, file_path in log_files.items():
                    analyzer.add_log_file(machine_id, file_path)
                analyzer.parse_logs()

            find_clock_jumps(analyzer)

        elif choice == "5":
            if not analyzer.logs:
                log_files = get_log_files()
                for machine_id, file_path in log_files.items():
                    analyzer.add_log_file(machine_id, file_path)
                analyzer.parse_logs()

            analyze_event_distribution(analyzer)

        # elif choice == "6":
        #     if not analyzer.logs:
        #         log_files = get_log_files()
        #         for machine_id, file_path in log_files.items():
        #             analyzer.add_log_file(machine_id, file_path)
        #         analyzer.parse_logs()

        #     analyze_message_patterns(analyzer)

        elif choice == "7":
            if not analyzer.logs:
                log_files = get_log_files()
                for machine_id, file_path in log_files.items():
                    analyzer.add_log_file(machine_id, file_path)
                analyzer.parse_logs()

            generate_report(analyzer)

        elif choice == "8":
            if not analyzer.logs:
                log_files = get_log_files()
                for machine_id, file_path in log_files.items():
                    analyzer.add_log_file(machine_id, file_path)
                analyzer.parse_logs()

            run_quick_analysis(analyzer)

        elif choice == "9":
            print("\nExiting Lamport Clock Analyzer. Goodbye!")
            break

        else:
            print("\nInvalid choice. Please try again.")
            input("\nPress Enter to continue...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nProgram interrupted. Exiting...")
        sys.exit(0)