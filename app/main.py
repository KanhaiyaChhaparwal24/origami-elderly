from app.ingest import simulate_patient_data, simulate_family_communication_scenario
from app.storage import save_blob, load_blob
from app.serializer import deserialize_record
from app.adapter import (
    sensor_to_alert, 
    medication_to_alert, 
    build_care_summary,
    check_family_contact_status,
    family_communication_to_notification
)


def demo():
    """Original demo functionality"""
    record, blob = simulate_patient_data()
    path = save_blob(record.patient_id, blob)
    print("Saved record to", path)

    raw = load_blob(path)
    rec = deserialize_record(raw)

    alerts = []
    for sr in rec.sensor_readings:
        alert = sensor_to_alert(sr)
        if alert:
            alerts.append(alert)
    for me in rec.medication_events:
        alert = medication_to_alert(me)
        if alert:
            alerts.append(alert)

    summary = build_care_summary(rec.patient_id, alerts)
    print("Care Summary:")
    for al in summary.alerts:
        print(f"- [{al.alert_type}] {al.message}")


def family_communication_demo():
    """Professional demo showcasing family communication features"""
    print("\nFamily Communication Demo")
    print("-" * 30)
    
    # Run the family communication scenario
    record, care_summary, family_service = simulate_family_communication_scenario()
    
    # Save the updated record with family communications
    from app.serializer import serialize_record
    blob = serialize_record(record)
    path = save_blob(f"{record.patient_id}_with_family", blob)
    print(f"Enhanced record saved: {path}")
    
    # Display summary statistics
    print(f"Patient: {record.name} (ID: {record.patient_id})")
    print(f"Emergency Contacts: {len(record.emergency_contacts)}")
    print(f"Alerts Generated: {len(care_summary.alerts)}")
    print(f"Family Communications: {len(record.family_communications)}")
    print(f"Care Summary: {care_summary.summary_text}")
    
    return record, care_summary


def demonstrate_use_case_scenarios():
    """Display supported use cases"""
    print("\nSupported Use Cases:")
    scenarios = [
        "Fall Detection & Emergency Response",
        "Medication Adherence Monitoring", 
        "Vital Signs Anomaly Detection",
        "Family Communication & Notifications",
        "Daily Wellness Updates"
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"  {i}. {scenario}")


if __name__ == "__main__":
    print("Origami Elderly Care Framework Demo")
    print("====================================")
    
    # Run original demo
    print("\nBasic Demo:")
    demo()
    
    # Run family communication demo
    family_communication_demo()
    
    # Show use case scenarios
    demonstrate_use_case_scenarios()
    
    print("\nDemo completed. Check 'data_store' directory for saved files.")
