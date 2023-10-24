import base64
from .unpack import PACKER
import re


def DEJUICE(content):
    def find_single_match(data, patron, index=0):
        try:
            if index == 0:
                matches = re.search(patron, data, flags=re.DOTALL)
                if matches:
                    if len(matches.groups()) == 1:
                        return matches.group(1)
                    elif len(matches.groups()) > 1:
                        return matches.groups()
                    else:
                        return matches.group()
                else:
                    return ""
            else:
                matches = re.findall(patron, data, flags=re.DOTALL)
                return matches[index]
        except:
            return ""

    def dejuice(data):
        juiced = find_single_match(data, r'JuicyCodes.Run\((.*?)\);')
        b64_data = juiced.replace('+', '').replace('"', '')
        b64_decode = base64.b64decode(b64_data)
        dejuiced = PACKER(b64_decode)
        return dejuiced

    return dejuice(data=content)
