import json
import requests
import time


__version__ = '0.6.1'
TRANSPORTS = []


class EngineIO(object):

    _engineIO_protocol = 3
    _engineIO_request_index = 0

    def __init__(
            self,
            host, port=None, Namespace=None,
            wait_for_connection=True, transports=TRANSPORTS,
            resource='engine.io', **kw):
        self._url = 'http://%s:%s/%s/' % (host, port, resource)
        self._session = requests.Session()
        print self._url

        response = self._session.get(self._url, params={
            'EIO': self._engineIO_protocol,
            'transport': 'polling',
            't': self._get_timestamp(),
        })
        print response.url

        engineIO_packets = _decode_content(response.content)
        print engineIO_packets
        engineIO_packet_type, engineIO_packet_data = engineIO_packets[0]
        assert engineIO_packet_type == 0
        engineIO_packet_json = json.loads(engineIO_packet_data)
        print engineIO_packet_json
        # engineIO_packet_json['pingInterval']
        # engineIO_packet_json['pingTimeout']
        # engineIO_packet_json['upgrades']
        self._session_id = engineIO_packet_json['sid']

    def wait(self):
        while True:
            self._process_packets()

    def _process_packets(self):
        for engineIO_packet in self._recv_packet():
            self._process_packet(engineIO_packet)

    def _process_packet(self, packet):
        engineIO_packet_type, engineIO_packet_data = packet
        print 'engineIO_packet_type = %s' % engineIO_packet_type
        engineIO_packet_data_parsed = _parse_engineIO_data(
            engineIO_packet_data)
        # Launch callbacks
        namespace = self.get_namespace()
        delegate = {
            0: self._on_open,
            1: self._on_close,
            2: self._on_ping,
            3: self._on_pong,
            4: self._on_message,
            5: self._on_upgrade,
            6: self._on_noop,
        }[engineIO_packet_type]
        delegate(engineIO_packet_data_parsed, namespace._find_packet_callback)
        return engineIO_packet_data

    def get_namespace(self):
        pass

    def _on_open(self):
        pass

    def _on_close(self):
        pass

    def _on_ping(self):
        pass

    def _on_pong(self):
        pass

    def _on_message(self):
        pass

    def _on_upgrade(self):
        pass

    def _on_noop(self):
        pass

    def _get_timestamp(self):
        timestamp = '%s-%s' % (
            int(time.time() * 1000), self._engineIO_request_index)
        self._engineIO_request_index += 1
        return timestamp

    def _message(self, engineIO_packet_data):
        engineIO_packet_type = 4
        response = self._session.post(self._url, params={
            'EIO': self._engineIO_protocol,
            'transport': 'polling',
            't': self._get_timestamp(),
            'sid': self._session_id,
        }, data=_encode_content([
            (engineIO_packet_type, engineIO_packet_data),
        ]), headers={
            'content-type': 'application/octet-stream',
        })
        engineIO_packets = _decode_content(response.content)
        for engineIO_packet_type, engineIO_packet_data in engineIO_packets:
            socketIO_packet_type = int(engineIO_packet_data[0])
            socketIO_packet_data = engineIO_packet_data[1:]
            print 'engineIO_packet_type = %s' % engineIO_packet_type
            print 'socketIO_packet_type = %s' % socketIO_packet_type
            print 'socketIO_packet_data = %s' % socketIO_packet_data

    def _ping(self):
        engineIO_packet_type = 2
        engineIO_packet_data = ''
        response = self._session.post(self._url, params={
            'EIO': self._engineIO_protocol,
            'transport': 'polling',
            't': self._get_timestamp(),
            'sid': self._session_id,
        }, data=_encode_content([
            (engineIO_packet_type, engineIO_packet_data),
        ]), headers={
            'content-type': 'application/octet-stream',
        })
        engineIO_packets = _decode_content(response.content)
        for engineIO_packet_type, engineIO_packet_data in engineIO_packets:
            socketIO_packet_type = int(engineIO_packet_data[0])
            socketIO_packet_data = engineIO_packet_data[1:]
            print 'engineIO_packet_type = %s' % engineIO_packet_type
            print 'socketIO_packet_type = %s' % socketIO_packet_type
            print 'socketIO_packet_data = %s' % socketIO_packet_data

    def _recv_packet(self):
        response = self._session.get(self._url, params={
            'EIO': self._engineIO_protocol,
            'transport': 'polling',
            't': self._get_timestamp(),
            'sid': self._session_id,
        })
        for engineIO_packet in _decode_content(response.content):
            yield engineIO_packet


class SocketIO(EngineIO):

    def __init__(
            self,
            host, port=None, Namespace=None,
            wait_for_connection=True, transports=TRANSPORTS,
            resource='socket.io', **kw):
        super(SocketIO, self).__init__(
            host, port, Namespace,
            wait_for_connection, transports,
            resource, **kw)

    def define(self, Namespace, path=''):
        pass

    def emit(self, event, *args, **kw):
        socketIO_packet_type = 2
        socketIO_packet_data = json.dumps([event])
        self._message(str(socketIO_packet_type) + socketIO_packet_data)

    def on(self, event, callback):
        pass

    def _process_packet(self, packet):
        engineIO_packet_data = super(SocketIO, self)._process_packet(packet)
        socketIO_packet_type = int(engineIO_packet_data[0])
        socketIO_packet_data = engineIO_packet_data[1:]
        print 'socketIO_packet_type = %s' % socketIO_packet_type
        socketIO_packet_data_parsed = _parse_socketIO_data(
            socketIO_packet_data)
        # Launch callbacks
        namespace = self.get_namespace()
        delegate = {
            0: self._on_connect,
            1: self._on_disconnect,
            2: self._on_event,
            3: self._on_ack,
            4: self._on_error,
            5: self._on_binary_event,
            6: self._on_binary_ack,
        }[socketIO_packet_type]
        delegate(
            socketIO_packet_data_parsed, namespace._find_packet_callback)
        return socketIO_packet_data

    def _on_connect(self):
        pass

    def _on_disconnect(self):
        pass

    def _on_event(self):
        pass

    def _on_ack(self):
        pass

    def _on_error(self):
        pass

    def _on_binary_event(self):
        pass

    def _on_binary_ack(self):
        pass


class BaseNamespace(object):
    pass


class LoggingNamespace(BaseNamespace):
    pass


def _decode_content(content):
    print content
    packets = []
    content_index = 0
    content_length = len(content)
    while content_index < content_length:
        try:
            content_index, packet_length = _read_packet_length(
                content, content_index)
        except IndexError:
            break
        content_index, packet_string = _read_packet_string(
            content, content_index, packet_length)
        packet_type = int(packet_string[0])
        packet_data = packet_string[1:]
        packets.append((packet_type, packet_data))
    return packets


def _encode_content(packets):
    parts = []
    for packet_type, packet_data in packets:
        packet_string = str(packet_type) + str(packet_data)
        parts.append(_make_packet_header(packet_string) + packet_string)
    return ''.join(parts)


def _read_packet_length(content, content_index):
    while ord(content[content_index]) != 0:
        content_index += 1
    content_index += 1
    packet_length_string = ''
    while ord(content[content_index]) != 255:
        packet_length_string += str(ord(content[content_index]))
        content_index += 1
    return content_index, int(packet_length_string)


def _read_packet_string(content, content_index, packet_length):
    while ord(content[content_index]) == 255:
        content_index += 1
    packet_string = content[content_index:content_index + packet_length]
    return content_index + packet_length, packet_string


def _make_packet_header(packet_string):
    length_string = str(len(packet_string))
    header_digits = [0]
    for i in xrange(len(length_string)):
        header_digits.append(ord(length_string[i]) - 48)
    header_digits.append(255)
    return ''.join(chr(x) for x in header_digits)


def find_callback(args, kw=None):
    pass
