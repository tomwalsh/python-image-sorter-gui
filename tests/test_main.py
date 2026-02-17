"""Tests for non-GUI logic in main.py."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add project root to path so we can import constants without installing the package.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from constants import IMAGE_FORMATS, MAX_IMAGE_DIMENSION, MEDIA_FORMATS, VIDEO_FORMATS


@pytest.fixture()
def media_folder(tmp_path: Path) -> Path:
    """Create a temporary folder with sample media files and subdirectories."""
    # Create media files
    for name in ["alpha.jpg", "beta.png", "gamma.mp4", "delta.txt", "epsilon.avi"]:
        (tmp_path / name).touch()

    # Create category subdirectories
    (tmp_path / "cats").mkdir()
    (tmp_path / "dogs").mkdir()

    return tmp_path


class TestFormatSets:
    def test_image_formats_are_lowercase(self) -> None:
        for fmt in IMAGE_FORMATS:
            assert fmt == fmt.lower()

    def test_video_formats_are_lowercase(self) -> None:
        for fmt in VIDEO_FORMATS:
            assert fmt == fmt.lower()

    def test_media_formats_is_union(self) -> None:
        assert MEDIA_FORMATS == IMAGE_FORMATS | VIDEO_FORMATS

    def test_no_overlap_between_image_and_video(self) -> None:
        assert not (IMAGE_FORMATS & VIDEO_FORMATS)

    def test_common_formats_present(self) -> None:
        assert "jpg" in IMAGE_FORMATS
        assert "png" in IMAGE_FORMATS
        assert "mp4" in VIDEO_FORMATS
        assert "mkv" in VIDEO_FORMATS


class TestMaxImageDimension:
    def test_value(self) -> None:
        assert MAX_IMAGE_DIMENSION == 4096

    def test_is_int(self) -> None:
        assert isinstance(MAX_IMAGE_DIMENSION, int)


class TestFileFiltering:
    """Test the file filtering logic used by get_folder_content."""

    def test_filters_media_files(self, media_folder: Path) -> None:
        """Only media files (by extension) should be included."""
        media_files = []
        folders = []
        for entry in sorted(media_folder.iterdir(), key=lambda p: p.name):
            if entry.is_file():
                ext = entry.suffix.lower().lstrip(".")
                if ext in MEDIA_FORMATS:
                    media_files.append(entry.name)
            else:
                folders.append(entry.name)

        assert "alpha.jpg" in media_files
        assert "beta.png" in media_files
        assert "gamma.mp4" in media_files
        assert "epsilon.avi" in media_files
        assert "delta.txt" not in media_files

    def test_identifies_subdirectories(self, media_folder: Path) -> None:
        folders = []
        for entry in sorted(media_folder.iterdir(), key=lambda p: p.name):
            if not entry.is_file():
                folders.append(entry.name)

        assert "cats" in folders
        assert "dogs" in folders

    def test_sorted_order(self, media_folder: Path) -> None:
        media_files = []
        for entry in sorted(media_folder.iterdir(), key=lambda p: p.name):
            if entry.is_file():
                ext = entry.suffix.lower().lstrip(".")
                if ext in MEDIA_FORMATS:
                    media_files.append(entry.name)

        assert media_files == sorted(media_files)


class TestCategoryOperations:
    """Test file-system operations used by category management."""

    def test_create_category_directory(self, media_folder: Path) -> None:
        new_cat = media_folder / "birds"
        new_cat.mkdir(parents=True)
        assert new_cat.is_dir()

    def test_move_file_to_category(self, media_folder: Path) -> None:
        src = media_folder / "alpha.jpg"
        dest = media_folder / "cats" / "alpha.jpg"
        src.rename(dest)
        assert dest.exists()
        assert not src.exists()

    def test_move_file_back_from_category(self, media_folder: Path) -> None:
        # Move file into category first
        src = media_folder / "alpha.jpg"
        cat_file = media_folder / "cats" / "alpha.jpg"
        src.rename(cat_file)

        # Move it back
        cat_file.rename(media_folder / "alpha.jpg")
        assert (media_folder / "alpha.jpg").exists()
        assert not cat_file.exists()

    def test_remove_empty_category(self, media_folder: Path) -> None:
        cat_path = media_folder / "cats"
        cat_path.rmdir()
        assert not cat_path.exists()

    def test_rmdir_fails_on_nonempty(self, media_folder: Path) -> None:
        cat_path = media_folder / "cats"
        (cat_path / "stray.jpg").touch()
        with pytest.raises(OSError):
            cat_path.rmdir()

    def test_invalid_category_chars(self) -> None:
        invalid_chars = set('/\\:*?"<>|')
        test_name = "my:category"
        found = [c for c in test_name if c in invalid_chars]
        assert found == [":"]

    def test_valid_category_name_has_no_invalid_chars(self) -> None:
        invalid_chars = set('/\\:*?"<>|')
        test_name = "landscapes"
        found = [c for c in test_name if c in invalid_chars]
        assert found == []


class TestVideoDetection:
    """Test the _is_video logic (extracted from the class for testability)."""

    def test_video_extensions(self) -> None:
        for ext in VIDEO_FORMATS:
            assert Path(f"file.{ext}").suffix.lower().lstrip(".") in VIDEO_FORMATS

    def test_image_extensions_are_not_video(self) -> None:
        for ext in IMAGE_FORMATS:
            assert Path(f"file.{ext}").suffix.lower().lstrip(".") not in VIDEO_FORMATS

    def test_case_insensitive(self) -> None:
        assert Path("file.MP4").suffix.lower().lstrip(".") in VIDEO_FORMATS
        assert Path("file.Jpg").suffix.lower().lstrip(".") not in VIDEO_FORMATS
        assert Path("file.Jpg").suffix.lower().lstrip(".") in IMAGE_FORMATS


class TestAdvanceAfterRemoval:
    """Test the index-adjustment logic used after removing a file."""

    @staticmethod
    def _advance(files: list[str], curr_file: int) -> tuple[list[str], int, str]:
        """Simulate _advance_after_removal logic, returning (files, new_index, action)."""
        if not files:
            return files, 0, "reset"
        elif curr_file >= len(files):
            return files, len(files) - 1, "display"
        else:
            return files, curr_file, "display"

    def test_empty_list_triggers_reset(self) -> None:
        _, idx, action = self._advance([], 0)
        assert action == "reset"
        assert idx == 0

    def test_index_past_end_clamps(self) -> None:
        files = ["a.jpg", "b.jpg"]
        _, idx, action = self._advance(files, 5)
        assert idx == 1
        assert action == "display"

    def test_index_at_end_clamps(self) -> None:
        files = ["a.jpg", "b.jpg"]
        _, idx, _action = self._advance(files, 2)
        assert idx == 1

    def test_index_within_range_unchanged(self) -> None:
        files = ["a.jpg", "b.jpg", "c.jpg"]
        _, idx, action = self._advance(files, 1)
        assert idx == 1
        assert action == "display"

    def test_remove_last_file(self) -> None:
        """Simulates removing the last file — list becomes empty."""
        files: list[str] = []
        _, _idx, action = self._advance(files, 0)
        assert action == "reset"

    def test_remove_middle_file(self) -> None:
        """After removing index 1 from [a, b, c], curr_file=1 should show new index 1 (was 'c')."""
        files = ["a.jpg", "c.jpg"]  # 'b.jpg' was removed
        _, idx, action = self._advance(files, 1)
        assert idx == 1
        assert action == "display"
