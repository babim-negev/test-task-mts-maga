from ansible import constants as C
from ansible.plugins.callback.default import (
    CallbackModule as DefaultCallbackModule,
    DOCUMENTATION as DEFAULT_DOCUMENTATION,
)


DOCUMENTATION = DEFAULT_DOCUMENTATION.replace("name: default", "name: kyverno_mvp_readable", 1)


class CallbackModule(DefaultCallbackModule):
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = "stdout"
    CALLBACK_NAME = "kyverno_mvp_readable"

    def v2_runner_on_ok(self, result):
        msg = result.result.get("msg")

        if isinstance(msg, str) and msg.startswith("Добавьте эти записи в /etc/hosts"):
            if self._last_task_banner != result.task._uuid:
                self._print_task_banner(result.task)

            self._handle_warnings_and_exception(result)
            self._display.display(msg.rstrip(), color=C.COLOR_OK)
            return

        super().v2_runner_on_ok(result)
