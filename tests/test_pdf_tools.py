"""Generated small files exercise Phase 2 without touching personal data."""

import tempfile
import unittest
from pathlib import Path

from PIL import Image
from pypdf import PdfReader, PdfWriter

from toolkit.cli import run_cli
from toolkit.pdf_tools import (
    PdfToolError,
    combine_scans,
    extract_pdf_pages,
    images_to_pdf,
    merge_pdfs,
    split_pdf_pages,
)


class PdfToolTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def make_pdf(self, name, widths):
        """Write a PDF whose distinct page widths reveal page order."""
        path = self.folder / name
        writer = PdfWriter()
        for width in widths:
            writer.add_blank_page(width=width, height=200)
        with path.open("wb") as stream:
            writer.write(stream)
        return path

    def make_image(self, name, size=(150, 150)):
        path = self.folder / name
        image = Image.new("RGBA", size, (40, 80, 120, 160))
        if path.suffix.lower() in {".jpg", ".jpeg"}:
            image.convert("RGB").save(path)
        else:
            image.save(path)
        image.close()
        return path

    def widths(self, path):
        return [float(page.mediabox.width) for page in PdfReader(path).pages]

    def test_merge_preserves_order_sources_and_existing_output(self):
        first = self.make_pdf("数学 作业 1.pdf", [101, 102])
        second = self.make_pdf("第二份.pdf", [203])
        original = first.read_bytes()
        output = merge_pdfs([first, second])
        first_output_bytes = output.read_bytes()
        other = merge_pdfs([first, second])
        self.assertEqual(self.widths(output), [101, 102, 203])
        self.assertIn("数学 作业 1_merged_2files", output.name)
        self.assertIn("(2)", other.name)
        self.assertEqual(first.read_bytes(), original)
        self.assertEqual(output.read_bytes(), first_output_bytes)
        self.assertNotEqual(output, other)

    def test_main_menu_can_merge_real_files(self):
        first = self.make_pdf("first.pdf", [111])
        second = self.make_pdf("second.pdf", [222])
        answers = iter(["1", "1", str(first), str(second), "", "", "5", "6"])
        messages = []
        result = run_cli(
            input_func=lambda _prompt: next(answers),
            output_func=messages.append,
        )
        self.assertEqual(result, 0)
        output = self.folder / "first_merged_2files.pdf"
        self.assertEqual(self.widths(output), [111, 222])
        self.assertIn("已生成：", "\n".join(messages))

    def test_split_each_page_and_extract_range(self):
        source = self.make_pdf("course.pdf", [100, 200, 300])
        outputs = split_pdf_pages(source)
        self.assertEqual([path.name for path in outputs], [
            "course_page_001.pdf", "course_page_002.pdf", "course_page_003.pdf",
        ])
        self.assertEqual([self.widths(path) for path in outputs], [[100], [200], [300]])
        extracted = extract_pdf_pages(source, 2, 3)
        self.assertEqual(extracted.name, "course_pages_002-003.pdf")
        self.assertEqual(self.widths(extracted), [200, 300])
        self.assertTrue(source.exists())

    def test_images_and_mixed_scans_keep_input_order(self):
        image1 = self.make_image("scan 甲.png", (150, 300))
        image2 = self.make_image("scan 乙.jpg", (300, 150))
        image_pdf = images_to_pdf([image1, image2])
        widths = self.widths(image_pdf)
        self.assertEqual(len(widths), 2)
        self.assertLess(widths[0], widths[1])

        first_pdf = self.make_pdf("first.pdf", [301])
        last_pdf = self.make_pdf("last.pdf", [503])
        combined = combine_scans([first_pdf, image1, last_pdf])
        mixed_widths = self.widths(combined)
        self.assertEqual(len(mixed_widths), 3)
        self.assertEqual(mixed_widths[0], 301)
        self.assertEqual(mixed_widths[2], 503)
        self.assertTrue(0 < mixed_widths[1] < 301)

    def test_bad_files_and_page_ranges_have_clear_errors(self):
        good = self.make_pdf("good.pdf", [100])
        bad = self.folder / "broken.pdf"
        bad.write_bytes(b"not a PDF")
        with self.assertRaisesRegex(PdfToolError, "至少需要 2 个文件"):
            merge_pdfs([])
        with self.assertRaisesRegex(PdfToolError, "至少需要 2 个文件"):
            merge_pdfs([good])
        with self.assertRaisesRegex(PdfToolError, "无法读取 PDF"):
            merge_pdfs([good, bad])
        with self.assertRaisesRegex(PdfToolError, "页码范围"):
            extract_pdf_pages(good, 2, 3)
        with self.assertRaisesRegex(PdfToolError, "输出文件夹不存在"):
            split_pdf_pages(good, self.folder / "missing")
        self.assertFalse((self.folder / "good_merged_2files.pdf").exists())

    def test_bad_image_and_password_protected_pdf(self):
        broken_image = self.folder / "broken.png"
        broken_image.write_bytes(b"not an image")
        with self.assertRaisesRegex(PdfToolError, "无法读取图片"):
            images_to_pdf([broken_image])

        protected = self.folder / "protected.pdf"
        writer = PdfWriter()
        writer.add_blank_page(width=100, height=100)
        writer.encrypt("secret")
        with protected.open("wb") as stream:
            writer.write(stream)
        good = self.make_pdf("good.pdf", [100])
        with self.assertRaisesRegex(PdfToolError, "密码保护"):
            merge_pdfs([good, protected])
        self.assertTrue(protected.exists())


if __name__ == "__main__":
    unittest.main()
