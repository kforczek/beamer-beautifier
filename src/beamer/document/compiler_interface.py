from src.beamer.page_getter import PageGetter


class PriorityLoadTask:
    def __init__(self, frame_idx: int, page_idx: int, page_getter: PageGetter):
        self.frame_idx = frame_idx
        self.page_idx = page_idx
        self.page_getter = page_getter


class IBackgroundCompiler:
    def set_priority_task(self, priority_task: PriorityLoadTask):
        raise NotImplementedError("Override in subclass")
