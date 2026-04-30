from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models import db, File
import os
from flask import current_app


api_bp = Blueprint('api', __name__)

@api_bp.route('/files', methods=['GET'])
@login_required
def get_files():
    files = File.query.filter_by(user_id=current_user.id).order_by(File.upload_date.desc()).all()
    
    file_list = []
    for f in files:
        file_list.append({
            'id': f.id,
            'filename': f.filename_original,
            'size_kb': round(f.file_size / 1024, 2),
            'date': f.upload_date.strftime('%Y-%m-%d %H:%M:%S'),
            'download_url': f"/downloads/{f.filename_saved}"
        })
        
    return jsonify(file_list)

@api_bp.route('/files/<int:file_id>', methods=['DELETE'])
@login_required
def delete_file(file_id):
    file_obj = File.query.get_or_404(file_id)
    if file_obj.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
        
    try:
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file_obj.filename_saved)
        if os.path.exists(file_path):
            os.remove(file_path)
        db.session.delete(file_obj)
        db.session.commit()
        
        return jsonify({'message': 'File deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500