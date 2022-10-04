dict_config = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'base': {
            'format': '%(asctime)s | %(levelname)s | %(name)s | %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'base'
        },
        'file': {
            'class': 'logging.FileHandler',
            'level': 'ERROR',
            'formatter': 'base',
            'filename': 'logfile.log',
            'mode': 'a'
        }
    },
    'loggers': {
        'main': {
            'level': 'DEBUG',
            'handlers': ['file', 'console'],
        },
        'start_controller': {
            'level': 'DEBUG',
            'handlers': ['file', 'console'],
        },
        'admin_controller': {
            'level': 'DEBUG',
            'handlers': ['file', 'console'],
        }
    }
}
