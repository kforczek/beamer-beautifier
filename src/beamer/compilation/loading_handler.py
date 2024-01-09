from typing import List
from threading import Thread, Lock

from src.beamer.frame.frame import Frame
from src.beamer.graphics import pixmap_from_document
from .loading_handler_iface import PriorityLoadTask, BackgroundRegenerationTask, IPageLoadingHandler


class PageLoadingHandler(IPageLoadingHandler):
    """A multi-threaded handler for performing compilation & loading tasks in the background."""
    def __init__(self):
        self._frames = []
        self._compiled_indexes = set()

        self._priority_task = None
        self._priority_lock = Lock()

        self._finished_lock = Lock()
        self._compiling_thread_finished = False

    def init_frames(self, frames: List[Frame]):
        if self._frames:
            raise RuntimeError("The list can be initialized only once!")
        self._frames = frames

    def start(self):
        thread = Thread(target=self._run)
        thread.start()

    def set_priority_task(self, priority_task: PriorityLoadTask):
        if not isinstance(priority_task, BackgroundRegenerationTask) and priority_task.frame_idx in self._compiled_indexes:
            # Speed-up possible - the new thread will only read already compiled data
            thread = Thread(target=self._compile_frame_with_output, args=(priority_task,))
            thread.start()
            return

        with self._priority_lock:
            self._priority_task = priority_task

            with self._finished_lock:
                if not self._compiling_thread_finished:
                    return

        # Thread has finished - to resolve the priority task call a new thread needs to be created
        thread = Thread(target=self._compile_priority)
        thread.start()

    def _run(self):
        for idx in range(len(self._frames)):
            while self._compile_priority():
                pass

            self._compile_frame_silent(idx)

        self._safe_finish_work()

    def _compile_priority(self) -> bool:
        with self._priority_lock:
            resolved_priority = self._priority_task

        if resolved_priority is None:
            return False

        self._compile_frame_with_output(resolved_priority)

        with self._priority_lock:
            if self._priority_task == resolved_priority:
                # Set priority index as None (resolved) only if no other priority has been externally set while this
                # one was being compiled
                self._priority_task = None

        return True

    def _compile_frame_silent(self, frame_idx: int):
        if frame_idx in self._compiled_indexes:
            return

        for improvements in (self._frames[frame_idx].local_improvements(),
                             self._frames[frame_idx].background_improvements(),
                             self._frames[frame_idx].global_improvements()):

            if not improvements.all_improvements():
                improvements.generate_improvements()

            for version in improvements.all_improvements():
                version.compile()

        self._compiled_indexes.add(frame_idx)

    def _compile_frame_with_output(self, task_info: PriorityLoadTask):
        if isinstance(task_info, BackgroundRegenerationTask):
            self._regenerate_backgrounds_with_output(task_info)
            return

        frame = self._frames[task_info.frame_idx]
        for improvements, notify_slot in ((frame.local_improvements(), task_info.page_getter.add_local_version),
                                          (frame.background_improvements(), task_info.page_getter.add_background_version),
                                          (frame.global_improvements(), task_info.page_getter.add_global_version)):
            regenerate = task_info.frame_idx not in self._compiled_indexes
            _compile_improvements_category_with_output(improvements, notify_slot, task_info.page_idx, regenerate)

        self._compiled_indexes.add(task_info.frame_idx)

    def _regenerate_backgrounds_with_output(self, task_info: BackgroundRegenerationTask):
        self._compiled_indexes.remove(task_info.frame_idx)

        improvements = self._frames[task_info.frame_idx].background_improvements()
        notify_slot = task_info.page_getter.add_background_version
        _compile_improvements_category_with_output(improvements, notify_slot, task_info.page_idx, True)

        self._compiled_indexes.add(task_info.frame_idx)

    def _safe_finish_work(self):
        """Try to set finished flag, but compile any priorities if they arise in the meantime."""
        any_remaining_priorities = True
        while any_remaining_priorities:
            self._priority_lock.acquire()
            if self._priority_task:
                self._priority_lock.release()
                self._compile_priority()
                continue

            any_remaining_priorities = False
            with self._finished_lock:
                self._compiling_thread_finished = True
            self._priority_lock.release()


def _compile_improvements_category_with_output(improvements, notify_slot, page_idx, regenerate):
    if regenerate:
        improvements_source = improvements.improvements_generator()
    else:
        improvements_source = improvements.all_improvements()

    useless_versions = []
    for version in improvements_source:
        doc = version.doc()
        if not doc:
            useless_versions.append(version)
            continue
        pixmap = pixmap_from_document(doc, page_idx)
        notify_slot(pixmap)

    for version_to_remove in useless_versions:
        improvements.remove_improvement(version_to_remove)
