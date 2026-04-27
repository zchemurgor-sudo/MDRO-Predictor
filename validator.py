"""
ML Problem Specification Validator

This validator checks a student's clinical question specification
against key concepts from the week: leakage, confounding, temporal framing.

Designed to be embedded directly in a Jupyter notebook cell.
"""

import os

# excel sheet .xlsx
# submission.yaml or submission.yml

# ── YAML LOADING ──────────────────────────────────────────────────────

def load_yaml_safe(path):
    """
    Load YAML specification file.
    Tries PyYAML first, falls back to simple parser.
    """
    if not os.path.exists(path):
        return None
    
    try:
        import yaml
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    except ImportError:
        return parse_yaml_simple(path)


def parse_yaml_simple(path):
    """
    Minimal YAML parser for our template structure.
    Handles flat and single-level nested dicts.
    """
    result = {}
    current_section = None
    
    with open(path, 'r') as f:
        for line in f:
            stripped = line.rstrip()
            
            # Skip empty lines and comments
            if not stripped or stripped.lstrip().startswith('#'):
                continue
            
            # Top-level section (no indent)
            if not line[0].isspace() and ':' in stripped:
                key = stripped.split(':')[0].strip()
                value = ':'.join(stripped.split(':')[1:]).strip()
                
                if value:
                    result[key] = value
                else:
                    result[key] = {}
                    current_section = key
            
            # Nested key-value (indented)
            elif current_section and ':' in stripped:
                key = stripped.strip().split(':')[0].strip()
                value = ':'.join(stripped.strip().split(':')[1:]).strip()
                # Remove quotes if present
                value = value.strip('\'"')
                result[current_section][key] = value
    
    return result


# ── SIMPLE KEYWORD DEFINITIONS ───────────────────────────────────────────────

VAGUE_OUTCOME_KEYWORDS = [
    "complications", "events", "problems", "outcomes", "bad things",
    "health issues", "something", "some condition", "stuff"
]

LEAKAGE_KEYWORDS = [
    "discharge", "final diagnosis", "after discharge", "outcome", "death",
    "readmission", "readmitted", "hospitalized", "length of stay", "los",
    "treatment outcome", "final lab", "recovery", "disposition", "died"
]

CONFOUNDING_KEYWORDS = [
    "severity", "comorbidity", "comorbidities", "age", "underlying",
    "socioeconomic", "adherence", "compliance", "baseline health",
    "acuity", "chronic", "sicker", "disease burden"
]


# ── VALIDATION FUNCTIONS ──────────────────────────────────────────────

def validate_clinical_context(spec):
    """
    Validate Section 1: Clinical Context
    
    Checks for:
    - Specific specialty and setting
    - Clear, measurable outcome (not vague)
    - Clinical rationale
    """
    section = spec.get('clinical_context', {})
    points = 0
    feedback = []
    
    # Check specialty
    specialty = section.get('specialty', '').strip()
    if specialty and len(specialty) > 2:
        feedback.append(f"  ✓ Specialty: {specialty}")
        points += 5
    else:
        feedback.append(f"  ✗ Specialty missing or too short")
        feedback.append(f"    → Add your specialty (e.g., Nephrology, Cardiology)")
    
    # Check setting
    setting = section.get('setting', '').strip()
    if setting and len(setting) > 2:
        feedback.append(f"  ✓ Setting: {setting}")
        points += 5
    else:
        feedback.append(f"  ✗ Setting missing")
        feedback.append(f"    → Where will this run? (e.g., ICU, outpatient clinic)")
    
    # Check outcome (most important)
    outcome = section.get('outcome_of_interest', '').strip()
    if not outcome:
        feedback.append(f"  ✗ No outcome specified")
        points += 0
    else:
        # Check for vague terms
        outcome_lower = outcome.lower()
        vague_found = [kw for kw in VAGUE_OUTCOME_KEYWORDS if kw in outcome_lower]
        
        if vague_found:
            feedback.append(f"  ⚠️  Outcome may be vague: '{vague_found[0]}' detected")
            feedback.append(f"     → Try: 'kidney failure requiring dialysis' instead of 'complications'")
            points += 8
        else:
            feedback.append(f"  ✓ Outcome specific: '{outcome}'")
            points += 10
    
    # Check why it matters
    why = section.get('why_matters', '').strip()
    if why and len(why) > 2:
        feedback.append(f"  ✓ Clinical importance stated")
        points += 5
    else:
        feedback.append(f"  ⚠️  Why this matters not explained")
        feedback.append(f"     → Why is this prediction important clinically?")
    
    return points, feedback


def validate_problem_type(spec):
    """
    Validate Section 2: Problem Type
    
    Checks for:
    - Valid problem type (binary, multiclass, regression)
    - Clear label definition
    - Reasoning provided
    """
    section = spec.get('problem_type', {})
    points = 0
    feedback = []
    
    ptype = str(section.get('problem_type', '')).strip().lower()
    valid_types = ['binary', 'multiclass', 'regression', 'classification']
    
    if any(t in ptype for t in valid_types):
        feedback.append(f"  ✓ Problem type: {section.get('problem_type')}")
        points += 10
    else:
        feedback.append(f"  ✗ Problem type unclear: '{section.get('problem_type')}'")
        feedback.append(f"    → Choose: binary (yes/no), multiclass (3+ categories), or regression")
        points += 0
    
    label = section.get('label', '').strip()
    if label and len(label) > 2:
        feedback.append(f"  ✓ Label: {label}")
        points += 10
    else:
        feedback.append(f"  ✗ Label missing or too vague")
        feedback.append(f"    → Define it: 'readmitted_30d: yes/no'")
        points += 0
    
    reason = section.get('reason', '').strip()
    if reason and len(reason) > 2:
        feedback.append(f"  ✓ Reasoning: {reason}")
        points += 5
    else:
        feedback.append(f"  ⚠️  No reasoning provided")
        feedback.append(f"    → Why is this the right type?")
    
    return points, feedback


def validate_features(spec):
    """
    Validate Section 3: Features Available
    
    Checks for:
    - Clear prediction timepoint
    - Realistic feature list (2+ features)
    - Data source identified
    """
    section = spec.get('features_available', {})
    points = 0
    feedback = []
    
    pred_time = section.get('at_prediction_time', '').strip()
    if pred_time and len(pred_time) > 2:
        feedback.append(f"  ✓ Prediction time: {pred_time}")
        points += 8
    else:
        feedback.append(f"  ✗ Prediction time not specified")
        feedback.append(f"    → When? (e.g., 'At clinic visit', 'After 48h')")
    
    # Get features (handle string or list)
    features = section.get('example_features', [])
    if isinstance(features, str):
        features = [f.strip() for f in features.split(',')]
    
    if features and len(features) >= 2:
        feedback.append(f"  ✓ Features: {len(features)} listed")
        points += 10
        
        # Check for obvious leakage in feature names
        feature_str = ' '.join(str(f).lower() for f in features)
        leaked = [kw for kw in LEAKAGE_KEYWORDS if kw in feature_str]
        if leaked:
            feedback.append(f"  ⚠️  Potential leakage detected in features: {leaked[0]}")
            feedback.append(f"     → Are these available at prediction time?")
    elif features and len(features) == 1:
        feedback.append(f"  ⚠️  Only 1 feature — consider adding 2-3 more")
        points += 5
    else:
        feedback.append(f"  ✗ No features listed")
        feedback.append(f"    → List realistic features for your domain")
    
    source = section.get('data_source', '').strip()
    if source and len(source) > 2:
        feedback.append(f"  ✓ Data source: {source}")
        points += 7
    else:
        feedback.append(f"  ⚠️  Data source not specified")
        feedback.append(f"    → Where? (e.g., 'EHR labs', 'patient interview')")
    
    return points, feedback


def validate_temporal_framing(spec):
    """
    Validate Section 4: Temporal Framing
    
    Checks for:
    - Specific prediction timepoint
    - Reasonable prediction window
    - Clinical action defined
    """
    section = spec.get('temporal_framing', {})
    points = 0
    feedback = []
    
    timepoint = section.get('prediction_timepoint', '').strip()
    if timepoint and len(timepoint) > 2:
        feedback.append(f"  ✓ Timepoint: {timepoint}")
        points += 8
    else:
        feedback.append(f"  ✗ Prediction timepoint missing")
        feedback.append(f"    → When? (e.g., 'At discharge', 'After 48h')")
    
    window = section.get('window', '').strip()
    if window and len(window) > 2:
        feedback.append(f"  ✓ Window: {window}")
        points += 8
        
        # Check if window is in the past (nonsensical)
        if any(kw in window.lower() for kw in ['yesterday', 'past', 'before', 'already']):
            feedback.append(f"  ⚠️  Window seems backward — predict the FUTURE, not past")
    else:
        feedback.append(f"  ✗ Window not specified")
        feedback.append(f"    → How far ahead? (e.g., '30 days', '6 months')")
    
    action = section.get('clinical_action', '').strip()
    if action and len(action) > 2:
        feedback.append(f"  ✓ Action: {action}")
        points += 9
    else:
        feedback.append(f"  ✗ No clinical action defined")
        feedback.append(f"    → What changes when model says high-risk?")
    
    return points, feedback


def validate_leakage(spec):
    """
    Validate Section 5: Leakage Check (MONDAY CONCEPT)
    
    Checks for:
    - At least one potential leak identified
    - Concrete example provided
    - Decision made (keep or remove)
    """
    section = spec.get('leakage_check', {})
    points = 0
    feedback = []
    
    leaks = section.get('potential_leaks', '').strip()
    if leaks and len(leaks) > 2:
        feedback.append(f"  ✓ Leaks identified: {leaks[:50]}...")
        points += 10
        
        # Check for quality keywords
        leaks_lower = leaks.lower()
        if any(kw in leaks_lower for kw in LEAKAGE_KEYWORDS):
            feedback.append(f"  ✓ Leakage terms correctly identified")
            points += 3
    else:
        feedback.append(f"  ✗ No potential leaks identified")
        feedback.append(f"    → Think: What won't exist at prediction time?")
    
    example = section.get('example', '').strip()
    if example and len(example) > 2:
        feedback.append(f"  ✓ Concrete example provided")
        points += 5
    else:
        feedback.append(f"  ⚠️  No concrete example")
        feedback.append(f"    → E.g., 'Don't use: discharge diagnosis'")
        points += 2
    
    decision = section.get('decision', '').strip()
    if decision and len(decision) > 2:
        decision_lower = decision.lower()
        if any(kw in decision_lower for kw in ['remove', 'keep', 'exclude', 'use']):
            feedback.append(f"  ✓ Decision made: {decision[:50]}...")
            points += 7
        else:
            feedback.append(f"  ⚠️  Decision unclear — keep or remove?")
            points += 4
    else:
        feedback.append(f"  ✗ No decision on leaks")
        feedback.append(f"    → For each leak: Keep or Remove? Why?")
    
    return points, feedback


def validate_confounding(spec):
    """
    Validate Section 6: Confounding Check (TUESDAY CONCEPT)
    
    Checks for:
    - Confounder identified
    - Concrete example
    - Action plan to check for confounding
    """
    section = spec.get('confounding_check', {})
    points = 0
    feedback = []
    
    confounders = section.get('suspected_confounders', '').strip()
    if confounders and len(confounders) > 2:
        feedback.append(f"  ✓ Confounders: {confounders[:50]}...")
        points += 10
        
        conf_lower = confounders.lower()
        if any(kw in conf_lower for kw in CONFOUNDING_KEYWORDS):
            feedback.append(f"  ✓ Confounding concepts detected")
            points += 3
    else:
        feedback.append(f"  ✗ No confounders identified")
        feedback.append(f"    → What drives BOTH feature AND outcome?")
    
    example = section.get('example', '').strip()
    if example and len(example) > 2:
        feedback.append(f"  ✓ Example: {example[:50]}...")
        points += 5
    else:
        feedback.append(f"  ⚠️  No example")
        feedback.append(f"    → E.g., 'Severity drives both meds and readmission'")
        points += 2
    
    action = section.get('action', '').strip()
    if action and len(action) > 2:
        action_lower = action.lower()
        if any(kw in action_lower for kw in ['stratify', 'control', 'adjust', 'check']):
            feedback.append(f"  ✓ Action plan: {action[:50]}...")
            points += 7
        else:
            feedback.append(f"  ⚠️  Action unclear — how will you check?")
            points += 4
    else:
        feedback.append(f"  ✗ No action plan")
        feedback.append(f"    → How? (e.g., 'Stratify by severity')")
    
    return points, feedback


def validate_ml_appropriate(spec):
    """
    Validate Section 7: ML Appropriateness
    
    Checks for:
    - Clear YES/NO/MAYBE answer
    - Reasoning provided
    - Quality of reasoning (non-linear, interactions, etc.)
    """
    section = spec.get('ml_appropriate', {})
    points = 0
    feedback = []
    
    suitable = str(section.get('is_ml_suitable', '')).strip().lower()
    if any(a in suitable for a in ['yes', 'no', 'maybe']):
        feedback.append(f"  ✓ ML suitability: {section.get('is_ml_suitable')}")
        points += 10
    else:
        feedback.append(f"  ✗ ML suitability unclear")
        feedback.append(f"    → Answer: YES / NO / MAYBE")
    
    reasoning = section.get('reasoning', '').strip()
    if reasoning and len(reasoning) > 2:
        feedback.append(f"  ✓ Reasoning: {reasoning[:50]}...")
        points += 10
        
        # Check for quality thinking
        reasoning_lower = reasoning.lower()
        quality_indicators = [
            'non-linear', 'complex', 'interaction', 'pattern',
            'rule', 'threshold', 'relationship', 'rare', 'data'
        ]
        found = [kw for kw in quality_indicators if kw in reasoning_lower]
        if found:
            feedback.append(f"  ✓ Quality reasoning (mentions: {found[0]})")
            points += 5
    else:
        feedback.append(f"  ✗ No reasoning")
        feedback.append(f"    → Why ML? (e.g., 'non-linear relationships')")
    
    return points, feedback


# ── MAIN VALIDATOR ────────────────────────────────────────────────────

def validate_specification(spec_path):
    """
    Run all validators and produce final report.
    """
    # Load spec
    spec = load_yaml_safe(spec_path)
    if spec is None:
        print(f"\n❌ ERROR: Could not find or parse {spec_path}")
        print(f"   Make sure the file exists in the current directory.\n")
        return
    
    if not isinstance(spec, dict):
        print(f"\n❌ ERROR: Specification is not valid YAML structure\n")
        return
    
    # Print header
    print("\n" + "=" * 70)
    print("WEEK 3 THURSDAY: ML PROBLEM SPECIFICATION VALIDATOR".center(70))
    print("=" * 70 + "\n")
    print(f"Validating: {spec_path}\n")
    
    # Run all validators
    scores = {}
    all_feedback = {}
    
    print("SECTION 1: CLINICAL CONTEXT")
    print("-" * 70)
    pts, fb = validate_clinical_context(spec)
    scores['clinical_context'] = pts
    all_feedback['clinical_context'] = fb
    print('\n'.join(fb))
    print(f"Score: {pts}/25\n")
    
    print("SECTION 2: PROBLEM TYPE")
    print("-" * 70)
    pts, fb = validate_problem_type(spec)
    scores['problem_type'] = pts
    all_feedback['problem_type'] = fb
    print('\n'.join(fb))
    print(f"Score: {pts}/25\n")
    
    print("SECTION 3: FEATURES AVAILABLE")
    print("-" * 70)
    pts, fb = validate_features(spec)
    scores['features'] = pts
    all_feedback['features'] = fb
    print('\n'.join(fb))
    print(f"Score: {pts}/25\n")
    
    print("SECTION 4: TEMPORAL FRAMING")
    print("-" * 70)
    pts, fb = validate_temporal_framing(spec)
    scores['temporal'] = pts
    all_feedback['temporal'] = fb
    print('\n'.join(fb))
    print(f"Score: {pts}/25\n")
    
    print("SECTION 5: LEAKAGE CHECK")
    print("-" * 70)
    pts, fb = validate_leakage(spec)
    scores['leakage'] = pts
    all_feedback['leakage'] = fb
    print('\n'.join(fb))
    print(f"Score: {pts}/25\n")
    
    print("SECTION 6: CONFOUNDING CHECK")
    print("-" * 70)
    pts, fb = validate_confounding(spec)
    scores['confounding'] = pts
    all_feedback['confounding'] = fb
    print('\n'.join(fb))
    print(f"Score: {pts}/25\n")
    
    print("SECTION 7: ML APPROPRIATENESS")
    print("-" * 70)
    pts, fb = validate_ml_appropriate(spec)
    scores['ml'] = pts
    all_feedback['ml'] = fb
    print('\n'.join(fb))
    print(f"Score: {pts}/25\n")
    
    # Final report
    total = sum(scores.values())
    max_total = 175
    normalized = round((total / max_total) * 100)
    
    print("=" * 70)
    print("FINAL REPORT".center(70))
    print("=" * 70 + "\n")
    
    sections = [
        ("1. Clinical Context", scores['clinical_context']),
        ("2. Problem Type", scores['problem_type']),
        ("3. Features Available", scores['features']),
        ("4. Temporal Framing", scores['temporal']),
        ("5. Leakage Check", scores['leakage']),
        ("6. Confounding Check", scores['confounding']),
        ("7. ML Appropriateness", scores['ml']),
    ]
    
    for name, score in sections:
        pct = score / 25
        bar_len = int(pct * 20)
        bar = "█" * bar_len + "░" * (20 - bar_len)
        
        if pct >= 0.9:
            grade = "EXCELLENT"
        elif pct >= 0.7:
            grade = "GOOD"
        elif pct >= 0.4:
            grade = "PARTIAL"
        else:
            grade = "NEEDS WORK"
        
        print(f"  {name:<25} [{bar}] {score}/25  {grade}")
    
    print(f"\n  {'TOTAL':<25} {normalized}/100")
    
    print("\n" + "=" * 70)
    print("FEEDBACK".center(70))
    print("=" * 70 + "\n")
    
    if normalized >= 85:
        print("🎯 EXCELLENT! Your specification is solid.")
        print("You've thought through leakage, confounding, and timing.")
        print("Ready for Week 4 — the data audit.\n")
    elif normalized >= 70:
        print("👍 GOOD! You have the right framework.")
        print("Review sections marked PARTIAL or GOOD and refine.\n")
    elif normalized >= 50:
        print("⚠️  PARTIAL — You're on track but missing key elements.")
        print("Common gaps:")
        print("  - Outcome too vague (be specific!)")
        print("  - Leakage not identified (what's NOT at prediction time?)")
        print("  - Confounding not addressed\n")
    else:
        print("✗ NEEDS WORK — Several sections incomplete.")
        print("Focus on:")
        print("  1. Define a SPECIFIC outcome")
        print("  2. Identify one potential LEAK")
        print("  3. Name one CONFOUNDER")
        print("  4. State WHEN you predict and WHAT you'll do\n")
    
    print("=" * 70)
    print("NEXT STEPS".center(70))
    print("=" * 70 + "\n")
    print("1. Review the feedback above")
    print("2. Edit your YAML file to address suggestions")
    print("3. Re-run this validator to check improvements")
    print("4. Submit your final specification to the Google Form\n")
    print("This question becomes your focus for Week 4 (Data Audit).")
    print("Make it solid now — it saves time later!\n")


# ── ENTRY POINT ───────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "my_specification.yaml"
    validate_specification(path)
