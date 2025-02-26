#!/usr/bin/env python3

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import argparse
import os
from tabulate import tabulate

def load_data(grpc_file, json_file, wire_file):
    """Load data from the CSV files"""

    # Check if files exist
    files_to_check = [
        (grpc_file, "gRPC"),
        (json_file, "JSON"),
        (wire_file, "Wire Protocol")
    ]

    dataframes = {}
    for file_path, protocol in files_to_check:
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            df['protocol'] = protocol  # Add a column to identify the protocol
            dataframes[protocol] = df
            print(f"Loaded {len(df)} records from {protocol} metrics file")
        else:
            print(f"Warning: {protocol} metrics file '{file_path}' not found")

    if not dataframes:
        print("Error: No data files found. Please run the experiments first.")
        return None

    return dataframes

def analyze_operation_metrics(dataframes):
    """Analyze metrics by operation for each protocol"""

    all_stats = []

    # Get unique operations across all dataframes
    all_operations = set()
    for protocol, df in dataframes.items():
        all_operations.update(df['operation'].unique())

    # Compare metrics for each operation
    for operation in sorted(all_operations):
        operation_stats = {'operation': operation}

        for protocol, df in dataframes.items():
            op_data = df[df['operation'] == operation]

            if len(op_data) == 0:
                operation_stats[f'{protocol}_count'] = 0
                operation_stats[f'{protocol}_avg_time_ms'] = '-'
                operation_stats[f'{protocol}_avg_size_bytes'] = '-'
                operation_stats[f'{protocol}_success_rate'] = '-'
            else:
                # Calculate metrics
                count = len(op_data)
                avg_time = op_data['duration_ms'].mean()
                avg_size = op_data['payload_size_bytes'].mean()
                success_count = len(op_data[op_data['status'] == 'success'])
                success_rate = (success_count / count) * 100 if count > 0 else 0

                operation_stats[f'{protocol}_count'] = count
                operation_stats[f'{protocol}_avg_time_ms'] = avg_time
                operation_stats[f'{protocol}_avg_size_bytes'] = avg_size
                operation_stats[f'{protocol}_success_rate'] = success_rate

        all_stats.append(operation_stats)

    return pd.DataFrame(all_stats)

def calculate_protocol_summaries(dataframes):
    """Calculate overall summary statistics for each protocol"""

    summaries = []

    for protocol, df in dataframes.items():
        # Overall metrics
        total_operations = len(df)
        total_time = df['duration_ms'].sum()
        total_size = df['payload_size_bytes'].sum()
        success_count = len(df[df['status'] == 'success'])
        success_rate = (success_count / total_operations) * 100 if total_operations > 0 else 0

        avg_time = df['duration_ms'].mean()
        avg_size = df['payload_size_bytes'].mean()

        # Calculate metrics for specific operation categories
        message_ops = df[df['operation'].str.contains('message', case=False)]
        if len(message_ops) > 0:
            msg_avg_time = message_ops['duration_ms'].mean()
            msg_avg_size = message_ops['payload_size_bytes'].mean()
        else:
            msg_avg_time = 0
            msg_avg_size = 0

        account_ops = df[df['operation'].str.contains('account', case=False)]
        if len(account_ops) > 0:
            acct_avg_time = account_ops['duration_ms'].mean()
            acct_avg_size = account_ops['payload_size_bytes'].mean()
        else:
            acct_avg_time = 0
            acct_avg_size = 0

        # Add to summaries
        summaries.append({
            'protocol': protocol,
            'total_operations': total_operations,
            'total_time_ms': total_time,
            'total_size_bytes': total_size,
            'success_rate': success_rate,
            'avg_time_ms': avg_time,
            'avg_size_bytes': avg_size,
            'msg_avg_time_ms': msg_avg_time,
            'msg_avg_size_bytes': msg_avg_size,
            'acct_avg_time_ms': acct_avg_time,
            'acct_avg_size_bytes': acct_avg_size
        })

    return pd.DataFrame(summaries)

def message_size_analysis(dataframes):
    """Analyze the effect of message size on performance"""

    size_metrics = []

    for protocol, df in dataframes.items():
        # Look for operations with message size info in additional_info
        send_ops = df[df['operation'] == 'send_message']

        for _, row in send_ops.iterrows():
            size = None
            try:
                # Extract size from additional_info (format: "size=X, index=Y")
                if 'size=' in row['additional_info']:
                    size_str = row['additional_info'].split('size=')[1].split(',')[0]
                    size = int(size_str)
            except:
                continue

            if size is not None:
                size_metrics.append({
                    'protocol': protocol,
                    'message_size': size,
                    'duration_ms': row['duration_ms'],
                    'payload_size_bytes': row['payload_size_bytes']
                })

    if size_metrics:
        return pd.DataFrame(size_metrics)
    else:
        return None

def create_visualizations(dataframes, operation_stats, protocol_summaries, size_metrics, output_dir):
    """Create visualizations for the metrics"""

    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 1. Operation execution time comparison
    plt.figure(figsize=(12, 8))

    # Get list of operations and protocols from the operation_stats
    operations = operation_stats['operation'].unique()
    protocols = []
    for col in operation_stats.columns:
        if col.endswith('_avg_time_ms') and not col.startswith('operation'):
            protocols.append(col.split('_avg_time_ms')[0])

    # Create bar data
    bar_data = {}
    for protocol in protocols:
        bar_data[protocol] = []
        for op in operations:
            op_row = operation_stats[operation_stats['operation'] == op]
            if not op_row.empty and f'{protocol}_avg_time_ms' in op_row.columns:
                time_value = op_row[f'{protocol}_avg_time_ms'].values[0]
                if isinstance(time_value, (int, float)):
                    bar_data[protocol].append(time_value)
                else:
                    bar_data[protocol].append(0)
            else:
                bar_data[protocol].append(0)

    # Set up the bar chart
    x = np.arange(len(operations))
    width = 0.2
    n_protocols = len(protocols)
    offsets = np.linspace(-((n_protocols-1)/2)*width, ((n_protocols-1)/2)*width, n_protocols)

    for i, protocol in enumerate(protocols):
        plt.bar(x + offsets[i], bar_data[protocol], width, label=protocol)

    plt.xlabel('Operation')
    plt.ylabel('Average Time (ms)')
    plt.title('Average Execution Time by Operation and Protocol')
    plt.xticks(x, operations, rotation=45, ha='right')
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'operation_time_comparison.png'))
    plt.close()

    # 2. Data transfer size comparison
    plt.figure(figsize=(12, 8))

    # Create bar data for size
    bar_data = {}
    for protocol in protocols:
        bar_data[protocol] = []
        for op in operations:
            op_row = operation_stats[operation_stats['operation'] == op]
            if not op_row.empty and f'{protocol}_avg_size_bytes' in op_row.columns:
                size_value = op_row[f'{protocol}_avg_size_bytes'].values[0]
                if isinstance(size_value, (int, float)):
                    bar_data[protocol].append(size_value)
                else:
                    bar_data[protocol].append(0)
            else:
                bar_data[protocol].append(0)

    # Set up the bar chart
    for i, protocol in enumerate(protocols):
        plt.bar(x + offsets[i], bar_data[protocol], width, label=protocol)

    plt.xlabel('Operation')
    plt.ylabel('Average Size (bytes)')
    plt.title('Average Data Transfer Size by Operation and Protocol')
    plt.xticks(x, operations, rotation=45, ha='right')
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'operation_size_comparison.png'))
    plt.close()

    # 3. Message size vs. performance plot
    if size_metrics is not None and not size_metrics.empty:
        plt.figure(figsize=(10, 6))

        for protocol in size_metrics['protocol'].unique():
            protocol_data = size_metrics[size_metrics['protocol'] == protocol]

            # Group by message size and calculate average duration
            grouped = protocol_data.groupby('message_size')['duration_ms'].mean().reset_index()

            plt.plot(grouped['message_size'], grouped['duration_ms'], 'o-', label=protocol)

        plt.xlabel('Message Size (bytes)')
        plt.ylabel('Average Time (ms)')
        plt.title('Message Size vs. Average Delivery Time')
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'message_size_vs_time.png'))
        plt.close()

        # 4. Message size vs. payload size
        plt.figure(figsize=(10, 6))

        for protocol in size_metrics['protocol'].unique():
            protocol_data = size_metrics[size_metrics['protocol'] == protocol]

            # Group by message size and calculate average payload size
            grouped = protocol_data.groupby('message_size')['payload_size_bytes'].mean().reset_index()

            plt.plot(grouped['message_size'], grouped['payload_size_bytes'], 'o-', label=protocol)

        plt.xlabel('Message Size (bytes)')
        plt.ylabel('Total Transfer Size (bytes)')
        plt.title('Message Size vs. Total Network Transfer')
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'message_size_vs_transfer.png'))
        plt.close()

    # 5. Protocol comparison summary chart
    plt.figure(figsize=(10, 6))
    protocols = protocol_summaries['protocol'].tolist()
    avg_times = protocol_summaries['avg_time_ms'].tolist()
    avg_sizes = protocol_summaries['avg_size_bytes'].tolist()

    x = np.arange(len(protocols))
    width = 0.35

    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax2 = ax1.twinx()

    bars1 = ax1.bar(x - width/2, avg_times, width, label='Avg Time (ms)', color='skyblue')
    bars2 = ax2.bar(x + width/2, avg_sizes, width, label='Avg Size (bytes)', color='orange')

    ax1.set_xlabel('Protocol')
    ax1.set_ylabel('Average Time (ms)', color='skyblue')
    ax1.tick_params(axis='y', labelcolor='skyblue')

    ax2.set_ylabel('Average Size (bytes)', color='orange')
    ax2.tick_params(axis='y', labelcolor='orange')

    plt.title('Protocol Performance Comparison')
    ax1.set_xticks(x)
    ax1.set_xticklabels(protocols)

    # Add legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

    fig.tight_layout()
    plt.savefig(os.path.join(output_dir, 'protocol_comparison.png'))
    plt.close()

def format_for_console(stats_df, name, exclude_cols=None):
    """Format dataframe for console output"""
    df_for_display = stats_df.copy()

    # Exclude certain columns if needed
    if exclude_cols:
        df_for_display = df_for_display.drop(columns=[col for col in exclude_cols if col in df_for_display.columns])

    # Round float values for better display
    for col in df_for_display.columns:
        if df_for_display[col].dtype in [np.float64, np.float32]:
            df_for_display[col] = df_for_display[col].round(2)

    print(f"\n{name}:")
    print(tabulate(df_for_display, headers='keys', tablefmt='grid', showindex=False))

def main():
    parser = argparse.ArgumentParser(description='Compare metrics from different message server implementations')
    parser.add_argument('--grpc', default='message_server_metrics.csv', help='gRPC metrics CSV file')
    parser.add_argument('--json', default='json_server_metrics.csv', help='JSON metrics CSV file')
    parser.add_argument('--wire', default='wire_server_metrics.csv', help='Wire Protocol metrics CSV file')
    parser.add_argument('--output', default='comparison_results', help='Output directory for visualizations')

    args = parser.parse_args()

    # Load data from CSV files
    dataframes = load_data(args.grpc, args.json, args.wire)

    if dataframes is None or len(dataframes) == 0:
        return

    # Analyze metrics by operation
    operation_stats = analyze_operation_metrics(dataframes)

    # Calculate protocol summaries
    protocol_summaries = calculate_protocol_summaries(dataframes)

    # Analyze message size effects
    size_metrics = message_size_analysis(dataframes)

    # Display results
    format_for_console(protocol_summaries, "Protocol Summary")
    format_for_console(operation_stats, "Operation Metrics by Protocol")

    # Create visualizations
    create_visualizations(dataframes, operation_stats, protocol_summaries, size_metrics, args.output)

    print(f"\nAnalysis complete! Visualizations saved to '{args.output}' directory.")
    print("\nKey findings:")

    # Determine the fastest protocol
    if len(protocol_summaries) > 1:
        fastest = protocol_summaries.loc[protocol_summaries['avg_time_ms'].idxmin()]
        most_efficient = protocol_summaries.loc[protocol_summaries['avg_size_bytes'].idxmin()]

        print(f"- {fastest['protocol']} is the fastest protocol with an average response time of {fastest['avg_time_ms']:.2f}ms")
        print(f"- {most_efficient['protocol']} is the most network-efficient protocol with an average transfer size of {most_efficient['avg_size_bytes']:.2f} bytes")

        # Compare message operations specifically
        message_times = {}
        message_sizes = {}
        for protocol, df in dataframes.items():
            message_ops = df[df['operation'].str.contains('message', case=False)]
            if len(message_ops) > 0:
                message_times[protocol] = message_ops['duration_ms'].mean()
                message_sizes[protocol] = message_ops['payload_size_bytes'].mean()

        if message_times:
            fastest_msg = min(message_times.items(), key=lambda x: x[1])
            smallest_msg = min(message_sizes.items(), key=lambda x: x[1])

            print(f"- For message operations specifically, {fastest_msg[0]} is fastest ({fastest_msg[1]:.2f}ms)")
            print(f"- For message operations specifically, {smallest_msg[0]} is most network-efficient ({smallest_msg[1]:.2f} bytes)")

if __name__ == "__main__":
    main()