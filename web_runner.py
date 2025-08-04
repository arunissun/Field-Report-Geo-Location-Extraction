"""
Web-based runner for Field Reports Pipeline (Free Replit Compatible)
Provides HTTP endpoints to run main.py and final_run.py remotely
"""

from flask import Flask, jsonify, request, send_file, session, redirect, url_for, render_template_string
import subprocess
import os
import sys
import logging
from datetime import datetime
import hashlib
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Configure Flask session secret from .env file
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'default-secret-change-this')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add src to Python path
src_dir = os.path.join(os.path.dirname(__file__), 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Simple user management - Load from .env file
AUTHORIZED_USERS = {
    'admin': os.environ.get('ADMIN_PASSWORD', 'default-admin-password'),
    'ifrc': os.environ.get('IFRC_PASSWORD', 'default-ifrc-password'),
    # Add more users as needed
}

def check_auth():
    """Check if user is authenticated"""
    return session.get('authenticated') == True

def require_auth(f):
    """Decorator to require authentication"""
    def decorated_function(*args, **kwargs):
        if not check_auth():
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def run_script(script_name, timeout=1800):
    """Run a Python script and return the result"""
    try:
        print(f"EXECUTING: {script_name} - Started at {datetime.now().strftime('%H:%M:%S')}")
        
        # Ensure AUTO_MODE is set for automatic execution
        env = os.environ.copy()
        env['AUTO_MODE'] = 'true'
        
        result = subprocess.run(
            ['/home/runner/workspace/.pythonlibs/bin/python3', script_name], 
            capture_output=True, 
            text=True, 
            timeout=timeout,
            env=env
        )
        
        status = "SUCCESS" if result.returncode == 0 else "FAILED"
        print(f"COMPLETED: {script_name} - Status: {status} - Duration: {datetime.now().strftime('%H:%M:%S')}")
        
        if result.returncode != 0 and result.stderr:
            print(f"ERROR OUTPUT: {result.stderr.strip()}")
        
        return {
            'success': result.returncode == 0,
            'script': script_name,
            'timestamp': datetime.now().isoformat(),
            'stdout': result.stdout,
            'stderr': result.stderr,
            'return_code': result.returncode
        }
        
    except subprocess.TimeoutExpired:
        print(f"TIMEOUT: {script_name} - Exceeded {timeout} seconds")
        return {
            'success': False,
            'script': script_name,
            'timestamp': datetime.now().isoformat(),
            'error': f'Script timed out after {timeout} seconds'
        }
    except Exception as e:
        print(f"EXCEPTION: {script_name} - Error: {str(e)}")
        return {
            'success': False,
            'script': script_name,
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        # Check credentials
        if username in AUTHORIZED_USERS and AUTHORIZED_USERS[username] == password:
            session['authenticated'] = True
            session['username'] = username
            print(f"SECURITY: Successful login for user: {username} from {request.remote_addr}")
            return redirect(url_for('home'))
        else:
            print(f"SECURITY: Failed login attempt for user: {username} from {request.remote_addr}")
            error = "Invalid credentials. Please try again."
            return render_template_string(LOGIN_TEMPLATE, error=error)
    
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/logout')
def logout():
    """Logout and clear session"""
    username = session.get('username', 'unknown')
    session.clear()
    print(f"SECURITY: User {username} logged out")
    return redirect(url_for('login'))

# Login page template
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>IFRC Field Reports Pipeline - Login</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 400px; margin: 50px auto; padding: 20px; }
        .header { text-align: center; margin-bottom: 30px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input[type="text"], input[type="password"] { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
        button { width: 100%; padding: 10px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background: #0056b3; }
        .error { color: red; margin-bottom: 15px; text-align: center; }
        .info { color: #666; font-size: 12px; margin-top: 20px; text-align: center; }
    </style>
</head>
<body>
    <div class="header">
        <h2>🌍 IFRC Field Reports Pipeline</h2>
        <p>🔒 Restricted Access - Please Login</p>
    </div>
    
    {% if error %}
        <div class="error">{{ error }}</div>
    {% endif %}
    
    <form method="POST">
        <div class="form-group">
            <label for="username">Username:</label>
            <input type="text" id="username" name="username" required>
        </div>
        
        <div class="form-group">
            <label for="password">Password:</label>
            <input type="password" id="password" name="password" required>
        </div>
        
        <button type="submit">Login</button>
    </form>
    
    <div class="info">
        <p>Access restricted to authorized IFRC personnel only.</p>
        <p>Contact system administrator for credentials.</p>
    </div>
</body>
</html>
"""

@app.route('/')
@require_auth
def home():
    """Home page with available endpoints (requires authentication)"""
    username = session.get('username', 'user')
    return f"""
    <div style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px;">
        <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
            <h1>🌍 Field Reports Pipeline Runner</h1>
            <p><strong>Welcome, {username}!</strong> | <a href="/logout" style="color: #dc3545;">Logout</a></p>
            <p><strong>Deployment:</strong> {request.host} | <strong>Status:</strong> ✅ Secure Access</p>
        </div>
        
        <h2>📊 Automated Daily Execution via GitHub Actions</h2>
        <p><strong>Schedule:</strong> Daily at 10:00 AM UTC</p>
        
        <h2>🚀 Available Endpoints:</h2>
        <div style="background: #fff; border: 1px solid #dee2e6; border-radius: 5px; padding: 15px;">
            <h3>🔧 Pipeline Operations</h3>
            <ul>
                <li><a href="/run-main">/run-main</a> - Run main.py (field reports processing)</li>
                <li><a href="/run-final">/run-final</a> - Run final_run.py (GeoNames enrichment)</li>
                <li><a href="/run-both">/run-both</a> - Run both scripts sequentially</li>
            </ul>
            
            <h3>📈 Monitoring & Data</h3>
            <ul>
                <li><a href="/status">/status</a> - Check service status</li>
                <li><a href="/logs">/logs</a> - View recent execution logs</li>
            </ul>
            
            <h3>📁 Data Downloads</h3>
            <ul>
                <li><a href="/data/raw/all_raw_reports.json">/data/raw/all_raw_reports.json</a> - Download raw data</li>
                <li><a href="/data/processed/all_processed_reports.json">/data/processed/all_processed_reports.json</a> - Download processed data</li>
                <li><a href="/data/extracted/location_extraction_results.json">/data/extracted/location_extraction_results.json</a> - Download location extractions</li>
                <li><a href="/data/extracted/country_associations.json">/data/extracted/country_associations.json</a> - Download country associations</li>
                <li><a href="/data/extracted/geonames_enriched_associations.json">/data/extracted/geonames_enriched_associations.json</a> - Download GeoNames enriched data</li>
            </ul>
        </div>
        
        <div style="background: #e9ecef; padding: 15px; border-radius: 5px; margin-top: 20px;">
            <h2>⚙️ Setup Instructions:</h2>
            <ol>
                <li>GitHub Actions automatically run daily at 10 AM UTC</li>
                <li>No manual intervention required for scheduled execution</li>
                <li>Use endpoints above for manual processing when needed</li>
            </ol>
            
            <p><strong>🔒 Security:</strong> This interface is protected and logs all access attempts.</p>
            <p><strong>💡 Note:</strong> Scripts run automatically without user input (AUTO_MODE=true)</p>
        </div>
    </div>
    """

@app.route('/run-main')
@require_auth
def run_main():
    """Run main.py (field reports processing)"""
    result = run_script('main.py')
    return jsonify(result)

@app.route('/run-final')
@require_auth
def run_final():
    """Run final_run.py (GeoNames enrichment)"""
    result = run_script('final_run.py')
    return jsonify(result)

@app.route('/run-both')
@require_auth
def run_both():
    """Run both scripts sequentially (without git commit)"""
    print("PIPELINE START: Running both scripts sequentially")
    results = []
    
    # Run main.py first
    print("STEP 1: Executing main.py (field reports processing)")
    main_result = run_script('main.py')
    results.append(main_result)
    
    # Only run final_run.py if main.py succeeded
    if main_result['success']:
        print("STEP 2: main.py completed successfully, executing final_run.py (GeoNames enrichment)")
        final_result = run_script('final_run.py')
        results.append(final_result)
    else:
        print("STEP 2: main.py failed, skipping final_run.py")
        results.append({
            'success': False,
            'script': 'final_run.py',
            'timestamp': datetime.now().isoformat(),
            'error': 'Skipped due to main.py failure'
        })
    
    pipeline_success = all(r['success'] for r in results)
    print(f"PIPELINE COMPLETE: Overall status: {'SUCCESS' if pipeline_success else 'FAILED'}")
    
    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'overall_success': pipeline_success,
        'pipeline_results': results
    })

@app.route('/run-both-and-commit')
@require_auth
def run_both_and_commit():
    """Run both scripts sequentially and commit results to git (ADMIN ONLY)"""
    
    # Only allow admin user for git operations
    current_user = session.get('username', '')
    if current_user != 'admin':
        print(f"SECURITY: Non-admin user {current_user} attempted git commit from {request.remote_addr}")
        return jsonify({
            'error': 'Access denied',
            'message': 'Git commit operations are restricted to admin users only',
            'timestamp': datetime.now().isoformat()
        }), 403
    
    print(f"PIPELINE START: Running complete pipeline with git commit (USER: {current_user})")
    results = []
    
    # Run main.py first
    print("STEP 1: Executing main.py (field reports processing)")
    main_result = run_script('main.py')
    results.append(main_result)
    
    # Only run final_run.py if main.py succeeded
    if main_result['success']:
        print("STEP 2: main.py completed successfully, executing final_run.py (GeoNames enrichment)")
        final_result = run_script('final_run.py')
        results.append(final_result)
    else:
        print("STEP 2: main.py failed, skipping final_run.py")
        results.append({
            'success': False,
            'script': 'final_run.py',
            'timestamp': datetime.now().isoformat(),
            'error': 'Skipped due to main.py failure'
        })
    
    # If both scripts succeeded, commit changes to git
    commit_result = {'success': False, 'message': 'Skipped - pipeline failed'}
    
    if all(r['success'] for r in results):
        print("STEP 3: Pipeline succeeded, committing changes to git repository")
        commit_result = commit_data_to_git()
    else:
        print("STEP 3: Pipeline failed, skipping git commit")
    
    pipeline_success = all(r['success'] for r in results) and commit_result['success']
    print(f"PIPELINE COMPLETE: Overall status: {'SUCCESS' if pipeline_success else 'FAILED'}")
    
    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'overall_success': pipeline_success,
        'pipeline_results': results,
        'git_commit': commit_result
    })

def commit_data_to_git():
    """Commit updated data files to git repository"""
    try:
        import subprocess
        import json
        from datetime import datetime
        
        print("GIT: Checking for changes in data files")
        
        # Check if there are changes
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True, cwd='.')
        
        if not result.stdout.strip():
            print("GIT: No changes detected, nothing to commit")
            return {
                'success': True,
                'message': 'No changes to commit',
                'timestamp': datetime.now().isoformat()
            }
        
        print("GIT: Changes detected, preparing commit")
        
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
        
        print(f"GIT: Data summary - Raw reports: {raw_count}, Processed reports: {processed_count}")
        
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
        
        print("GIT: Committing changes")
        
        # Commit changes
        commit_result = subprocess.run(['git', 'commit', '-m', commit_msg], 
                                     capture_output=True, text=True, cwd='.')
        
        if commit_result.returncode != 0:
            print(f"GIT: Commit failed - {commit_result.stderr}")
            return {
                'success': False,
                'message': f'Git commit failed: {commit_result.stderr}',
                'timestamp': datetime.now().isoformat()
            }
        
        print("GIT: Pushing to remote repository")
        
        # Push to repository
        push_result = subprocess.run(['git', 'push'], 
                                   capture_output=True, text=True, cwd='.')
        
        if push_result.returncode != 0:
            print(f"GIT: Push failed - {push_result.stderr}")
            return {
                'success': False,
                'message': f'Git push failed: {push_result.stderr}',
                'timestamp': datetime.now().isoformat()
            }
        
        print("GIT: Successfully committed and pushed changes")
        
        return {
            'success': True,
            'message': f'Successfully committed and pushed data update',
            'commit_message': commit_msg,
            'raw_count': raw_count,
            'processed_count': processed_count,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"GIT: Operation failed - {str(e)}")
        return {
            'success': False,
            'message': f'Git operation failed: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }

@app.route('/health')
def health_check():
    """Health check endpoint for Replit (no auth required)"""
    return jsonify({
        'status': 'healthy',
        'service': 'Field Reports Pipeline Web Runner',
        'timestamp': datetime.now().isoformat(),
        'port': int(os.environ.get('PORT', 5000)),
        'security': 'Authentication enabled'
    })

@app.route('/api/github-actions')
def github_actions_endpoint():
    """Special endpoint for GitHub Actions (bypasses web auth)"""
    # Verify this is actually GitHub Actions
    user_agent = request.headers.get('User-Agent', '')
    if not ('GitHub-Actions' in user_agent or 'github-actions' in user_agent.lower()):
        return jsonify({
            'error': 'Access denied',
            'message': 'This endpoint is restricted to GitHub Actions'
        }), 403
    
    return jsonify({
        'available_endpoints': [
            '/run-both-and-commit',
            '/health',
            '/api/github-actions'
        ],
        'instructions': 'Use /run-both-and-commit for automated pipeline execution',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/status')
@require_auth
def status():
    """Check service status"""
    return jsonify({
        'status': 'running',
        'timestamp': datetime.now().isoformat(),
        'auto_mode': os.environ.get('AUTO_MODE', 'false'),
        'available_scripts': ['main.py', 'final_run.py'],
        'automation': 'GitHub Actions - Daily at 10:00 AM UTC',
        'replit_status': 'Active (Free Tier)',
        'last_activity': datetime.now().isoformat(),
        'authenticated_user': session.get('username', 'anonymous')
    })

@app.route('/logs')
@require_auth
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
    
@app.route('/data/extracted/country_associations.json')
def serve_country_associations():
    """Serve country associations data file"""
    try:
        file_path = 'data/extracted/country_associations.json'
        if os.path.exists(file_path):
            return send_file(file_path, mimetype='application/json')
        else:
            return jsonify({'error': 'Country associations file not found'}), 404
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
    print("Field Reports Pipeline Web Runner - Starting...")
    
    # Get port from environment (Replit compatibility)
    port = int(os.environ.get('PORT', 5000))
    
    print(f"Web service running on port {port}")
    print("Ready to process field reports via HTTP endpoints")
    
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
