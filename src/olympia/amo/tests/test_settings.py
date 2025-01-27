import os
import json

import pytest

from django.conf import settings

from olympia.lib.settings_base import get_sentry_release


@pytest.mark.parametrize(
    'key', ('SHARED_STORAGE', 'GUARDED_ADDONS_PATH', 'TMP_PATH', 'MEDIA_ROOT')
)
def test_base_paths_bytestring(key):
    """Make sure all relevant base paths are bytestrings.

    Filenames and filesystem paths are generally handled as byte-strings
    and we are running into various errors if they're not.

    One of many examples would be

    >>> os.path.join('path1', 'pæth2'.encode('utf-8'))
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "/usr/lib64/python2.7/posixpath.py", line 80, in join
        path += '/' + b
    UnicodeDecodeError: 'ascii' codec can't decode byte...

    See https://github.com/mozilla/addons-server/issues/3579 for context.
    """
    assert isinstance(getattr(settings, key), str)


def test_sentry_release_config():
    version_json = os.path.join(settings.ROOT, 'version.json')
    original = None

    # There is a version.json that contains `version: origin/master`
    # by default in the repository. We should ignore that and fetch
    # the git commit.
    assert len(get_sentry_release()) == 40

    # Cleanup for tests
    if os.path.exists(version_json):
        with open(version_json) as fobj:
            original = fobj.read()

        os.remove(version_json)

    # by default, if no version.json exists it simply fetches a git-sha
    assert len(get_sentry_release()) == 40

    # It fetches `version` from the version.json
    with open(version_json, 'w') as fobj:
        fobj.write(json.dumps({'version': '2018.07.19'}))

    assert get_sentry_release() == '2018.07.19'

    os.remove(version_json)

    # Or tries to get the commit from version.json alternatively
    with open(version_json, 'w') as fobj:
        fobj.write(json.dumps({'commit': '1111111'}))

    assert get_sentry_release() == '1111111'

    if original:
        with open(version_json, 'w') as fobj:
            fobj.write(original)

    # Usual state of things, version is empty but commit is set
    with open(version_json, 'w') as fobj:
        fobj.write(json.dumps({'version': '', 'commit': '1111111'}))

    assert get_sentry_release() == '1111111'

    if original:
        with open(version_json, 'w') as fobj:
            fobj.write(original)
