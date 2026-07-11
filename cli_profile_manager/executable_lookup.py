import os
import shutil


_EXECUTABLE_LOOKUP_CACHE = {}


def reset_executable_lookup_cache():
    _EXECUTABLE_LOOKUP_CACHE.clear()


def executable_lookup_cache_key(command, path=None, environ=None):
    environ = os.environ if environ is None else environ
    return (command, environ.get("PATH") if path is None else path)


def _is_explicit_executable_path(command):
    return (
        os.path.isabs(command)
        or os.path.dirname(command) != ""
        or "\\" in command
    )


def executable_path(command, path=None):
    if _is_explicit_executable_path(command):
        return shutil.which(command, path=path)
    key = executable_lookup_cache_key(command, path=path)
    if key not in _EXECUTABLE_LOOKUP_CACHE:
        _EXECUTABLE_LOOKUP_CACHE[key] = shutil.which(command, path=path)
    return _EXECUTABLE_LOOKUP_CACHE[key]
