import yarl
from bs4 import BeautifulSoup
from html import unescape, escape
import re
import m3u8 as _m3u8
import json
import regex as regex_original
from typing import Literal, Union, List, Dict, Any

def load(string: str, escaped: bool = True, error_1: bool = True, iterate: bool = False) -> Union[Dict, str]:
    """
    Load a string as JSON (dict).
    
    :param string: string to load as json (dict)
    :param escaped: if true it will try to unescape the string and then load it as json
    :param error_1: if true it will not print the error
    :param iterate: if true iterates over the keys in the dict and if the value is a string and contains { and } then it tries to load it as json
    :return: dict if valid json otherwise original string
    """
    if escaped:
        string = load(string, escaped=False, iterate=iterate, error_1=error_1)
        if isinstance(string, str):
            string = unescape(string)
            string = load(string, escaped=False, iterate=iterate, error_1=error_1)
            if isinstance(string, str):
                _string = string.replace("\\\"", "\"").replace("\\\\", "/")
                _string = load(_string, escaped=False, iterate=iterate, error_1=error_1)
                if isinstance(_string, dict):
                    string = _string
    else:
        try:
            string = json.loads(string)
        except Exception as e:
            if not error_1:
                print(e)
    try:
        if isinstance(string, str):
            return string
        if iterate and isinstance(string, dict):
            for key in string:
                if isinstance(string[key], str) and "{" in string[key] and "}" in string[key]:
                    string[key] = load(string[key], escaped=escaped, iterate=iterate, error_1=error_1)
                elif isinstance(string[key], dict):
                    string[key] = load(string[key], escaped=escaped, iterate=iterate, error_1=error_1)
    except Exception as e:
        if not error_1:
            print(e)
    return string


def stringify(string: Dict, escaped: bool = False) -> str:
    """
    Convert a dictionary to a string.
    
    :param string: dict to stringify
    :param escaped: if true it will escape the string
    :return: stringified dict
    """
    # Note: modifying input dict in place is dangerous, but keeping original behavior for now
    # except making a copy if needed? No, original code modified it.
    # But wait, original code:
    # for key in string: if type(string[key]) == dict: string[key] = stringify(string[key], escaped)
    # This recursively stringifies nested dicts?
    # And then json.dumps the whole thing.
    
    # Let's keep it but maybe safer to copy? 
    # Original:
    # for key in string:
    #    if type(string[key]) == dict:
    #        string[key] = stringify(string[key], escaped)
    # string = json.dumps(string)
    
    # If I pass a dict, it modifies it in place!
    # I should probably fix this side effect if I can, but it might break usage.
    # I'll keep it but add type hint.
    
    for key in string:
        if isinstance(string[key], dict):
            string[key] = stringify(string[key], escaped)
    result = json.dumps(string)
    if escaped:
        result = escape(result)
    return result


def html(string: str) -> BeautifulSoup:
    """
    Parse HTML string.
    :param string: HTML string
    :return: BeautifulSoup object
    """
    return BeautifulSoup(string, "html.parser")


def xml(string: str) -> BeautifulSoup:
    """
    Parse XML string.
    :param string: XML string
    :return: BeautifulSoup object
    """
    return BeautifulSoup(string, "xml")


def reg_compile(pattern: str):
    return regex_original.compile(pattern)


def regex(string: str, pattern: str) -> List[str]:
    """
    Clean string and find all regex matches.
    """
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
    return [a for a in a_matches if a]

def get_val_js_var(var_name: str, content: str, val_type: Literal["str", "int", "float", "bool"] = "str", mode: Literal["dict", "var"]="dict", minimal: bool = True, require_end_semi: bool = False) -> Union[str, int, float, bool, None]:
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
    
    # Removed print(pattern) to reduce noise
    match = regex(content, pattern)
    if match:
        val = match[0]
        val = val.strip().strip('"').strip("'")
        if val_type == "int":
            return int(val)
        elif val_type == "float":
            return float(val)
        elif val_type == "bool":
            return val.lower() in ["true", "1", "yes"]
        return val
    return None

def js(string: str) -> Dict:
    import js2xml
    import xmltodict
    xml_data = js2xml.parse(string)
    json_data = load(json.dumps(xmltodict.parse(xml_data.toxml()), indent=4))
    return json_data


def m3u8(string: str):
    """
    Parse m3u8 playlist.
    :param string: content of m3u8 file
    :return: m3u8.parse(playlist)
    """
    return _m3u8.parse(string)

def parse_m3u8(string: str):
    """Alias for m3u8"""
    return m3u8(string)


def m3u8_master(string: str, key_plus: str = "p") -> Dict[str, str]:
    """
    Parse master m3u8 playlist to get resolutions and URLs.
    :param string: the content of the m3u8 file
    :param key_plus: suffix for resolution key (default 'p')
    :return: dict like {"720p": "url", ...}
    """
    ret = {
        video["stream_info"]["resolution"].lower().split("x")[-1] + key_plus: video['uri']
        for video in m3u8(string)['playlists']
    }
    return ret


def reg_replace(pattern: str, sub: str, string: str) -> str:
    """
    Regex replace.
    :param pattern: regex pattern
    :param sub: replacement string
    :param string: input string
    :return: string with replacements
    """
    return re.sub(pattern, sub, string)


def URL(string: str) -> yarl.URL:
    return yarl.URL(string)


def re_compile(string: str):
    return re.compile(string)


def seconds_to_read(secs: int) -> str:
    """
    Convert seconds to human readable string.
    :param secs: seconds
    :return: x day(s) x hours(s) x minute(s) x second(s)
    """
    days = secs // 86400
    hours = (secs - days * 86400) // 3600
    minutes = (secs - days * 86400 - hours * 3600) // 60
    seconds = secs - days * 86400 - hours * 3600 - minutes * 60
    
    parts = []
    if days:
        parts.append("{0} day{1}".format(days, "s" if days != 1 else ""))
    if hours:
        parts.append("{0} hour{1}".format(hours, "s" if hours != 1 else ""))
    if minutes:
        parts.append("{0} minute{1}".format(minutes, "s" if minutes != 1 else ""))
    if seconds:
        parts.append("{0} second{1}".format(seconds, "s" if seconds != 1 else ""))
        
    return ", ".join(parts)

def secondsToRead(secs: int) -> str:
    """Alias for seconds_to_read"""
    return seconds_to_read(secs)


def seconds_to_text(secs: int) -> str:
    """
    Convert seconds to (DD):HH:MM:SS format.
    :param secs: seconds
    :return: (DD):HH:MM:SS
    """
    days = secs // 86400
    hours = (secs - days * 86400) // 3600
    minutes = (secs - days * 86400 - hours * 3600) // 60
    seconds = secs - days * 86400 - hours * 3600 - minutes * 60
    
    result = ""
    if days:
        result += "{0}:".format(days)
    
    # Always show hours if days are present? Original code:
    # ("{0}:".format(hours) if hours else "00:")
    # It seems to always show HH:MM:SS at least.
    
    result += "{0:02d}:".format(hours)
    result += "{0:02d}:".format(minutes)
    result += "{0:02d}".format(seconds)
    
    return result

def secondsToText(secs: int) -> str:
    """Alias for seconds_to_text"""
    return seconds_to_text(secs)
