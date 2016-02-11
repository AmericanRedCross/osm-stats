import os
from fabric.operations import run, put, sudo

def deploy():
    put('.env', '~/', use_sudo=True)
    put('docker-compose.yml', '~/', use_sudo=True)
    put('osm-stats-api', '~/', use_sudo=True)
    put('planet-stream', '~/', use_sudo=True)
    sudo('yum update -y')
    sudo('yum install -y docker')
    sudo('pip install docker-compose')
    sudo('service docker start')
    sudo('usermod -a -G docker ec2-user')
    run('docker-compose build')
    run('docker-compose up')
