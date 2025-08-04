"""
Web-based runner for Field Reports Pipeline (Free Replit Compatible)
Provides HTTP endpoints to run main.py and final_run.py remotely
"""

from flask import Flask, jsonify, request
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
    <h2>Available Endpoints:</h2>
    <ul>
        <li><a href="/run-main">/run-main</a> - Run main.py (field reports processing)</li>
        <li><a href="/run-final">/run-final</a> - Run final_run.py (GeoNames enrichment)</li>
        <li><a href="/run-both">/run-both</a> - Run both scripts sequentially</li>
        <li><a href="/status">/status</a> - Check service status</li>
    </ul>
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

@app.route('/run-both')
def run_both():
    """Run both scripts sequentially"""
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
    
    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'overall_success': all(r['success'] for r in results),
        'results': results
    })

@app.route('/status')
def status():
    """Check service status"""
    return jsonify({
        'status': 'running',
        'timestamp': datetime.now().isoformat(),
        'auto_mode': os.environ.get('AUTO_MODE', 'false'),
        'available_scripts': ['main.py', 'final_run.py']
    })

if __name__ == '__main__':
    print("Starting Field Reports Pipeline Web Runner...")
    print("Available at: http://localhost:8080")
    app.run(host='0.0.0.0', port=8080, debug=False)
