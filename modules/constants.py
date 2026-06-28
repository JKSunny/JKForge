STEP_SKIPPED    = -1
STEP_WAITING    = 0
STEP_DONE       = 1
STEP_FAILED     = 2
STEP_RUNNING    = 3

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

REQUIRED_BASE_FILES = [
    "assets0.pk3",
    "assets1.pk3",
    "assets2.pk3",
    "assets3.pk3",
]