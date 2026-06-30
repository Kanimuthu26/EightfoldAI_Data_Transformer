import os
import json
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from ingestion.registry import detect_adapter
from engine.pipeline import UnificationPipeline
from storage.canonical_store import store
from projection.config_schema import validate_projection_config
from projection.project import project_profile
from projection.validate import validate_projected_output

api_bp = Blueprint('api', __name__)

UPLOAD_FOLDER = 'uploads'

def get_upload_path(filename: str) -> str:
    path = os.path.join(current_app.root_path, '..', UPLOAD_FOLDER)
    os.makedirs(path, exist_ok=True)
    return os.path.join(path, secure_filename(filename))

@api_bp.route('/ingest', methods=['POST'])
def ingest():
    """
    Ingests a single source file or URL.
    Returns detected adapter type and parsed raw records count.
    """
    filepath_or_url = None
    
    # Check if file upload
    if 'file' in request.files:
        file = request.files['file']
        if file.filename != '':
            filepath = get_upload_path(file.filename)
            file.save(filepath)
            filepath_or_url = filepath
            
    # Check if URL passed
    if not filepath_or_url and request.json:
        filepath_or_url = request.json.get('url')

    if not filepath_or_url:
        return jsonify({"success": False, "error": "No file uploaded or URL provided."}), 400

    adapter = detect_adapter(filepath_or_url)
    if not adapter:
        return jsonify({
            "success": False, 
            "error": f"No adapter registered to handle: {os.path.basename(filepath_or_url) if os.path.exists(filepath_or_url) else filepath_or_url}"
        }), 400

    try:
        raw_records = adapter.extract(filepath_or_url)
        # Convert dataclasses to dict
        raw_list = []
        for r in raw_records:
            raw_list.append({
                "field": r.field,
                "value": r.value,
                "source": r.source,
                "method": r.method,
                "record_id": r.record_id
            })
            
        # Count distinct record_ids = actual number of candidate rows parsed
        unique_record_ids = len(set(r.record_id for r in raw_records))

        return jsonify({
            "success": True,
            "filepath_or_url": filepath_or_url,
            "filename_or_url": os.path.basename(filepath_or_url) if os.path.exists(filepath_or_url) else filepath_or_url,
            "adapter": adapter.__class__.__name__,
            "raw_records_count": len(raw_records),
            "candidates_count": unique_record_ids,
            "raw_records": raw_list
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@api_bp.route('/run-pipeline', methods=['POST'])
def run_pipeline():
    """
    Runs the unification pipeline for a list of files and URLs.
    Saves results to the canonical store and returns the unified profiles.
    """
    data = request.json or {}
    inputs = data.get('inputs', [])
    priority_list = data.get('priority_list', None)

    if not inputs:
        return jsonify({"success": False, "error": "No inputs provided."}), 400

    try:
        pipeline = UnificationPipeline(priority_list=priority_list)
        
        # Clear stale profiles so re-runs always reflect current inputs
        store.clear()
        canonical_profiles = pipeline.run(inputs)
        
        # Save fresh results to global canonical store
        store.save_all(canonical_profiles)

        return jsonify({
            "success": True,
            "candidates_count": len(canonical_profiles),
            "candidates": [p.to_dict() for p in canonical_profiles]
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@api_bp.route('/candidates', methods=['GET'])
def list_candidates():
    """
    Lists all unified profiles in the store.
    """
    profiles = store.list_profiles()
    return jsonify({
        "success": True,
        "candidates": [p.to_dict() for p in profiles]
    })

@api_bp.route('/candidates/<id>', methods=['GET'])
def get_candidate(id):
    """
    Retrieves a single full canonical record (debug view).
    """
    profile = store.get_profile(id)
    if not profile:
        return jsonify({"success": False, "error": f"Candidate {id} not found."}), 404
    return jsonify({
        "success": True,
        "candidate": profile.to_dict()
    })

@api_bp.route('/project', methods=['POST'])
def project():
    """
    Applies a projection runtime configuration JSON to selected candidate profiles.
    """
    data = request.json or {}
    config = data.get('config')
    candidate_ids = data.get('candidate_ids', [])

    if not config:
        return jsonify({"success": False, "error": "No projection config provided."}), 400

    # 1. Validate the projection config against the config schema
    try:
        validate_projection_config(config)
    except Exception as e:
        return jsonify({"success": False, "error": f"Invalid projection config: {str(e)}"}), 400

    # Get profiles from store
    if candidate_ids:
        profiles = [store.get_profile(cid) for cid in candidate_ids if store.get_profile(cid)]
    else:
        profiles = store.list_profiles()

    projected_results = []
    
    # 2. Project and Validate each profile
    try:
        for profile in profiles:
            # Project profile
            projected = project_profile(profile, config)
            # Validate output types against config (null out failing fields instead of crashing)
            validated = validate_projected_output(projected, config.get("fields", []))
            projected_results.append(validated)
            
        return jsonify({
            "success": True,
            "projected": projected_results
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
