from typing import List
from threading import Thread, Lock

from src.beamer.frame.frame import Frame
from src.beamer.graphics import pixmap_from_document
from .compiler_interface import PriorityLoadTask, IBackgroundCompiler


class BackgroundCompiler(IBackgroundCompiler):
    def __init__(self):
        self._frames = []
        self._compiled_indexes = set()
        self._priority_task = None
        self._priority_lock = Lock()
        self._stop_flag = False

    def init_frames(self, frames: List[Frame]):
        if self._frames:
            raise RuntimeError("The list can be initialized only once!")
        self._frames = frames

    def start(self):
        thread = Thread(target=self._run)
        thread.start()

    def stop(self):
        self._stop_flag = True

    def set_priority_task(self, priority_task: PriorityLoadTask):
        if priority_task.frame_idx in self._compiled_indexes:
            # Speed-up possible - the new thread will only read already compiled data
            thread = Thread(target=self._compile_frame_with_output, args=(priority_task,))
            thread.start()
            return

        with self._priority_lock:
            self._priority_task = priority_task

    def _run(self):
        while not self._stop_flag:
            for idx in range(len(self._frames)):
                while self._compile_priority():
                    pass

                self._compile_frame_silent(idx)

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
        frame = self._frames[task_info.frame_idx]
        for improvements, notify_slot in ((frame.local_improvements(), task_info.page_getter.add_local_version),
                                          (frame.background_improvements(), task_info.page_getter.add_background_version),
                                          (frame.global_improvements(), task_info.page_getter.add_global_version)):

            if task_info.frame_idx in self._compiled_indexes:
                improvements_source = improvements.all_improvements()
            else:
                improvements_source = improvements.improvements_generator()

            useless_versions = []
            for version in improvements_source:
                doc = version.doc()
                if not doc:
                    useless_versions.append(version)
                    continue
                pixmap = pixmap_from_document(doc, task_info.page_idx)
                notify_slot(pixmap)

            for version_to_remove in useless_versions:
                improvements.remove_improvement(version_to_remove)

        self._compiled_indexes.add(task_info.frame_idx)

    # def _is_task_simple(self, task: PriorityLoadTask):
    #     """True if the task involves only reading generated and compiled improvements - this would mean
    #         that a new thread can be created for this task (no concurrent writing will be involved). False otherwise."""
    #     frame = self._frames[task.frame_idx]
    #
    #     are_improvements_generated = False
    #     for improvements in (frame.local_improvements(), frame.background_improvements(), frame.global_improvements()):
    #         for version in improvements.all_improvements():
    #             are_improvements_generated = True
    #             if not version.is_compiled():
    #                 return False
    #
    #     return are_improvements_generated
