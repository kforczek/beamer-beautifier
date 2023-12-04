class PageInfo:
    """Represents a set of thumbnails for a page along with its proposed
        local (frame) and global (document) improvements. First element
        in each of the vectors is the original one."""
    def __init__(self, local_improvements, global_improvements):
        self.local_improvements = local_improvements
        self.global_improvements = global_improvements
