#!/usr/bin/env python3

import subprocess
import os

with open('Procfile') as file:
    run_command = file.readline()
    run_command = run_command.replace('web: ', '')
    run_command += ' -b 0.0.0.0:8000'

print(run_command)
my_env = os.environ.copy()
my_env['SERVER_CONF'] = 'configmodule.DevelopmentConfig'
subprocess.run(run_command.split(' '), check=False, env=my_env)
