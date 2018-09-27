
import requests
from django.conf import settings


class ServiceObject:
    def __init__(self, **kwargs):
        self.query = {}
        self.data = None
        for k, v in kwargs.items():
            setattr(self, k, v)

        self.kwargs = kwargs
        self.prepare()
        print('1')

    def url_format(self):
        raise NotImplementedError

    def prepare(self):
        self.url = self.url_format().format(**self.kwargs)
        if self.nocache:
            if not self.query:
                self.query = {}
            self.query['nocache'] = 1

    def _action(self):

        self._result = requests.request(self.method, self.url, data=self.query).json()

    def action(self):
        return self._action()

    def result(self):
        if hasattr(self, '_result'):
            return self._result
        else:
            self.action()
            return self._result


class GetServiceObject(ServiceObject):

    # def __init__(self, **kwargs):
    #     print('2')
    #     self.method = 'get'
    #     super(ServiceObject, self).__init__(**kwargs)

    #     print(self.method)
    @property
    def method(self):
        return 'get'


class Combin(GetServiceObject):

    # def __init__(self, start='start', end='end', code=None, line=False, volume=False, describe=False):
    #     super().__init__(self, start=start, end=end, code=code, line=line, volume=volume,
    #                      describe=describe)

    def __init__(self, **kwargs):
        super(GetServiceObject, self).__init__(**kwargs)

    def prepare(self):
        host = settings.STOCKSERVER
        host = host[:-1] if host.endswith('/') else host
        line = self.kwargs.get('line', False)
        volume = self.kwargs.get('volume', False)
        describe = self.kwargs.get('describe', False)
        baseinfo = self.kwargs.get('baseinfo', False)
        k = self.kwargs.get('k', 10)

        if not self.query:
            self.query = {}
        if line:
            self.query['line'] = 1
        if volume:
            self.query['volume'] = 1
        if describe:
            self.query['describe'] = 1
        if baseinfo:
            self.query['baseinfo'] = 1
        self.query['k'] = k
        self.url = f'{host}/k/combin/{self.start}/{self.end}/{self.code}'

        if self.query:
            self.url = '?'.join([self.url, '&'.join(['%s=%s' % (key, value) for key, value in self.query.items()])])
