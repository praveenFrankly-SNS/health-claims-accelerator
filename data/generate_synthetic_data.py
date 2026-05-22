import os
import json
import csv
import random
from datetime import datetime, timedelta

# Dynamically find the repo root
if os.path.exists("../notebooks") and os.path.exists("../data"):
    repo_root = ".."
elif os.path.exists("./notebooks") and os.path.exists("./data"):
    repo_root = "."
else:
    repo_root = "."

def create_directories():
    os.makedirs(f"{repo_root}/data/raw/structured", exist_ok=True)
    os.makedirs(f"{repo_root}/data/raw/unstructured", exist_ok=True)

def generate_synthetic_claims(num_claims=10):
    claims = []
    hospitals = ["Apollo Hospital", "Fortis Healthcare", "Max Super Speciality", "AIIMS", "Manipal Hospital"]
    diagnoses = [
        {"desc": "Appendectomy", "code": "K35.80", "amount": random.randint(40000, 80000)},
        {"desc": "Dengue Fever", "code": "A90", "amount": random.randint(15000, 30000)},
        {"desc": "Knee Replacement", "code": "Z96.65", "amount": random.randint(200000, 350000)},
        {"desc": "Cataract Surgery", "code": "H25.9", "amount": random.randint(20000, 45000)},
        {"desc": "Viral Pneumonia", "code": "J12.9", "amount": random.randint(30000, 70000)}
    ]

    for i in range(num_claims):
        diagnosis = random.choice(diagnoses)
        admission_date = datetime.today() - timedelta(days=random.randint(10, 60))
        discharge_date = admission_date + timedelta(days=random.randint(1, 10))
        
        claim = {
            "claim_id": f"CLM-2026-{10000+i}",
            "policy_number": f"POL-HLT-{20000+i}",
            "claimant_name": f"Patient {i}",
            "date_of_loss": admission_date.strftime("%Y-%m-%d"),
            "hospital_name": random.choice(hospitals),
            "claimed_amount": diagnosis["amount"] + random.randint(-5000, 5000),
            "submission_date": discharge_date.strftime("%Y-%m-%d"),
            "status": "NEW"
        }
        claims.append(claim)
        
        # Also generate a fake unstructured PDF text (Discharge Summary)
        generate_discharge_summary(claim, diagnosis, admission_date, discharge_date)

    # Save to CSV
    csv_file = f"{repo_root}/data/raw/structured/claims.csv"
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=claims[0].keys())
        writer.writeheader()
        writer.writerows(claims)
    print(f"Generated {num_claims} structured claims at {csv_file}")

def generate_discharge_summary(claim, diagnosis, admin_date, discharge_date):
    summary = f"""
    DISCHARGE SUMMARY
    -----------------
    Patient Name: {claim['claimant_name']}
    Policy Number: {claim['policy_number']}
    Admission Date: {admin_date.strftime("%Y-%m-%d")}
    Discharge Date: {discharge_date.strftime("%Y-%m-%d")}
    Hospital: {claim['hospital_name']}
    
    Diagnosis: {diagnosis['desc']}
    ICD-10 Code: {diagnosis['code']}
    
    Course in the Hospital:
    The patient presented with symptoms relating to {diagnosis['desc']}. 
    Routine investigations were carried out. The patient was managed conservatively/surgically 
    and responded well to the treatment. At the time of discharge, the patient's condition was stable.
    
    Final Bill Amount: INR {claim['claimed_amount']}
    
    Attending Physician: Dr. Smith (Reg No: MC-5544)
    """
    
    # Intentionally remove physician registration for 10% of cases to simulate Agent 1 finding missing fields
    if random.random() < 0.1:
        summary = summary.replace("Attending Physician: Dr. Smith (Reg No: MC-5544)", "Attending Physician: Dr. Smith")
    
    filename = f"{repo_root}/data/raw/unstructured/{claim['claim_id']}_discharge_summary.txt"
    with open(filename, "w") as f:
        f.write(summary)

if __name__ == "__main__":
    create_directories()
    generate_synthetic_claims(50)
    print("Synthetic data generation complete.")
