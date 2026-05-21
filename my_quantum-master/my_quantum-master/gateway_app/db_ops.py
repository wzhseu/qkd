from typing import Optional, List
from gateway_app import db
from sqlalchemy import func
from gateway_app.models import Key, PhysicalKey, KeySession, RunLog, ImportedFile, KeyUsageStats
from datetime import date, datetime
import os
import fnmatch
import hashlib
import re


HEX_64_RE = re.compile(r'^[0-9a-fA-F]{64}$')
HEX_32_RE = re.compile(r'^[0-9a-fA-F]{32}$')


def compute_hash(content: str) -> str:
    """计算内容的SHA256哈希值"""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def compute_file_hash(file_path: str) -> Optional[str]:
    """计算文件内容的SHA256哈希值"""
    try:
        with open(file_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception:
        return None


def key_exists_by_hash(key_hash: str) -> bool:
    """检查指定哈希的密钥是否已存在"""
    return Key.query.filter_by(key_hash=key_hash).first() is not None


def save_key(value: str, source: Optional[str] = None, file_path: Optional[str] = None,
             skip_duplicate: bool = True) -> Optional[Key]:
    """保存密钥到数据库
    
    Args:
        value: 密钥值
        source: 密钥来源
        file_path: 原始文件路径
        skip_duplicate: 是否跳过重复密钥（基于哈希去重）
        
    Returns:
        Key对象，如果是重复密钥且skip_duplicate=True则返回None
    """
    if not value:
        return None
    value = value.strip().lower()
    if not HEX_64_RE.match(value):
        save_log(f"Skipped invalid quantum key from {file_path or source}: expected 64 hex chars", level='WARNING', source='ingest')
        return None
    
    # 计算密钥哈希
    key_hash = compute_hash(value)
    
    # 检查是否已存在相同哈希的密钥
    if skip_duplicate and key_exists_by_hash(key_hash):
        return None
    
    key = Key(
        key_value=value,
        key_hash=key_hash,
        source=source,
        file_path=file_path,
        length=len(value),
    )
    db.session.add(key)
    db.session.commit()
    
    _update_daily_stats(imported_count=1, imported_length=len(value))
    
    return key


def consume_key(key_id: int, request_ip: Optional[str] = None) -> Optional[Key]:
    """标记密钥为已使用"""
    key = Key.query.get(key_id)
    if not key:
        return None
    if key.status != 'used':
        key.mark_used(request_ip=request_ip)
        db.session.commit()
        _update_daily_stats(used_count=1, used_length=key.length or 0, request_count=1)
    return key


def consume_latest_key(request_ip: Optional[str] = None) -> Optional[Key]:
    """获取并消费最新的未使用密钥"""
    k = Key.query.filter_by(status='unused').order_by(Key.created_at.desc()).first()
    if not k:
        return None
    k.mark_used(request_ip=request_ip)
    db.session.commit()
    _update_daily_stats(used_count=1, used_length=k.length or 0, request_count=1)
    return k


def save_physical_key(key_id: str, value: str, source: Optional[str] = None,
                      file_path: Optional[str] = None, skip_duplicate: bool = True) -> Optional[PhysicalKey]:
    """Save a physical-layer SM4 wrapping key."""
    if not key_id or not value:
        return None
    key_id = key_id.strip()
    value = value.strip().lower()
    if not HEX_32_RE.match(value):
        save_log(f"Skipped invalid physical key {key_id}: expected 32 hex chars", level='WARNING', source='physical-ingest')
        return None

    key_hash = compute_hash(value)
    if skip_duplicate and PhysicalKey.query.filter_by(key_hash=key_hash).first():
        return None
    if PhysicalKey.query.get(key_id):
        return None

    key = PhysicalKey(
        id=key_id,
        key_value=value,
        key_hash=key_hash,
        source=source,
        file_path=file_path,
    )
    db.session.add(key)
    db.session.commit()
    return key


def ingest_physical_key_file(file_path: str, source: Optional[str] = None) -> int:
    """Import b.txt lines formatted as 'physical_key_id,32hex'."""
    abs_path = os.path.abspath(file_path)
    if not os.path.exists(abs_path):
        return 0

    count = 0
    with open(abs_path, 'r', encoding='utf-8', errors='ignore') as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith('#'):
                continue
            if ',' in line:
                key_id, value = [part.strip() for part in line.split(',', 1)]
            else:
                parts = line.split()
                if len(parts) != 2:
                    save_log(f"Skipped invalid physical key line in {abs_path}", level='WARNING', source='physical-ingest')
                    continue
                key_id, value = parts
            key = save_physical_key(key_id, value, source=source or 'physical-import', file_path=abs_path)
            if key:
                count += 1
    return count


def get_physical_key(key_id: str) -> Optional[PhysicalKey]:
    return PhysicalKey.query.get(key_id)


def get_key_session(session_id: str) -> Optional[KeySession]:
    return KeySession.query.get(session_id)


def get_or_create_session_key(session_id: str, self_id: str, peer_id: str) -> KeySession:
    """Return the same quantum/physical key pair for both parties of a session."""
    if not session_id or not self_id or not peer_id:
        raise ValueError('session_id, self_id, and peer_id are required')

    session = KeySession.query.get(session_id)
    if session:
        expected_peer = session.party_b if self_id == session.party_a else session.party_a
        if self_id not in (session.party_a, session.party_b):
            raise ValueError('device is not part of this key session')
        if peer_id != expected_peer:
            raise ValueError('peer_id does not match existing key session')
    else:
        quantum_key = Key.query.filter_by(status='unused').order_by(Key.created_at.desc()).first()
        if not quantum_key:
            raise ValueError('no unused quantum key available')
        physical_key = PhysicalKey.query.filter_by(status='unused').order_by(PhysicalKey.created_at.desc()).first()
        if not physical_key:
            raise ValueError('no unused physical key available')

        quantum_key.status = 'reserved'
        quantum_key.request_ip = f'{self_id}<->{peer_id}:{session_id}'
        physical_key.mark_reserved(session_id)
        session = KeySession(
            session_id=session_id,
            party_a=self_id,
            party_b=peer_id,
            quantum_key_id=quantum_key.id,
            physical_key_id=physical_key.id,
        )
        db.session.add(session)

    session.claim(self_id)
    if session.status == 'used':
        session.quantum_key.mark_used(request_ip=f'{session.party_a}<->{session.party_b}:{session.session_id}')
        session.physical_key.mark_used()
    db.session.commit()
    return session


def list_keys(status: Optional[str] = None, limit: int = 100) -> List[Key]:
    """查询密钥列表"""
    q = Key.query
    if status:
        q = q.filter_by(status=status)
    return q.order_by(Key.created_at.desc()).limit(limit).all()


def get_key_stats() -> dict:
    """获取密钥统计信息"""
    total = Key.query.count()
    unused = Key.query.filter_by(status='unused').count()
    used = Key.query.filter_by(status='used').count()
    total_length = db.session.query(func.sum(Key.length)).filter_by(status='unused').scalar() or 0
    
    # 今日请求数
    today = date.today()
    today_stats = KeyUsageStats.query.filter_by(date=today).first()
    today_requests = today_stats.request_count if today_stats else 0
    
    # 独立 IP 数
    unique_ips = db.session.query(Key.request_ip).filter(
        Key.request_ip.isnot(None),
        Key.request_ip != ''
    ).distinct().count()
    
    return {
        'total': total,
        'unused': unused,
        'used': used,
        'total_unused_length': total_length,
        'today_requests': today_requests,
        'unique_ips': unique_ips,
    }


def get_physical_key_stats() -> dict:
    total = PhysicalKey.query.count()
    unused = PhysicalKey.query.filter_by(status='unused').count()
    reserved = PhysicalKey.query.filter_by(status='reserved').count()
    used = PhysicalKey.query.filter_by(status='used').count()
    return {
        'total': total,
        'unused': unused,
        'reserved': reserved,
        'used': used,
    }


def get_ip_stats(limit: int = 100) -> List[dict]:
    """获取 IP 请求统计"""
    result = db.session.query(
        Key.request_ip,
        func.count(Key.id).label('count'),
        func.min(Key.used_at).label('first_used'),
        func.max(Key.used_at).label('last_used')
    ).filter(
        Key.status == 'used'
    ).group_by(Key.request_ip).order_by(func.count(Key.id).desc()).limit(limit).all()
    
    return [
        {
            'ip': r.request_ip,
            'count': r.count,
            'first_used': r.first_used.isoformat() if r.first_used else None,
            'last_used': r.last_used.isoformat() if r.last_used else None,
        }
        for r in result
    ]


def save_log(message: str, level: str = 'INFO', source: Optional[str] = None, 
             file_path: Optional[str] = None) -> RunLog:
    """保存日志"""
    log = RunLog(
        level=level,
        message=message,
        source=source,
        file_path=file_path,
    )
    db.session.add(log)
    db.session.commit()
    return log


def list_logs(level: Optional[str] = None, limit: int = 200) -> List[RunLog]:
    """查询日志列表"""
    q = RunLog.query
    if level:
        q = q.filter_by(level=level)
    return q.order_by(RunLog.created_at.desc()).limit(limit).all()


def ingest_key_file(file_path: str, source: Optional[str] = None, 
                    per_line: bool = False, skip_imported: bool = True) -> int:
    """导入密钥文件
    
    使用文件内容SHA256哈希进行去重，确保相同内容不会重复导入。
    
    Args:
        file_path: 文件路径
        source: 密钥来源标识
        per_line: 是否按行导入
        skip_imported: 是否跳过已导入的文件
        
    Returns:
        成功导入的密钥数量
    """
    abs_path = os.path.abspath(file_path)
    
    # 先计算文件内容哈希
    file_hash = compute_file_hash(abs_path)
    if not file_hash:
        save_log(f"Failed to compute hash for file {abs_path}", level='ERROR', source='ingest')
        return 0
    
    # 检查是否已导入（基于内容哈希去重）
    if skip_imported:
        existing = ImportedFile.query.filter_by(file_path=abs_path).first()
        if existing:
            # 使用内容哈希检测文件是否真正变化
            if existing.content_hash == file_hash:
                # 文件内容完全相同，跳过
                return 0
            # 文件内容已变化，但需要检查是否有新密钥
        else:
            # 检查是否有其他路径的文件具有相同哈希（同一文件可能被复制到不同位置）
            same_hash_file = ImportedFile.query.filter_by(content_hash=file_hash).first()
            if same_hash_file:
                # 相同内容的文件已被导入，创建记录但不导入密钥
                try:
                    stat = os.stat(abs_path)
                    imported = ImportedFile(
                        file_path=abs_path,
                        content_hash=file_hash,
                        mtime=stat.st_mtime,
                        size=stat.st_size,
                        source=source,
                        keys_count=0,  # 重复内容，未导入新密钥
                    )
                    db.session.add(imported)
                    db.session.commit()
                    save_log(f"Skipped duplicate content file {abs_path} (same as {same_hash_file.file_path})", 
                            level='INFO', source='ingest')
                except Exception as e:
                    save_log(f"Failed to record skipped file: {e}", level='ERROR', source='ingest')
                return 0
    
    try:
        with open(abs_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read().strip()
    except Exception as e:
        save_log(f"Failed to read file {abs_path}: {e}", level='ERROR', source='ingest')
        return 0
    
    if not content:
        return 0
    
    count = 0
    skipped = 0
    if per_line:
        for line in content.split('\n'):
            line = line.strip()
            if line:
                key = save_key(line, source=source, file_path=abs_path, skip_duplicate=True)
                if key:
                    count += 1
                else:
                    skipped += 1
    else:
        key = save_key(content, source=source, file_path=abs_path, skip_duplicate=True)
        if key:
            count = 1
        else:
            skipped = 1
    
    # 记录已导入文件
    try:
        stat = os.stat(abs_path)
        imported = ImportedFile.query.filter_by(file_path=abs_path).first()
        if imported:
            imported.content_hash = file_hash
            imported.mtime = stat.st_mtime
            imported.size = stat.st_size
            imported.keys_count += count
            imported.imported_at = datetime.utcnow()
        else:
            imported = ImportedFile(
                file_path=abs_path,
                content_hash=file_hash,
                mtime=stat.st_mtime,
                size=stat.st_size,
                source=source,
                keys_count=count,
            )
            db.session.add(imported)
        db.session.commit()
        
        if skipped > 0:
            save_log(f"Imported {count} key(s), skipped {skipped} duplicate(s) from {abs_path}", 
                    level='INFO', source='ingest')
    except Exception as e:
        save_log(f"Failed to record import: {e}", level='ERROR', source='ingest')
    
    return count


def ingest_keys_from_dir(dir_path: str, source: Optional[str] = None,
                         per_line: bool = False, recursive: bool = True,
                         file_patterns: Optional[List[str]] = None,
                         skip_imported: bool = True) -> dict:
    """从目录导入密钥文件"""
    abs_dir = os.path.abspath(dir_path)
    if not os.path.isdir(abs_dir):
        return {'ingested': 0, 'files': 0, 'error': f'Directory not found: {abs_dir}'}
    
    patterns = file_patterns or ['*.txt']
    total_keys = 0
    total_files = 0
    
    def match_patterns(filename):
        return any(fnmatch.fnmatch(filename, p) for p in patterns)
    
    if recursive:
        for root, dirs, files in os.walk(abs_dir):
            for fname in files:
                if match_patterns(fname):
                    fpath = os.path.join(root, fname)
                    count = ingest_key_file(fpath, source=source, per_line=per_line, 
                                           skip_imported=skip_imported)
                    if count > 0:
                        total_keys += count
                        total_files += 1
    else:
        for fname in os.listdir(abs_dir):
            fpath = os.path.join(abs_dir, fname)
            if os.path.isfile(fpath) and match_patterns(fname):
                count = ingest_key_file(fpath, source=source, per_line=per_line,
                                       skip_imported=skip_imported)
                if count > 0:
                    total_keys += count
                    total_files += 1
    
    return {'ingested': total_keys, 'files': total_files}


def _update_daily_stats(imported_count: int = 0, imported_length: int = 0,
                        used_count: int = 0, used_length: int = 0,
                        request_count: int = 0):
    """更新每日统计数据"""
    today = date.today()
    stats = KeyUsageStats.query.filter_by(date=today).first()
    
    if not stats:
        stats = KeyUsageStats(date=today)
        db.session.add(stats)
    
    # 某些情况下模型属性可能为 None（例如未从 DB 读取或默认未生效），
    # 使用安全的累加写法以避免 NoneType += int 的 TypeError。
    stats.imported_count = (stats.imported_count or 0) + imported_count
    stats.imported_length = (stats.imported_length or 0) + imported_length
    stats.used_count = (stats.used_count or 0) + used_count
    stats.used_length = (stats.used_length or 0) + used_length
    stats.request_count = (stats.request_count or 0) + request_count
    stats.updated_at = datetime.utcnow()
    
    db.session.commit()


def get_daily_stats(days: int = 7) -> List[dict]:
    """获取每日统计数据"""
    stats = KeyUsageStats.query.order_by(KeyUsageStats.date.desc()).limit(days).all()
    return [s.to_dict() for s in stats]


def list_imported_files(limit: int = 50) -> List[ImportedFile]:
    """查询已导入文件列表"""
    return ImportedFile.query.order_by(ImportedFile.imported_at.desc()).limit(limit).all()
