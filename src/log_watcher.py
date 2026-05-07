"""Tail -F equivalent: watch log files for new lines, handle rotation."""

import logging
import os
import time
import threading

logger = logging.getLogger(__name__)


class LogWatcher:
    """Watches a single log file, calling callback for each new line.
    Handles log rotation (file deleted/recreated)."""

    def __init__(self, filepath: str, callback, stop_event: threading.Event):
        self._filepath = filepath
        self._callback = callback
        self._stop = stop_event

    def run(self):
        logger.info("Watching: %s", self._filepath)
        while not self._stop.is_set():
            try:
                self._tail()
            except Exception as e:
                logger.error("Error watching %s: %s", self._filepath, e)
                if self._stop.wait(2):
                    break

    def _tail(self):
        # Wait for file to exist AND be readable. os.path.isfile silently
        # returns False on permission denial (common when a parent dir is
        # mode 0700 and we run as a different uid), so we probe with os.access
        # and log a warning every minute so the cause is obvious.
        complaint_interval = 60
        last_complaint = 0.0
        while True:
            if self._stop.is_set():
                return
            exists = os.path.exists(self._filepath)
            readable = exists and os.access(self._filepath, os.R_OK)
            if readable:
                break
            now = time.monotonic()
            if now - last_complaint >= complaint_interval:
                if not exists:
                    logger.warning("Log file missing or unreachable: %s "
                                   "(parent dir may be unreadable to this user)",
                                   self._filepath)
                else:
                    logger.warning("Log file exists but is not readable: %s "
                                   "(check file/directory permissions; e.g. NPMplus "
                                   "writes /data/logs as root mode 0700, run npmgraf as root)",
                                   self._filepath)
                last_complaint = now
            if self._stop.wait(1):
                return

        with open(self._filepath, "r") as f:
            # Seek to end
            f.seek(0, 2)
            inode = os.fstat(f.fileno()).st_ino

            while not self._stop.is_set():
                line = f.readline()
                if line:
                    line = line.rstrip("\n")
                    if line:
                        logger.debug("Read line from %s: %.200s", self._filepath, line)
                        try:
                            self._callback(line)
                        except Exception as e:
                            logger.error("Callback error for %s: %s", self._filepath, e)
                else:
                    # No new data - check for rotation (rename or copytruncate)
                    try:
                        if not os.path.isfile(self._filepath):
                            logger.info("File removed, waiting for recreation: %s", self._filepath)
                            return  # Will re-enter _tail
                        st = os.stat(self._filepath)
                        if st.st_ino != inode:
                            logger.info("File rotated (rename): %s", self._filepath)
                            return  # Will re-enter _tail
                        if st.st_size < f.tell():
                            logger.info("File truncated (copytruncate rotation): %s", self._filepath)
                            f.seek(0)
                            continue
                    except OSError:
                        return  # File gone, retry

                    self._stop.wait(0.1)
