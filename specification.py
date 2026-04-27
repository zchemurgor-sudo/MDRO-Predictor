# ==========================================
# MDRO PREDICTOR: CLINICAL SPECIFICATION
# ==========================================

# STEP 1: Define the Research Blueprint
my_specification = '''
clinical_context:
  specialty: "Infectious Diseases / Clinical Microbiology"
  setting: "Admission Ward / Triage (e.g., KNH Casualty)"
  outcome_of_interest: "Detection of Multidrug-Resistant Organisms (MDRO) in urine"
  why_matters: "Enables immediate precision empiric antibiotic therapy before culture results return."

problem_type:
  problem_type: "binary"
  label: "mdro_detected: yes/no"
  reason: "Binary matches the clinical choice: either switch to reserve antibiotics or stay with standard care."

features_available:
  at_prediction_time: "At Admission / Initial Clerkship"
  example_features: "age, prior_antibiotic_use_6m, recent_hospitalization_3m, indwelling_catheter_status"
  data_source: "Patient interview (history) and Electronic Health Records"

temporal_framing:
  prediction_timepoint: "At the moment of admission"
  window: "Immediate (48-72 hour window before lab confirmation)"
  clinical_action: "Initiate 'reserve' antibiotics and barrier nursing/isolation precautions."

leakage_check:
  potential_leaks: "Final culture sensitivity results, total length of hospital stay"
  example: "Don't use: The final sensitivity report, which is the 'answer' we are trying to predict."
  decision: "REMOVE. These are not available at 3am when the patient arrives."

confounding_check:
  suspected_confounders: "Patient Age / Frailty"
  example: "Age drives both the likelihood of having a catheter and the risk of harboring MDROs."
  action: "Stratify by age groups to see if features like catheters remain significant in young vs. old patients."

ml_appropriate:
  is_ml_suitable: "YES"
  reasoning: "Resistance involves complex interactions between travel history, prior meds, and age that simple rules miss."
'''

# STEP 2: Write to file
with open('my_specification.yaml', 'w') as f:
    f.write(my_specification)

print("✓ Created my_specification.yaml")
