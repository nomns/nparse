from datetime import datetime

def parse_line(line: str):
    """
    Parses and then returns an everquest log entry's date and text.
    """
    index = line.find("]") + 1
    sdate = line[1:index-1].strip()
    text = line[index:].strip()
    return datetime.strptime(sdate, '%a %b %d %H:%M:%S %Y'), text
