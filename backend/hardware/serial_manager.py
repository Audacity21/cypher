import json
import queue
import threading
import time
import uuid

import serial


class SerialManager:
    def __init__(
        self,
        port: str,
        baud_rate: int = 115200,
        timeout: float = 2.0,
    ):
        self.port = port
        self.baud_rate = baud_rate
        self.timeout = timeout

        self.connection = None
        self.reader_thread = None
        self.running = False

        self.pending_responses = {}
        self.pending_lock = threading.Lock()
        self.write_lock = threading.Lock()

        self.event_queue = queue.Queue()

    def connect(self):
        print(
            f"Connecting to Cypher hardware on {self.port}..."
        )

        self.connection = serial.Serial(
            port=self.port,
            baudrate=self.baud_rate,
            timeout=0.2,
        )

        time.sleep(2)

        self.running = True

        self.reader_thread = threading.Thread(
            target=self._reader_loop,
            daemon=True,
        )

        self.reader_thread.start()

        print("Cypher hardware connected.")

    def disconnect(self):
        self.running = False

        if self.reader_thread:
            self.reader_thread.join(
                timeout=1
            )

        if (
            self.connection
            and self.connection.is_open
        ):
            self.connection.close()

        print(
            "Cypher hardware disconnected."
        )

    def send_command(
        self,
        command: str,
        args: dict | None = None,
    ):
        if (
            not self.connection
            or not self.connection.is_open
        ):
            raise RuntimeError(
                "Arduino is not connected."
            )

        command_id = str(
            uuid.uuid4()
        )

        response_queue = queue.Queue(
            maxsize=1
        )

        with self.pending_lock:
            self.pending_responses[
                command_id
            ] = response_queue

        message = {
            "type": "cmd",
            "id": command_id,
            "cmd": command,
        }

        if args is not None:
            message["args"] = args

        serialized = json.dumps(
            message,
            separators=(",", ":"),
        ) + "\n"

        with self.write_lock:
            self.connection.write(
                serialized.encode(
                    "utf-8"
                )
            )

        try:
            response = (
                response_queue.get(
                    timeout=self.timeout
                )
            )

            return response

        except queue.Empty:
            raise TimeoutError(
                f"Timed out waiting for response to {command}"
            )

        finally:
            with self.pending_lock:
                self.pending_responses.pop(
                    command_id,
                    None,
                )

    def get_event(
        self,
        timeout=None,
    ):
        try:
            return self.event_queue.get(
                timeout=timeout
            )

        except queue.Empty:
            return None

    def _reader_loop(self):
        while self.running:
            try:
                raw = (
                    self.connection.readline()
                )

                if not raw:
                    continue

                line = raw.decode(
                    "utf-8",
                    errors="replace",
                ).strip()

                if not line:
                    continue

                try:
                    message = json.loads(
                        line
                    )

                except json.JSONDecodeError:
                    print(
                        f"Ignoring invalid JSON: {line}"
                    )
                    continue

                self._route_message(
                    message
                )

            except serial.SerialException as error:
                print(
                    f"Serial error: {error}"
                )

                self.running = False

            except Exception as error:
                print(
                    f"Reader error: {error}"
                )

    def _route_message(
        self,
        message,
    ):
        message_type = (
            message.get("type")
        )

        if message_type == "resp":
            command_id = (
                message.get("id")
            )

            if not command_id:
                print(
                    "Received response without id"
                )
                return

            with self.pending_lock:
                response_queue = (
                    self.pending_responses.get(
                        command_id
                    )
                )

            if response_queue:
                response_queue.put(
                    message
                )

            else:
                print(
                    f"Received response for unknown id: {command_id}"
                )

        elif message_type == "event":
            self.event_queue.put(
                message
            )

        elif message_type == "ready":
            print(
                "Arduino READY:",
                message,
            )

        else:
            print(
                "Unknown message:",
                message,
            )
