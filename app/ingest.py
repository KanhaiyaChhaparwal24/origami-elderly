from datetime import datetime, timedelta
from app.serializer import (
    build_sensor_reading,
    build_medication_event,
    build_elderly_record,
    serialize_record
)
from app.family_service import create_sample_emergency_contacts, FamilyService

def simulate_patient_data():
    now = datetime.utcnow()

    # Vital signs
    sr1 = build_sensor_reading(
        "deviceA", "patient123", now,
        {"heart_rate": 85, "spo2": 98}
    )

    sr2 = build_sensor_reading(
        "deviceA", "patient123", now + timedelta(minutes=5),
        {"heart_rate": 130, "spo2": 88}, fall_detected=True
    )

    # Medication event
    med1 = build_medication_event(
        "patient123", "med01", "Aspirin",
        scheduled=now.replace(hour=8, minute=0), taken=None
    )

    # Emergency contacts
    emergency_contacts = create_sample_emergency_contacts()
    
    # Create initial record without communications
    record = build_elderly_record(
        "patient123", "Mrs. Sharma", 78,
        [sr1, sr2], [med1], emergency_contacts, []
    )

    blob = serialize_record(record)
    return record, blob

def simulate_family_communication_scenario():
    """Simulate a complete scenario with family communications"""
    from app.adapter import (
        sensor_to_alert, 
        medication_to_alert, 
        build_care_summary,
        check_family_contact_status
    )
    
    # Get initial patient data
    record, _ = simulate_patient_data()
    
    # Generate alerts from sensor data and medications
    alerts = []
    for sr in record.sensor_readings:
        alert = sensor_to_alert(sr)
        if alert:
            alerts.append(alert)
    
    for med in record.medication_events:
        alert = medication_to_alert(med)
        if alert:
            alerts.append(alert)
    
    # Process family communications
    family_service = FamilyService()
    family_communications = family_service.process_alerts_for_family_notification(record, alerts)
    
    # Update record with family communications
    updated_record = build_elderly_record(
        record.patient_id, record.name, record.age,
        record.sensor_readings, record.medication_events,
        record.emergency_contacts, family_communications
    )
    
    # Check for communication failures
    communication_alerts = check_family_contact_status(updated_record)
    all_alerts = alerts + communication_alerts
    
    # Build comprehensive care summary
    from app.adapter import family_communication_to_notification
    family_notifications = [
        family_communication_to_notification(comm) 
        for comm in family_communications
    ]
    
    care_summary = build_care_summary(
        record.patient_id, 
        all_alerts, 
        family_notifications
    )
    
    return updated_record, care_summary, family_service

if __name__ == "__main__":
    rec, blob = simulate_patient_data()
    print("Simulated record:", rec)
    
    print("\n" + "="*50)
    print("FAMILY COMMUNICATION SCENARIO")
    print("="*50)
    
    updated_rec, summary, family_service = simulate_family_communication_scenario()
    print(f"\nPatient: {updated_rec.name} (ID: {updated_rec.patient_id})")
    print(f"Emergency Contacts: {len(updated_rec.emergency_contacts)}")
    print(f"Family Communications: {len(updated_rec.family_communications)}")
    print(f"\nCare Summary: {summary.summary_text}")
    print(f"Total Alerts: {len(summary.alerts)}")
    print(f"Family Notifications: {len(summary.family_notifications)}")