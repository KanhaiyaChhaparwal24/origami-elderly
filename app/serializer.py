from google.protobuf.timestamp_pb2 import Timestamp
from datetime import datetime
import generated.origami.backend_pb2 as backend_pb

def to_timestamp(dt: datetime) -> Timestamp:
    ts = Timestamp()
    ts.FromDatetime(dt)
    return ts

def build_sensor_reading(device_id, patient_id, dt, vitals, fall_detected=False):
    r = backend_pb.SensorReading()
    r.device_id = device_id
    r.patient_id = patient_id
    r.timestamp.CopyFrom(to_timestamp(dt))
    r.vitals.heart_rate = vitals.get("heart_rate", 0.0)
    r.vitals.spo2 = vitals.get("spo2", 0.0)
    r.vitals.body_temp = vitals.get("body_temp", 0.0)
    r.vitals.systolic = vitals.get("systolic", 0.0)
    r.vitals.diastolic = vitals.get("diastolic", 0.0)
    r.fall_detected = fall_detected
    return r

def build_medication_event(patient_id, med_id, med_name, scheduled, taken=None):
    m = backend_pb.MedicationEvent()
    m.patient_id = patient_id
    m.medication_id = med_id
    m.medication_name = med_name
    m.scheduled_time.CopyFrom(to_timestamp(scheduled))
    if taken:
        m.taken_time.CopyFrom(to_timestamp(taken))
        m.taken = True
    else:
        m.taken = False
    return m

def build_emergency_contact(contact_id, name, relationship, phone, email="", is_primary=False, notify_on_alert=True):
    contact = backend_pb.EmergencyContact()
    contact.contact_id = contact_id
    contact.name = name
    contact.relationship = relationship
    contact.phone = phone
    contact.email = email
    contact.is_primary = is_primary
    contact.notify_on_alert = notify_on_alert
    return contact

def build_family_communication(patient_id, contact_id, dt, comm_type, message, successful=True, alert_id=""):
    comm = backend_pb.FamilyCommunication()
    comm.patient_id = patient_id
    comm.contact_id = contact_id
    comm.timestamp.CopyFrom(to_timestamp(dt))
    comm.communication_type = comm_type
    comm.message = message
    comm.successful = successful
    comm.alert_id = alert_id
    return comm

def build_elderly_record(patient_id, name, age, readings, meds, contacts=None, communications=None):
    rec = backend_pb.ElderlyRecord()
    rec.patient_id = patient_id
    rec.name = name
    rec.age = age
    rec.sensor_readings.extend(readings)
    rec.medication_events.extend(meds)
    if contacts:
        rec.emergency_contacts.extend(contacts)
    if communications:
        rec.family_communications.extend(communications)
    return rec

def serialize_record(record: backend_pb.ElderlyRecord) -> bytes:
    return record.SerializeToString()

def deserialize_record(data: bytes) -> backend_pb.ElderlyRecord:
    rec = backend_pb.ElderlyRecord()
    rec.ParseFromString(data)
    return rec
