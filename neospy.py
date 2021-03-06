import sys
import os
import time
import commands
from datetime import datetime, timedelta
sys.path.append('./')
from config import config
sys.path.append('./python/')
import neoapi
from log import logging

#how mand blocks behind the best block count
RESTART_THRESHOLD = config['restartthreshold']
#avoid restarting within the time after start(minute)
START_SILENT = config['startsilent']
#check interval(second)
INTERVAL = config['interval']
LOCAL_SRV = config['localsrv']

lastRestartTimestamp = datetime.fromtimestamp(0)
restart_cnt = 0

def getBestBlockCount():
    maxHeight = -1
    for seed in config['seeds']:
        height = neoapi.getCurrentHeight('http://' + seed)
        if maxHeight < height:
            maxHeight = height
    logging.info('[getBestBlockCount] maxheight: {0}'.format(maxHeight))
    return maxHeight

def getLocalBlockCount():
    height = neoapi.getCurrentHeight(LOCAL_SRV)
    logging.info('[getLocalBlockCount] localheight: {0}'.format(height))
    return height

def isLocalRunning():
    (state, output) = commands.getstatusoutput('ps -ef | grep "./neo-cli" | wc -l')
    logging.info('[isLocalRunning] shell command, state: {0}, output: {1}'.format(state, output))
    if state != 0:
        height = getLocalBlockCount()
        logging.info('[isLocalRunning] command failed, use rpc getblockcount. height: {0}'.format(height))
        if height < 0:
            return False
        return True
    if int(output) <= 2:
        return False
    return True

def startLocalNode():
    result = os.system('./shell/start.sh {0}'.format(config['neoclipath']))
    if result == 0:
        global lastRestartTimestamp 
        lastRestartTimestamp = datetime.now()
        return True
    return False

def stopLocalNode():
    result = os.system('./shell/stop.sh')
    if result == 0:
        return True
    os.system('ps -ef | grep "./neo-cli" | awk \'{print $2}\' | xargs kill')
    return True

def restartRecently():
    if timedelta(minutes=START_SILENT) < datetime.now() - lastRestartTimestamp:
        return True
    return False

while True:
    if not isLocalRunning():
        startLocalNode()
        continue
    time.sleep(INTERVAL)
    localBlockCount = getLocalBlockCount()
    bestBlockCount = getBestBlockCount()
    if localBlockCount < 0 or bestBlockCount < 0:
        logging.error('[wrongheight] wrong height, localheight: {0}, bestheight: {1}'.format(localBlockCount, bestBlockCount))
        continue
    if RESTART_THRESHOLD < bestBlockCount - localBlockCount and not restartRecently():
        restart_cnt += 1
        logging.warning('[restart] restarting, restart_cnt: {0}, localheight: {1}, bestheight: {2}'.format(restart_cnt, localBlockCount, bestBlockOount))
        stopLocalNode()