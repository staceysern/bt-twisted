from bottle import route, run
import bencode

@route('/failure')
def failure():
    d = {'failure reason': "Just because"}
    return bencode.bencode(d)

@route('/warning')
def warning():
    d = {'interval':10, 'complete': 0, 'incomplete': 10,
         'peers': [{'peer id': 'peer1', 'ip': '193.24.32.17', 'port': 6969},
                   {'peer id': 'peer2', 'ip': '194.25.33.18', 'port': 7070},
                   {'peer id': 'peer3', 'ip': '195.26.34.19', 'port': 7171},
                   {'peer id': 'peer4', 'ip': '196.27.35.20', 'port': 7272},
                   {'peer id': 'peer2', 'ip': '197.28.36.21', 'port': 7373}],
         'warning message': 'Fake tracker warning'}
    return bencode.bencode(d)

@route('/announce')
def announce():
    d = {'interval':10, 'complete': 0, 'incomplete': 10,
         'peers': [{'peer id': 'peer1', 'ip': '193.24.32.17', 'port': 6969},
                   {'peer id': 'peer2', 'ip': '194.25.33.18', 'port': 7070},
                   {'peer id': 'peer3', 'ip': '195.26.34.19', 'port': 7171},
                   {'peer id': 'peer4', 'ip': '196.27.35.20', 'port': 7272},
                   {'peer id': 'peer2', 'ip': '197.28.36.21', 'port': 7373}]}
    return bencode.bencode(d)

run(host='localhost', port=1061, debug=True)
