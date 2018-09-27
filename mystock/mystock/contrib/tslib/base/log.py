import logging

import logstash


def get_logstash(name, host='localhost', type='logstash', port=5959):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.addHandler(logstash.TCPLogstashHandler(host, port, message_type=type, version=1))

    return logger
