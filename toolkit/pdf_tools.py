"""Conservative PDF and image operations for homework files.

Every public function creates a new PDF and leaves its input files unchanged.
Input order is preserved; an existing output name gets a numbered suffix.
"""

from contextlib import ExitStack
from io import BytesIO
from pathlib import Path
from typing import Sequence

from PIL import Image, ImageOps, UnidentifiedImageError
from pypdf import PdfReader, PdfWriter


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp"}


class PdfToolError(ValueError):
    """An expected input or file problem that can be shown to the user."""


def _source_paths(files: Sequence[str | Path], suffixes: set[str], minimum: int) -> list[Path]:
    """Check that an ordered collection contains readable-looking source files."""
    if isinstance(files, (str, Path)):
        raise PdfToolError("请逐个提供文件路径，不要只传入一个路径字符串。")
    try:
        paths = [Path(item).expanduser() for item in files]
    except (TypeError, ValueError) as exc:
        raise PdfToolError("文件路径列表无效。") from exc
    if len(paths) < minimum:
        raise PdfToolError(f"至少需要 {minimum} 个文件。")
    for path in paths:
        if path.suffix.lower() not in suffixes:
            raise PdfToolError(f"不支持的文件格式：{path}")
        if not path.is_file():
            raise PdfToolError(f"文件不存在或不是普通文件：{path}")
    return paths


def _output_folder(first_source: Path, output_dir: str | Path | None) -> Path:
    """Use the first source's folder unless an existing folder is specified."""
    folder = first_source.parent if output_dir is None else Path(output_dir).expanduser()
    if not folder.is_dir():
        raise PdfToolError(f"输出文件夹不存在：{folder}")
    return folder


def _base_name(source: Path, label: str) -> str:
    """Build a short filename stem while retaining useful Chinese text and spaces."""
    stem = source.stem[:60].rstrip(" .") or "homework"
    return f"{stem}_{label}"


def _save_new_pdf(data: bytes, folder: Path, stem: str) -> Path:
    """Write bytes exclusively; retry with (2), (3), ... if a name exists."""
    number = 1
    while True:
        suffix = "" if number == 1 else f" ({number})"
        destination = folder / f"{stem}{suffix}.pdf"
        created = False
        try:
            with destination.open("xb") as output:
                created = True
                output.write(data)
            return destination
        except FileExistsError:
            number += 1
        except OSError as exc:
            if created:
                destination.unlink(missing_ok=True)  # Only remove our incomplete output.
            raise PdfToolError(f"无法写入输出文件：{destination}（{exc}）") from exc


def _reader(path: Path, stack: ExitStack) -> PdfReader:
    """Open and validate a PDF while keeping its stream alive until writing ends."""
    try:
        stream = stack.enter_context(path.open("rb"))
        reader = PdfReader(stream, strict=False)
        if reader.is_encrypted:
            raise PdfToolError(f"PDF 受密码保护，暂不支持：{path}")
        if len(reader.pages) == 0:
            raise PdfToolError(f"PDF 没有页面：{path}")
        return reader
    except PdfToolError:
        raise
    except Exception as exc:
        raise PdfToolError(f"无法读取 PDF：{path}（{exc}）") from exc


def _writer_bytes(writer: PdfWriter) -> bytes:
    """Finish the PDF in memory before creating any output file."""
    try:
        buffer = BytesIO()
        writer.write(buffer)
        return buffer.getvalue()
    except Exception as exc:
        raise PdfToolError(f"生成 PDF 失败：{exc}") from exc


def _load_image(path: Path) -> Image.Image:
    """Open one image, correct EXIF rotation, and place transparency on white."""
    try:
        with Image.open(path) as original:
            if getattr(original, "n_frames", 1) != 1:
                raise PdfToolError(f"暂不支持多帧图片：{path}")
            oriented = ImageOps.exif_transpose(original)
            rgba = oriented.convert("RGBA")
            white = Image.new("RGB", rgba.size, "white")
            white.paste(rgba, mask=rgba.getchannel("A"))
            return white
    except PdfToolError:
        raise
    except (OSError, ValueError, UnidentifiedImageError, Image.DecompressionBombError) as exc:
        raise PdfToolError(f"无法读取图片：{path}（{exc}）") from exc


def _images_pdf_bytes(images: list[Image.Image]) -> bytes:
    """Save ordered images as one PDF; each image becomes one page."""
    try:
        buffer = BytesIO()
        images[0].save(
            buffer, format="PDF", save_all=True,
            append_images=images[1:], resolution=300.0,
        )
        return buffer.getvalue()
    except Exception as exc:
        raise PdfToolError(f"图片转 PDF 失败：{exc}") from exc


def merge_pdfs(files: Sequence[str | Path], output_dir: str | Path | None = None) -> Path:
    """Merge at least two PDFs in the supplied order into a new file."""
    paths = _source_paths(files, {".pdf"}, 2)
    folder = _output_folder(paths[0], output_dir)
    with ExitStack() as stack:
        writer = PdfWriter()
        for path in paths:
            try:
                writer.append(_reader(path, stack))
            except PdfToolError:
                raise
            except Exception as exc:
                raise PdfToolError(f"无法合并 PDF：{path}（{exc}）") from exc
        data = _writer_bytes(writer)
    return _save_new_pdf(data, folder, _base_name(paths[0], f"merged_{len(paths)}files"))


def split_pdf_pages(file: str | Path, output_dir: str | Path | None = None) -> list[Path]:
    """Create one numbered PDF for every page of a source PDF."""
    path = _source_paths([file], {".pdf"}, 1)[0]
    folder = _output_folder(path, output_dir)
    with ExitStack() as stack:
        reader = _reader(path, stack)
        width = max(3, len(str(len(reader.pages))))
        prepared = []
        for number, page in enumerate(reader.pages, start=1):
            writer = PdfWriter()
            try:
                writer.add_page(page)
            except Exception as exc:
                raise PdfToolError(f"无法拆分第 {number} 页：{exc}") from exc
            prepared.append((
                _base_name(path, f"page_{number:0{width}d}"),
                _writer_bytes(writer),
            ))
    created = []
    try:
        for stem, data in prepared:
            created.append(_save_new_pdf(data, folder, stem))
    except PdfToolError:
        for output in created:
            output.unlink(missing_ok=True)  # Roll back only files created in this call.
        raise
    return created


def extract_pdf_pages(
    file: str | Path, first_page: int, last_page: int,
    output_dir: str | Path | None = None,
) -> Path:
    """Copy an inclusive, one-based page range to a new PDF."""
    path = _source_paths([file], {".pdf"}, 1)[0]
    folder = _output_folder(path, output_dir)
    with ExitStack() as stack:
        reader = _reader(path, stack)
        total = len(reader.pages)
        if not (1 <= first_page <= last_page <= total):
            raise PdfToolError(f"页码范围应在 1 到 {total} 之间，且起始页不大于结束页。")
        writer = PdfWriter()
        for index in range(first_page - 1, last_page):
            try:
                writer.add_page(reader.pages[index])
            except Exception as exc:
                raise PdfToolError(f"无法提取第 {index + 1} 页：{exc}") from exc
        data = _writer_bytes(writer)
    width = max(3, len(str(total)))
    stem = _base_name(path, f"pages_{first_page:0{width}d}-{last_page:0{width}d}")
    return _save_new_pdf(data, folder, stem)


def images_to_pdf(files: Sequence[str | Path], output_dir: str | Path | None = None) -> Path:
    """Convert one or more ordered JPG, PNG, or BMP images to a new PDF."""
    paths = _source_paths(files, IMAGE_SUFFIXES, 1)
    folder = _output_folder(paths[0], output_dir)
    images = []
    try:
        for path in paths:
            images.append(_load_image(path))
        data = _images_pdf_bytes(images)
    finally:
        for image in images:
            image.close()
    return _save_new_pdf(data, folder, _base_name(paths[0], f"images_{len(paths)}files"))


def combine_scans(files: Sequence[str | Path], output_dir: str | Path | None = None) -> Path:
    """Combine PDFs and images in the exact supplied order into a new PDF."""
    paths = _source_paths(files, {".pdf"} | IMAGE_SUFFIXES, 2)
    folder = _output_folder(paths[0], output_dir)
    with ExitStack() as stack:
        writer = PdfWriter()
        for path in paths:
            if path.suffix.lower() == ".pdf":
                reader = _reader(path, stack)
            else:
                image = _load_image(path)
                try:
                    stream = stack.enter_context(BytesIO(_images_pdf_bytes([image])))
                finally:
                    image.close()
                reader = PdfReader(stream)
            try:
                writer.append(reader)
            except Exception as exc:
                raise PdfToolError(f"无法合并扫描文件：{path}（{exc}）") from exc
        data = _writer_bytes(writer)
    return _save_new_pdf(data, folder, _base_name(paths[0], f"scans_{len(paths)}files"))
