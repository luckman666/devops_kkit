from kkit import settings


def SaltMinionShellScript():
    shellcontext =('#!bin/bash\nyum install epel-release' \
                  ' salt-minion -y && sed -e"s/^#\(master:\).*/\\1 %s/" -i /etc/salt/minion -e' \
                  ' "s/^#\(id:\).*/\\1 ${HOSTNAME}/" -i /etc/salt/minion && systemctl restart ' \
                  'salt-minion.service && systemctl enable salt-minion.service') % settings.salt_master_ip_addr

    return shellcontext
