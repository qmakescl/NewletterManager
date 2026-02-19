"""동기화 상태 공유 모듈.

순환 import 없이 sync lock을 main과 라우터가 공유하기 위한 모듈.
"""

import threading

sync_lock = threading.Lock()
