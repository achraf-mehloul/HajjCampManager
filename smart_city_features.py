#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
وحدة المميزات الذكية للمدينة
Smart City Features Module

تحتوي على جميع المميزات الجديدة:
- Transportation & Parking
- Urban Planning
- Housing Management
- Safety & Inspection
- Infrastructure Management
- Land Surveying
- Environment & Waste
- Smart Government Integration
"""

import os
import datetime
import json
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import pandas as pd
from sqlalchemy import and_, or_

# استيراد النماذج
from models import (
    db, MDBPanel, User, Contractor,
    # Transportation & Parking
    ParkingArea, TrafficZone, TransportRoute,
    # Urban Planning
    UrbanPlan, ZoningArea,
    # Housing
    HousingUnit, HousingInspection,
    # Safety & Inspection
    SafetyInspection, HazardReport,
    # Infrastructure
    InfrastructureNetwork, InfrastructureMalfunction,
    # Land Surveying
    LandParcel, SurveyPoint,
    # Environment & Waste
    WasteCollectionPoint, EnvironmentalReport,
    # Government Integration
    GovernmentIntegration, ExternalReport
)

# إنشاء Blueprint
smart_city_bp = Blueprint('smart_city', __name__, url_prefix='/smart-city')

# ===== Transportation & Parking =====

@smart_city_bp.route('/transportation')
@login_required
def transportation_dashboard():
    """لوحة معلومات النقل والمواقف"""
    parking_areas = ParkingArea.query.filter_by(is_active=True).all()
    traffic_zones = TrafficZone.query.all()
    transport_routes = TransportRoute.query.filter_by(is_active=True).all()
    
    # إحصائيات
    total_parking_capacity = sum([area.capacity for area in parking_areas])
    total_occupied = sum([area.current_occupancy for area in parking_areas])
    occupancy_rate = (total_occupied / total_parking_capacity * 100) if total_parking_capacity > 0 else 0
    
    # مناطق الازدحام النشطة
    active_congestion = TrafficZone.query.filter(
        and_(
            TrafficZone.zone_type == 'congestion',
            or_(TrafficZone.end_time.is_(None), TrafficZone.end_time > datetime.datetime.now())
        )
    ).count()
    
    return render_template('smart_city/transportation_dashboard.html',
                         parking_areas=parking_areas,
                         traffic_zones=traffic_zones,
                         transport_routes=transport_routes,
                         total_parking_capacity=total_parking_capacity,
                         total_occupied=total_occupied,
                         occupancy_rate=round(occupancy_rate, 1),
                         active_congestion=active_congestion,
                         current_date=datetime.datetime.now().strftime("%Y-%m-%d"))

@smart_city_bp.route('/parking/add', methods=['GET', 'POST'])
@login_required
def add_parking_area():
    """إضافة منطقة موقف جديدة"""
    if request.method == 'POST':
        parking_area = ParkingArea(
            name=request.form['name'],
            area_type=request.form['area_type'],
            capacity=int(request.form['capacity']),
            coordinates=request.form['coordinates'],
            center_lat=float(request.form['center_lat']) if request.form['center_lat'] else None,
            center_lng=float(request.form['center_lng']) if request.form['center_lng'] else None,
            hourly_rate=float(request.form['hourly_rate']) if request.form['hourly_rate'] else 0.0,
            accessibility_features=request.form['accessibility_features'],
            operating_hours=request.form['operating_hours'],
            contact_info=request.form['contact_info'],
            notes=request.form['notes']
        )
        
        db.session.add(parking_area)
        db.session.commit()
        flash('تم إضافة منطقة الموقف بنجاح', 'success')
        return redirect(url_for('smart_city.transportation_dashboard'))
    
    return render_template('smart_city/add_parking_area.html',
                         current_date=datetime.datetime.now().strftime("%Y-%m-%d"))

@smart_city_bp.route('/traffic/add', methods=['GET', 'POST'])
@login_required
def add_traffic_zone():
    """إضافة منطقة مرورية جديدة"""
    if request.method == 'POST':
        traffic_zone = TrafficZone(
            name=request.form['name'],
            zone_type=request.form['zone_type'],
            coordinates=request.form['coordinates'],
            severity_level=request.form['severity_level'],
            start_time=datetime.datetime.strptime(request.form['start_time'], '%Y-%m-%dT%H:%M') if request.form['start_time'] else None,
            end_time=datetime.datetime.strptime(request.form['end_time'], '%Y-%m-%dT%H:%M') if request.form['end_time'] else None,
            is_permanent=bool(request.form.get('is_permanent')),
            description=request.form['description'],
            alternative_routes=request.form['alternative_routes']
        )
        
        db.session.add(traffic_zone)
        db.session.commit()
        flash('تم إضافة المنطقة المرورية بنجاح', 'success')
        return redirect(url_for('smart_city.transportation_dashboard'))
    
    return render_template('smart_city/add_traffic_zone.html',
                         current_date=datetime.datetime.now().strftime("%Y-%m-%d"))

# ===== Urban Planning =====

@smart_city_bp.route('/urban-planning')
@login_required
def urban_planning_dashboard():
    """لوحة معلومات التخطيط الحضري"""
    urban_plans = UrbanPlan.query.all()
    zoning_areas = ZoningArea.query.filter_by(is_active=True).all()
    
    # إحصائيات
    approved_plans = UrbanPlan.query.filter_by(approval_status='approved').count()
    pending_plans = UrbanPlan.query.filter_by(approval_status='pending').count()
    total_zoned_area = sum([area.min_lot_size or 0 for area in zoning_areas])
    
    return render_template('smart_city/urban_planning_dashboard.html',
                         urban_plans=urban_plans,
                         zoning_areas=zoning_areas,
                         approved_plans=approved_plans,
                         pending_plans=pending_plans,
                         total_zoned_area=total_zoned_area,
                         current_date=datetime.datetime.now().strftime("%Y-%m-%d"))

@smart_city_bp.route('/urban-plan/add', methods=['GET', 'POST'])
@login_required
def add_urban_plan():
    """إضافة مخطط حضري جديد"""
    if request.method == 'POST':
        urban_plan = UrbanPlan(
            plan_name=request.form['plan_name'],
            plan_type=request.form['plan_type'],
            coordinates=request.form['coordinates'],
            land_use_category=request.form['land_use_category'],
            approval_status=request.form['approval_status'],
            approval_date=datetime.datetime.strptime(request.form['approval_date'], '%Y-%m-%d') if request.form['approval_date'] else None,
            expiry_date=datetime.datetime.strptime(request.form['expiry_date'], '%Y-%m-%d') if request.form['expiry_date'] else None,
            planning_authority=request.form['planning_authority'],
            description=request.form['description'],
            restrictions=request.form['restrictions'],
            building_height_limit=float(request.form['building_height_limit']) if request.form['building_height_limit'] else None,
            density_limit=float(request.form['density_limit']) if request.form['density_limit'] else None,
            setback_requirements=request.form['setback_requirements']
        )
        
        db.session.add(urban_plan)
        db.session.commit()
        flash('تم إضافة المخطط الحضري بنجاح', 'success')
        return redirect(url_for('smart_city.urban_planning_dashboard'))
    
    return render_template('smart_city/add_urban_plan.html',
                         current_date=datetime.datetime.now().strftime("%Y-%m-%d"))

# ===== Housing Management =====

@smart_city_bp.route('/housing')
@login_required
def housing_dashboard():
    """لوحة معلومات الإسكان"""
    housing_units = HousingUnit.query.all()
    recent_inspections = HousingInspection.query.order_by(HousingInspection.inspection_date.desc()).limit(10).all()
    
    # إحصائيات
    total_units = len(housing_units)
    occupied_units = len([unit for unit in housing_units if unit.occupancy_status == 'occupied'])
    vacant_units = len([unit for unit in housing_units if unit.occupancy_status == 'vacant'])
    damaged_units = len([unit for unit in housing_units if unit.condition_status in ['poor', 'damaged']])
    
    occupancy_rate = (occupied_units / total_units * 100) if total_units > 0 else 0
    
    return render_template('smart_city/housing_dashboard.html',
                         housing_units=housing_units,
                         recent_inspections=recent_inspections,
                         total_units=total_units,
                         occupied_units=occupied_units,
                         vacant_units=vacant_units,
                         damaged_units=damaged_units,
                         occupancy_rate=round(occupancy_rate, 1),
                         current_date=datetime.datetime.now().strftime("%Y-%m-%d"))

@smart_city_bp.route('/housing/add', methods=['GET', 'POST'])
@login_required
def add_housing_unit():
    """إضافة وحدة سكنية جديدة"""
    if request.method == 'POST':
        housing_unit = HousingUnit(
            unit_number=request.form['unit_number'],
            building_number=request.form['building_number'],
            unit_type=request.form['unit_type'],
            housing_category=request.form['housing_category'],
            coordinates=request.form['coordinates'],
            center_lat=float(request.form['center_lat']) if request.form['center_lat'] else None,
            center_lng=float(request.form['center_lng']) if request.form['center_lng'] else None,
            condition_status=request.form['condition_status'],
            occupancy_status=request.form['occupancy_status'],
            occupancy_level=int(request.form['occupancy_level']) if request.form['occupancy_level'] else 0,
            max_capacity=int(request.form['max_capacity']) if request.form['max_capacity'] else 0,
            floor_area=float(request.form['floor_area']) if request.form['floor_area'] else None,
            number_of_rooms=int(request.form['number_of_rooms']) if request.form['number_of_rooms'] else None,
            number_of_bathrooms=int(request.form['number_of_bathrooms']) if request.form['number_of_bathrooms'] else None,
            has_parking=bool(request.form.get('has_parking')),
            accessibility_features=request.form['accessibility_features'],
            owner_name=request.form['owner_name'],
            owner_contact=request.form['owner_contact'],
            rental_status=request.form['rental_status'],
            monthly_rent=float(request.form['monthly_rent']) if request.form['monthly_rent'] else None,
            utilities_included=request.form['utilities_included'],
            notes=request.form['notes']
        )
        
        db.session.add(housing_unit)
        db.session.commit()
        flash('تم إضافة الوحدة السكنية بنجاح', 'success')
        return redirect(url_for('smart_city.housing_dashboard'))
    
    return render_template('smart_city/add_housing_unit.html',
                         current_date=datetime.datetime.now().strftime("%Y-%m-%d"))

# ===== API Endpoints =====

@smart_city_bp.route('/api/parking-occupancy')
@login_required
def api_parking_occupancy():
    """API لبيانات إشغال المواقف"""
    parking_areas = ParkingArea.query.filter_by(is_active=True).all()
    data = []
    for area in parking_areas:
        occupancy_rate = (area.current_occupancy / area.capacity * 100) if area.capacity > 0 else 0
        data.append({
            'id': area.id,
            'name': area.name,
            'type': area.area_type,
            'capacity': area.capacity,
            'occupied': area.current_occupancy,
            'occupancy_rate': round(occupancy_rate, 1),
            'coordinates': json.loads(area.coordinates) if area.coordinates else None,
            'center_lat': area.center_lat,
            'center_lng': area.center_lng
        })
    return jsonify(data)

@smart_city_bp.route('/api/traffic-zones')
@login_required
def api_traffic_zones():
    """API لبيانات المناطق المرورية"""
    traffic_zones = TrafficZone.query.all()
    data = []
    for zone in traffic_zones:
        data.append({
            'id': zone.id,
            'name': zone.name,
            'type': zone.zone_type,
            'severity': zone.severity_level,
            'coordinates': json.loads(zone.coordinates) if zone.coordinates else None,
            'is_active': zone.end_time is None or zone.end_time > datetime.datetime.now(),
            'description': zone.description
        })
    return jsonify(data)
