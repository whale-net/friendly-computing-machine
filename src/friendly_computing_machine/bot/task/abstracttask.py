from datetime import timedelta, datetime
from abc import abstractmethod, ABC
from typing import Optional

from friendly_computing_machine.db.dal import (
    upsert_task,
    get_last_successful_task_instance,
)
from friendly_computing_machine.models.task import (
    TaskCreate,
    Task,
    TaskInstanceCreate,
    TaskInstanceStatus,
)


class AbstractTask(ABC):
    def __init__(self):
        """
        self.
        :param period:
        """

        # RBAR for each task, but that's fine for the volume
        self._task: Task = upsert_task(self.to_task_create())

        last_task_instance = get_last_successful_task_instance(self._task)
        print("last instnace", last_task_instance)
        if last_task_instance is not None:
            self._last_success = last_task_instance.as_of
        else:
            self._last_success = datetime.min
        # default to last success for now
        self._last_attempt = self._last_success

        # internal bool for basic synchronization
        # i think bool updates are atomic in python. at least I hope they are
        # not that i anticipate on running into this situation often; hopefully just in debug
        self._is_running = False

    def should_run(self) -> bool:
        if self._is_running:
            return False
        return self._last_attempt + self.period < datetime.now()

    def run(self, force_run: bool = False, *args, **kwargs) -> TaskInstanceCreate:
        """
        run the task if it should run

        :param force_run: bypass the should_run check
        :param args:
        :param kwargs:
        :return:
        """
        if force_run or self.should_run():
            try:
                self._is_running = True
                self._last_attempt = datetime.now()
                try:
                    status = self._run(*args, **kwargs)
                except Exception as e:
                    # TODO log exception
                    print(e)
                    status = TaskInstanceStatus.EXCEPTION
                self._last_success = datetime.now()
            finally:
                self._is_running = False
        else:
            status = TaskInstanceStatus.SKIPPED

        return self.to_task_instance_create(status=status)

    @abstractmethod
    def _run(self, *args, **kwargs) -> TaskInstanceStatus:
        """
        implement this one, actually does the work
        :return:
        """
        pass

    @property
    @abstractmethod
    def period(self) -> timedelta:
        """
        the period you hope this task will run
        :return:
        """
        pass

    @property
    def task_name(self) -> str:
        return type(self).__name__

    def __hash__(self):
        return self.task_name.__hash__()

    def to_task_create(self) -> TaskCreate:
        # should probably be a class method, but whatever
        return TaskCreate(name=self.task_name)

    def to_task_instance_create(self, status: TaskInstanceStatus) -> TaskInstanceCreate:
        return TaskInstanceCreate(
            task_id=self._task.id,
            # for now, this datetime is set here
            as_of=datetime.now(),
            status=status,
        )


class ScheduledAbstractTask(AbstractTask):  # , ABC):
    def __init__(self):
        super().__init__()

    @property
    @abstractmethod
    def start_date(self) -> datetime:
        """
        When this should run. This date + period will be repeated indefinitely

        Do not use datetime.min, there is no purpose for that. Just use non-scheduled tasks

        """
        pass

    def should_run(self) -> bool:
        if self._is_running:
            return False

        last_expected_run = self.get_last_expected_run_datetime()
        # min signals no run expected
        # this is implicitly checked in the below condition, but better to be explicit
        if last_expected_run == datetime.min:
            return False

        # schedule a run if the last expected run is after our last success
        # this means a run is considered complete if there is any success after an expected run
        # this will allow us to catch up with at most 1 run and not allow any current delay to affect future runs
        return self._last_success < self.get_last_expected_run_datetime()

    def get_last_expected_run_datetime(self) -> datetime:
        """
        when did we expect last expect this function to run

        :return: returns min date if not expected to have ran yet
        """
        return ScheduledAbstractTask._get_last_expected_run_datetime(
            self.start_date, self.period
        )

    @staticmethod
    def _get_last_expected_run_datetime(
        start_date: datetime, period: timedelta, now: Optional[datetime] = None
    ) -> datetime:
        if now is None:
            now = datetime.now()
        # expose this as static for easier testing
        # if we are not past the start date, return min date
        # this signals "not expected to have run yet"
        if now < start_date:
            return datetime.min

        seconds_since_start = (now - start_date).total_seconds()
        expected_runs_since_start = seconds_since_start // period.total_seconds()
        return start_date + (period * expected_runs_since_start)
