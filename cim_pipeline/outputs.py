import abc
import json
import logging
import sqlite3
from dataclasses import asdict, is_dataclass
from typing import List

from .models import Config, ResultRecord


class OutputBase(abc.ABC):
    """
    Abstract base class for output handlers.

    Subclasses must implement the write() method to persist results.
    """

    def __init__(self, config: Config, logger: logging.Logger):
        """
        Initializes the output handler.

        Args:
            config (Config): The application configuration object.
            logger (logging.Logger): The logger for status and error messages.
        """
        self.config = config
        self.logger = logger
        self.output_path = config.output_file

    @abc.abstractmethod
    def write(self, results: List[ResultRecord]) -> None:
        """
        Persist result records to the output destination.

        Args:
            results (List[ResultRecord]): A list of result records to write.
        """
        raise NotImplementedError


class JsonOutput(OutputBase):
    """
    Output handler for writing results to a JSON file.
    """

    def write(self, results: List[ResultRecord]) -> None:
        if not self.output_path:
            self.logger.error(
                "JSON output requested but no output file path was provided."
            )
            return

        if results and is_dataclass(results[0]):
            output_data = [asdict(record) for record in results]
        else:
            output_data = [record.__dict__ for record in results]

        try:
            with open(self.output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=4)
            self.logger.info(
                f"Successfully wrote {len(results)} records to "
                f"{self.output_path}"
            )
        except IOError as e:
            self.logger.error(
                f"Failed to write to JSON file at {self.output_path}: {e}"
            )


class SqliteOutput(OutputBase):
    """
    Output handler for writing results to a SQLite database.

    Manages the connection lifecycle within the write method to ensure
    resources are properly handled.
    """

    def _create_table(self, conn: sqlite3.Connection):
        """Creates the results table if it doesn't already exist."""
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_case TEXT,
                result TEXT,
                bundle INTEGER,
                cim_url TEXT,
                timestamp TEXT,
                platform TEXT
            )
        ''')
        conn.commit()

    def write(self, results: List[ResultRecord]) -> None:
        if not self.output_path:
            self.logger.error(
                "SQLite output requested but no database path was provided."
            )
            return

        try:
            with sqlite3.connect(self.output_path) as conn:
                self._create_table(conn)

                cursor = conn.cursor()
                data_to_insert = [
                    (
                        r.test_case,
                        r.result,
                        r.bundle,
                        r.cim_url,
                        r.timestamp,
                        r.platform
                    )
                    for r in results
                ]

                cursor.executemany(
                    '''
                    INSERT OR IGNORE INTO results (
                        test_case, result, bundle, cim_url, timestamp, platform
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    ''',
                    data_to_insert
                )

                conn.commit()
                rowcount = cursor.rowcount
                self.logger.info(
                    f"Wrote {rowcount} new records to {self.output_path}"
                )

        except sqlite3.Error as e:
            self.logger.error(
                f"An error occurred with the SQLite database at "
                f"{self.output_path}: {e}"
            )
