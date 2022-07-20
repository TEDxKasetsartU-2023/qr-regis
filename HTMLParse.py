# html parser for variables html mail sender
# | IMPORT SECTION
import re
from typing import Dict, List

# | FUNCIONS 
def text2list(html_text: str, pattern: str) -> List[str]:
    """
    convert text to list by regex
    """
    return re.findall(pattern, html_text)

def list2dct(variable_lst: List[str]) -> Dict[str, str]:
    """
    convert list to dict ({{var}} -> var)
    """
    dct = {}
    for i in variable_lst:
        dct[i] = i[2:-2]
    
    return dct

def html_parse(html_filename: str, pattern: str, variable_dct: Dict[str, str]) -> str:
    """
    open html -> get list -> get dict -> replace all var in html
    """
    with open(html_filename, "rt", encoding="utf-8-sig") as file:
        data = file.read()
        lst = text2list(data, pattern)
        dct = list2dct(lst)
    
    for v, v_name in dct.items():
        data = data.replace(v, variable_dct[v_name])
    
    return data

# | MAIN SECTION
if __name__ == "__main__":
    print(html_parse("./mail.html", "{{\w*}}", {"name": "NAME", "code": "CODE"}))
