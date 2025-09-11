#!/usr/bin/env python3
"""
Elderly Care CLI Tool
Command-line interface for the elderly care monitoring system
"""

import argparse
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from app.ingest import simulate_patient_data, simulate_family_communication_scenario
from app.storage import save_blob, load_blob
from app.serializer import deserialize_record
from app.family_service import FamilyService


def main():
    parser = argparse.ArgumentParser(description="Elderly Care Monitoring System")
    parser.add_argument('command', choices=['demo', 'simulate', 'load', 'contacts'], 
                       help='Command to execute')
    parser.add_argument('--patient-id', type=str, default='patient123',
                       help='Patient ID to work with')
    parser.add_argument('--output', type=str, default='data_store',
                       help='Output directory for data files')
    
    args = parser.parse_args()
    
    if args.command == 'demo':
        run_demo()
    elif args.command == 'simulate':
        run_simulation(args.patient_id)
    elif args.command == 'load':
        load_patient_data(args.patient_id)
    elif args.command == 'contacts':
        show_emergency_contacts(args.patient_id)


def run_demo():
    """Run the full demo scenario"""
    print("Elderly Care System Demo")
    print("-" * 30)
    
    # Basic simulation
    record, _ = simulate_patient_data()
    print(f"Generated data for {record.name} (ID: {record.patient_id})")
    
    # Family communication scenario
    enhanced_record, care_summary, family_service = simulate_family_communication_scenario()
    
    print(f"Generated {len(care_summary.alerts)} alerts")
    print(f"Sent {len(care_summary.family_notifications)} family notifications")
    print(f"Managing {len(enhanced_record.emergency_contacts)} emergency contacts")
    
    # Show alert summary
    print("\nAlert Summary:")
    for alert in care_summary.alerts:
        print(f"  • {alert.alert_type}: {alert.message}")
    
    print(f"\nData saved to data_store/")


def run_simulation(patient_id):
    """Run simulation for specific patient"""
    print(f"Running simulation for patient: {patient_id}")
    
    record, care_summary, family_service = simulate_family_communication_scenario()
    
    # Save enhanced record
    from app.serializer import serialize_record
    blob = serialize_record(record)
    path = save_blob(f"{patient_id}_simulation", blob)
    
    print(f"Simulation complete - saved to {path}")
    print(f"Alerts: {len(care_summary.alerts)}")
    print(f"Emergency contacts: {len(record.emergency_contacts)}")
    print(f"Family communications: {len(record.family_communications)}")


def load_patient_data(patient_id):
    """Load and display patient data"""
    try:
        file_path = Path("data_store") / f"{patient_id}.pb"
        if not file_path.exists():
            file_path = Path("data_store") / f"{patient_id}_with_family.pb"
        
        if not file_path.exists():
            print(f"No data found for patient: {patient_id}")
            return
        
        print(f"Loading data for patient: {patient_id}")
        
        raw_data = load_blob(file_path)
        record = deserialize_record(raw_data)
        
        print(f"Patient: {record.name} (Age: {record.age})")
        print(f"Sensor readings: {len(record.sensor_readings)}")
        print(f"Medication events: {len(record.medication_events)}")
        print(f"Emergency contacts: {len(record.emergency_contacts)}")
        print(f"Family communications: {len(record.family_communications)}")
        
        # Show latest sensor data
        if record.sensor_readings:
            latest = record.sensor_readings[-1]
            print(f"\nLatest sensor reading:")
            print(f"  Device: {latest.device_id}")
            print(f"  Heart Rate: {latest.vitals.heart_rate} bpm")
            print(f"  SpO2: {latest.vitals.spo2}%")
            print(f"  Fall detected: {'Yes' if latest.fall_detected else 'No'}")
    
    except Exception as e:
        print(f"Error loading patient data: {e}")


def show_emergency_contacts(patient_id):
    """Show emergency contacts for patient"""
    try:
        file_path = Path("data_store") / f"{patient_id}_with_family.pb"
        if not file_path.exists():
            file_path = Path("data_store") / f"{patient_id}.pb"
        
        if not file_path.exists():
            print(f"No data found for patient: {patient_id}")
            return
        
        raw_data = load_blob(file_path)
        record = deserialize_record(raw_data)
        
        print(f"Emergency Contacts for {record.name}")
        print("-" * 40)
        
        for contact in record.emergency_contacts:
            primary_status = " (PRIMARY)" if contact.is_primary else ""
            notify_status = "Yes" if contact.notify_on_alert else "No"
            
            print(f"\n{contact.name}{primary_status}")
            print(f"  Relationship: {contact.relationship}")
            print(f"  Phone: {contact.phone}")
            print(f"  Email: {contact.email}")
            print(f"  Notify on Alert: {notify_status}")
    
    except Exception as e:
        print(f"Error loading emergency contacts: {e}")


if __name__ == "__main__":
    main()