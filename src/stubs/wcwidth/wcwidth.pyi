from .table_vs16 import VS16_NARROW_TO_WIDE as VS16_NARROW_TO_WIDE
from .table_wide import WIDE_EASTASIAN as WIDE_EASTASIAN
from .table_zero import ZERO_WIDTH as ZERO_WIDTH
from .unicode_versions import list_versions as list_versions

def wcwidth(wc: str, unicode_version: str = "auto") -> int: ...
def wcswidth(pwcs: str, n: int = None, unicode_version: str = "auto") -> int: ...
