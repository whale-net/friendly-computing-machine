import time
from datetime import timedelta, datetime
from abc import abstractmethod, ABC


class Task(ABC):
    def __init__(self):
        """
        self.
        :param period:
        """

        self._last_attempt = datetime.min
        self._last_success = datetime.min

        # internal bool for basic synchronization
        # i think bool updates are atomic in python. at least I hope they are
        # not that i anticipate on running into this situation often; hopefully just in debug
        self.__is_running = False

    def should_run(self) -> bool:
        if self.__is_running:
            return False
        return self._last_attempt + self.period < datetime.now()

    def run(self, force_run: bool = False, *args, **kwargs):
        """
        run the task if it should run

        :param args:
        :param kwargs:
        :return:
        """
        if force_run or self.should_run():
            try:
                self.__is_running = True
                self._last_attempt = datetime.now()
                self._run(*args, **kwargs)
                self._last_success = datetime.now()
            finally:
                self.__is_running = False

    @abstractmethod
    def _run(self, *args, **kwargs):
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
    def name(self) -> str:
        return self.__name__

    def __hash__(self):
        return self.name.__hash__()


class TaskPool:
    def __init__(self, sleep_period=timedelta(seconds=5)):
        self._tasks: set[Task] = set()
        self._sleep_period_milliseconds = sleep_period.total_seconds() * 1000
        self.__should_run = True

    def add_task(self, task: Task):
        self._tasks.add(task)

    def start(self):
        while self.__should_run:
            self._process_tasks()
            time.sleep(self._sleep_period_milliseconds)

    def _process_tasks(self):
        # TODO - thread pool this
        # most tasks will be API calls
        for task in self._tasks:
            task.run()

    def stop(self):
        """
        stop taskpool, intended to be externally triggered

        :return:
        """
        self.__should_run = False


class FindTeams(Task):
    @property
    def period(self) -> timedelta:
        return timedelta(minutes=1)

    def _run(self):
        pass


def create_default_taskpool() -> TaskPool:
    # unsure how to specify which tasks I actually want, so just going to make this register everything for now
    # with the option to comment out individual ones while I work on this
    tp = TaskPool()
    tp.add_task(FindTeams())
    return tp
