import unittest
import logging
import logging.config
import svg-export-layers


__author__ = 'Tullio Facchinetti'


log_config = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '[%(asctime)s.%(msecs).03d] %(levelname)s %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        }
    },
    'handlers': {
        'test_handler': {
            'level': 'DEBUG',
            # 'class': 'logging.StreamHandler',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'myagolib_test.log',
            'maxBytes': 20000000,
            'backupCount': 5,
            'formatter': 'standard'
        }
    },
    'loggers': {
        'test_logger': {
            'handlers': ['test_handler'],
            'level': 'DEBUG',
        }
    }
}


class TestReports(unittest.TestCase):
    pass

if __name__ == '__main__':
    logging.config.dictConfig(log_config)
    unittest.main(warnings='ignore')
