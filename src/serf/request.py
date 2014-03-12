import string
import msgpack

from . import _exceptions
from . import constant


class BaseRequest (object ) :
    command = None

    must_be_argument = tuple()
    optional_argument = tuple()

    def __init__ (self, **body) :
        self.seq = None
        self.body = body
        self.callbacks = list()

        self.is_checked = False

    def _get_is_checked (self, ) :
        return self._is_checked

    def _set_is_checked (self, b, ) :
        self._is_checked = b

    is_checked = property(_get_is_checked, _set_is_checked, )

    def check (self, client, ) :
        self.do_check(client, )

        self.is_checked = True

        return self

    def do_check (self, client, ) :
        # check argument
        _all_argument = set(self.must_be_argument) | set(self.optional_argument, )
        if not _all_argument :
            if self.body :
                raise _exceptions.InvalidRequest('request body be empty', )

        else :
            if not hasattr(self.body, 'keys', ) or not callable(self.body.keys, ) :
                raise _exceptions.InvalidRequest('invalid request body', )

            # check whether unknown arguments exist
            if set(self.body.keys()) - set(_all_argument) :
                raise _exceptions.InvalidRequest('unknown argument found in request', )

            # check must be arguments exist
            if set(self.must_be_argument, ) - set(self.body.keys()) :
                raise _exceptions.InvalidRequest('some argument missing in request', )

        return

    def __getstate__ (self, ) :
        return dict(
                command=self.command,
                seq=self.seq,
                body=self.body,
                callbacks=self.callbacks,
            )

    def __repr__ (self, ) :
        return '<%s: %s, %s, %s>' % (
                self.__class__.__name__,
                self.command,
                self.seq,
                str(self.body) if self.body else '',
            )

    @classmethod
    def dumps (cls, command, seq, body, ) :
        return msgpack.packb(dict(
                Command=command,
                Seq=seq,
            ), ) + (msgpack.packb(body, ) if body else '')

    def __str__ (self, ) :
        if not self.is_checked :
            raise _exceptions.UncheckedRequest

        if self.seq is None :
            self.seq = 0

        return self.dumps(
                self.command.replace('_', '-', ),
                self.seq,
                self.body,
            )

    @property
    def is_stream (self, ) :
        return self.command in constant.STREAM_COMMANDS

    def add_callback (self, *callbacks) :
        self.callbacks.extend(callbacks)

        return self


class RequestHandshake (BaseRequest, ) :
    """
    {"Version": 1}
    """

    must_be_argument = ('Version', )

    def do_check (self, client, ) :
        if 'Version' not in self.body :
            self.body['Version'] = client.ipc_version

        super(RequestHandshake, self).do_check(client, )

        return


class RequestEvent (BaseRequest, ) :
    """
        {"Name": "foo", "Payload": "test payload", "Coalesce": true}
    """
    must_be_argument = (
            'Name',
            'Payload',
        )
    optional_argument = (
            'Coalesce',
        )

    def do_check (self, client, ) :
        super(RequestEvent, self).do_check(client, )

        try :
            self.body['Name']
            self.body['Payload']
        except KeyError :
            raise _exceptions.InvalidRequest('invalid request, some key is missing.', )

        if type(self.body.get('Name', ), ) not in (str, unicode, ) :
            raise _exceptions.InvalidRequest('invalid request, `Name` must be str.', )

        if type(self.body.get('Payload', ), ) not in (str, unicode, ) :
            raise _exceptions.InvalidRequest('invalid request, `Payload` must be str.', )

        if 'Coalesce' in self.body and type(self.body.get('Coalesce', ), ) not in (bool, ) :
            raise _exceptions.InvalidRequest('invalid request, `Coalesce` must be bool.', )

        # check payload
        self._is_checked = True
        if len(str(self)) > constant.PAYLOAD_SIZE_LIMIT :
            raise _exceptions.InvalidRequest(
                    'invalid request, message size must be smaller than %s.' % (
                            constant.PAYLOAD_SIZE_LIMIT,
                        ), )
        self._is_checked = False

        return


class RequestStream (BaseRequest, ) :
    """
        {"Type": "member-join,user:deploy"}`
    """
    must_be_argument = (
            'Type',
        )

    def do_check (self, client, ) :
        super(RequestStream, self).do_check(client, )

        try :
            self.body['Type']
        except KeyError :
            raise _exceptions.InvalidRequest('invalid request, some key is missing.', )

        if type(self.body.get('Type', ), ) not in (str, unicode, ) :
            raise _exceptions.InvalidRequest('invalid request, `Type` must be str.', )

        _types = filter(string.strip, self.body.get('Type').split(','), )
        if len(_types) < 1 :
            raise _exceptions.InvalidRequest('invalid request, `Type` must be filled.', )

        return


class RequestLeave (BaseRequest, ) :
    def do_check (self, client, ) :
        super(RequestLeave, self).do_check(client, )

        return


class RequestForceLeave (BaseRequest, ) :
    """
        {"Node": "failed-node-name"}
    """
    must_be_argument = (
            'Node',
        )

    def do_check (self, client, ) :
        super(RequestForceLeave, self).do_check(client, )

        try :
            self.body['Node']
        except KeyError :
            raise _exceptions.InvalidRequest('invalid request, some key is missing.', )

        if type(self.body.get('Node', ), ) not in (str, unicode, ) :
            raise _exceptions.InvalidRequest('invalid request, `Type` must be str.', )

        return


class RequestMonitor (BaseRequest, ) :
    """
        {"LogLevel": "DEBUG"}
    """
    must_be_argument = (
            'LogLevel',
        )

    def do_check (self, client, ) :
        super(RequestMonitor, self).do_check(client, )

        try :
            self.body['LogLevel']
        except KeyError :
            raise _exceptions.InvalidRequest('invalid request, some key is missing.', )

        if type(self.body.get('LogLevel', ), ) not in (str, unicode, ) :
            raise _exceptions.InvalidRequest('invalid request, `Type` must be str.', )

        return


class RequestStop (BaseRequest, ) :
    """
        {"Stop": 50}
    """
    must_be_argument = (
            'Stop',
        )

    def do_check (self, client, ) :
        super(RequestStop, self).do_check(client, )

        try :
            self.body['Stop']
        except KeyError :
            raise _exceptions.InvalidRequest('invalid request, some key is missing.', )

        if type(self.body.get('Stop', ), ) not in (int, long, ) :
            raise _exceptions.InvalidRequest('invalid request, `Type` must be int.', )

        return


class RequestJoin (BaseRequest, ) :
    """
        {"Existing": ["192.168.0.1:6000", "192.168.0.2:6000"], "Replay": false}
    """
    must_be_argument = (
            'Existing',
            'Replay',
        )

    def do_check (self, client, ) :
        super(RequestJoin, self).do_check(client, )

        try :
            self.body['Existing']
        except KeyError :
            raise _exceptions.InvalidRequest('invalid request, some key is missing.', )

        if type(self.body.get('Existing', ), ) not in (list, tuple, ) :
            raise _exceptions.InvalidRequest(
                    'invalid request, `Existing` must be list or tuple.', )

        if self.body.get('Replay', ) and type(self.body.get('Replay', ), ) not in (bool, ) :
            raise _exceptions.InvalidRequest('invalid request, `Replay` must be bool.', )

        return


