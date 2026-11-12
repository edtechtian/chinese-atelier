"""Run original application endpoints without opening a network server."""
import copy, json, os, sys, types
from pathlib import Path
ROOT = Path('/atelier')
sys.path.insert(0, str(ROOT))
from server import Handler, APIError
from app.storage import Store
from app import learning_api, visual

class BrowserHandler(Handler):
    def __init__(self, host, path, body):
        self.server, self.path, self.body = host, path, body
        self.headers, self.result = {}, None
    def teacher(self):
        return self.server.teacher_open
    def json_body(self):
        if not isinstance(self.body, dict): raise APIError(400, 'Expected a JSON object.')
        return self.body
    def send(self, value, status=200, content_type='application/json; charset=utf-8', extra=None):
        if isinstance(value, bytes): value = value.decode('utf-8')
        self.result = {'status': status, 'body': value, 'contentType': content_type}

host = types.SimpleNamespace(root=ROOT, store=Store(ROOT), sessions={}, failures=[], teacher_open=False)

def browser_request(path, body_json=None):
    body = json.loads(body_json) if body_json else None
    handler = BrowserHandler(host, path, body)
    endpoint = path.split('?')[0]
    before = copy.deepcopy(host.store.state)
    try:
        if endpoint == '/api/browser/teacher/open':
            host.teacher_open = True
            handler.send({'ok': True, 'mode': 'same_device'})
        elif endpoint == '/api/teacher/logout':
            host.teacher_open = False
            handler.send({'ok': True})
        elif endpoint == '/api/teacher/login':
            raise APIError(400, 'Use the same-device teacher view in the browser edition.')
        elif endpoint == '/api/teacher/source':
            raise APIError(409, 'Original source import requires the local Python application. Existing source references remain available.')
        elif body is None: handler.api_get(endpoint)
        else: handler.api_post(endpoint)
        host.store.save_state()
    except (APIError, learning_api.LearningError, visual.VisualError) as error:
        host.store.state = before
        handler.send({'error': error.message, 'details': getattr(error, 'details', None)}, error.status)
    except Exception:
        host.store.state = before
        raise
    return json.dumps(handler.result, ensure_ascii=False)
