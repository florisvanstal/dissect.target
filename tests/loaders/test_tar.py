import pytest

from dissect.target import Target
from dissect.target.loaders.tar import TarLoader
from dissect.target.plugins.os.windows._os import WindowsPlugin
from tests._utils import absolute_path


def test_tar_loader_compressed_tar_file(target_win: Target):
    archive_path = absolute_path("_data/loaders/tar/test-archive.tar.gz")

    loader = TarLoader(archive_path)
    loader.map(target_win)

    assert len(target_win.filesystems) == 2

    test_file = target_win.fs.path("test-data/test-file.txt")

    assert test_file.exists()
    assert test_file.open().read() == b"test-value\n"


def test_tar_sensitive_drive_letter(target_win: Target):
    tar_file = absolute_path("_data/loaders/tar/uppercase_driveletter.tar")

    loader = TarLoader(tar_file)
    loader.map(target_win)

    # mounts = /, c: and sysvol
    assert len(target_win.fs.mounts) == 3
    assert "C:" not in target_win.fs.mounts.keys()
    assert target_win.fs.get("C:/test.file").open().read() == b"hello_world"
    assert target_win.fs.get("c:/test.file").open().read() == b"hello_world"


def test_tar_loader_compressed_tar_file_with_empty_dir(target_unix):
    archive_path = absolute_path("_data/loaders/tar/test-archive-empty-folder.tgz")
    loader = TarLoader(archive_path)
    loader.map(target_unix)

    assert len(target_unix.filesystems) == 2
    test_file = target_unix.fs.path("test/test_file_with_content")
    assert test_file.exists()
    assert test_file.is_file()
    assert test_file.open().read() == b"This is a test!\n"
    empty_folder = target_unix.fs.path("test/empty_dir")
    assert empty_folder.exists()
    assert empty_folder.is_dir()


@pytest.mark.parametrize(
    "archive",
    [
        ("_data/loaders/tar/test-windows-sysvol-absolute.tar"),
        ("_data/loaders/tar/test-windows-sysvol-relative.tar"),
        ("_data/loaders/tar/test-windows-fs-c-relative.tar"),
        ("_data/loaders/tar/test-windows-fs-c-absolute.tar"),
    ],
)
def test_tar_loader_windows_sysvol_formats(target_default, archive):
    loader = TarLoader(absolute_path(archive))
    loader.map(target_default)
    assert WindowsPlugin(target_default).detect(target_default)


def test_tar_anonymous_filesystems(target_default: Target):
    tar_file = absolute_path("_data/loaders/tar/test-anon-filesystems.tar")

    loader = TarLoader(tar_file)
    loader.map(target_default)

    # mounts = $fs$/fs0, $fs$/fs1 and /
    assert len(target_default.fs.mounts) == 3
    assert "$fs$/fs0" in target_default.fs.mounts.keys()
    assert "$fs$/fs1" in target_default.fs.mounts.keys()
    assert "/" in target_default.fs.mounts.keys()
    assert target_default.fs.get("$fs$/fs0/foo").open().read() == b"hello world\n"
    assert target_default.fs.get("$fs$/fs1/bar").open().read() == b"hello world\n"
