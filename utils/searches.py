import re


# returns a level group with current level
level: re.Pattern = re.compile(
    r"^You have gained a level! Welcome to level (?P<level>\d+)!$"
)
