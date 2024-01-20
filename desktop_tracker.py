import logging
import os
import subprocess
import time
from datetime import datetime, timezone


date_format = '%Y-%m-%d %H:%M:%S'
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] %(message)s', datefmt=date_format)


class LastOpenedResolver:

    local_timezone = datetime.now(timezone.utc).astimezone().tzinfo
    NULL_VALUE = '(null)'

    @classmethod
    def convert_to_local_timezone(cls, last_opened_date: str) -> str:
        last_used_datetime = datetime.strptime(last_opened_date, f'{date_format} %z')

        last_used_local = last_used_datetime.astimezone(cls.local_timezone)

        return last_used_local.strftime(date_format)

    @classmethod
    def get_last_opened_time(cls, file_path: str) -> str | None:
        # Run mdls command to get the last used date. Specific for MacOS.
        mdls_output = subprocess.check_output(['mdls', '-name', 'kMDItemLastUsedDate', file_path])

        # Decode the output and extract the last used date
        last_opened_date = mdls_output.decode().partition('= ')[2].strip()
        if last_opened_date == cls.NULL_VALUE:
            return None

        return cls.convert_to_local_timezone(last_opened_date)


class MonitorOpened:

    def __init__(self, root_path: str):
        self.root_path: str = root_path
        self.path_to_last_opened: dict[str, str] = {}

        for path in os.listdir(root_path):
            last_opened = LastOpenedResolver.get_last_opened_time(os.path.join(root_path, path))
            if last_opened:
                self.path_to_last_opened[path] = last_opened

    def monitor_directory(self):

        while True:
            listed = set(os.listdir(self.root_path))
            for path, last_opened in self.path_to_last_opened.items():
                # only monitors those files and directories that existed at program start
                if path in listed:
                    # if path was not deleted, renamed or moved
                    current_opened_time = LastOpenedResolver.get_last_opened_time(os.path.join(self.root_path, path))
                    if current_opened_time != last_opened:
                        logging.info(f"Opened directory or file: {path} at {current_opened_time}")
                        # change last opened time to track whether the path is opened again
                        self.path_to_last_opened[path] = current_opened_time

            time.sleep(1)


if __name__ == "__main__":
    start_time = datetime.now()
    logging.info(f"Monitoring started at {start_time}")

    root_path_to_monitor = os.path.expanduser('~/Desktop')
    monitor = MonitorOpened(root_path_to_monitor)

    try:
        monitor.monitor_directory()
    except KeyboardInterrupt:
        pass
    finally:
        end_time = datetime.now()
        logging.info(f"Monitoring stopped at {end_time}")
        logging.info(f"Total runtime: {end_time - start_time}")
