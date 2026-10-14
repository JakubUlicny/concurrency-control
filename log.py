import logging
from logging.handlers import TimedRotatingFileHandler
import os

logger = logging.getLogger("mylogger")
logger.setLevel(logging.INFO)

file_formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s"
)

logfolder="/var/log/app/"
os.makedirs(logfolder, exist_ok=True)

# ================= INFO：keep 7 days =================
info_handler = TimedRotatingFileHandler(
    filename=logfolder+"info.log",
    when="D",
    interval=1,
    backupCount=7,        
    encoding="utf-8"
)
info_handler.setLevel(logging.INFO)
info_handler.addFilter(lambda r: r.levelno == logging.INFO)
info_handler.setFormatter(file_formatter)

# ================= WARNING：always keep =================
warning_handler = logging.FileHandler(
    logfolder+"warning.log", encoding="utf-8"
)
warning_handler.setLevel(logging.WARNING)
warning_handler.addFilter(lambda r: r.levelno == logging.WARNING)
warning_handler.setFormatter(file_formatter)
# ================= ERROR：always keep =================
error_handler = logging.FileHandler(
    logfolder+"error.log", encoding="utf-8"
)
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(file_formatter)



# -------------------------------------------------------------------
# terminal output set
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

console_formatter = logging.Formatter(
    "%(message)s"
)
console_handler.setFormatter(console_formatter)


# -------------------------------------------------------------------
logger.addHandler(console_handler)
logger.addHandler(info_handler)
logger.addHandler(warning_handler)
logger.addHandler(error_handler)
