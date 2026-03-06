import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

# تهيئة قاعدة البيانات
db = SQLAlchemy()

# دالة للحصول على قيمة إعداد من قاعدة البيانات
def get_setting(key, default=None):
    """الحصول على قيمة إعداد من قاعدة البيانات"""
    from sqlalchemy.exc import OperationalError
    try:
        setting = SystemSettings.query.filter_by(key=key).first()
        if setting:
            return setting.value
        return default
    except (OperationalError, Exception):
        return default

# نموذج اللوحات
class MDBPanel(db.Model):
    __tablename__ = 'mdb_panel'

    # إضافة فهارس لتحسين الأداء
    __table_args__ = (
        db.Index('idx_mdb_panel_mdb', 'mdb'),
        db.Index('idx_mdb_panel_area_name', 'area_name'),
        db.Index('idx_mdb_panel_status', 'status'),
        db.Index('idx_mdb_panel_panel_type', 'panel_type'),
    )

    id = db.Column(db.Integer, primary_key=True)
    mdb = db.Column(db.String(100), nullable=False)
    maximo_tag = db.Column(db.String(100), nullable=False)
    x_coordinate = db.Column(db.Float)
    y_coordinate = db.Column(db.Float)
    notes = db.Column(db.Text)
    phase = db.Column(db.String(100))
    implementation_year = db.Column(db.Integer)
    area_code = db.Column(db.String(100))
    panel_type = db.Column(db.String(100))
    area_name = db.Column(db.String(100))
    status = db.Column(db.String(100), default='عامل')  # حالة اللوحة (عامل، معطل، تحت الصيانة)
    last_maintenance_date = db.Column(db.DateTime)  # تاريخ آخر صيانة
    issues_count = db.Column(db.Integer, default=0)  # عدد المشاكل المسجلة

    # معلومات القواطع والحدود
    breaker_capacity = db.Column(db.Float)  # سعة القاطع (أمبير)
    max_voltage = db.Column(db.Float, default=250.0)  # الحد الأقصى للجهد (فولت)
    min_voltage = db.Column(db.Float, default=210.0)  # الحد الأدنى للجهد (فولت)
    warning_threshold = db.Column(db.Float, default=70.0)  # نسبة التحذير (%)
    danger_threshold = db.Column(db.Float, default=80.0)  # نسبة الخطر (%)

    # معلومات إضافية
    location_url = db.Column(db.String(255))  # رابط الموقع على الخارطة
    responsible_contractor_id = db.Column(db.Integer, db.ForeignKey('contractor.id'))
    responsible_contractor = db.relationship('Contractor', foreign_keys=[responsible_contractor_id])
    is_scada_connected = db.Column(db.Boolean, default=False)  # هل اللوحة مربوطة بنظام سكادا

    # ربط اللوحة بالمخيم والشركة والدولة
    camp_id = db.Column(db.Integer, db.ForeignKey('camp.id'))
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'))
    country_id = db.Column(db.Integer, db.ForeignKey('country.id'))

    # العلاقات الجديدة
    camp = db.relationship('Camp', foreign_keys=[camp_id], backref=db.backref('panels', lazy=True))
    company = db.relationship('Company', foreign_keys=[company_id], backref=db.backref('panels', lazy=True))
    country = db.relationship('Country', foreign_keys=[country_id], backref=db.backref('panels', lazy=True))

    def __repr__(self):
        return f'<MDBPanel {self.mdb}>'

# نموذج المقاولين
class Contractor(db.Model):
    __tablename__ = 'contractor'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contact_person = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    area_responsibility = db.Column(db.Text)  # المناطق المسؤول عنها (مخزنة كنص JSON)
    issues_count = db.Column(db.Integer, default=0)  # عدد المشاكل المسجلة
    is_manager = db.Column(db.Boolean, default=False)  # إضافة حقل لتحديد ما إذا كان المقاول مديرًا

    # العلاقة مع المقاولين التابعين (للمقاول المدير)
    parent_contractor_id = db.Column(db.Integer, db.ForeignKey('contractor.id'))
    sub_contractors = db.relationship('Contractor', backref=db.backref('parent_contractor', remote_side=[id]), lazy=True)

    # العلاقة مع أعضاء المجموعة
    team_members = db.relationship('ContractorTeamMember', backref='contractor', lazy=True, cascade="all, delete-orphan")

    # العلاقة مع فرق العمل
    teams = db.relationship('ContractorTeam', backref='contractor', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Contractor {self.name}>'

# نموذج فرق المقاول
class ContractorTeam(db.Model):
    __tablename__ = 'contractor_team'

    id = db.Column(db.Integer, primary_key=True)
    contractor_id = db.Column(db.Integer, db.ForeignKey('contractor.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)  # اسم الفريق
    area_responsibility = db.Column(db.Text)  # المناطق المسؤول عنها (مخزنة كنص JSON)
    description = db.Column(db.Text)  # وصف الفريق
    is_active = db.Column(db.Boolean, default=True)  # حالة الفريق (نشط/غير نشط)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)
    parent_team_id = db.Column(db.Integer, db.ForeignKey('contractor_team.id'))  # إضافة علاقة مع الفريق الأب

    # العلاقة مع أعضاء الفريق
    members = db.relationship('ContractorTeamMember', backref='team', lazy=True, cascade="all, delete-orphan")

    # العلاقة مع المستخدمين
    users = db.relationship('User', backref='team', lazy=True)

    # العلاقة مع الفرق الفرعية
    sub_teams = db.relationship('ContractorTeam', backref=db.backref('parent_team', remote_side=[id]), lazy=True)

    def __repr__(self):
        return f'<Team {self.name} for {self.contractor.name}>'

# نموذج أعضاء مجموعة المقاول
class ContractorTeamMember(db.Model):
    __tablename__ = 'contractor_team_member'

    id = db.Column(db.Integer, primary_key=True)
    contractor_id = db.Column(db.Integer, db.ForeignKey('contractor.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('contractor_team.id'))  # الفريق الذي ينتمي إليه العضو (اختياري)
    name = db.Column(db.String(100), nullable=False)  # اسم العضو
    position = db.Column(db.String(100))  # المنصب أو الوظيفة
    phone = db.Column(db.String(20))  # رقم الهاتف
    email = db.Column(db.String(100))  # البريد الإلكتروني
    is_active = db.Column(db.Boolean, default=True)  # حالة العضو (نشط/غير نشط)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)

    def __repr__(self):
        team_name = self.team.name if self.team else "No Team"
        return f'<TeamMember {self.name} for {self.contractor.name} in {team_name}>'

# نموذج أنواع طلبات الفحص
class InspectionRequestType(db.Model):
    __tablename__ = 'inspection_request_type'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # اسم نوع الطلب
    description = db.Column(db.Text)  # وصف نوع الطلب
    is_active = db.Column(db.Boolean, default=True)  # هل النوع نشط
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)

    def __repr__(self):
        return f'<InspectionRequestType {self.name}>'

# نموذج طلبات الفحص
class InspectionRequest(db.Model):
    __tablename__ = 'inspection_request'

    # إضافة فهارس لتحسين الأداء
    __table_args__ = (
        db.Index('idx_inspection_panel_id', 'panel_id'),
        db.Index('idx_inspection_requester_id', 'requester_id'),
        db.Index('idx_inspection_assignee_id', 'assignee_id'),
        db.Index('idx_inspection_contractor_id', 'contractor_id'),
        db.Index('idx_inspection_team_id', 'team_id'),
        db.Index('idx_inspection_status', 'status'),
        db.Index('idx_inspection_created_at', 'created_at'),
    )

    id = db.Column(db.Integer, primary_key=True)
    request_number = db.Column(db.String(50), unique=True)  # رقم الطلب
    panel_id = db.Column(db.Integer, db.ForeignKey('mdb_panel.id'), nullable=False)
    requester_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assignee_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # الشخص المكلف بالفحص
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'))  # الشخص المخصص له الطلب (مسجل القراءات)
    assigned_group_id = db.Column(db.Integer, db.ForeignKey('user_group.id'))  # المجموعة المكلفة بالفحص
    assigned_sub_group_id = db.Column(db.Integer, db.ForeignKey('sub_group.id'))  # المجموعة الفرعية المكلفة
    contractor_id = db.Column(db.Integer, db.ForeignKey('contractor.id'))
    team_id = db.Column(db.Integer, db.ForeignKey('contractor_team.id'))
    title = db.Column(db.String(255))  # عنوان الطلب
    description = db.Column(db.Text)  # وصف الطلب
    request_type = db.Column(db.String(100))  # نوع الطلب (للتوافق مع الإصدارات السابقة)
    request_type_id = db.Column(db.Integer, db.ForeignKey('inspection_request_type.id'))  # معرف نوع الطلب
    status = db.Column(db.String(50), default='جديد')  # جديد، قيد التنفيذ، مكتمل، ملغي
    priority = db.Column(db.String(50), default='متوسط')  # منخفض، متوسط، عالي
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    completed_at = db.Column(db.DateTime)
    started_at = db.Column(db.DateTime)  # وقت بدء التنفيذ
    processing_time = db.Column(db.Integer)  # وقت المعالجة بالدقائق
    completion_time = db.Column(db.Integer)  # وقت الإنجاز بالدقائق
    completed_by = db.Column(db.Integer, db.ForeignKey('user.id'))  # الشخص الذي أكمل الطلب
    due_date = db.Column(db.DateTime)  # تاريخ الاستحقاق
    image_path = db.Column(db.String(255))  # مسار الصورة المرفقة
    mutawif_name = db.Column(db.String(100))  # اسم المطوف
    pilgrim_guide_name = db.Column(db.String(100))  # اسم المرشد
    location_details = db.Column(db.Text)  # تفاصيل الموقع
    responsible_person = db.Column(db.String(100))  # الشخص المسؤول
    notes = db.Column(db.Text)  # ملاحظات إضافية

    # العلاقات
    panel = db.relationship('MDBPanel', backref=db.backref('inspection_requests', lazy=True))
    requester = db.relationship('User', foreign_keys=[requester_id], backref=db.backref('requested_inspections', lazy=True))
    assignee = db.relationship('User', foreign_keys=[assignee_id], backref=db.backref('assigned_inspections', lazy=True))
    assigned_user = db.relationship('User', foreign_keys=[assigned_to], backref=db.backref('assigned_to_inspections', lazy=True))
    assigned_group = db.relationship('UserGroup', foreign_keys=[assigned_group_id], backref=db.backref('assigned_inspection_requests', lazy=True))
    assigned_sub_group = db.relationship('SubGroup', foreign_keys=[assigned_sub_group_id], backref=db.backref('assigned_inspection_requests', lazy=True))
    completed_user = db.relationship('User', foreign_keys=[completed_by], backref=db.backref('completed_inspections', lazy=True))
    contractor = db.relationship('Contractor', backref=db.backref('inspection_requests', lazy=True))
    team = db.relationship('ContractorTeam', backref=db.backref('inspection_requests', lazy=True))
    request_type_obj = db.relationship('InspectionRequestType', backref=db.backref('inspection_requests', lazy=True))

    def __repr__(self):
        return f'<InspectionRequest {self.id}>'

    def get_active_assignments(self):
        """الحصول على التوزيعات النشطة لهذا الطلب"""
        return InspectionRequestAssignment.query.filter_by(
            inspection_request_id=self.id,
            is_active=True
        ).all()

    def is_assigned_to_user(self, user_id):
        """التحقق من تخصيص الطلب لمستخدم معين"""
        return (
            self.assignee_id == user_id or
            self.assigned_to == user_id or
            InspectionRequestAssignment.query.filter_by(
                inspection_request_id=self.id,
                user_id=user_id,
                is_active=True
            ).first() is not None
        )

# نموذج البلاغات
class Issue(db.Model):
    __tablename__ = 'issue'

    # إضافة فهارس لتحسين الأداء
    __table_args__ = (
        db.Index('idx_issue_panel_id', 'panel_id'),
        db.Index('idx_issue_contractor_id', 'contractor_id'),
        db.Index('idx_issue_status', 'status'),
        db.Index('idx_issue_created_at', 'created_at'),
        db.Index('idx_issue_assignee_id', 'assignee_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    panel_id = db.Column(db.Integer, db.ForeignKey('mdb_panel.id'), nullable=True)  # يمكن أن يكون فارغاً للبلاغات العامة
    contractor_id = db.Column(db.Integer, db.ForeignKey('contractor.id'))
    title = db.Column(db.String(255))  # عنوان البلاغ
    issue_type = db.Column(db.String(100))  # نوع المشكلة
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default='مفتوح')  # مفتوح، قيد المعالجة، مغلق
    priority = db.Column(db.String(50), default='متوسط')  # منخفض، متوسط، عالي
    responsible_person = db.Column(db.String(100))  # الشخص المسؤول
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    closed_at = db.Column(db.DateTime)
    started_at = db.Column(db.DateTime)  # وقت بدء المعالجة
    processing_time = db.Column(db.Integer)  # وقت المعالجة بالدقائق
    closure_time = db.Column(db.Integer)  # وقت الإقفال بالدقائق
    image_path = db.Column(db.String(255))  # مسار الصورة المرفقة
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))  # من قام بإنشاء البلاغ
    assignee_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # الشخص المكلف بمعالجة البلاغ
    assigned_group_id = db.Column(db.Integer, db.ForeignKey('user_group.id'))  # المجموعة المكلفة بمعالجة البلاغ
    assigned_sub_group_id = db.Column(db.Integer, db.ForeignKey('sub_group.id'))  # المجموعة الفرعية المكلفة
    resolved_by = db.Column(db.Integer, db.ForeignKey('user.id'))  # الشخص الذي قام بحل البلاغ
    resolution_notes = db.Column(db.Text)  # ملاحظات الحل

    # العلاقات
    panel = db.relationship('MDBPanel', backref=db.backref('issues', lazy=True))
    contractor = db.relationship('Contractor', backref=db.backref('issues', lazy=True))
    creator = db.relationship('User', foreign_keys=[created_by], backref=db.backref('created_issues', lazy=True))
    assignee = db.relationship('User', foreign_keys=[assignee_id], backref=db.backref('assigned_issues', lazy=True))
    assigned_group = db.relationship('UserGroup', foreign_keys=[assigned_group_id], backref=db.backref('assigned_issues', lazy=True))
    assigned_sub_group = db.relationship('SubGroup', foreign_keys=[assigned_sub_group_id], backref=db.backref('assigned_issues', lazy=True))
    resolver = db.relationship('User', foreign_keys=[resolved_by], backref=db.backref('resolved_issues', lazy=True))

    def __repr__(self):
        return f'<Issue {self.id}>'

    def get_active_assignments(self):
        """الحصول على التوزيعات النشطة لهذا البلاغ"""
        return IssueAssignment.query.filter_by(
            issue_id=self.id,
            is_active=True
        ).all()

    def is_assigned_to_user(self, user_id):
        """التحقق من تخصيص البلاغ لمستخدم معين"""
        return (
            self.assignee_id == user_id or
            self.responsible_person == str(user_id) or
            IssueAssignment.query.filter_by(
                issue_id=self.id,
                user_id=user_id,
                is_active=True
            ).first() is not None
        )

# نموذج توزيع الطلبات على المستخدمين
class RequestAssignment(db.Model):
    __tablename__ = 'request_assignment'

    id = db.Column(db.Integer, primary_key=True)
    request_type = db.Column(db.String(20), nullable=False)  # 'inspection' أو 'issue'
    request_id = db.Column(db.Integer, nullable=False)  # معرف الطلب أو البلاغ
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.datetime.now)
    accepted_at = db.Column(db.DateTime)  # وقت قبول الطلب
    is_accepted = db.Column(db.Boolean, default=False)  # هل تم قبول الطلب
    is_active = db.Column(db.Boolean, default=True)  # هل التخصيص نشط

    # العلاقات
    user = db.relationship('User', backref=db.backref('request_assignments', lazy=True))

    def __repr__(self):
        return f'<RequestAssignment {self.request_type}-{self.request_id} to {self.user_id}>'

# نموذج البلاغات المرسلة لعدة مستخدمين
class IssueAssignment(db.Model):
    __tablename__ = 'issue_assignment'

    id = db.Column(db.Integer, primary_key=True)
    issue_id = db.Column(db.Integer, db.ForeignKey('issue.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.datetime.now)
    accepted_at = db.Column(db.DateTime)  # وقت قبول البلاغ
    is_accepted = db.Column(db.Boolean, default=False)  # هل تم قبول البلاغ
    is_active = db.Column(db.Boolean, default=True)  # هل التخصيص نشط

    # العلاقات
    issue = db.relationship('Issue', backref=db.backref('assignments', lazy=True))
    user = db.relationship('User', backref=db.backref('issue_assignments', lazy=True))

    def __repr__(self):
        return f'<IssueAssignment {self.issue_id} to {self.user_id}>'

# نموذج طلبات الفحص المرسلة لعدة مستخدمين
class InspectionRequestAssignment(db.Model):
    __tablename__ = 'inspection_request_assignment'

    id = db.Column(db.Integer, primary_key=True)
    inspection_request_id = db.Column(db.Integer, db.ForeignKey('inspection_request.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.datetime.now)
    accepted_at = db.Column(db.DateTime)  # وقت قبول الطلب
    is_accepted = db.Column(db.Boolean, default=False)  # هل تم قبول الطلب
    is_active = db.Column(db.Boolean, default=True)  # هل التخصيص نشط

    # العلاقات
    inspection_request = db.relationship('InspectionRequest', backref=db.backref('assignments', lazy=True))
    user = db.relationship('User', backref=db.backref('inspection_assignments', lazy=True))

    def __repr__(self):
        return f'<InspectionRequestAssignment {self.inspection_request_id} to {self.user_id}>'

# نموذج المستخدمين
class User(db.Model, UserMixin):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    role = db.Column(db.String(20), default='user')  # admin, user, contractor
    contractor_id = db.Column(db.Integer, db.ForeignKey('contractor.id'))
    team_id = db.Column(db.Integer, db.ForeignKey('contractor_team.id'))  # إضافة علاقة مع الفريق
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)
    last_login = db.Column(db.DateTime)
    is_manager = db.Column(db.Boolean, default=False)  # إضافة حقل لتحديد ما إذا كان المقاول مديرًا
    assigned_areas = db.Column(db.Text)  # المناطق المخصصة للمستخدم (محفوظة ك JSON)

    # العلاقة مع المقاول (إذا كان المستخدم مقاول)
    contractor = db.relationship('Contractor', backref=db.backref('users', lazy=True))

    def __repr__(self):
        return f'<User {self.username}>'

    def get_id(self):
        return str(self.id)

    def get_assigned_areas(self):
        """الحصول على قائمة المناطق المخصصة"""
        if self.assigned_areas:
            try:
                import json
                return json.loads(self.assigned_areas)
            except:
                return []
        return []

    def set_assigned_areas(self, areas):
        """تحديد قائمة المناطق المخصصة"""
        import json
        self.assigned_areas = json.dumps(areas) if areas else None

    def has_area_access(self, area_name):
        """فحص إذا كان المستخدم لديه صلاحية للوصول إلى منطقة معينة"""
        # المدير يمكنه الوصول إلى جميع المناطق
        if self.role == 'admin':
            return True

        # فحص المناطق المخصصة
        assigned_areas = self.get_assigned_areas()
        return area_name in assigned_areas if assigned_areas else True

    def set_password(self, password):
        """تعيين كلمة مرور مشفرة للمستخدم"""
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """التحقق من صحة كلمة المرور"""
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)

    def is_contractor_manager(self):
        """التحقق مما إذا كان المستخدم مقاول مدير"""
        return self.role == 'contractor' and self.is_manager

# نموذج المجموعات/الفرق
class UserGroup(db.Model):
    __tablename__ = 'user_group'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # اسم المجموعة
    description = db.Column(db.Text)  # وصف المجموعة
    leader_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # قائد المجموعة
    assigned_areas = db.Column(db.Text)  # المناطق المخصصة (محفوظة ك JSON)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))

    # العلاقات
    leader = db.relationship('User', foreign_keys=[leader_id], backref=db.backref('led_groups', lazy=True))
    creator = db.relationship('User', foreign_keys=[created_by])

    def __repr__(self):
        return f'<UserGroup {self.name}>'

    def get_assigned_areas(self):
        """الحصول على قائمة المناطق المخصصة"""
        if self.assigned_areas:
            try:
                import json
                return json.loads(self.assigned_areas)
            except:
                return []
        return []

    def set_assigned_areas(self, areas):
        """تحديد قائمة المناطق المخصصة"""
        import json
        self.assigned_areas = json.dumps(areas) if areas else None

# نموذج عضوية المجموعة
class UserGroupMembership(db.Model):
    __tablename__ = 'user_group_membership'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('user_group.id'), nullable=False)
    role_in_group = db.Column(db.String(50), default='member')  # member, leader, admin
    joined_at = db.Column(db.DateTime, default=datetime.datetime.now)
    is_active = db.Column(db.Boolean, default=True)

    # العلاقات
    user = db.relationship('User', backref=db.backref('group_memberships', lazy=True))
    group = db.relationship('UserGroup', backref=db.backref('memberships', lazy=True))

    def __repr__(self):
        return f'<UserGroupMembership {self.user_id}-{self.group_id}>'

# نموذج المجموعات الفرعية (مجموعات داخل الفريق)
class SubGroup(db.Model):
    __tablename__ = 'sub_group'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    parent_group_id = db.Column(db.Integer, db.ForeignKey('user_group.id'), nullable=False)
    assigned_areas = db.Column(db.Text)  # مناطق مخصصة لهذه المجموعة الفرعية
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)

    # العلاقات
    parent_group = db.relationship('UserGroup', backref=db.backref('sub_groups', lazy=True))

    def __repr__(self):
        return f'<SubGroup {self.name}>'

    def get_assigned_areas(self):
        """الحصول على قائمة المناطق المخصصة"""
        if self.assigned_areas:
            try:
                import json
                return json.loads(self.assigned_areas)
            except:
                return []
        return []

    def set_assigned_areas(self, areas):
        """تحديد قائمة المناطق المخصصة"""
        import json
        self.assigned_areas = json.dumps(areas) if areas else None

# نموذج عضوية المجموعة الفرعية
class SubGroupMembership(db.Model):
    __tablename__ = 'sub_group_membership'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    sub_group_id = db.Column(db.Integer, db.ForeignKey('sub_group.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.datetime.now)
    is_active = db.Column(db.Boolean, default=True)

    # العلاقات
    user = db.relationship('User', backref=db.backref('sub_group_memberships', lazy=True))
    sub_group = db.relationship('SubGroup', backref=db.backref('memberships', lazy=True))

    def __repr__(self):
        return f'<SubGroupMembership {self.user_id}-{self.sub_group_id}>'

# نموذج مناطق الخارطة (Polygons)
class MapArea(db.Model):
    __tablename__ = 'map_area'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    coordinates = db.Column(db.Text, nullable=False)  # تخزين الإحداثيات كنص JSON
    color = db.Column(db.String(20), default='#3388ff')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)

    def __repr__(self):
        return f'<MapArea {self.name}>'

# نموذج الأعمدة الديناميكية
class DynamicColumn(db.Model):
    __tablename__ = 'dynamic_column'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # اسم العمود
    display_name = db.Column(db.String(100), nullable=False)  # اسم العرض
    data_type = db.Column(db.String(50), nullable=False)  # نوع البيانات (نص، رقم، تاريخ)
    is_active = db.Column(db.Boolean, default=True)  # هل العمود نشط
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)

    def __repr__(self):
        return f'<DynamicColumn {self.name}>'

# نموذج إعدادات النظام
class SystemSettings(db.Model):
    __tablename__ = 'system_settings'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), nullable=False, unique=True)  # مفتاح الإعداد
    value = db.Column(db.Text, nullable=False)  # قيمة الإعداد
    description = db.Column(db.Text)  # وصف الإعداد
    updated_at = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    def __repr__(self):
        return f'<SystemSettings {self.key}>'

# نموذج قراءات الكهرباء
class ElectricalReading(db.Model):
    __tablename__ = 'electrical_reading'

    # إضافة فهارس لتحسين الأداء
    __table_args__ = (
        db.Index('idx_electrical_reading_panel_id', 'panel_id'),
        db.Index('idx_electrical_reading_timestamp', 'timestamp'),
        db.Index('idx_electrical_reading_panel_timestamp', 'panel_id', 'timestamp'),
        db.Index('idx_electrical_reading_current_status', 'current_status'),
    )

    id = db.Column(db.Integer, primary_key=True)
    panel_id = db.Column(db.Integer, db.ForeignKey('mdb_panel.id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)  # وقت القراءة
    is_three_phase = db.Column(db.Boolean, default=True)  # هل القراءة ثلاثية الطور

    # القراءات الأساسية - التيار
    current_l1 = db.Column(db.Float)  # التيار L1
    current_l2 = db.Column(db.Float)  # التيار L2
    current_l3 = db.Column(db.Float)  # التيار L3
    current = db.Column(db.Float)  # متوسط التيار أو التيار الأحادي

    # القراءات الأساسية - الجهد
    voltage_l1_l2 = db.Column(db.Float)  # الجهد L1-L2
    voltage_l2_l3 = db.Column(db.Float)  # الجهد L2-L3
    voltage_l3_l1 = db.Column(db.Float)  # الجهد L3-L1
    voltage_l1_n = db.Column(db.Float)  # الجهد L1-N
    voltage_l2_n = db.Column(db.Float)  # الجهد L2-N
    voltage_l3_n = db.Column(db.Float)  # الجهد L3-N
    voltage = db.Column(db.Float)  # متوسط الجهد أو الجهد الأحادي

    # القراءات الأساسية - القدرة الفعالة (P)
    active_power_l1 = db.Column(db.Float)  # القدرة الفعالة L1
    active_power_l2 = db.Column(db.Float)  # القدرة الفعالة L2
    active_power_l3 = db.Column(db.Float)  # القدرة الفعالة L3
    active_power_total = db.Column(db.Float)  # إجمالي القدرة الفعالة

    # القراءات الأساسية - القدرة الظاهرية (S)
    apparent_power_l1 = db.Column(db.Float)  # القدرة الظاهرية L1
    apparent_power_l2 = db.Column(db.Float)  # القدرة الظاهرية L2
    apparent_power_l3 = db.Column(db.Float)  # القدرة الظاهرية L3
    apparent_power_total = db.Column(db.Float)  # إجمالي القدرة الظاهرية

    # القراءات الأساسية - القدرة غير الفعالة (Q)
    reactive_power_l1 = db.Column(db.Float)  # القدرة غير الفعالة L1
    reactive_power_l2 = db.Column(db.Float)  # القدرة غير الفعالة L2
    reactive_power_l3 = db.Column(db.Float)  # القدرة غير الفعالة L3
    reactive_power_total = db.Column(db.Float)  # إجمالي القدرة غير الفعالة

    # القراءات الأساسية - معامل القدرة
    power_factor_l1 = db.Column(db.Float)  # معامل القدرة L1
    power_factor_l2 = db.Column(db.Float)  # معامل القدرة L2
    power_factor_l3 = db.Column(db.Float)  # معامل القدرة L3
    power_factor = db.Column(db.Float)  # متوسط معامل القدرة أو معامل القدرة الأحادي

    # القراءات الأساسية - أخرى
    power = db.Column(db.Float)  # القدرة (للتوافق مع الإصدارات السابقة)
    energy = db.Column(db.Float)  # الطاقة (كيلوواط ساعة)
    frequency = db.Column(db.Float)  # التردد (هرتز)
    load = db.Column(db.Float)  # الحمل (أمبير)

    # حالة القراءة
    current_status = db.Column(db.String(20), default='normal')  # normal, warning, danger
    voltage_status = db.Column(db.String(20), default='normal')  # normal, warning, danger
    power_status = db.Column(db.String(20), default='normal')  # normal, warning, danger

    # العلاقة مع اللوحة
    panel = db.relationship('MDBPanel', backref=db.backref('readings', lazy=True))

    def __repr__(self):
        return f'<ElectricalReading {self.id} for panel {self.panel_id}>'

# نموذج التنبيهات
class Alert(db.Model):
    __tablename__ = 'alert'

    # إضافة فهارس لتحسين الأداء
    __table_args__ = (
        db.Index('idx_alert_panel_id', 'panel_id'),
        db.Index('idx_alert_reading_id', 'reading_id'),
        db.Index('idx_alert_timestamp', 'timestamp'),
        db.Index('idx_alert_severity', 'severity'),
        db.Index('idx_alert_is_read', 'is_read'),
        db.Index('idx_alert_is_resolved', 'is_resolved'),
    )

    id = db.Column(db.Integer, primary_key=True)
    panel_id = db.Column(db.Integer, db.ForeignKey('mdb_panel.id'), nullable=False)
    reading_id = db.Column(db.Integer, db.ForeignKey('electrical_reading.id'), nullable=False)
    alert_type = db.Column(db.String(50), nullable=False)  # current, voltage, power, trip
    severity = db.Column(db.String(20), nullable=False)  # warning, danger
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.now)
    is_read = db.Column(db.Boolean, default=False)
    is_resolved = db.Column(db.Boolean, default=False)
    resolved_at = db.Column(db.DateTime)

    # العلاقات
    panel = db.relationship('MDBPanel', backref=db.backref('alerts', lazy=True))
    reading = db.relationship('ElectricalReading', backref=db.backref('alerts', lazy=True))

    def __repr__(self):
        return f'<Alert {self.id} for panel {self.panel_id}>'

# نموذج قيم الأعمدة الديناميكية
class DynamicColumnValue(db.Model):
    __tablename__ = 'dynamic_column_value'

    # إضافة فهارس لتحسين الأداء
    __table_args__ = (
        db.Index('idx_dynamic_column_value_panel_id', 'panel_id'),
        db.Index('idx_dynamic_column_value_column_id', 'column_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    panel_id = db.Column(db.Integer, db.ForeignKey('mdb_panel.id'), nullable=False)
    column_id = db.Column(db.Integer, db.ForeignKey('dynamic_column.id'), nullable=False)
    value = db.Column(db.Text)

    # العلاقات
    panel = db.relationship('MDBPanel', backref=db.backref('dynamic_values', lazy=True))
    column = db.relationship('DynamicColumn', backref=db.backref('values', lazy=True))

    def __repr__(self):
        return f'<DynamicColumnValue {self.id}>'

# نموذج النقاط الساخنة (Hot Spots)
class HotSpot(db.Model):
    __tablename__ = 'hot_spot'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    x_coordinate = db.Column(db.Float, nullable=False)
    y_coordinate = db.Column(db.Float, nullable=False)
    radius = db.Column(db.Float, default=100.0)  # نصف قطر النقطة الساخنة بالمتر
    color = db.Column(db.String(20), default='#FF0000')
    intensity = db.Column(db.Float, default=1.0)  # شدة النقطة الساخنة (1.0 - 10.0)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<HotSpot {self.name}>'

# نموذج وحدات القياس
class MeasurementUnit(db.Model):
    __tablename__ = 'measurement_unit'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)  # اسم الوحدة (مثل: A, KVA, W)
    display_name = db.Column(db.String(100), nullable=False)  # اسم العرض (مثل: أمبير، كيلو فولت أمبير، واط)
    category = db.Column(db.String(50), nullable=False)  # فئة الوحدة (current, voltage, power, energy, etc.)
    conversion_factor = db.Column(db.Float, default=1.0)  # معامل التحويل إلى الوحدة الأساسية
    is_default = db.Column(db.Boolean, default=False)  # هل هي الوحدة الافتراضية للفئة
    is_active = db.Column(db.Boolean, default=True)  # هل الوحدة نشطة
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    def __repr__(self):
        return f'<MeasurementUnit {self.name}>'

# نموذج القوائم المنسدلة
class DropdownList(db.Model):
    __tablename__ = 'dropdown_list'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # اسم القائمة المنسدلة
    display_name = db.Column(db.String(100), nullable=False)  # اسم العرض
    description = db.Column(db.Text)  # وصف القائمة
    field_type = db.Column(db.String(50), nullable=False)  # نوع الحقل المرتبط (current, voltage, power, etc.)
    is_active = db.Column(db.Boolean, default=True)  # هل القائمة نشطة
    visibility = db.Column(db.String(50), default='all')  # من يمكنه رؤية القائمة (all, admin, contractor)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    # العلاقة مع عناصر القائمة
    items = db.relationship('DropdownItem', backref='dropdown_list', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<DropdownList {self.name}>'

# نموذج عناصر القائمة المنسدلة
class DropdownItem(db.Model):
    __tablename__ = 'dropdown_item'

    id = db.Column(db.Integer, primary_key=True)
    dropdown_id = db.Column(db.Integer, db.ForeignKey('dropdown_list.id'), nullable=False)
    value = db.Column(db.String(100), nullable=False)  # قيمة العنصر
    display_text = db.Column(db.String(100), nullable=False)  # نص العرض
    order = db.Column(db.Integer, default=0)  # ترتيب العنصر في القائمة
    is_active = db.Column(db.Boolean, default=True)  # هل العنصر نشط
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)

    def __repr__(self):
        return f'<DropdownItem {self.display_text}>'

# نموذج القراءات اليدوية
class ManualReading(db.Model):
    __tablename__ = 'manual_reading'

    # إضافة فهارس لتحسين الأداء
    __table_args__ = (
        db.Index('idx_manual_reading_panel_id', 'panel_id'),
        db.Index('idx_manual_reading_timestamp', 'timestamp'),
        db.Index('idx_manual_reading_created_by', 'created_by'),
    )

    id = db.Column(db.Integer, primary_key=True)
    panel_id = db.Column(db.Integer, db.ForeignKey('mdb_panel.id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)  # وقت القراءة
    reading_type = db.Column(db.String(50), default='manual')  # نوع القراءة (manual, imported)
    is_three_phase = db.Column(db.Boolean, default=True)  # هل القراءة ثلاثية الطور
    panel_status = db.Column(db.String(50), default='عامل')  # حالة اللوحة (عامل، معطل، تحت الصيانة، مفصول)
    mutawif_name = db.Column(db.String(100))  # اسم المطوف

    # القراءات الأساسية - التيار
    current_l1 = db.Column(db.Float)  # التيار L1
    current_l2 = db.Column(db.Float)  # التيار L2
    current_l3 = db.Column(db.Float)  # التيار L3
    current_unit_id = db.Column(db.Integer, db.ForeignKey('measurement_unit.id'))  # وحدة التيار

    # القراءات الأساسية - الجهد
    voltage_l1_l2 = db.Column(db.Float)  # الجهد L1-L2
    voltage_l2_l3 = db.Column(db.Float)  # الجهد L2-L3
    voltage_l3_l1 = db.Column(db.Float)  # الجهد L3-L1
    voltage_l1_n = db.Column(db.Float)  # الجهد L1-N
    voltage_l2_n = db.Column(db.Float)  # الجهد L2-N
    voltage_l3_n = db.Column(db.Float)  # الجهد L3-N
    voltage_unit_id = db.Column(db.Integer, db.ForeignKey('measurement_unit.id'))  # وحدة الجهد

    # القراءات الأساسية - القدرة الفعالة (P)
    active_power_l1 = db.Column(db.Float)  # القدرة الفعالة L1
    active_power_l2 = db.Column(db.Float)  # القدرة الفعالة L2
    active_power_l3 = db.Column(db.Float)  # القدرة الفعالة L3
    active_power_total = db.Column(db.Float)  # إجمالي القدرة الفعالة
    active_power_unit_id = db.Column(db.Integer, db.ForeignKey('measurement_unit.id'))  # وحدة القدرة الفعالة

    # القراءات الأساسية - القدرة الظاهرية (S)
    apparent_power_l1 = db.Column(db.Float)  # القدرة الظاهرية L1
    apparent_power_l2 = db.Column(db.Float)  # القدرة الظاهرية L2
    apparent_power_l3 = db.Column(db.Float)  # القدرة الظاهرية L3
    apparent_power_total = db.Column(db.Float)  # إجمالي القدرة الظاهرية
    apparent_power_unit_id = db.Column(db.Integer, db.ForeignKey('measurement_unit.id'))  # وحدة القدرة الظاهرية

    # القراءات الأساسية - القدرة غير الفعالة (Q)
    reactive_power_l1 = db.Column(db.Float)  # القدرة غير الفعالة L1
    reactive_power_l2 = db.Column(db.Float)  # القدرة غير الفعالة L2
    reactive_power_l3 = db.Column(db.Float)  # القدرة غير الفعالة L3
    reactive_power_total = db.Column(db.Float)  # إجمالي القدرة غير الفعالة
    reactive_power_unit_id = db.Column(db.Integer, db.ForeignKey('measurement_unit.id'))  # وحدة القدرة غير الفعالة

    # القراءات الأساسية - معامل القدرة
    power_factor_l1 = db.Column(db.Float)  # معامل القدرة L1
    power_factor_l2 = db.Column(db.Float)  # معامل القدرة L2
    power_factor_l3 = db.Column(db.Float)  # معامل القدرة L3
    power_factor_total = db.Column(db.Float)  # إجمالي معامل القدرة

    # القراءات الأساسية - الطاقة
    energy = db.Column(db.Float)  # الطاقة
    energy_unit_id = db.Column(db.Integer, db.ForeignKey('measurement_unit.id'))  # وحدة الطاقة

    # القراءات الأساسية - أخرى
    frequency = db.Column(db.Float)  # التردد
    breaker_capacity = db.Column(db.Float)  # سعة القاطع
    load_percentage = db.Column(db.Float)  # نسبة الحمل
    current_status = db.Column(db.String(20), default='normal')  # حالة التيار (normal, warning, danger)
    dropdown_values = db.Column(db.Text)  # قيم القوائم المنسدلة بتنسيق JSON

    # للتوافق مع الإصدارات السابقة
    current = db.Column(db.Float)  # التيار (متوسط أو أحادي)
    voltage = db.Column(db.Float)  # الجهد (متوسط أو أحادي)
    power = db.Column(db.Float)  # القدرة (متوسط أو أحادي)
    power_unit_id = db.Column(db.Integer, db.ForeignKey('measurement_unit.id'))  # وحدة القدرة
    power_factor = db.Column(db.Float)  # معامل القدرة (متوسط أو أحادي)

    # معلومات إضافية
    notes = db.Column(db.Text)  # ملاحظات
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))  # من قام بإضافة القراءة
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)

    # العلاقات
    panel = db.relationship('MDBPanel', backref=db.backref('manual_readings', lazy=True))
    current_unit = db.relationship('MeasurementUnit', foreign_keys=[current_unit_id])
    voltage_unit = db.relationship('MeasurementUnit', foreign_keys=[voltage_unit_id])
    power_unit = db.relationship('MeasurementUnit', foreign_keys=[power_unit_id])
    active_power_unit = db.relationship('MeasurementUnit', foreign_keys=[active_power_unit_id])
    apparent_power_unit = db.relationship('MeasurementUnit', foreign_keys=[apparent_power_unit_id])
    reactive_power_unit = db.relationship('MeasurementUnit', foreign_keys=[reactive_power_unit_id])
    energy_unit = db.relationship('MeasurementUnit', foreign_keys=[energy_unit_id])
    user = db.relationship('User', backref=db.backref('manual_readings', lazy=True))

    def __repr__(self):
        return f'<ManualReading {self.id} for panel {self.panel_id}>'

# نموذج الدول
class Country(db.Model):
    __tablename__ = 'country'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)  # اسم الدولة
    code = db.Column(db.String(10))  # رمز الدولة (مثل SA, EG, etc.)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)

    def __repr__(self):
        return f'<Country {self.name}>'

# نموذج الشركات
class Company(db.Model):
    __tablename__ = 'company'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)  # اسم الشركة
    country_id = db.Column(db.Integer, db.ForeignKey('country.id'), nullable=False)  # الدولة
    contact_person = db.Column(db.String(100))  # الشخص المسؤول (اختياري)
    phone = db.Column(db.String(20))  # رقم الهاتف (اختياري)
    email = db.Column(db.String(100))  # البريد الإلكتروني
    address = db.Column(db.Text)  # العنوان
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)

    # العلاقات
    country = db.relationship('Country', backref=db.backref('companies', lazy=True))

    def __repr__(self):
        return f'<Company {self.name}>'

    def get_contact_info(self):
        """الحصول على معلومات الاتصال المتاحة"""
        contact_info = {}
        if self.contact_person:
            contact_info['contact_person'] = self.contact_person
        if self.phone:
            contact_info['phone'] = self.phone
        if self.email:
            contact_info['email'] = self.email
        return contact_info

# نموذج المخيمات
class Camp(db.Model):
    __tablename__ = 'camp'

    id = db.Column(db.Integer, primary_key=True)
    camp_number = db.Column(db.String(50), nullable=False)  # رقم المخيم
    square_number = db.Column(db.String(50), nullable=False)  # رقم المربع
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)  # الشركة
    pilgrims_count = db.Column(db.Integer, default=0)  # عدد الحجاج
    total_area = db.Column(db.Float)  # المساحة الإجمالية
    zone_style = db.Column(db.String(100))  # Zone/Style
    coordinates = db.Column(db.Text)  # الإحداثيات (polygon coordinates)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)

    # العلاقات
    company = db.relationship('Company', backref=db.backref('camps', lazy=True))

    def __repr__(self):
        return f'<Camp {self.camp_number} - Square {self.square_number}>'

    def get_coordinates_list(self):
        """تحويل الإحداثيات من نص إلى قائمة"""
        if self.coordinates:
            try:
                points = []
                coords_str = self.coordinates.strip()
                if coords_str:
                    # محاولة تحليل تنسيقات مختلفة من الإحداثيات

                    # التنسيق 1: نقطة واحدة "lat,lng"
                    if ',' in coords_str and ' ' not in coords_str:
                        parts = coords_str.split(',')
                        if len(parts) >= 2:
                            try:
                                lat = float(parts[0])
                                lng = float(parts[1])
                                points.append([lat, lng])
                            except ValueError:
                                pass

                    # التنسيق 2: نقاط متعددة مفصولة بمسافات "lat1,lng1 lat2,lng2"
                    elif ' ' in coords_str:
                        coord_pairs = coords_str.split(' ')
                        for pair in coord_pairs:
                            if ',' in pair:
                                parts = pair.split(',')
                                if len(parts) >= 2:
                                    try:
                                        lat = float(parts[0])
                                        lng = float(parts[1])
                                        points.append([lat, lng])
                                    except ValueError:
                                        continue

                    # التنسيق 3: JSON array
                    elif coords_str.startswith('[') and coords_str.endswith(']'):
                        import json
                        try:
                            coords_json = json.loads(coords_str)
                            if isinstance(coords_json, list):
                                for coord in coords_json:
                                    if isinstance(coord, list) and len(coord) >= 2:
                                        try:
                                            lat = float(coord[0])
                                            lng = float(coord[1])
                                            points.append([lat, lng])
                                        except (ValueError, TypeError):
                                            continue
                        except json.JSONDecodeError:
                            pass

                return points
            except Exception as e:
                print(f"خطأ في تحليل الإحداثيات: {e}")
                return []
        return []

    def get_center_coordinates(self):
        """حساب الإحداثيات المركزية للمخيم"""
        points = self.get_coordinates_list()
        if points and len(points) > 0:
            # التحقق من صحة الإحداثيات (يجب أن تكون في نطاق معقول)
            valid_points = []
            for point in points:
                lat, lng = point[0], point[1]
                # التحقق من أن الإحداثيات في نطاق معقول (منطقة مكة المكرمة)
                if 20.0 <= lat <= 22.0 and 39.0 <= lng <= 41.0:
                    valid_points.append(point)

            if valid_points:
                avg_lat = sum(point[0] for point in valid_points) / len(valid_points)
                avg_lng = sum(point[1] for point in valid_points) / len(valid_points)
                return [avg_lat, avg_lng]

        # إرجاع إحداثيات افتراضية لمنطقة منى إذا لم تكن هناك إحداثيات صحيحة
        return [21.3891, 39.8579]

# نموذج ربط اللوحات بالمخيمات
class PanelCampAssignment(db.Model):
    __tablename__ = 'panel_camp_assignment'

    id = db.Column(db.Integer, primary_key=True)
    panel_id = db.Column(db.Integer, db.ForeignKey('mdb_panel.id'), nullable=False)
    camp_id = db.Column(db.Integer, db.ForeignKey('camp.id'), nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.datetime.now)
    is_active = db.Column(db.Boolean, default=True)

    # العلاقات
    panel = db.relationship('MDBPanel', backref=db.backref('camp_assignments', lazy=True))
    camp = db.relationship('Camp', backref=db.backref('panel_assignments', lazy=True))

    def __repr__(self):
        return f'<PanelCampAssignment Panel:{self.panel_id} Camp:{self.camp_id}>'

# نماذج المميزات الجديدة

# 1. نموذج المواقف والنقل
class ParkingArea(db.Model):
    __tablename__ = 'parking_area'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    area_type = db.Column(db.String(50), nullable=False)  # public, private, maintenance, emergency
    capacity = db.Column(db.Integer, default=0)
    current_occupancy = db.Column(db.Integer, default=0)
    coordinates = db.Column(db.Text)  # polygon coordinates
    center_lat = db.Column(db.Float)
    center_lng = db.Column(db.Float)
    hourly_rate = db.Column(db.Float, default=0.0)
    is_active = db.Column(db.Boolean, default=True)
    accessibility_features = db.Column(db.Text)  # JSON for wheelchair access, etc.
    operating_hours = db.Column(db.String(100))  # "24/7" or "06:00-22:00"
    contact_info = db.Column(db.String(200))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    def __repr__(self):
        return f'<ParkingArea {self.name}>'

class TrafficZone(db.Model):
    __tablename__ = 'traffic_zone'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    zone_type = db.Column(db.String(50), nullable=False)  # congestion, restricted, closed
    coordinates = db.Column(db.Text)  # polygon coordinates
    severity_level = db.Column(db.String(20), default='medium')  # low, medium, high, critical
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    is_permanent = db.Column(db.Boolean, default=False)
    description = db.Column(db.Text)
    alternative_routes = db.Column(db.Text)  # JSON array of route suggestions
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    def __repr__(self):
        return f'<TrafficZone {self.name}>'

class TransportRoute(db.Model):
    __tablename__ = 'transport_route'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    route_type = db.Column(db.String(50), nullable=False)  # bus, metro, taxi, shuttle
    route_coordinates = db.Column(db.Text)  # line coordinates
    stops = db.Column(db.Text)  # JSON array of stop coordinates and names
    schedule = db.Column(db.Text)  # JSON schedule information
    fare = db.Column(db.Float, default=0.0)
    is_active = db.Column(db.Boolean, default=True)
    operator = db.Column(db.String(100))
    contact_info = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)

    def __repr__(self):
        return f'<TransportRoute {self.name}>'

# 2. نموذج التخطيط الحضري
class UrbanPlan(db.Model):
    __tablename__ = 'urban_plan'

    id = db.Column(db.Integer, primary_key=True)
    plan_name = db.Column(db.String(100), nullable=False)
    plan_type = db.Column(db.String(50), nullable=False)  # zoning, development, master_plan
    coordinates = db.Column(db.Text)  # polygon coordinates
    land_use_category = db.Column(db.String(50))  # residential, commercial, industrial, mixed
    approval_status = db.Column(db.String(30), default='pending')  # pending, approved, rejected
    approval_date = db.Column(db.DateTime)
    expiry_date = db.Column(db.DateTime)
    planning_authority = db.Column(db.String(100))
    description = db.Column(db.Text)
    restrictions = db.Column(db.Text)  # JSON array of restrictions
    building_height_limit = db.Column(db.Float)
    density_limit = db.Column(db.Float)
    setback_requirements = db.Column(db.Text)  # JSON
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    def __repr__(self):
        return f'<UrbanPlan {self.plan_name}>'

class ZoningArea(db.Model):
    __tablename__ = 'zoning_area'

    id = db.Column(db.Integer, primary_key=True)
    zone_name = db.Column(db.String(100), nullable=False)
    zone_code = db.Column(db.String(20), nullable=False)
    zone_type = db.Column(db.String(50), nullable=False)  # R1, R2, C1, I1, etc.
    coordinates = db.Column(db.Text)  # polygon coordinates
    permitted_uses = db.Column(db.Text)  # JSON array
    prohibited_uses = db.Column(db.Text)  # JSON array
    max_building_height = db.Column(db.Float)
    max_floor_area_ratio = db.Column(db.Float)
    min_lot_size = db.Column(db.Float)
    setback_front = db.Column(db.Float)
    setback_rear = db.Column(db.Float)
    setback_side = db.Column(db.Float)
    parking_requirements = db.Column(db.Text)  # JSON
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)

    def __repr__(self):
        return f'<ZoningArea {self.zone_name}>'

# 3. نموذج الإسكان
class HousingUnit(db.Model):
    __tablename__ = 'housing_unit'

    id = db.Column(db.Integer, primary_key=True)
    unit_number = db.Column(db.String(50), nullable=False)
    building_number = db.Column(db.String(50))
    unit_type = db.Column(db.String(50), nullable=False)  # residential, commercial, mixed, vacant
    housing_category = db.Column(db.String(50))  # apartment, villa, studio, shop, office
    coordinates = db.Column(db.Text)  # polygon coordinates for the unit/building
    center_lat = db.Column(db.Float)
    center_lng = db.Column(db.Float)
    condition_status = db.Column(db.String(30), default='good')  # good, fair, poor, damaged, abandoned
    occupancy_status = db.Column(db.String(30), default='unknown')  # occupied, vacant, under_construction
    occupancy_level = db.Column(db.Integer, default=0)  # number of occupants
    max_capacity = db.Column(db.Integer, default=0)
    floor_area = db.Column(db.Float)
    number_of_rooms = db.Column(db.Integer)
    number_of_bathrooms = db.Column(db.Integer)
    has_parking = db.Column(db.Boolean, default=False)
    accessibility_features = db.Column(db.Text)  # JSON
    last_inspection_date = db.Column(db.DateTime)
    next_inspection_date = db.Column(db.DateTime)
    owner_name = db.Column(db.String(100))
    owner_contact = db.Column(db.String(100))
    rental_status = db.Column(db.String(30))  # owned, rented, vacant
    monthly_rent = db.Column(db.Float)
    utilities_included = db.Column(db.Text)  # JSON array
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    def __repr__(self):
        return f'<HousingUnit {self.unit_number}>'

class HousingInspection(db.Model):
    __tablename__ = 'housing_inspection'

    id = db.Column(db.Integer, primary_key=True)
    housing_unit_id = db.Column(db.Integer, db.ForeignKey('housing_unit.id'), nullable=False)
    inspector_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    inspection_date = db.Column(db.DateTime, default=datetime.datetime.now)
    inspection_type = db.Column(db.String(50), nullable=False)  # routine, complaint, emergency, pre_rental
    overall_condition = db.Column(db.String(30))  # excellent, good, fair, poor, critical
    structural_condition = db.Column(db.String(30))
    electrical_condition = db.Column(db.String(30))
    plumbing_condition = db.Column(db.String(30))
    safety_compliance = db.Column(db.Boolean, default=True)
    violations_found = db.Column(db.Text)  # JSON array of violations
    recommendations = db.Column(db.Text)
    follow_up_required = db.Column(db.Boolean, default=False)
    follow_up_date = db.Column(db.DateTime)
    photos = db.Column(db.Text)  # JSON array of photo paths
    inspector_notes = db.Column(db.Text)

    # العلاقات
    housing_unit = db.relationship('HousingUnit', backref=db.backref('inspections', lazy=True))
    inspector = db.relationship('User', backref=db.backref('housing_inspections', lazy=True))

    def __repr__(self):
        return f'<HousingInspection {self.id}>'

# 4. نموذج السلامة والرقابة
class SafetyInspection(db.Model):
    __tablename__ = 'safety_inspection'

    id = db.Column(db.Integer, primary_key=True)
    inspection_code = db.Column(db.String(50), unique=True, nullable=False)
    asset_type = db.Column(db.String(50), nullable=False)  # panel, housing, infrastructure, public_area
    asset_id = db.Column(db.Integer)  # ID of the related asset
    coordinates = db.Column(db.Text)  # inspection location
    inspector_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    inspection_date = db.Column(db.DateTime, default=datetime.datetime.now)
    inspection_type = db.Column(db.String(50), nullable=False)  # routine, emergency, complaint, follow_up
    safety_category = db.Column(db.String(50))  # electrical, structural, fire, environmental, traffic
    risk_level = db.Column(db.String(20), default='low')  # low, medium, high, critical
    hazards_identified = db.Column(db.Text)  # JSON array of hazards
    safety_violations = db.Column(db.Text)  # JSON array of violations
    immediate_actions_taken = db.Column(db.Text)
    recommendations = db.Column(db.Text)
    follow_up_required = db.Column(db.Boolean, default=False)
    follow_up_date = db.Column(db.DateTime)
    status = db.Column(db.String(30), default='open')  # open, in_progress, resolved, closed
    resolution_date = db.Column(db.DateTime)
    photos = db.Column(db.Text)  # JSON array of photo paths
    inspector_signature = db.Column(db.String(255))
    supervisor_approval = db.Column(db.Boolean, default=False)
    supervisor_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    # العلاقات
    inspector = db.relationship('User', foreign_keys=[inspector_id], backref=db.backref('safety_inspections', lazy=True))
    supervisor = db.relationship('User', foreign_keys=[supervisor_id], backref=db.backref('supervised_inspections', lazy=True))

    def __repr__(self):
        return f'<SafetyInspection {self.inspection_code}>'

class HazardReport(db.Model):
    __tablename__ = 'hazard_report'

    id = db.Column(db.Integer, primary_key=True)
    report_number = db.Column(db.String(50), unique=True, nullable=False)
    hazard_type = db.Column(db.String(50), nullable=False)  # electrical, structural, environmental, traffic
    severity = db.Column(db.String(20), default='medium')  # low, medium, high, critical
    coordinates = db.Column(db.Text)
    description = db.Column(db.Text, nullable=False)
    reported_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    reported_by_public = db.Column(db.String(100))  # for public reports
    contact_info = db.Column(db.String(200))
    report_date = db.Column(db.DateTime, default=datetime.datetime.now)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    status = db.Column(db.String(30), default='reported')  # reported, investigating, resolved, closed
    resolution_date = db.Column(db.DateTime)
    resolution_notes = db.Column(db.Text)
    photos = db.Column(db.Text)  # JSON array of photo paths

    # العلاقات
    reported_by = db.relationship('User', foreign_keys=[reported_by_id], backref=db.backref('hazard_reports', lazy=True))
    assigned_to = db.relationship('User', foreign_keys=[assigned_to_id], backref=db.backref('assigned_hazards', lazy=True))

    def __repr__(self):
        return f'<HazardReport {self.report_number}>'

# 5. نموذج البنية التحتية
class InfrastructureNetwork(db.Model):
    __tablename__ = 'infrastructure_network'

    id = db.Column(db.Integer, primary_key=True)
    network_name = db.Column(db.String(100), nullable=False)
    network_type = db.Column(db.String(50), nullable=False)  # water, electricity, sewage, telecom, gas
    coordinates = db.Column(db.Text)  # line or polygon coordinates
    network_status = db.Column(db.String(30), default='operational')  # operational, maintenance, out_of_service
    capacity = db.Column(db.Float)
    current_load = db.Column(db.Float)
    installation_date = db.Column(db.DateTime)
    last_maintenance_date = db.Column(db.DateTime)
    next_maintenance_date = db.Column(db.DateTime)
    operator_company = db.Column(db.String(100))
    contact_info = db.Column(db.String(200))
    specifications = db.Column(db.Text)  # JSON technical specifications
    connected_assets = db.Column(db.Text)  # JSON array of connected asset IDs
    service_area = db.Column(db.Text)  # polygon coordinates of service area
    emergency_contact = db.Column(db.String(200))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    def __repr__(self):
        return f'<InfrastructureNetwork {self.network_name}>'

class InfrastructureMalfunction(db.Model):
    __tablename__ = 'infrastructure_malfunction'

    id = db.Column(db.Integer, primary_key=True)
    malfunction_code = db.Column(db.String(50), unique=True, nullable=False)
    network_id = db.Column(db.Integer, db.ForeignKey('infrastructure_network.id'), nullable=False)
    malfunction_type = db.Column(db.String(50), nullable=False)  # outage, leak, damage, overload
    severity = db.Column(db.String(20), default='medium')  # low, medium, high, critical
    coordinates = db.Column(db.Text)  # specific location of malfunction
    description = db.Column(db.Text, nullable=False)
    reported_date = db.Column(db.DateTime, default=datetime.datetime.now)
    reported_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    estimated_repair_time = db.Column(db.Integer)  # in hours
    affected_radius = db.Column(db.Float)  # in meters
    affected_assets = db.Column(db.Text)  # JSON array of affected asset IDs
    status = db.Column(db.String(30), default='reported')  # reported, investigating, repairing, resolved
    assigned_contractor_id = db.Column(db.Integer, db.ForeignKey('contractor.id'))
    resolution_date = db.Column(db.DateTime)
    resolution_notes = db.Column(db.Text)
    cost_estimate = db.Column(db.Float)
    actual_cost = db.Column(db.Float)

    # العلاقات
    network = db.relationship('InfrastructureNetwork', backref=db.backref('malfunctions', lazy=True))
    reported_by = db.relationship('User', backref=db.backref('infrastructure_reports', lazy=True))
    assigned_contractor = db.relationship('Contractor', backref=db.backref('infrastructure_assignments', lazy=True))

    def __repr__(self):
        return f'<InfrastructureMalfunction {self.malfunction_code}>'

# 6. نموذج المسح وإدارة الأراضي
class LandParcel(db.Model):
    __tablename__ = 'land_parcel'

    id = db.Column(db.Integer, primary_key=True)
    parcel_number = db.Column(db.String(50), unique=True, nullable=False)
    deed_number = db.Column(db.String(50))  # رقم الصك
    coordinates = db.Column(db.Text, nullable=False)  # polygon coordinates
    area_sqm = db.Column(db.Float)  # area in square meters
    ownership_type = db.Column(db.String(30), nullable=False)  # public, private, government, waqf
    owner_name = db.Column(db.String(100))
    owner_id_number = db.Column(db.String(50))
    owner_contact = db.Column(db.String(200))
    land_use_type = db.Column(db.String(50))  # residential, commercial, industrial, agricultural, vacant
    zoning_classification = db.Column(db.String(50))
    usage_rights = db.Column(db.Text)  # JSON array of usage rights
    restrictions = db.Column(db.Text)  # JSON array of restrictions
    survey_date = db.Column(db.DateTime)
    surveyor_name = db.Column(db.String(100))
    survey_accuracy = db.Column(db.String(20))  # high, medium, low
    title_status = db.Column(db.String(30))  # clear, disputed, pending, encumbered
    market_value = db.Column(db.Float)
    assessed_value = db.Column(db.Float)
    tax_assessment_date = db.Column(db.DateTime)
    easements = db.Column(db.Text)  # JSON array of easements
    encroachments = db.Column(db.Text)  # JSON array of encroachments
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    def __repr__(self):
        return f'<LandParcel {self.parcel_number}>'

class SurveyPoint(db.Model):
    __tablename__ = 'survey_point'

    id = db.Column(db.Integer, primary_key=True)
    point_number = db.Column(db.String(50), nullable=False)
    parcel_id = db.Column(db.Integer, db.ForeignKey('land_parcel.id'), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    elevation = db.Column(db.Float)
    point_type = db.Column(db.String(30))  # corner, boundary, reference, control
    survey_method = db.Column(db.String(50))  # GPS, total_station, photogrammetry
    accuracy_horizontal = db.Column(db.Float)  # in meters
    accuracy_vertical = db.Column(db.Float)  # in meters
    survey_date = db.Column(db.DateTime, default=datetime.datetime.now)
    surveyor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    notes = db.Column(db.Text)

    # العلاقات
    parcel = db.relationship('LandParcel', backref=db.backref('survey_points', lazy=True))
    surveyor = db.relationship('User', backref=db.backref('survey_points', lazy=True))

    def __repr__(self):
        return f'<SurveyPoint {self.point_number}>'

# 7. نموذج البيئة والنفايات
class WasteCollectionPoint(db.Model):
    __tablename__ = 'waste_collection_point'

    id = db.Column(db.Integer, primary_key=True)
    point_name = db.Column(db.String(100), nullable=False)
    point_type = db.Column(db.String(50), nullable=False)  # container, dumpster, recycling, hazardous
    coordinates = db.Column(db.Text)
    capacity = db.Column(db.Float)  # in cubic meters or tons
    current_level = db.Column(db.Float, default=0.0)  # percentage full
    waste_types = db.Column(db.Text)  # JSON array of accepted waste types
    collection_schedule = db.Column(db.Text)  # JSON schedule
    last_collection_date = db.Column(db.DateTime)
    next_collection_date = db.Column(db.DateTime)
    contractor_id = db.Column(db.Integer, db.ForeignKey('contractor.id'))
    status = db.Column(db.String(30), default='operational')  # operational, full, damaged, maintenance
    accessibility = db.Column(db.String(30))  # easy, moderate, difficult
    environmental_impact = db.Column(db.String(30))  # low, medium, high
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    # العلاقة
    contractor = db.relationship('Contractor', backref=db.backref('waste_collection_points', lazy=True))

    def __repr__(self):
        return f'<WasteCollectionPoint {self.point_name}>'

class EnvironmentalReport(db.Model):
    __tablename__ = 'environmental_report'

    id = db.Column(db.Integer, primary_key=True)
    report_number = db.Column(db.String(50), unique=True, nullable=False)
    report_type = db.Column(db.String(50), nullable=False)  # waste_overflow, pollution, illegal_dumping, odor
    coordinates = db.Column(db.Text)
    description = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(20), default='medium')  # low, medium, high, critical
    reported_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    reported_by_public = db.Column(db.String(100))  # for public reports
    contact_info = db.Column(db.String(200))
    report_date = db.Column(db.DateTime, default=datetime.datetime.now)
    assigned_contractor_id = db.Column(db.Integer, db.ForeignKey('contractor.id'))
    status = db.Column(db.String(30), default='reported')  # reported, investigating, cleaning, resolved
    estimated_cleanup_time = db.Column(db.Integer)  # in hours
    actual_cleanup_time = db.Column(db.Integer)  # in hours
    cleanup_cost = db.Column(db.Float)
    resolution_date = db.Column(db.DateTime)
    resolution_notes = db.Column(db.Text)
    photos_before = db.Column(db.Text)  # JSON array of photo paths
    photos_after = db.Column(db.Text)  # JSON array of photo paths
    environmental_impact = db.Column(db.Text)  # JSON assessment

    # العلاقات
    reported_by = db.relationship('User', backref=db.backref('environmental_reports', lazy=True))
    assigned_contractor = db.relationship('Contractor', backref=db.backref('environmental_assignments', lazy=True))

    def __repr__(self):
        return f'<EnvironmentalReport {self.report_number}>'

# 8. نموذج التكامل الحكومي الذكي
class GovernmentIntegration(db.Model):
    __tablename__ = 'government_integration'

    id = db.Column(db.Integer, primary_key=True)
    system_name = db.Column(db.String(100), nullable=False)  # Balady, Civil Defense, etc.
    api_endpoint = db.Column(db.String(255))
    api_key = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    last_sync_date = db.Column(db.DateTime)
    sync_frequency = db.Column(db.String(20))  # hourly, daily, weekly
    data_types = db.Column(db.Text)  # JSON array of data types to sync
    mapping_config = db.Column(db.Text)  # JSON field mapping configuration
    error_log = db.Column(db.Text)  # JSON array of recent errors
    success_rate = db.Column(db.Float, default=0.0)  # percentage
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    def __repr__(self):
        return f'<GovernmentIntegration {self.system_name}>'

class ExternalReport(db.Model):
    __tablename__ = 'external_report'

    id = db.Column(db.Integer, primary_key=True)
    external_id = db.Column(db.String(100))  # ID from external system
    source_system = db.Column(db.String(50), nullable=False)  # balady, civil_defense, etc.
    report_type = db.Column(db.String(50), nullable=False)
    coordinates = db.Column(db.Text)
    description = db.Column(db.Text)
    status = db.Column(db.String(30), default='received')  # received, processing, forwarded, resolved
    received_date = db.Column(db.DateTime, default=datetime.datetime.now)
    forwarded_to_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    forwarded_to_contractor_id = db.Column(db.Integer, db.ForeignKey('contractor.id'))
    internal_reference = db.Column(db.String(100))  # reference to internal issue/request
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, urgent
    response_required = db.Column(db.Boolean, default=False)
    response_deadline = db.Column(db.DateTime)
    response_sent = db.Column(db.Boolean, default=False)
    response_date = db.Column(db.DateTime)
    raw_data = db.Column(db.Text)  # JSON of original data from external system

    # العلاقات
    forwarded_to = db.relationship('User', backref=db.backref('external_reports', lazy=True))
    forwarded_to_contractor = db.relationship('Contractor', backref=db.backref('external_reports', lazy=True))

    def __repr__(self):
        return f'<ExternalReport {self.external_id}>'

# 9. نماذج تجربة الحجاج والسياح 360°
class PilgrimageLocation(db.Model):
    __tablename__ = 'pilgrimage_location'

    id = db.Column(db.Integer, primary_key=True)
    location_name = db.Column(db.String(100), nullable=False)
    location_name_en = db.Column(db.String(100))
    location_type = db.Column(db.String(50), nullable=False)  # holy_site, service, shopping, transport, emergency
    coordinates = db.Column(db.Text)
    center_lat = db.Column(db.Float)
    center_lng = db.Column(db.Float)
    description = db.Column(db.Text)
    description_en = db.Column(db.Text)
    panorama_images = db.Column(db.Text)  # JSON array of 360° image URLs
    virtual_tour_url = db.Column(db.String(255))
    # دعم النماذج ثلاثية الأبعاد
    model_3d_fbx = db.Column(db.String(500))  # FBX model URL
    model_3d_usdz = db.Column(db.String(500))  # USDZ model URL (iOS AR)
    model_3d_gltf = db.Column(db.String(500))  # glTF model URL
    model_3d_glb = db.Column(db.String(500))  # GLB model URL
    model_3d_preview = db.Column(db.String(500))  # Preview image for 3D model
    # إعدادات النموذج ثلاثي الأبعاد
    model_3d_settings = db.Column(db.Text)  # JSON settings for 3D viewer
    # دعم الفيديوهات 360°
    video_360_urls = db.Column(db.Text)  # JSON array of 360° video URLs
    video_360_thumbnails = db.Column(db.Text)  # JSON array of video thumbnails
    capacity = db.Column(db.Integer)
    current_occupancy = db.Column(db.Integer, default=0)
    accessibility_features = db.Column(db.Text)  # JSON
    operating_hours = db.Column(db.String(100))
    contact_info = db.Column(db.Text)  # JSON
    amenities = db.Column(db.Text)  # JSON array of available amenities
    crowd_level = db.Column(db.String(20), default='normal')  # low, normal, high, very_high
    safety_rating = db.Column(db.Integer, default=5)  # 1-5 scale
    cleanliness_rating = db.Column(db.Integer, default=5)  # 1-5 scale
    is_featured = db.Column(db.Boolean, default=False)
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    def __repr__(self):
        return f'<PilgrimageLocation {self.location_name}>'

class PilgrimageReport(db.Model):
    __tablename__ = 'pilgrimage_report'

    id = db.Column(db.Integer, primary_key=True)
    report_number = db.Column(db.String(50), unique=True, nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('pilgrimage_location.id'))
    report_type = db.Column(db.String(50), nullable=False)  # crowding, cleanliness, accessibility, emergency, lost_person
    coordinates = db.Column(db.Text)
    description = db.Column(db.Text, nullable=False)
    description_en = db.Column(db.Text)
    urgency = db.Column(db.String(20), default='medium')  # low, medium, high, emergency
    reported_by_name = db.Column(db.String(100))
    reported_by_nationality = db.Column(db.String(50))
    contact_info = db.Column(db.String(200))
    preferred_language = db.Column(db.String(10), default='ar')  # ar, en, ur, etc.
    report_date = db.Column(db.DateTime, default=datetime.datetime.now)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    status = db.Column(db.String(30), default='reported')  # reported, investigating, resolved, closed
    resolution_date = db.Column(db.DateTime)
    resolution_notes = db.Column(db.Text)
    resolution_notes_en = db.Column(db.Text)
    satisfaction_rating = db.Column(db.Integer)  # 1-5 scale
    photos = db.Column(db.Text)  # JSON array of photo paths
    ai_response = db.Column(db.Text)  # AI-generated response
    human_followup_required = db.Column(db.Boolean, default=False)

    # العلاقات
    location = db.relationship('PilgrimageLocation', backref=db.backref('reports', lazy=True))
    assigned_to = db.relationship('User', backref=db.backref('pilgrimage_reports', lazy=True))

    def __repr__(self):
        return f'<PilgrimageReport {self.report_number}>'

class VirtualTourInteraction(db.Model):
    __tablename__ = 'virtual_tour_interaction'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('pilgrimage_location.id'))
    user_ip = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
    country = db.Column(db.String(50))
    language = db.Column(db.String(10))
    interaction_type = db.Column(db.String(50))  # view, zoom, rotate, click_info, report_issue
    interaction_data = db.Column(db.Text)  # JSON data about the interaction
    duration_seconds = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.now)

    # العلاقة
    location = db.relationship('PilgrimageLocation', backref=db.backref('interactions', lazy=True))

    def __repr__(self):
        return f'<VirtualTourInteraction {self.session_id}>'

# نماذج الخدمات التفاعلية للحجاج
class ServiceCategory(db.Model):
    """فئات الخدمات (مطاعم، مساجد، خدمات عامة، إلخ)"""
    __tablename__ = 'service_category'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    name_en = db.Column(db.String(100))
    icon = db.Column(db.String(50))  # Font Awesome icon class
    color = db.Column(db.String(7), default='#007bff')  # Hex color
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)

    def __repr__(self):
        return f'<ServiceCategory {self.name}>'

class InteractiveLocation(db.Model):
    """المواقع التفاعلية على الخريطة (مطاعم، مساجد، خدمات)"""
    __tablename__ = 'interactive_location'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    name_en = db.Column(db.String(200))
    description = db.Column(db.Text)
    description_en = db.Column(db.Text)

    # الموقع الجغرافي
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(500))
    address_en = db.Column(db.String(500))

    # معلومات الخدمة
    category_id = db.Column(db.Integer, db.ForeignKey('service_category.id'), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    website = db.Column(db.String(200))
    operating_hours = db.Column(db.String(200))

    # التقييم والمعلومات
    rating = db.Column(db.Float, default=0.0)
    price_range = db.Column(db.String(10))  # $, $$, $$$, $$$$
    capacity = db.Column(db.Integer)
    amenities = db.Column(db.Text)  # JSON array

    # الصور والوسائط
    main_image = db.Column(db.String(500))
    gallery_images = db.Column(db.Text)  # JSON array of image paths
    panorama_360_images = db.Column(db.Text)  # JSON array of 360° image paths
    virtual_tour_url = db.Column(db.String(500))

    # إعدادات العرض
    is_featured = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    display_order = db.Column(db.Integer, default=0)

    # معلومات إدارية
    added_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    verified = db.Column(db.Boolean, default=False)
    verification_date = db.Column(db.DateTime)
    last_updated = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)

    # العلاقات
    category = db.relationship('ServiceCategory', backref=db.backref('locations', lazy=True))
    added_by_user = db.relationship('User', backref=db.backref('added_locations', lazy=True))

    def __repr__(self):
        return f'<InteractiveLocation {self.name}>'

    def to_dict(self):
        """تحويل البيانات إلى قاموس للاستخدام في JSON"""
        return {
            'id': self.id,
            'name': self.name,
            'name_en': self.name_en,
            'description': self.description,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'address': self.address,
            'category': self.category.name if self.category else None,
            'category_icon': self.category.icon if self.category else None,
            'category_color': self.category.color if self.category else '#007bff',
            'phone': self.phone,
            'rating': self.rating,
            'price_range': self.price_range,
            'operating_hours': self.operating_hours,
            'main_image': self.main_image,
            'panorama_360_images': self.panorama_360_images,
            'is_featured': self.is_featured
        }

class LocationConnection(db.Model):
    """الروابط بين المواقع للتنقل في الجولة الافتراضية"""
    __tablename__ = 'location_connection'

    id = db.Column(db.Integer, primary_key=True)
    from_location_id = db.Column(db.Integer, db.ForeignKey('interactive_location.id'), nullable=False)
    to_location_id = db.Column(db.Integer, db.ForeignKey('interactive_location.id'), nullable=False)

    # معلومات الاتصال
    connection_type = db.Column(db.String(50), default='walking')  # walking, driving, public_transport
    distance_meters = db.Column(db.Float)
    estimated_time_minutes = db.Column(db.Integer)

    # إعدادات العرض في الجولة الافتراضية
    hotspot_position_x = db.Column(db.Float)  # موقع النقطة الساخنة في الصورة 360°
    hotspot_position_y = db.Column(db.Float)
    hotspot_position_z = db.Column(db.Float)
    hotspot_label = db.Column(db.String(100))

    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)

    # العلاقات
    from_location = db.relationship('InteractiveLocation', foreign_keys=[from_location_id],
                                   backref=db.backref('outgoing_connections', lazy=True))
    to_location = db.relationship('InteractiveLocation', foreign_keys=[to_location_id],
                                 backref=db.backref('incoming_connections', lazy=True))

    def __repr__(self):
        return f'<LocationConnection {self.from_location_id} -> {self.to_location_id}>'

# نماذج الرحلات والذكاء الاصطناعي
class TripPackage(db.Model):
    """نموذج حزم الرحلات"""
    __tablename__ = 'trip_packages'

    id = db.Column(db.Integer, primary_key=True)
    package_name = db.Column(db.String(200), nullable=False)
    package_name_en = db.Column(db.String(200))
    package_type = db.Column(db.String(50), nullable=False)  # hajj, umrah, tourism, custom
    duration_days = db.Column(db.Integer, nullable=False)
    price_per_person = db.Column(db.Float, nullable=False)
    max_participants = db.Column(db.Integer, default=50)
    current_bookings = db.Column(db.Integer, default=0)

    # تفاصيل الحزمة
    description = db.Column(db.Text)
    description_en = db.Column(db.Text)
    included_services = db.Column(db.Text)  # JSON
    excluded_services = db.Column(db.Text)  # JSON
    itinerary = db.Column(db.Text)  # JSON - برنامج الرحلة

    # معلومات الإقامة
    accommodation_type = db.Column(db.String(100))  # hotel, apartment, tent
    accommodation_rating = db.Column(db.Integer)  # 1-5 stars
    meals_included = db.Column(db.String(100))  # breakfast, half_board, full_board

    # معلومات النقل
    transport_type = db.Column(db.String(100))  # bus, flight, train
    departure_city = db.Column(db.String(100))

    # التوقيتات
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    booking_deadline = db.Column(db.DateTime)

    # الحالة والتقييم
    is_active = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)
    rating = db.Column(db.Float, default=0.0)
    reviews_count = db.Column(db.Integer, default=0)

    # الصور والوسائط
    main_image = db.Column(db.String(500))
    gallery_images = db.Column(db.Text)  # JSON
    video_url = db.Column(db.String(500))
    virtual_tour_url = db.Column(db.String(500))

    # معلومات إضافية
    difficulty_level = db.Column(db.String(50))  # easy, moderate, challenging
    age_restrictions = db.Column(db.String(200))
    health_requirements = db.Column(db.Text)
    required_documents = db.Column(db.Text)  # JSON

    # التواريخ
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    def __repr__(self):
        return f'<TripPackage {self.package_name}>'

class TripBooking(db.Model):
    """نموذج حجوزات الرحلات"""
    __tablename__ = 'trip_bookings'

    id = db.Column(db.Integer, primary_key=True)
    booking_number = db.Column(db.String(50), unique=True, nullable=False)
    package_id = db.Column(db.Integer, db.ForeignKey('trip_packages.id'), nullable=False)

    # معلومات العميل
    customer_name = db.Column(db.String(200), nullable=False)
    customer_email = db.Column(db.String(200), nullable=False)
    customer_phone = db.Column(db.String(50), nullable=False)
    customer_nationality = db.Column(db.String(100))
    customer_passport = db.Column(db.String(50))

    # تفاصيل الحجز
    number_of_travelers = db.Column(db.Integer, nullable=False)
    travelers_details = db.Column(db.Text)  # JSON - تفاصيل المسافرين
    total_amount = db.Column(db.Float, nullable=False)
    paid_amount = db.Column(db.Float, default=0.0)
    payment_status = db.Column(db.String(50), default='pending')  # pending, partial, paid, refunded

    # الحالة
    booking_status = db.Column(db.String(50), default='confirmed')  # confirmed, cancelled, completed
    special_requests = db.Column(db.Text)
    notes = db.Column(db.Text)

    # التواريخ
    booking_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    travel_date = db.Column(db.DateTime)
    cancellation_date = db.Column(db.DateTime)

    # معلومات الدفع
    payment_method = db.Column(db.String(100))
    transaction_id = db.Column(db.String(200))
    invoice_number = db.Column(db.String(100))

    # العلاقات
    package = db.relationship('TripPackage', backref='bookings')

    def __repr__(self):
        return f'<TripBooking {self.booking_number}>'

class AIModel(db.Model):
    """نموذج نماذج الذكاء الاصطناعي"""
    __tablename__ = 'ai_models'

    id = db.Column(db.Integer, primary_key=True)
    model_name = db.Column(db.String(200), nullable=False)
    model_type = db.Column(db.String(100), nullable=False)  # chatbot, trip_planner, translator, etc.

    # إعدادات النموذج
    api_provider = db.Column(db.String(100), nullable=False)  # openai, anthropic, google, etc.
    api_key = db.Column(db.String(500), nullable=False)
    model_version = db.Column(db.String(100))

    # الإعدادات
    temperature = db.Column(db.Float, default=0.7)
    max_tokens = db.Column(db.Integer, default=1000)
    system_prompt = db.Column(db.Text)

    # الحالة
    is_active = db.Column(db.Boolean, default=True)
    is_default = db.Column(db.Boolean, default=False)

    # الإحصائيات
    usage_count = db.Column(db.Integer, default=0)
    success_rate = db.Column(db.Float, default=0.0)
    average_response_time = db.Column(db.Float, default=0.0)

    # التواريخ
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    last_used = db.Column(db.DateTime)

    def __repr__(self):
        return f'<AIModel {self.model_name}>'

class TripReview(db.Model):
    """نموذج تقييمات الرحلات"""
    __tablename__ = 'trip_reviews'

    id = db.Column(db.Integer, primary_key=True)
    package_id = db.Column(db.Integer, db.ForeignKey('trip_packages.id'), nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey('trip_bookings.id'))

    # معلومات المراجع
    reviewer_name = db.Column(db.String(200), nullable=False)
    reviewer_email = db.Column(db.String(200))
    reviewer_nationality = db.Column(db.String(100))

    # التقييم
    overall_rating = db.Column(db.Integer, nullable=False)  # 1-5
    accommodation_rating = db.Column(db.Integer)
    transport_rating = db.Column(db.Integer)
    guide_rating = db.Column(db.Integer)
    value_rating = db.Column(db.Integer)

    # المراجعة
    review_title = db.Column(db.String(200))
    review_text = db.Column(db.Text, nullable=False)
    review_text_en = db.Column(db.Text)

    # الوسائط
    review_images = db.Column(db.Text)  # JSON

    # الحالة
    is_verified = db.Column(db.Boolean, default=False)
    is_featured = db.Column(db.Boolean, default=False)
    is_published = db.Column(db.Boolean, default=True)

    # التواريخ
    review_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    trip_date = db.Column(db.DateTime)

    def __repr__(self):
        return f'<TripReview {self.reviewer_name}>'

class CustomTrip(db.Model):
    """نموذج الرحلات المخصصة"""
    __tablename__ = 'custom_trips'

    id = db.Column(db.Integer, primary_key=True)
    trip_number = db.Column(db.String(50), unique=True, nullable=False)

    # معلومات العميل
    customer_name = db.Column(db.String(200), nullable=False)
    customer_email = db.Column(db.String(200), nullable=False)
    customer_phone = db.Column(db.String(50), nullable=False)

    # تفاصيل الرحلة المطلوبة
    trip_type = db.Column(db.String(50), nullable=False)  # hajj, umrah, tourism
    preferred_dates = db.Column(db.Text)  # JSON
    duration_days = db.Column(db.Integer)
    number_of_travelers = db.Column(db.Integer, nullable=False)
    budget_range = db.Column(db.String(100))

    # التفضيلات
    preferred_locations = db.Column(db.Text)  # JSON
    accommodation_preferences = db.Column(db.Text)  # JSON
    transport_preferences = db.Column(db.Text)  # JSON
    special_requirements = db.Column(db.Text)

    # الاستجابة
    ai_suggestions = db.Column(db.Text)  # JSON - اقتراحات الذكاء الاصطناعي
    estimated_cost = db.Column(db.Float)
    proposed_itinerary = db.Column(db.Text)  # JSON

    # الحالة
    status = db.Column(db.String(50), default='pending')  # pending, quoted, approved, rejected
    notes = db.Column(db.Text)

    # التواريخ
    request_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    response_date = db.Column(db.DateTime)

    def __repr__(self):
        return f'<CustomTrip {self.trip_number}>'

class TripItinerary(db.Model):
    """نموذج برنامج الرحلة اليومي"""
    __tablename__ = 'trip_itineraries'

    id = db.Column(db.Integer, primary_key=True)
    package_id = db.Column(db.Integer, db.ForeignKey('trip_packages.id'), nullable=False)
    day_number = db.Column(db.Integer, nullable=False)

    # تفاصيل اليوم
    day_title = db.Column(db.String(200), nullable=False)
    day_title_en = db.Column(db.String(200))
    day_description = db.Column(db.Text)
    day_description_en = db.Column(db.Text)

    # الأنشطة
    activities = db.Column(db.Text)  # JSON
    meals = db.Column(db.Text)  # JSON
    accommodation = db.Column(db.String(200))

    # التوقيتات
    start_time = db.Column(db.Time)
    end_time = db.Column(db.Time)

    # المواقع
    locations = db.Column(db.Text)  # JSON
    transport_details = db.Column(db.Text)

    # معلومات إضافية
    tips = db.Column(db.Text)
    what_to_bring = db.Column(db.Text)
    weather_info = db.Column(db.Text)

# ==================== نماذج البانوراما 360° ====================

class Asset(db.Model):
    """نموذج الأصول المستوردة من Excel"""
    __tablename__ = 'assets'
    
    __table_args__ = (
        db.Index('idx_asset_number', 'asset_number'),
        db.Index('idx_asset_area', 'area'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    asset_number = db.Column(db.String(100), unique=True, nullable=False)  # رقم الأصل
    description = db.Column(db.Text)  # الوصف
    area = db.Column(db.String(100))  # المنطقة (منى، عرفات، مزدلفة)
    country = db.Column(db.String(100))  # الدولة
    company_name = db.Column(db.String(200))  # المطوف/الشركة
    x_coordinate = db.Column(db.Float)  # خط الطول
    y_coordinate = db.Column(db.Float)  # خط العرض
    asset_type = db.Column(db.String(100))  # نوع الأصل (لوحة، مطعم، مطبخ، حلاق، بقالة، إلخ)
    status = db.Column(db.String(50), default='active')  # active, inactive, maintenance
    
    # ربط تلقائي مع المخيمات (بناءً على الموقع الجغرافي)
    camp_id = db.Column(db.Integer, db.ForeignKey('camp.id'))
    camp = db.relationship('Camp', backref=db.backref('assets', lazy=True))
    square_number = db.Column(db.String(50))  # رقم المربع (يُملأ تلقائياً من المخيم)
    
    # ربط مع اللوحات الموجودة
    panel_id = db.Column(db.Integer, db.ForeignKey('mdb_panel.id'))
    panel = db.relationship('MDBPanel', backref=db.backref('linked_asset', uselist=False))
    
    # معلومات الاستيراد
    imported_at = db.Column(db.DateTime, default=datetime.datetime.now)
    imported_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    importer = db.relationship('User', backref=db.backref('imported_assets', lazy=True))
    
    # معلومات إضافية
    notes = db.Column(db.Text)
    extra_data = db.Column(db.Text)  # JSON - أي بيانات إضافية
    
    def __repr__(self):
        return f'<Asset {self.asset_number}>'

class Panorama360(db.Model):
    """نموذج البانوراما 360 درجة"""
    __tablename__ = 'panorama_360'
    
    __table_args__ = (
        db.Index('idx_panorama_area', 'area'),
        db.Index('idx_panorama_active', 'is_active'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)  # عنوان البانوراما
    description = db.Column(db.Text)  # الوصف
    location_name = db.Column(db.String(200))  # اسم الموقع (منى - المخيم 5)
    area = db.Column(db.String(100))  # المنطقة
    image_path = db.Column(db.String(500), nullable=False)  # مسار الصورة
    
    # الإحداثيات (موقع التقاط الصورة)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    
    # الإعدادات
    auto_rotate = db.Column(db.Boolean, default=True)  # دوران تلقائي
    initial_yaw = db.Column(db.Float, default=0)  # الاتجاه الابتدائي
    initial_pitch = db.Column(db.Float, default=0)  # الميل الابتدائي
    
    # الحالة
    is_active = db.Column(db.Boolean, default=True)
    view_count = db.Column(db.Integer, default=0)  # عدد المشاهدات
    
    # معلومات الإنشاء
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    creator = db.relationship('User', backref=db.backref('panoramas', lazy=True))
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    
    # العلاقات
    hotspots = db.relationship('PanoramaAssetHotspot', backref='panorama', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Panorama360 {self.title}>'

class PanoramaAssetHotspot(db.Model):
    """نموذج ربط الأصول بالبانوراما (النقاط التفاعلية)"""
    __tablename__ = 'panorama_asset_hotspots'
    
    id = db.Column(db.Integer, primary_key=True)
    panorama_id = db.Column(db.Integer, db.ForeignKey('panorama_360.id'), nullable=False)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False)
    
    # موقع النقطة على البانوراما
    pitch = db.Column(db.Float, nullable=False)  # الموقع العمودي (-90 to 90)
    yaw = db.Column(db.Float, nullable=False)  # الموقع الأفقي (-180 to 180)
    
    # نوع وشكل النقطة
    hotspot_type = db.Column(db.String(50), default='asset')  # asset, info, location
    icon_style = db.Column(db.String(50), default='default')  # default, warning, danger, success
    icon_size = db.Column(db.String(20), default='medium')  # small, medium, large
    # تخصيصات إضافية
    icon_key = db.Column(db.String(50))  # اسم الأيقونة/الشعار المخصص
    color_hex = db.Column(db.String(10))  # لون الأيقونة مثل #E11D48
    size_px = db.Column(db.Integer)  # حجم بكسل اختياري، يتجاوز icon_size إن وُجد
    label = db.Column(db.String(100))  # تسمية تظهر كـ Tooltip
    
    # الحالة
    is_active = db.Column(db.Boolean, default=True)
    click_count = db.Column(db.Integer, default=0)  # عدد النقرات
    
    # معلومات الإنشاء
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)
    
    # العلاقات
    asset = db.relationship('Asset', backref=db.backref('hotspots', lazy=True))
    
    def __repr__(self):
        return f'<PanoramaAssetHotspot {self.asset.asset_number} on {self.panorama.title}>'

    # الترتيب
    display_order = db.Column(db.Integer, default=0)
    is_optional = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<TripItinerary Day {self.day_number}>'

