#!/usr/bin/python

import re,os

CHARS_TO_REMOVE = ["\'",":"]

def sanitizeString(s):
    # Remove unusual characters
    sanitized = str(s)
    for sc in CHARS_TO_REMOVE:
        sanitized = sanitized.replace(sc,'')    
    return sanitized

def fuzzyMatch(targetName, f):
    sanitizedTarget = sanitizeString(targetName)
    sanitizedFile = sanitizeString(f)
    terms = sanitizedTarget.lower().replace('.',' ').split(' ')
    query_str = ''
    for term in terms:
        if term != '':
            if query_str != '':
                query_str = query_str+'[ .]+'
            query_str = query_str + re.escape(term)
    query_str = query_str + '.*'
    match = re.search(query_str,sanitizedFile.lower())
    if match:
        return f
    return None  

def parseEpisode(filename):
    season = 0
    episode = 0
    # First try, look for the form sNNeMM
    match = re.search('s([0-9]+)[\W]?e([0-9]+)',str(filename).lower())
    if match:
        season = int(match.group(1))
        episode = int(match.group(2))
    if not season and not episode:
        # Next look for NN*MM
        match = re.search('([0-9]+)[a-z]([0-9]+)',str(filename).lower())
        if match:
            season = int(match.group(1))
            episode = int(match.group(2))
    if not season and not episode:
            # Next look for NNMM
        match = re.search("[ .]([0-9]{3,4})[ .]",str(filename).lower())
        if match:
            # The episode is going the be the last 2 digits, the season will be what's left
            episode = int(match.group(1)[-2:])
            season = int(match.group(1)[:-2])
    if not season and not episode:
        # Next try season NN episode MM
        match = re.search("season[ .]*([0-9]+)[ .]*episode[ ]*([0-9]+)",str(filename).lower())
        if match:
            season = int(match.group(1))
            episode = int(match.group(2))

    return season, episode

def getExtension(filename):
    toks = str(filename).split('.')
    ret = '.err'
    if len(toks) > 1:
        ret = toks[len(toks)-1]
    return ret

def hasEpisodeInDir(dir_path,season,episode):
    if not os.path.exists(dir_path):
        return False
    for f in os.listdir(dir_path):
        ep_info = parseEpisode(f)
        if season == ep_info[0] and episode == ep_info[1]: 
            return True
    return False

if __name__ == '__main__':
  import sys
  print(fuzzyMatch(sys.argv[1],sys.argv[2]))
