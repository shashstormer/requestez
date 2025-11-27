import yarl
from bs4 import BeautifulSoup
from html import unescape, escape
import re
import m3u8 as _m3u8
import json
import regex as regex_original
from typing import Literal


def load(string, escaped=True, error_1=True, iterate=False):
    """
    :param string: string to load as json (dict)
    :param escaped: if true it will try to unescape the string and then load it as json
    :param error_1: if true it will not print the error
    :param iterate: if true iterates over the keys in the dict and if the value is a string and contains { and } then it tries to load it as json
    :return: dict if valid json otherwise original
    """
    if escaped:
        string = load(string, escaped=False, iterate=iterate, error_1=error_1)
        if type(string) == str:
            string = unescape(string)
            string = load(string, escaped=False, iterate=iterate, error_1=error_1)
            if type(string) == str:
                _string = string.replace("\\\"", "\"").replace("\\\\", "/")
                _string = load(_string, escaped=False, iterate=iterate, error_1=error_1)
                if type(_string) == dict:
                    string = _string
    else:
        try:
            string = json.loads(string)
        except Exception as e:
            if error_1:
                pass
            else:
                print(e)
    try:
        if type(string) == str:
            return string
        if iterate:
            for key in string:
                if (type(string[key]) == str) and ("{" in string[key]) and ("}" in string[key]):
                    string[key] = load(string[key], escaped=escaped, iterate=iterate, error_1=error_1)
                elif type(string[key] == dict):
                    string[key] = load(string[key], escaped=escaped, iterate=iterate, error_1=error_1)
    except Exception as e:
        if error_1:
            pass
        else:
            print(e)
    return string


def stringify(string, escaped=False):
    """

    :param string: dict to stringify
    :param escaped: if true it will escape the string
    :return: stringified dict
    """
    for key in string:
        if type(string[key]) == dict:
            string[key] = stringify(string[key], escaped)
    string = json.dumps(string)
    if escaped:
        string = escape(string)
    return string


def html(string):
    """
    :param string:
    :return: beautifulsoup object
    """
    string = BeautifulSoup(string, "html.parser")
    return string


def xml(string):
    string = BeautifulSoup(string, "xml")
    return string


def reg_compile(pattern):
    return regex_original.compile(pattern)


def regex(string, pattern):
    string = string.replace('\r', '').replace('\n', '').replace('\t', '') \
        .replace('\\/', '/').replace('&amp;', '&') \
        .replace('&#039;', "'").replace('&#8211;', '-') \
        .replace('&#8212;', '-').replace('&eacute;', 'é') \
        .replace('&acirc;', 'â').replace('&ecirc;', 'ê') \
        .replace('&icirc;', 'î').replace('&ocirc;', 'ô') \
        .replace('&hellip;', '...').replace('&quot;', '"') \
        .replace('&gt;', '>').replace('&egrave;', 'è') \
        .replace('&ccedil;', 'ç').replace('&laquo;', '<<') \
        .replace('&raquo;', '>>').replace('\xc9', 'E') \
        .replace('&ndash;', '-').replace('&ugrave;', 'ù') \
        .replace('&agrave;', 'à').replace('&lt;', '<') \
        .replace('&rsquo;', "'").replace('&lsquo;', '\'') \
        .replace('&nbsp;', '').replace('&#8217;', "'") \
        .replace('&#8230;', '...').replace('&#8242;', "'") \
        .replace('&#884;', '\'').replace('&#39;', '\'') \
        .replace('&#038;', '&').replace('&iuml;', 'ï') \
        .replace('&#8220;', '"').replace('&#8221;', '"') \
        .replace('–', '-').replace('—', '-').replace('&#58;', ':') \
        .replace(" : ", ":").replace(" :", ":").replace(": ", ":")
    string = re.sub(" *: *", ":", string)
    a_matches = re.compile(pattern, re.IGNORECASE).findall(string)
    a_matches = [a for a in a_matches if a]
    return a_matches

def get_val_js_var(var_name, content, val_type: Literal["str", "int", "float", "bool"] = "str", mode: Literal["dict", "var"]="dict", minimal=True, require_end_semi=False):
    """
    Finds value of variable from js style dictionary/var in HTML
    """
    pattern = ""
    if mode == "dict":
        if val_type == "str":
            pattern = rf"(?:{var_name}\s*:\s*(?:\"|')(.*?)(?:\"|')),"
        elif val_type == "int":
            pattern = rf"(?:{var_name}\s*:\s*(\d+)),"
        elif val_type == "float":
            pattern = rf"(?:{var_name}\s*:\s*(\d+\.\d+)),"""
    elif mode == "var":
        pattern = rf"{var_name}\s*=\s*(.*);"
        if minimal:
            pattern = rf"{var_name}\s*=\s*(.*?);"
        if not require_end_semi:
            pattern += "?"
    print(pattern)
    match = regex(content, pattern)
    if match:
        match = match[0]
        val = match
        val = val.strip().strip('"').strip("'")
        if val_type == "int":
            return int(val)
        elif val_type == "float":
            return float(val)
        elif val_type == "bool":
            return val.lower() in ["true", "1", "yes"]
        return val
    return None

def js(string):
    import js2xml
    import xmltodict
    xml_data = js2xml.parse(string)
    json_data = load(json.dumps(xmltodict.parse(xml_data.toxml()), indent=4))
    return json_data


def m3u8(string):
    """

    :param string:
    :return: m3u8.parse(playlist)
    """
    return _m3u8.parse(string)


def m3u8_master(string, key_plus="p"):
    """
    :param string: the content of the m3u8 file
    :param key_plus: the p in the end of the 720p in the return exapmle is added as the key_plus default is p
    :return: example {"720p": "https://example.com/720p.m3u8", "480p": "https://example.com/480p.m3u8"}
    """
    ret = {
        video["stream_info"]["resolution"].lower().split("x")[-1] + key_plus: video['uri']
        for video in m3u8(string)['playlists']
    }
    return ret


def reg_replace(pattern, sub, string):
    """

    :param pattern: what patterns to replace
    :param sub: what to substiruite it with
    :param string: what is the string that needs to be checked and replaced
    :return:
    """
    return re.sub(pattern, sub, string)


def URL(string):
    return yarl.URL(string)


def re_compile(string):
    return re.compile(string)


def secondsToRead(secs):
    """

    :param secs:
    :return: x day(s) x hours(s) x minute(s) x second(s)
    """
    days = secs // 86400
    hours = (secs - days * 86400) // 3600
    minutes = (secs - days * 86400 - hours * 3600) // 60
    seconds = secs - days * 86400 - hours * 3600 - minutes * 60
    result = ("{0} day{1}, ".format(days, "s" if days != 1 else "") if days else "") + \
             ("{0} hour{1}, ".format(hours, "s" if hours != 1 else "") if hours else "") + \
             ("{0} minute{1}, ".format(minutes, "s" if minutes != 1 else "") if minutes else "") + \
             ("{0} second{1}, ".format(seconds, "s" if seconds != 1 else "") if seconds else "")
    return result


def secondsToText(secs):
    """

    :param secs:
    :return: (DD):HH:MM:SS
    """
    days = secs // 86400
    hours = (secs - days * 86400) // 3600
    minutes = (secs - days * 86400 - hours * 3600) // 60
    seconds = secs - days * 86400 - hours * 3600 - minutes * 60
    result = ("{0}:".format(days) if days else "") + \
             ("{0}:".format(hours) if hours else "00:") + \
             ("{0}:".format(minutes) if minutes else "00:") + \
             ("{0}".format(seconds) if seconds else "00")
    return result


if __name__ == "__main__":
    pass
