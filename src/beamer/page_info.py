class PageInfo:
    """Represents a set of thumbnails for a page along with its proposed
        frame (local), background (local) and global (document) improvements. First element
        in each of the vectors is the original one."""
    def __init__(self, local_improvements, background_improvements, global_improvements):
        self.frame_improvements = local_improvements
        self.background_improvements = background_improvements
        self.global_improvements = global_improvements
