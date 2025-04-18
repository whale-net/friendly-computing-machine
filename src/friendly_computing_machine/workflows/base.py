from abc import ABC, abstractmethod
from typing import Any, Optional

from temporalio.client import (
    Schedule,
    ScheduleActionStartWorkflow,
    ScheduleSpec,
    ScheduleState,
)

from friendly_computing_machine.workflows.util import get_temporal_queue_name


class AbstractScheduleWorkflow(ABC):
    @abstractmethod
    async def run(self, wf_arg: Optional[Any] = None):
        """
        The main entry point for the workflow.

        Sorry that it has to be this way, but it makes things easier for me
        NOTE: the async
        """
        pass

    @abstractmethod
    def get_schedule_spec(self) -> ScheduleSpec:
        """
        Get the schedule spec for the workflow.

        Example:
        ```python
        return ScheduleSpec(
            intervals=[ScheduleIntervalSpec(every=timedelta(minutes=2))]
        ),
        ```
        """
        pass

    def get_schedule_state(self) -> str:
        """
        Return the schedule state for the workflow.
        Intended to be overridden by subclasses.

        Also not really sure what this is or how to use it properly,
        but we will find out soon enough I suppose

        :return: _description_
        """
        # default to nothing for now
        return ScheduleState(note="this is the default note")

    def get_id(self, app_env) -> str:
        # For now, just use the class name. should be fine
        return f"fcm-{app_env}-{self.__class__.__name__}"

    def get_schedule_id(self, app_env: str) -> str:
        return f"wf-schedule-{self.get_id(app_env)}"

    def get_temporal_queue_name(self) -> str:
        return get_temporal_queue_name("main")

    def get_schedule(self, app_env: str, wf_arg: Optional[Any] = None) -> Schedule:
        # TODO - wf_arg is kind of a hack but it is useful for now otherwise
        # calling this multiple time with different arg would break things
        # but could be fixed by hashing it and adding random shit to ids
        # would be a hack, but it'd work at least \(O.o)/

        if wf_arg is not None:
            action = ScheduleActionStartWorkflow(
                self.run,
                wf_arg,
                id=self.get_id(app_env),
                task_queue=self.get_temporal_queue_name(),
            )
        else:
            action = ScheduleActionStartWorkflow(
                self.run,
                id=self.get_id(app_env),
                task_queue=self.get_temporal_queue_name(),
            )

        return Schedule(
            action=action,
            spec=self.get_schedule_spec(),
            # I believe this can be left default but sue me
            state=self.get_schedule_state(),
        )
