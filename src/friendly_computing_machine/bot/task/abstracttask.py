from datetime import timedelta, datetime
from abc import abstractmethod, ABC

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
        if last_task_instance is not None:
            self._last_success = last_task_instance.as_of
        else:
            self._last_success = datetime.min
        # default to last success for now
        self._last_attempt = self._last_success

        # internal bool for basic synchronization
        # i think bool updates are atomic in python. at least I hope they are
        # not that i anticipate on running into this situation often; hopefully just in debug
        self.__is_running = False

    def should_run(self) -> bool:
        if self.__is_running:
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
                self.__is_running = True
                self._last_attempt = datetime.now()
                try:
                    status = self._run(*args, **kwargs)
                except Exception as e:
                    # TODO log exception
                    print(e)
                    status = TaskInstanceStatus.EXCEPTION
                self._last_success = datetime.now()
            finally:
                self.__is_running = False
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


class PersistentScheduledAbstractTask(AbstractTask, ABC):
    @property
    @abstractmethod
    def start_date(self) -> datetime:
        """when this"""
        pass
