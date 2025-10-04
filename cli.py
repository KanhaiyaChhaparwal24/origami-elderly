#!/usr/bin/env python3
"""
Multi-Application CLI Tool for Origami Framework
Command-line interface supporting multiple domains (elderly care, agriculture, security, etc.)
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from app.ingest import simulate_multi_application_scenario, simulate_elderly_data, simulate_agriculture_data
from app.storage import save_data_packet, load_data_packet, save_application_summary, get_storage_stats, list_stored_files
from app.adapter import get_system_overview, get_application_statistics, generate_application_summary
from app.registry import get_registry
from app.plugins.elderly_service import ElderlyServicePlugin
from app.plugins.agriculture_service import AgricultureServicePlugin


def initialize_plugins():
    """Initialize and register all available plugins"""
    registry = get_registry()
    
    # Register all available plugins
    plugins = [
        ElderlyServicePlugin(),
        AgricultureServicePlugin(),
    ]
    
    for plugin in plugins:
        if not registry.get_plugin(plugin.app_id):
            registry.register_plugin(plugin)


def main():
    parser = argparse.ArgumentParser(description="Multi-Application Monitoring System")
    parser.add_argument('command', choices=['demo', 'simulate', 'load', 'contacts', 'apps', 'stats', 'overview'], 
                       help='Command to execute')
    parser.add_argument('--app-id', type=str, choices=['elderly_care', 'agriculture', 'security'], 
                       help='Application ID to work with')
    parser.add_argument('--entity-id', type=str, default='default_entity',
                       help='Entity ID (patient, field, zone, etc.)')
    parser.add_argument('--output', type=str, default='data_store',
                       help='Output directory for data files')
    
    args = parser.parse_args()
    
    # Initialize plugins
    initialize_plugins()
    
    if args.command == 'demo':
        run_demo(args.app_id)
    elif args.command == 'simulate':
        run_simulation(args.app_id, args.entity_id)
    elif args.command == 'load':
        load_application_data(args.app_id, args.entity_id)
    elif args.command == 'contacts':
        show_contacts(args.app_id, args.entity_id)
    elif args.command == 'apps':
        list_applications()
    elif args.command == 'stats':
        show_statistics(args.app_id)
    elif args.command == 'overview':
        show_system_overview()


def run_demo(app_id: Optional[str] = None):
    """Run demonstration for specific application or all applications"""
    if app_id:
        print(f"Running demo for application: {app_id}")
        print("-" * 40)
        run_application_demo(app_id)
    else:
        print("Multi-Application System Demo")
        print("-" * 40)
        run_full_system_demo()


def run_application_demo(app_id: str):
    """Run demo for a specific application"""
    registry = get_registry()
    plugin = registry.get_plugin(app_id)
    
    if not plugin:
        print(f"No plugin found for application: {app_id}")
        return
    
    print(f"Application: {plugin.app_name}")
    print(f"Supported data types: {', '.join(plugin.supported_data_types)}")
    
    # Generate application-specific data
    if app_id == "elderly_care":
        packets = simulate_elderly_data()
        entity_id = "patient123"
    elif app_id == "agriculture":
        packets = simulate_agriculture_data()
        entity_id = "field_north_40"
    else:
        print(f"Demo not implemented for {app_id}")
        return
    
    # Process data through the system
    alerts = []
    notifications = []
    
    for packet in packets:
        packet_alerts = registry.generate_alerts(packet)
        alerts.extend(packet_alerts)
        
        for alert in packet_alerts:
            alert_notifications = registry.process_alert(alert)
            notifications.extend(alert_notifications)
    
    print(f"Generated {len(packets)} data packets")
    print(f"Generated {len(alerts)} alerts")
    print(f"Sent {len(notifications)} notifications")
    
    # Show alert details
    print("\nAlert Summary:")
    for alert in alerts:
        print(f"  • {alert.severity.upper()} {alert.type}: {alert.message}")
    
    # Generate and save summary
    summary = generate_application_summary(app_id, entity_id, "demo", alerts, notifications)
    if summary:
        path = save_application_summary(summary, f"{app_id}_demo_summary")
        print(f"\nSummary saved to: {path}")
        print(f"Summary: {summary.summary_text}")


def run_full_system_demo():
    """Run demonstration across all applications"""
    packets, alerts, notifications = simulate_multi_application_scenario()
    
    print(f"Generated {len(packets)} data packets across multiple applications")
    print(f"Generated {len(alerts)} alerts")
    print(f"Sent {len(notifications)} notifications")
    
    # Show breakdown by application
    apps = {}
    for packet in packets:
        if packet.app_id not in apps:
            apps[packet.app_id] = []
        apps[packet.app_id].append(packet)
    
    print("\nBreakdown by Application:")
    for app_id, app_packets in apps.items():
        app_alerts = [alert for alert in alerts if alert.app_id == app_id]
        app_notifications = [notif for notif in notifications if notif.app_id == app_id]
        
        print(f"  {app_id}:")
        print(f"    Data packets: {len(app_packets)}")
        print(f"    Alerts: {len(app_alerts)}")
        print(f"    Notifications: {len(app_notifications)}")


def run_simulation(app_id: Optional[str], entity_id: str):
    """Run simulation for specific application and entity"""
    if not app_id:
        print("Please specify --app-id for simulation")
        return
    
    print(f"Running simulation for {app_id} - Entity: {entity_id}")
    
    registry = get_registry()
    plugin = registry.get_plugin(app_id)
    
    if not plugin:
        print(f"No plugin found for application: {app_id}")
        return
    
    # Generate data based on application type
    if app_id == "elderly_care":
        packets = simulate_elderly_data()
    elif app_id == "agriculture":
        packets = simulate_agriculture_data()
    else:
        print(f"Simulation not implemented for {app_id}")
        return
    
    # Process and save results
    alerts = []
    for packet in packets:
        packet_alerts = registry.generate_alerts(packet)
        alerts.extend(packet_alerts)
        # Save sample packet
        save_data_packet(packet, f"{app_id}_{entity_id}_simulation")
    
    print(f"Simulation complete - generated {len(alerts)} alerts")
    print(f"Alerts: {', '.join([alert.type for alert in alerts])}")


def load_application_data(app_id: Optional[str], entity_id: str):
    """Load and display application data"""
    try:
        # List available files
        files = list_stored_files(app_id=app_id)
        
        if not files:
            print(f"No data found for application: {app_id or 'any'}")
            return
        
        print(f"Found {len(files)} files for {app_id or 'all applications'}")
        
        # Load and display first few files as examples
        for file_path in files[:3]:  # Show first 3 files
            print(f"\nFile: {file_path.name}")
            
            if file_path.name.endswith('.packet'):
                packet = load_data_packet(file_path)
                print(f"  App: {packet.app_id}")
                print(f"  Type: {packet.data_type}")
                print(f"  Source: {packet.source_id}")
                print(f"  Metadata: {dict(packet.metadata)}")
            else:
                print(f"  File type: {file_path.suffix}")
                print(f"  Size: {file_path.stat().st_size} bytes")
    
    except Exception as e:
        print(f"Error loading data: {e}")


def show_contacts(app_id: Optional[str], entity_id: str):
    """Show contacts for specific application and entity"""
    if not app_id:
        print("Please specify --app-id to show contacts")
        return
    
    registry = get_registry()
    plugin = registry.get_plugin(app_id)
    
    if not plugin:
        print(f"No plugin found for application: {app_id}")
        return
    
    print(f"Contacts for {app_id} - Entity: {entity_id}")
    print("-" * 40)
    
    contacts = plugin.get_contacts(entity_id)
    
    for contact in contacts:
        primary_status = " (PRIMARY)" if contact.is_primary else ""
        print(f"\n{contact.name}{primary_status}")
        print(f"  Role: {contact.role}")
        print(f"  Phone: {contact.phone}")
        print(f"  Email: {contact.email}")
        if contact.preferences:
            print(f"  Preferences: {dict(contact.preferences)}")


def list_applications():
    """List all registered applications"""
    registry = get_registry()
    applications = registry.get_applications()
    
    print("Registered Applications")
    print("-" * 30)
    
    for app in applications:
        print(f"\nApplication: {app.app_name}")
        print(f"  ID: {app.app_id}")
        print(f"  Version: {app.version}")
        print(f"  Description: {app.description}")
        print(f"  Data types: {', '.join(app.data_types)}")


def show_statistics(app_id: Optional[str]):
    """Show statistics for specific application or all applications"""
    print("System Statistics")
    print("-" * 30)
    
    # Storage statistics
    storage_stats = get_storage_stats()
    print(f"Total stored files: {storage_stats['total_files']}")
    print(f"Total storage size: {storage_stats['total_size_bytes']} bytes")
    print(f"Files by type: {storage_stats['by_type']}")
    
    if app_id:
        app_files = storage_stats['by_app'].get(app_id, 0)
        print(f"Files for {app_id}: {app_files}")
    else:
        print(f"Files by application: {storage_stats['by_app']}")


def show_system_overview():
    """Show system-wide overview"""
    print("System Overview")
    print("-" * 30)
    
    # Run a quick simulation to get data for overview
    packets, alerts, notifications = simulate_multi_application_scenario()
    overview = get_system_overview(alerts, notifications)
    
    print(f"Total alerts: {overview['total_alerts']}")
    print(f"Total notifications: {overview['total_notifications']}")
    print(f"Severity distribution: {overview['overall_severity']}")
    
    print("\nApplication Breakdown:")
    for app_id, stats in overview["applications"].items():
        print(f"  {app_id}:")
        print(f"    Alerts: {stats['total_alerts']}")
        print(f"    Notifications: {stats['total_notifications']}")
        print(f"    Success rate: {stats['successful_notifications']}/{stats['total_notifications']}")
        print(f"    Alert types: {stats['alert_types']}")


if __name__ == "__main__":
    main()