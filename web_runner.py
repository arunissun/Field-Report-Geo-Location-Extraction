"""
Web-based runner for Field Reports Pipeline (Free Replit Compatible)
Provides HTTP endpoints to run main.py and final_run.py remotely
"""

from flask import Flask, jsonify, request, send_file
import subprocess
import os
import sys
import logging
from datetime import datetime

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add src to Python path
src_dir = os.path.join(os.path.dirname(__file__), 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

def run_script(script_name, timeout=1800):
    """Run a Python script and return the result"""
    try:
        logger.info(f"Starting {script_name} at {datetime.now()}")
        
        # Ensure AUTO_MODE is set for automatic execution
        env = os.environ.copy()
        env['AUTO_MODE'] = 'true'
        
        result = subprocess.run(
            ['python', script_name], 
            capture_output=True, 
            text=True, 
            timeout=timeout,
            env=env
        )
        
        logger.info(f"Completed {script_name}")
        
        return {
            'success': result.returncode == 0,
            'script': script_name,
            'timestamp': datetime.now().isoformat(),
            'stdout': result.stdout,
            'stderr': result.stderr,
            'return_code': result.returncode
        }
        
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'script': script_name,
            'timestamp': datetime.now().isoformat(),
            'error': f'Script timed out after {timeout} seconds'
        }
    except Exception as e:
        return {
            'success': False,
            'script': script_name,
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }

@app.route('/')
def home():
    """Home page with available endpoints"""
    return """
    <h1>Field Reports Pipeline Runner</h1>
    <h2>🤖 Automated Daily Execution via GitHub Actions</h2>
    <p><strong>Schedule:</strong> Daily at 10:00 AM UTC</p>
    
    <h2>Available Endpoints:</h2>
    <ul>
        <li><a href="/run-main">/run-main</a> - Run main.py (field reports processing)</li>
        <li><a href="/run-final">/run-final</a> - Run final_run.py (GeoNames enrichment)</li>
        <li><a href="/run-both">/run-both</a> - Run both scripts sequentially</li>
        <li><a href="/run-both-and-commit">/run-both-and-commit</a> - Run pipeline and auto-commit to git</li>
        <li><a href="/status">/status</a> - Check service status</li>
        <li><a href="/logs">/logs</a> - View recent execution logs</li>
        <li><a href="/data/raw/all_raw_reports.json">/data/raw/all_raw_reports.json</a> - Download raw data</li>
        <li><a href="/data/processed/all_processed_reports.json">/data/processed/all_processed_reports.json</a> - Download processed data</li>
    </ul>
    
    <h2>Setup Instructions:</h2>
    <ol>
        <li>Push this code to your GitHub repository</li>
        <li>GitHub Actions will automatically run daily at 10 AM UTC</li>
        <li>No manual intervention required</li>
    </ol>
    
    <p><strong>Note:</strong> Scripts run automatically without user input (AUTO_MODE=true)</p>
    """

@app.route('/run-main')
def run_main():
    """Run main.py (field reports processing)"""
    result = run_script('main.py')
    return jsonify(result)

@app.route('/run-final')
def run_final():
    """Run final_run.py (GeoNames enrichment)"""
    result = run_script('final_run.py')
    return jsonify(result)

@app.route('/run-both-and-commit')
def run_both_and_commit():
    """Run both scripts sequentially and commit results to git"""
    results = []
    
    # Run main.py first
    logger.info("Running main.py first...")
    main_result = run_script('main.py')
    results.append(main_result)
    
    # Only run final_run.py if main.py succeeded
    if main_result['success']:
        logger.info("main.py succeeded, running final_run.py...")
        final_result = run_script('final_run.py')
        results.append(final_result)
    else:
        logger.warning("main.py failed, skipping final_run.py")
        results.append({
            'success': False,
            'script': 'final_run.py',
            'timestamp': datetime.now().isoformat(),
            'error': 'Skipped due to main.py failure'
        })
    
    # If both scripts succeeded, commit changes to git
    commit_result = {'success': False, 'message': 'Skipped - pipeline failed'}
    
    if all(r['success'] for r in results):
        logger.info("Pipeline succeeded, committing changes to git...")
        commit_result = commit_data_to_git()
    
    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'overall_success': all(r['success'] for r in results) and commit_result['success'],
        'pipeline_results': results,
        'git_commit': commit_result
    })

def commit_data_to_git():
    """Commit updated data files to git repository"""
    try:
        import subprocess
        import json
        from datetime import datetime
        
        # Check if there are changes
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True, cwd='.')
        
        if not result.stdout.strip():
            return {
                'success': True,
                'message': 'No changes to commit',
                'timestamp': datetime.now().isoformat()
            }
        
        # Get data counts for commit message
        raw_count = 0
        processed_count = 0
        
        try:
            with open('data/raw/all_raw_reports.json', 'r') as f:
                raw_data = json.load(f)
                raw_count = len(raw_data)
        except:
            pass
            
        try:
            with open('data/processed/all_processed_reports.json', 'r') as f:
                processed_data = json.load(f)
                processed_count = len(processed_data)
        except:
            pass
        
        # Configure git
        subprocess.run(['git', 'config', 'user.email', 'replit-automation@ifrc.org'], cwd='.')
        subprocess.run(['git', 'config', 'user.name', 'Replit Automation'], cwd='.')
        
        # Add all data files
        subprocess.run(['git', 'add', 'data/'], cwd='.')
        
        # Create commit message
        date_time = datetime.now().strftime('%Y-%m-%d %H:%M UTC')
        commit_msg = f"""Automated data update - {date_time}

Pipeline execution summary:
- Raw reports: {raw_count}
- Processed reports: {processed_count}
- Updated: raw, processed, extracted data and logs

Triggered by: GitHub Actions via Replit automation"""
        
        # Commit changes
        commit_result = subprocess.run(['git', 'commit', '-m', commit_msg], 
                                     capture_output=True, text=True, cwd='.')
        
        if commit_result.returncode != 0:
            return {
                'success': False,
                'message': f'Git commit failed: {commit_result.stderr}',
                'timestamp': datetime.now().isoformat()
            }
        
        # Push to repository
        push_result = subprocess.run(['git', 'push'], 
                                   capture_output=True, text=True, cwd='.')
        
        if push_result.returncode != 0:
            return {
                'success': False,
                'message': f'Git push failed: {push_result.stderr}',
                'timestamp': datetime.now().isoformat()
            }
        
        return {
            'success': True,
            'message': f'Successfully committed and pushed data update',
            'commit_message': commit_msg,
            'raw_count': raw_count,
            'processed_count': processed_count,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f'Git operation failed: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }

@app.route('/health')
def health_check():
    """Health check endpoint for Replit"""
    return jsonify({
        'status': 'healthy',
        'service': 'Field Reports Pipeline Web Runner',
        'timestamp': datetime.now().isoformat(),
        'port': int(os.environ.get('PORT', 5000))
    })

@app.route('/status')
def status():
    """Check service status"""
    return jsonify({
        'status': 'running',
        'timestamp': datetime.now().isoformat(),
        'auto_mode': os.environ.get('AUTO_MODE', 'false'),
        'available_scripts': ['main.py', 'final_run.py'],
        'automation': 'GitHub Actions - Daily at 10:00 AM UTC',
        'replit_status': 'Active (Free Tier)',
        'last_activity': datetime.now().isoformat()
    })

@app.route('/logs')
def logs():
    """Get recent execution logs"""
    try:
        logs_dir = 'data/logs'
        if not os.path.exists(logs_dir):
            return jsonify({'error': 'No logs directory found'})
        
        # Get the most recent log files
        log_files = []
        for file in os.listdir(logs_dir):
            if file.endswith('.json'):
                file_path = os.path.join(logs_dir, file)
                log_files.append({
                    'filename': file,
                    'modified': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
                    'size': os.path.getsize(file_path)
                })
        
        # Sort by modification time, most recent first
        log_files.sort(key=lambda x: x['modified'], reverse=True)
        
        return jsonify({
            'timestamp': datetime.now().isoformat(),
            'recent_logs': log_files[:5],  # Last 5 log files
            'logs_directory': logs_dir
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        })

# Data file serving endpoints for GitHub Actions
@app.route('/data/raw/all_raw_reports.json')
def serve_raw_data():
    """Serve raw reports data file"""
    try:
        file_path = 'data/raw/all_raw_reports.json'
        if os.path.exists(file_path):
            return send_file(file_path, mimetype='application/json')
        else:
            return jsonify({'error': 'Raw data file not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/data/processed/all_processed_reports.json')  
def serve_processed_data():
    """Serve processed reports data file"""
    try:
        file_path = 'data/processed/all_processed_reports.json'
        if os.path.exists(file_path):
            return send_file(file_path, mimetype='application/json')
        else:
            return jsonify({'error': 'Processed data file not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/data/extracted/location_extraction_results.json')
def serve_location_data():
    """Serve location extraction results file"""
    try:
        file_path = 'data/extracted/location_extraction_results.json'
        if os.path.exists(file_path):
            return send_file(file_path, mimetype='application/json')
        else:
            return jsonify({'error': 'Location data file not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/data/extracted/geonames_enriched_associations.json')
def serve_geonames_data():
    """Serve GeoNames enriched data file"""
    try:
        file_path = 'data/extracted/geonames_enriched_associations.json'
        if os.path.exists(file_path):
            return send_file(file_path, mimetype='application/json')
        else:
            return jsonify({'error': 'GeoNames data file not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/data/logs/<filename>')
def serve_log_file(filename):
    """Serve specific log file"""
    try:
        file_path = f'data/logs/{filename}'
        if os.path.exists(file_path) and filename.endswith('.json'):
            return send_file(file_path, mimetype='application/json')
        else:
            return jsonify({'error': 'Log file not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("Starting Field Reports Pipeline Web Runner...")
    print("Available at: http://localhost:5000")
    
    # Get port from environment (Replit compatibility)
    port = int(os.environ.get('PORT', 5000))
    
    print(f"Server starting on port {port}")
    print("Replit Web Service Ready!")
    
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
