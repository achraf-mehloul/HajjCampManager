from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import login_required, current_user
from flask_wtf.csrf import generate_csrf
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime
from models import db, Asset, Panorama360, PanoramaAssetHotspot, MDBPanel, Issue, Contractor
from functools import wraps

panorama360_bp = Blueprint('panorama360', __name__, url_prefix='/panorama360')

UPLOAD_FOLDER = 'static/uploads/panorama360'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

def allowed_file(filename): return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS
def _normalize_yaw_deg(yaw): return ((yaw + 180.0) % 360.0) - 180.0
def _clamp_pitch_deg(pitch): return max(-89.999, min(89.999, pitch))

@panorama360_bp.context_processor
def inject_csrf(): return dict(csrf_token=generate_csrf)

@panorama360_bp.route('/')
def gallery():
    p = Panorama360.query.filter_by(is_active=True).order_by(Panorama360.created_at.desc()).all()
    return render_template('panorama360/gallery.html', panoramas=p)

@panorama360_bp.route('/view/<int:panorama_id>')
def view_panorama(panorama_id):
    p = Panorama360.query.get_or_404(panorama_id)
    if not p.is_active: return redirect(url_for('panorama360.gallery'))
    p.view_count += 1; db.session.commit()
    h = PanoramaAssetHotspot.query.filter_by(panorama_id=panorama_id, is_active=True).all()
    hotspots = [{'id':hs.id,'asset_id':hs.asset_id,'pitch':hs.pitch,'yaw':hs.yaw,
                 'size_px':hs.size_px,'icon_size':hs.icon_size,'color_hex':hs.color_hex,
                 'label':hs.label,'icon_key':hs.icon_key} for hs in h]
    return render_template('panorama360/view.html', panorama=p, hotspots=hotspots)

@panorama360_bp.route('/admin')
@login_required
def admin_dashboard():
    if current_user.role != 'admin': return redirect(url_for('index'))
    return render_template('panorama360/admin_dashboard.html',
        total_assets=Asset.query.count(),
        total_panoramas=Panorama360.query.count(),
        total_hotspots=PanoramaAssetHotspot.query.count(),
        active_panoramas=Panorama360.query.filter_by(is_active=True).count(),
        recent_panoramas=Panorama360.query.order_by(Panorama360.created_at.desc()).limit(6).all())

@panorama360_bp.route('/admin/panoramas/create', methods=['GET','POST'])
@login_required
def create_panorama():
    if current_user.role != 'admin': return redirect(url_for('index'))
    if request.method == 'POST':
        if 'panorama_image' not in request.files: flash('لم تختار صورة','danger'); return redirect(request.url)
        f = request.files['panorama_image']
        if f.filename=='': flash('لم تختار صورة','danger'); return redirect(request.url)
        if f and allowed_file(f.filename):
            fn = secure_filename(f.filename).replace(' ','_').replace('(','').replace(')','')
            fn = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{fn}"
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            f.save(os.path.join(UPLOAD_FOLDER, fn))
            p = Panorama360(
                title=request.form.get('title'),
                description=request.form.get('description',''),
                location_name=request.form.get('location_name',''),
                area=request.form.get('area',''),
                image_path=f'uploads/panorama360/{fn}',
                created_by=current_user.id
            )
            db.session.add(p); db.session.commit()
            flash('تم الإنشاء','success')
            return redirect(url_for('panorama360.edit_hotspots_v2', panorama_id=p.id))
        flash('نوع الملف غير مدعوم','danger')
        return redirect(request.url)
    areas = [a[0] for a in db.session.query(Asset.area).distinct() if a[0]]
    return render_template('panorama360/create_panorama.html', areas=areas)

@panorama360_bp.route('/admin/panoramas/<int:pid>/edit-hotspots-v2')
@login_required
def edit_hotspots_v2(pid):
    if current_user.role != 'admin': return redirect(url_for('index'))
    p = Panorama360.query.get_or_404(pid)
    assets = Asset.query.filter(Asset.area==p.area, Asset.status=='active').order_by(Asset.asset_number).all() if p.area else Asset.query.order_by(Asset.asset_number).all()
    if not assets: assets = Asset.query.order_by(Asset.asset_number).all()
    hotspots = PanoramaAssetHotspot.query.filter_by(panorama_id=pid).all()
    return render_template('panorama360/edit_hotspots_v2.html', panorama=p, assets=assets, existing_hotspots=hotspots)

@panorama360_bp.route('/admin/panoramas')
@login_required
def manage_panoramas():
    if current_user.role != 'admin': return redirect(url_for('index'))
    return render_template('panorama360/manage_panoramas.html', panoramas=Panorama360.query.all())

@panorama360_bp.route('/api/hotspots/add', methods=['POST'])
@login_required
def api_add_hotspot():
    if current_user.role != 'admin': return jsonify({'success':False,'message':'غير مصرح'}),403
    data = request.get_json() or {}
    try:
        h = PanoramaAssetHotspot(
            panorama_id=int(data['panorama_id']),
            asset_id=int(data['asset_id']),
            pitch=_clamp_pitch_deg(float(data['pitch'])),
            yaw=_normalize_yaw_deg(float(data['yaw'])),
            hotspot_type=data.get('hotspot_type','asset'),
            icon_style=data.get('icon_style','default'),
            icon_size=data.get('icon_size','medium'),
            icon_key=data.get('icon_key'),
            color_hex=data.get('color_hex'),
            size_px=data.get('size_px'),
            label=data.get('label')
        )
        db.session.add(h); db.session.commit()
        return jsonify({'success':True,'hotspot_id':h.id,'message':'تم الإضافة'})
    except Exception as e: db.session.rollback(); return jsonify({'success':False,'message':str(e)}),500

@panorama360_bp.route('/api/hotspots/<int:hid>/delete', methods=['POST'])
@login_required
def api_delete_hotspot(hid):
    if current_user.role != 'admin': return jsonify({'success':False,'message':'غير مصرح'}),403
    try: db.session.delete(PanoramaAssetHotspot.query.get_or_404(hid)); db.session.commit(); return jsonify({'success':True,'message':'تم الحذف'})
    except Exception as e: db.session.rollback(); return jsonify({'success':False,'message':str(e)}),500

@panorama360_bp.route('/submit-report', methods=['POST'])
def submit_report():
    try:
        asset = Asset.query.get(request.form.get('asset_id'))
        if not asset: return jsonify({'success':False,'message':'الأصل غير موجود'}),404
        issue = Issue(
            panel_id=asset.panel_id,
            contractor_id=Contractor.query.first().id,
            title=f"بلاغ من بانوراما للأصل {asset.asset_number}",
            issue_type=request.form.get('issue_type','other'),
            description=request.form.get('notes',''),
            priority='متوسط',
            status='مفتوح',
            responsible_person=asset.company_name or 'مستخدم عام'
        )
        db.session.add(issue); db.session.commit()
        return jsonify({'success':True,'message':f'تم إرسال البلاغ #{issue.id}'})
    except Exception as e: db.session.rollback(); return jsonify({'success':False,'message':str(e)}),500