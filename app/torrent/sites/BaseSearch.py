import re
import socket
import requests

socket.setdefaulttimeout(15)

class BaseSearch:
    def __init__(self):
        return NotImplemented
    def search(self, terms, settings):
        return NotImplemented
