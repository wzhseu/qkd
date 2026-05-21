STATUS_OK = { "status": "ok" }
STATUS_FAIL = { "status": "fail" }

def ok_with_payload(payload):
    return { "status": "ok", "payload": payload }

def failed_with_explain(explain):
    return { "status": "fail", "explain": explain }

def get_value_with_check(obj, field):
    if field in obj:
        return obj[field], True
    return "Please specify the '{}' field".format(field), False

def get_param_or(request, key, fallback):
    if request.args.get(key) == None:
        return fallback
    return request.args.get(key)
