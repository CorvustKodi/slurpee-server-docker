#!/usr/bin/python

import re,os

CHARS_TO_REMOVE = ["\'"]

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
    # First try, look for the form sNNeMM
    season = 0
    episode = 0
    match = re.search('s([0-9]+)[\W]?e([0-9]+)',str(filename).lower())
    if match:
        season = int(match.group(1))
        episode = int(match.group(2))
        # Next look for NN*MM
    else:
        match = re.search('([0-9]+)[a-z]([0-9]+)',str(filename).lower())
        if match:
            # Next look for NNMM
            season = int(match.group(1))
            episode = int(match.group(2))
        else:
            match = re.search("[ .]([0-9]{3,4})[ .]",str(filename).lower())
            if match:
                season = int(match.group(1))/100
                episode = int(match.group(1))%100                
            else: # Next try season NN episode MM
                match = re.search("season[ .]*([0-9]+)[ .]*episode[ ]*([0-9]+)",str(filename).lower())
    return season, episode

def getExtension(filename):
    toks = str(filename).split('.')
    ret = '.err'
    if len(toks) > 1:
        ret = toks[len(toks)-1]
    return ret

def hasEpisodeInDir(dir_path,season,episode):
    for f in os.listdir(dir_path):
        ep_info = parseEpisode(f)
        if season == ep_info[0] and episode == ep_info[1]: 
            return True
    return False

if __name__ == '__main__':
  import sys
  print(fuzzyMatch(sys.argv[1],sys.argv[2]))
