#!/usr/bin/env python3

import subprocess
import os

run_command = "gunicorn --workers=2 --worker-connections=1000 --worker-class=gevent -t 300 wsgi:app  -b 0.0.0.0:8000"

print(run_command)
my_env = os.environ.copy()
my_env['SERVER_CONF'] = 'configmodule.DevelopmentConfig'
subprocess.run(run_command.split(' '), check=False, env=my_env)
