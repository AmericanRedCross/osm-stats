from fabric.operations import run, put, sudo


def setup_host(name="osmstats"):
    """ Update machine and install required packages """
    sudo('yum update -y')
    sudo('yum install -y docker awslogs')
    sudo('sed -i \'s/^log_group_name =.*/log_group_name = \/aws\/ec2\/%s/\' /etc/awslogs/awslogs.conf' % name)
    sudo('sed -i \'s/^log_stream_name =.*/log_stream_name = syslog/\' /etc/awslogs/awslogs.conf')
    sudo('pip install docker-compose')
    sudo('service docker start')
    sudo('service awslogs start')
    sudo('chkconfig awslogs on')
    sudo('usermod -a -G docker ec2-user')


def copy_files():
    """ Copy Docker files to host """
    put('.env', '~/', use_sudo=True)
    put('docker-compose.yml', '~/', use_sudo=True)
    put('osm-stats-api', '~/', use_sudo=True)
    put('planet-stream', '~/', use_sudo=True)
    put('forgettable', '~/', use_sudo=True)


def deploy():
    """ Deploy docker containers """
    run('docker-compose down')
    run('docker-compose build')
    run('docker-compose up -d')
