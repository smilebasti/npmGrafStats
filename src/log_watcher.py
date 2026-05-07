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
        # Wait for file to exist
        while not os.path.isfile(self._filepath):
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
                        try:
                            self._callback(line)
                        except Exception as e:
                            logger.error("Callback error for %s: %s", self._filepath, e)
                else:
                    # No new data - check for rotation
                    try:
                        if not os.path.isfile(self._filepath):
                            logger.info("File removed, waiting for recreation: %s", self._filepath)
                            return  # Will re-enter _tail
                        new_inode = os.stat(self._filepath).st_ino
                        if new_inode != inode:
                            logger.info("File rotated: %s", self._filepath)
                            return  # Will re-enter _tail
                    except OSError:
                        return  # File gone, retry

                    self._stop.wait(0.1)
