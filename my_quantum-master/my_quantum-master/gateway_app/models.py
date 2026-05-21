from datetime import datetime
from gateway_app import db


class Key(db.Model):
    """量子密钥表"""
    __tablename__ = 'keys'
    
    id = db.Column(db.Integer, primary_key=True)
    key_value = db.Column(db.String(512), nullable=False)  # 密钥值
    key_hash = db.Column(db.String(64), unique=True, nullable=True, index=True)  # 密钥内容SHA256哈希，用于去重
    status = db.Column(db.String(16), default='unused', nullable=False)  # unused|used
    source = db.Column(db.String(64), nullable=True)  # 来源：qkd_app/manual/auto-import
    file_path = db.Column(db.String(512), nullable=True)  # 原始文件路径
    length = db.Column(db.Integer, nullable=True)  # 密钥长度
    request_ip = db.Column(db.String(64), nullable=True)  # 请求设备的IP地址（手动使用为空）
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    used_at = db.Column(db.DateTime, nullable=True)

    def mark_used(self, request_ip: str = None):
        """标记密钥为已使用"""
        self.status = 'used'
        self.used_at = datetime.utcnow()
        if request_ip:
            self.request_ip = request_ip

    def to_dict(self):
        return {
            'id': self.id,
            'key_value': self.key_value,
            'key_hash': self.key_hash,
            'status': self.status,
            'source': self.source,
            'file_path': self.file_path,
            'length': self.length,
            'request_ip': self.request_ip,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'used_at': self.used_at.isoformat() if self.used_at else None,
        }


class PhysicalKey(db.Model):
    """Physical-layer key used to wrap quantum keys for one session."""
    __tablename__ = 'physical_keys'

    id = db.Column(db.String(128), primary_key=True)
    key_value = db.Column(db.String(32), nullable=False)
    key_hash = db.Column(db.String(64), unique=True, nullable=True, index=True)
    status = db.Column(db.String(16), default='unused', nullable=False)  # unused|reserved|used
    source = db.Column(db.String(64), nullable=True)
    file_path = db.Column(db.String(512), nullable=True)
    session_id = db.Column(db.String(128), nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    used_at = db.Column(db.DateTime, nullable=True)

    def mark_reserved(self, session_id: str):
        self.status = 'reserved'
        self.session_id = session_id

    def mark_used(self):
        self.status = 'used'
        self.used_at = datetime.utcnow()

    def to_dict(self):
        return {
            'id': self.id,
            'key_value': self.key_value,
            'key_hash': self.key_hash,
            'status': self.status,
            'source': self.source,
            'file_path': self.file_path,
            'session_id': self.session_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'used_at': self.used_at.isoformat() if self.used_at else None,
        }


class KeySession(db.Model):
    """Binds one A/B communication session to one quantum key and one physical key."""
    __tablename__ = 'key_sessions'

    session_id = db.Column(db.String(128), primary_key=True)
    party_a = db.Column(db.String(64), nullable=False)
    party_b = db.Column(db.String(64), nullable=False)
    quantum_key_id = db.Column(db.Integer, db.ForeignKey('keys.id'), nullable=False)
    physical_key_id = db.Column(db.String(128), db.ForeignKey('physical_keys.id'), nullable=False)
    status = db.Column(db.String(16), default='pending', nullable=False)  # pending|used
    claimed_a_at = db.Column(db.DateTime, nullable=True)
    claimed_b_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    used_at = db.Column(db.DateTime, nullable=True)

    quantum_key = db.relationship('Key')
    physical_key = db.relationship('PhysicalKey')

    def claim(self, self_id: str):
        now = datetime.utcnow()
        if self_id == self.party_a:
            self.claimed_a_at = self.claimed_a_at or now
        elif self_id == self.party_b:
            self.claimed_b_at = self.claimed_b_at or now
        else:
            raise ValueError('device is not part of this key session')
        if self.claimed_a_at and self.claimed_b_at:
            self.status = 'used'
            self.used_at = self.used_at or now

    def to_dict(self):
        return {
            'session_id': self.session_id,
            'party_a': self.party_a,
            'party_b': self.party_b,
            'quantum_key_id': self.quantum_key_id,
            'physical_key_id': self.physical_key_id,
            'status': self.status,
            'claimed_a_at': self.claimed_a_at.isoformat() if self.claimed_a_at else None,
            'claimed_b_at': self.claimed_b_at.isoformat() if self.claimed_b_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'used_at': self.used_at.isoformat() if self.used_at else None,
        }


class RunLog(db.Model):
    """运行日志表"""
    __tablename__ = 'run_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    level = db.Column(db.String(16), default='INFO', nullable=False)  # INFO/WARNING/ERROR
    message = db.Column(db.Text, nullable=False)
    source = db.Column(db.String(64), nullable=True)  # 日志来源
    file_path = db.Column(db.String(512), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'level': self.level,
            'message': self.message,
            'source': self.source,
            'file_path': self.file_path,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class ImportedFile(db.Model):
    """已导入文件记录表"""
    __tablename__ = 'imported_files'
    
    id = db.Column(db.Integer, primary_key=True)
    file_path = db.Column(db.String(512), unique=True, nullable=False)
    content_hash = db.Column(db.String(64), nullable=True, index=True)  # 文件内容SHA256哈希，用于检测变更
    mtime = db.Column(db.Float, nullable=True)  # 文件修改时间
    size = db.Column(db.Integer, nullable=True)  # 文件大小
    source = db.Column(db.String(64), nullable=True)
    keys_count = db.Column(db.Integer, default=0, nullable=False)  # 导入的密钥数量
    imported_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'file_path': self.file_path,
            'content_hash': self.content_hash,
            'mtime': self.mtime,
            'size': self.size,
            'source': self.source,
            'keys_count': self.keys_count,
            'imported_at': self.imported_at.isoformat() if self.imported_at else None,
        }


class KeyUsageStats(db.Model):
    """密钥使用统计表（按日期）"""
    __tablename__ = 'key_usage_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, unique=True, nullable=False)  # 统计日期
    imported_count = db.Column(db.Integer, default=0)  # 当日导入数量
    imported_length = db.Column(db.Integer, default=0)  # 当日导入总长度
    used_count = db.Column(db.Integer, default=0)  # 当日使用数量
    used_length = db.Column(db.Integer, default=0)  # 当日使用总长度
    request_count = db.Column(db.Integer, default=0)  # 总请求次数
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat() if self.date else None,
            'imported_count': self.imported_count,
            'imported_length': self.imported_length,
            'used_count': self.used_count,
            'used_length': self.used_length,
            'request_count': self.request_count,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
