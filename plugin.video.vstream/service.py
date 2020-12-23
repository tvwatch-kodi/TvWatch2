# -*- coding: utf-8 -*-
# https://github.com/Kodi-vStream/venom-xbmc-addons
import subprocess
import xbmcvfs
from datetime import datetime
from resources.lib.comaddon import addon, xbmc, VSlog, VSPath


def service():
    ADDON = addon()
    recordIsActivate = ADDON.getSetting('enregistrement_activer')
    if recordIsActivate == 'false':
        return

    pathRecording = 'special://userdata/addon_data/plugin.video.tvwatch2/Enregistrement'
    path = ''.join([pathRecording])
    if not xbmcvfs.exists(path):
        xbmcvfs.mkdir(path)

    recordList = xbmcvfs.listdir(path)
    interval = ADDON.getSetting('heure_verification')
    ADDON.setSetting('path_enregistrement_programmation', path)
    recordInProgress = False
    monitor = xbmc.Monitor()

    del ADDON

    while not monitor.abortRequested() and not recordInProgress == True:
        if monitor.waitForAbort(int(interval)):
            break

        hour = datetime.now().strftime('%d-%H-%M') + '.py'
        if hour in str(recordList):
            hour = path + '/' + hour
            hour = VSPath(hour)
            recordInProgress = True
            VSlog('python ' + hour)
            command = 'python ' + hour
            proc = subprocess.Popen(command, stdout=subprocess.PIPE)
            p_status = proc.wait()


if __name__ == '__main__':
    service()
