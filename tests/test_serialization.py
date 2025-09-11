from app.ingest import simulate_patient_data
from app.serializer import deserialize_record

def test_roundtrip():
    rec, blob = simulate_patient_data()
    rec2 = deserialize_record(blob)
    assert rec.patient_id == rec2.patient_id
    assert len(rec.sensor_readings) == len(rec2.sensor_readings)
