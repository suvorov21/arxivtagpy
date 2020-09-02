#!/usr/bin/env python3

import subprocess
import os

with open('Procfile') as file:
    run_command = file.readline()
    run_command = run_command.replace('web: ', '')

print(run_command)
my_env = os.environ.copy()
my_env['SERVER_CONF'] = 'configmodule.DevelopmentConfig'
subprocess.run(run_command.split(' '), check=False, env=my_env)
