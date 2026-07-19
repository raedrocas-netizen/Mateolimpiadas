import io
import os
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from helpers.performance import (
    begin_operation,
    current_context,
    finish_operation,
    record_socket_payload,
)


class PerformanceInstrumentationTests(unittest.TestCase):

    def test_instrumentation_is_disabled_by_default(self):
        with patch.dict(os.environ, {}, clear=True):
            context, token = begin_operation("GET /juez/login", kind="http")

        self.assertIsNone(context)
        self.assertIsNone(token)
        self.assertIsNone(current_context())

    def test_socket_payload_log_records_size_but_not_content(self):
        secret_value = "respuesta-que-no-debe-aparecer"
        output = io.StringIO()

        with patch.dict(os.environ, {"PERFORMANCE_LOGS": "1"}, clear=False):
            context, token = begin_operation("SocketIO prueba", kind="socket")
            record_socket_payload("estado_sala", {
                "message": "estado publico",
                "private_test_value": secret_value,
            })

            with redirect_stdout(output):
                finish_operation(context, token)

        log = output.getvalue()
        self.assertIn("Payload Socket.IO:", log)
        self.assertIn("estado_sala", log)
        self.assertNotIn(secret_value, log)
        self.assertGreater(
            context.socket_payloads["estado_sala"]["bytes"],
            0
        )


if __name__ == "__main__":
    unittest.main()
