"""
Family Communication Service for Elderly Care
Handles emergency contacts and family notifications
"""

from datetime import datetime
from typing import List, Optional
import generated.origami.backend_pb2 as backend_pb
import generated.origami.elderly_app_pb2 as app_pb
from app.serializer import build_family_communication, to_timestamp
import uuid


class FamilyService:
    """Service for managing family communications and emergency contacts"""
    
    def __init__(self):
        self.communication_log = []
    
    def get_emergency_contacts(self, elderly_record: backend_pb.ElderlyRecord, notify_on_alert=True) -> List[backend_pb.EmergencyContact]:
        """Get emergency contacts that should be notified"""
        if notify_on_alert:
            return [contact for contact in elderly_record.emergency_contacts if contact.notify_on_alert]
        return list(elderly_record.emergency_contacts)
    
    def get_primary_contact(self, elderly_record: backend_pb.ElderlyRecord) -> Optional[backend_pb.EmergencyContact]:
        """Get the primary emergency contact"""
        for contact in elderly_record.emergency_contacts:
            if contact.is_primary:
                return contact
        return None
    
    def send_emergency_alert(self, patient_id: str, contact: backend_pb.EmergencyContact, 
                           alert: app_pb.Alert, delivery_method="SMS") -> backend_pb.FamilyCommunication:
        """Simulate sending an emergency alert to a family member"""
        now = datetime.utcnow()
        
        # Create emergency message
        message = f"EMERGENCY ALERT for {patient_id}: {alert.message}"
        if alert.alert_type == "FALL":
            message += " Please check on them immediately."
        elif alert.alert_type == "VITALS_ANOMALY":
            message += " Vital signs are abnormal."
        
        # Simulate communication (in real implementation, would integrate with SMS/email service)
        success = self._simulate_communication_success(delivery_method)
        
        communication = build_family_communication(
            patient_id=patient_id,
            contact_id=contact.contact_id,
            dt=now,
            comm_type=delivery_method,
            message=message,
            successful=success,
            alert_id=alert.alert_id
        )
        
        self.communication_log.append(communication)
        return communication
    
    def send_daily_update(self, patient_id: str, contact: backend_pb.EmergencyContact,
                         care_summary: app_pb.CareSummary) -> backend_pb.FamilyCommunication:
        """Send daily wellness update to family member"""
        now = datetime.utcnow()
        
        # Create daily update message
        alert_count = len(care_summary.alerts)
        if alert_count == 0:
            message = f"Daily Update for {patient_id}: All systems normal. No alerts today."
        else:
            message = f"Daily Update for {patient_id}: {alert_count} alerts generated today. Please review."
        
        success = self._simulate_communication_success("EMAIL")
        
        communication = build_family_communication(
            patient_id=patient_id,
            contact_id=contact.contact_id,
            dt=now,
            comm_type="EMAIL",
            message=message,
            successful=success
        )
        
        self.communication_log.append(communication)
        return communication
    
    def schedule_wellness_check(self, patient_id: str, contact: backend_pb.EmergencyContact,
                              check_time: datetime) -> backend_pb.FamilyCommunication:
        """Schedule a wellness check call with family member"""
        message = f"Wellness check scheduled for {patient_id} at {check_time.strftime('%Y-%m-%d %H:%M')}"
        
        success = self._simulate_communication_success("CALL")
        
        communication = build_family_communication(
            patient_id=patient_id,
            contact_id=contact.contact_id,
            dt=check_time,
            comm_type="CALL",
            message=message,
            successful=success
        )
        
        self.communication_log.append(communication)
        return communication
    
    def process_alerts_for_family_notification(self, elderly_record: backend_pb.ElderlyRecord,
                                             alerts: List[app_pb.Alert]) -> List[backend_pb.FamilyCommunication]:
        """Process alerts and send appropriate family notifications"""
        communications = []
        emergency_contacts = self.get_emergency_contacts(elderly_record)
        
        for alert in alerts:
            if alert and self._should_notify_family(alert):
                # Send to primary contact first
                primary_contact = self.get_primary_contact(elderly_record)
                if primary_contact:
                    comm = self.send_emergency_alert(
                        elderly_record.patient_id, 
                        primary_contact, 
                        alert,
                        self._get_preferred_delivery_method(alert)
                    )
                    communications.append(comm)
                
                # Send to other emergency contacts for high-priority alerts
                if alert.score >= 0.9:  # Very high priority
                    for contact in emergency_contacts:
                        if not contact.is_primary:
                            comm = self.send_emergency_alert(
                                elderly_record.patient_id,
                                contact,
                                alert,
                                "SMS"  # Use SMS for urgent notifications
                            )
                            communications.append(comm)
        
        return communications
    
    def _should_notify_family(self, alert: app_pb.Alert) -> bool:
        """Determine if family should be notified for this alert"""
        high_priority_types = ["FALL", "VITALS_ANOMALY"]
        return alert.alert_type in high_priority_types and alert.score >= 0.7
    
    def _get_preferred_delivery_method(self, alert: app_pb.Alert) -> str:
        """Get preferred delivery method based on alert type"""
        if alert.alert_type == "FALL":
            return "CALL"  # Immediate phone call for falls
        elif alert.alert_type == "VITALS_ANOMALY":
            return "SMS"   # Quick SMS for vital sign issues
        else:
            return "EMAIL" # Email for less urgent alerts
    
    def _simulate_communication_success(self, delivery_method: str) -> bool:
        """Simulate communication success/failure (in real implementation, would use actual services)"""
        # Simulate different success rates for different methods
        success_rates = {
            "CALL": 0.85,
            "SMS": 0.95,
            "EMAIL": 0.98,
            "VISIT": 1.0
        }
        
        import random
        return random.random() < success_rates.get(delivery_method, 0.9)


def create_sample_emergency_contacts():
    """Create sample emergency contacts for testing"""
    from app.serializer import build_emergency_contact
    
    contacts = [
        build_emergency_contact(
            contact_id="contact_001",
            name="Rajesh Sharma",
            relationship="FAMILY",
            phone="+91-9876543210",
            email="rajesh.sharma@email.com",
            is_primary=True,
            notify_on_alert=True
        ),
        build_emergency_contact(
            contact_id="contact_002", 
            name="Dr. Priya Patel",
            relationship="DOCTOR",
            phone="+91-9876543211",
            email="dr.priya@hospital.com",
            is_primary=False,
            notify_on_alert=True
        ),
        build_emergency_contact(
            contact_id="contact_003",
            name="Maya Caregiver",
            relationship="CAREGIVER", 
            phone="+91-9876543212",
            email="maya.care@service.com",
            is_primary=False,
            notify_on_alert=True
        )
    ]
    
    return contacts