import configparser
import os

from flask import jsonify, request, send_from_directory

from gateway_app import create_app
from gateway_app.auto_importer import AutoImporter
from gateway_app.db_ops import (
    consume_key,
    consume_latest_key,
    get_daily_stats,
    get_ip_stats,
    get_key_stats,
    get_physical_key,
    get_physical_key_stats,
    ingest_key_file,
    ingest_keys_from_dir,
    list_imported_files,
    list_keys,
    list_logs,
    save_key,
    save_log,
)
from gateway_app.physical_keys import PhysicalKeyImporter


app = create_app()

cfg = configparser.ConfigParser(inline_comment_prefixes=("#", ";"))
_APP_DIR = os.path.dirname(os.path.abspath(__file__))
_CONFIG_PATH = os.path.join(_APP_DIR, 'config.ini')
cfg.read(_CONFIG_PATH, encoding='utf-8')

auto_importer = None
physical_key_importer = None


def _resolve_config_path(path_value):
    if os.path.isabs(path_value):
        return path_value
    base_dir = os.path.dirname(_APP_DIR)
    return os.path.normpath(os.path.join(base_dir, path_value))


def _maybe_start_auto_importer_from_config():
    global auto_importer
    if not cfg.has_section('auto_import') or not cfg.getboolean('auto_import', 'enabled', fallback=False):
        return

    dir_path = cfg.get('auto_import', 'path', fallback='').strip()
    if not dir_path:
        print('[AutoImporter] enabled=true but no path configured')
        return

    dir_path = _resolve_config_path(dir_path)
    source = cfg.get('auto_import', 'source', fallback='auto-import')
    per_line = cfg.getboolean('auto_import', 'per_line', fallback=True)
    recursive = cfg.getboolean('auto_import', 'recursive', fallback=True)
    interval = cfg.getint('auto_import', 'interval_sec', fallback=5)
    patterns_str = cfg.get('auto_import', 'patterns', fallback='')
    patterns = [p.strip() for p in patterns_str.split(',') if p.strip()] or None

    with app.app_context():
        summary = ingest_keys_from_dir(
            dir_path,
            source=source,
            per_line=per_line,
            recursive=recursive,
            file_patterns=patterns,
        )
        print(f"[AutoImporter] Initial import: {summary.get('ingested', 0)} key(s) from {summary.get('files', 0)} file(s)")

    auto_importer = AutoImporter(
        dir_path,
        source=source,
        per_line=per_line,
        recursive=recursive,
        interval_sec=interval,
        patterns=patterns,
        app=app,
    )
    auto_importer.start()
    print(f"[AutoImporter] Started. Watching: {dir_path}")


def _maybe_start_physical_importer_from_config():
    global physical_key_importer
    if not cfg.has_section('physical_import') or not cfg.getboolean('physical_import', 'enabled', fallback=False):
        return

    file_path = cfg.get('physical_import', 'path', fallback='').strip()
    if not file_path:
        print('[PhysicalKeyImporter] enabled=true but no path configured')
        return

    file_path = _resolve_config_path(file_path)
    source = cfg.get('physical_import', 'source', fallback='physical-import')
    interval = cfg.getint('physical_import', 'interval_sec', fallback=5)
    physical_key_importer = PhysicalKeyImporter(file_path, source=source, interval_sec=interval, app=app)
    physical_key_importer.start()


with app.app_context():
    _maybe_start_auto_importer_from_config()
    _maybe_start_physical_importer_from_config()


@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'database': 'connected',
        'stats': get_key_stats(),
        'physical_key_stats': get_physical_key_stats(),
    })


@app.route('/api/keys/stats', methods=['GET'])
def api_get_key_stats():
    return jsonify(get_key_stats())


@app.route('/api/keys', methods=['GET'])
def api_list_keys():
    status = request.args.get('status')
    limit = int(request.args.get('limit', 100))
    keys = list_keys(status=status, limit=limit)
    return jsonify({'count': len(keys), 'keys': [k.to_dict() for k in keys]})


@app.route('/api/keys', methods=['POST'])
def api_add_key():
    data = request.json or {}
    key_value = data.get('value')
    source = data.get('source', 'manual')
    if not key_value:
        return jsonify({'error': 'key value is required'}), 400
    key = save_key(key_value, source=source)
    if not key:
        return jsonify({'error': 'invalid or duplicate key'}), 400
    save_log(f"Added key: {key.id} (length={key.length})", source='api')
    return jsonify({'success': True, 'key': key.to_dict()})


@app.route('/api/keys/consume/<int:key_id>', methods=['POST'])
def api_consume_key(key_id):
    key = consume_key(key_id)
    if not key:
        return jsonify({'error': 'key not found'}), 404
    save_log(f"Consumed key: {key.id}", source='api')
    return jsonify({'success': True, 'key': key.to_dict()})


@app.route('/api/keys/consume/latest', methods=['POST'])
def api_consume_latest_key():
    request_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if request_ip and ',' in request_ip:
        request_ip = request_ip.split(',')[0].strip()
    key = consume_latest_key(request_ip=request_ip)
    if not key:
        save_log(f"No available key for IP={request_ip}", level='WARNING', source='api')
        return jsonify({'error': 'no available key'}), 404
    save_log(f"IP {request_ip} consumed key: {key.id} (length={key.length})", source='api')
    return jsonify({'success': True, 'key': key.to_dict(), 'key_value': key.key_value})


@app.route('/api/keys/import', methods=['POST'])
def api_import_keys():
    data = request.json or {}
    file_path = data.get('file_path')
    source = data.get('source', 'manual-import')
    per_line = data.get('per_line', False)
    if not file_path:
        return jsonify({'error': 'file_path is required'}), 400
    count = ingest_key_file(file_path, source=source, per_line=per_line)
    save_log(f"Imported {count} key(s) from {file_path}", source='api')
    return jsonify({'success': True, 'imported': count, 'file_path': file_path})


@app.route('/api/physical-keys/<physical_key_id>', methods=['GET'])
def api_get_physical_key(physical_key_id):
    key = get_physical_key(physical_key_id)
    if not key:
        return jsonify({'error': 'physical key not found'}), 404
    return jsonify({'success': True, 'key': key.to_dict()})


@app.route('/api/physical-keys/stats', methods=['GET'])
def api_get_physical_key_stats():
    return jsonify(get_physical_key_stats())


@app.route('/api/keys/stats/daily', methods=['GET'])
def api_get_daily_stats():
    days = int(request.args.get('days', 7))
    stats = get_daily_stats(days=days)
    return jsonify({'count': len(stats), 'stats': stats})


@app.route('/api/keys/stats/ip', methods=['GET'])
def api_get_ip_stats():
    limit = int(request.args.get('limit', 100))
    stats = get_ip_stats(limit=limit)
    return jsonify({'count': len(stats), 'stats': stats})


@app.route('/api/logs', methods=['GET'])
def api_list_logs():
    level = request.args.get('level')
    limit = int(request.args.get('limit', 200))
    logs = list_logs(level=level, limit=limit)
    return jsonify({'count': len(logs), 'logs': [l.to_dict() for l in logs]})


@app.route('/api/logs', methods=['POST'])
def api_add_log():
    data = request.json or {}
    message = data.get('message')
    level = data.get('level', 'INFO')
    source = data.get('source', 'api')
    if not message:
        return jsonify({'error': 'message is required'}), 400
    log = save_log(message, level=level, source=source)
    return jsonify({'success': True, 'log': log.to_dict()})


@app.route('/api/auto-import/status', methods=['GET'])
def api_auto_import_status():
    return jsonify({
        'running': auto_importer.is_running() if auto_importer else False,
        'physical_running': physical_key_importer.is_running() if physical_key_importer else False,
    })


@app.route('/api/imported-files', methods=['GET'])
def api_list_imported_files():
    limit = int(request.args.get('limit', 50))
    files = list_imported_files(limit=limit)
    return jsonify({'count': len(files), 'files': [f.to_dict() for f in files]})


if __name__ == '__main__':
    port = cfg.getint('server', 'port', fallback=5002) if cfg.has_section('server') else 5002
    print("=" * 60)
    print("QKD edge gateway database system")
    print(f"HTTP API: http://localhost:{port}")
    print("=" * 60)
    app.run(host='0.0.0.0', port=port, debug=True)
