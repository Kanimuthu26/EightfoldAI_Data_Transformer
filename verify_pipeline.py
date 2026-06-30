import json
from engine.pipeline import UnificationPipeline
from projection.project import project_profile
from projection.validate import validate_projected_output

def verify():
    print("======================================================================")
    print("      CANDIDATE DATA PIPELINE VERIFICATION & AUDIT REPORT")
    print("======================================================================\n")

    inputs = [
        "samples/recruiter_export.csv",
        "samples/ats_candidates.json",
        "samples/recruiter_notes.txt"
    ]

    print("Step 1: Running Unification Pipeline on Inputs:")
    for path in inputs:
        print(f"  - Ingesting: {path}")

    pipeline = UnificationPipeline()
    profiles = pipeline.run(inputs)

    print(f"\nSuccessfully unified data into {len(profiles)} Candidate Profiles:\n")

    for idx, p in enumerate(profiles):
        print(f"----------------------------------------------------------------------")
        print(f"Profile #{idx+1} | Candidate ID: {p.candidate_id}")
        print(f"----------------------------------------------------------------------")
        print(f"  Name:               {p.full_name}")
        print(f"  Headline:           {p.headline}")
        print(f"  Emails:             {p.emails}")
        print(f"  Phones:             {p.phones}")
        print(f"  Location:           {p.location}")
        print(f"  Years Exp:          {p.years_experience}")
        print(f"  Skills count:       {len(p.skills)} -> {[s.name for s in p.skills]}")
        print(f"  Experience count:   {len(p.experience)}")
        for e in p.experience:
            print(f"    * {e.title} at {e.company} ({e.start} to {e.end})")
        print(f"  Education count:    {len(p.education)}")
        for edu in p.education:
            print(f"    * {edu.degree} from {edu.institution} ({edu.end_year})")
        
        print(f"\n  Confidence Analytics:")
        print(f"    * Overall Confidence: {p.overall_confidence:.2f}")
        for s in p.skills[:3]:
            print(f"    * Skill '{s.name}' confidence: {s.confidence:.2f} (from sources: {s.sources})")
            
        print(f"\n  Provenance Traceability:")
        # Group provenance by field to make it readable
        prov_map = {}
        for prov in p.provenance:
            prov_map.setdefault(prov.field, []).append(f"{prov.source} ({prov.method})")
        for field, traces in prov_map.items():
            print(f"    * Field '{field}' <- " + " | ".join(traces))
        print("\n")

    # Step 3: Run Projection and Type Validation
    print("======================================================================")
    print("Step 2: Testing Runtime Output Projection & Schema Validation")
    print("======================================================================\n")

    test_config = {
        "fields": [
            { "path": "id", "from": "candidate_id", "type": "string", "required": True },
            { "path": "name", "from": "full_name", "type": "string" },
            { "path": "primary_email", "from": "emails[0]", "type": "string" },
            { "path": "contact_phone", "from": "phones[0]", "type": "string", "normalize": "E.164" },
            { "path": "skills_list", "from": "skills[].name", "type": "string[]", "normalize": "upper" },
            { "path": "years_exp", "from": "years_experience", "type": "number" },
            { "path": "country_code", "from": "location.country", "type": "string", "normalize": "upper" }
        ],
        "include_confidence": True,
        "on_missing": "null"
    }

    print("Using Projection Configuration:")
    print(json.dumps(test_config, indent=2))
    print("\nProjected and Validated Output Views:\n")

    projected_results = []
    for p in profiles:
        proj = project_profile(p, test_config)
        validated = validate_projected_output(proj, test_config["fields"])
        projected_results.append(validated)

    print(json.dumps(projected_results, indent=2))
    print("\nVerification Complete.")

if __name__ == "__main__":
    verify()
