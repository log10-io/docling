from pathlib import Path

from docling.backend.md_backend import MarkdownDocumentBackend
from docling.datamodel.base_models import InputFormat
from docling.datamodel.document import (
    ConversionResult,
    DoclingDocument,
    InputDocument,
)
from docling.document_converter import DocumentConverter
from docling_core.types.doc import DocItemLabel
from tests.verify_utils import CONFID_PREC, COORD_PREC

from .test_data_gen_flag import GEN_TEST_DATA
from .verify_utils import verify_document

GENERATE = GEN_TEST_DATA


def test_convert_valid():
    fmt = InputFormat.MD
    cls = MarkdownDocumentBackend

    root_path = Path("tests") / "data"
    relevant_paths = sorted((root_path / "md").glob("*.md"))
    assert len(relevant_paths) > 0

    yaml_filter = ["inline_and_formatting", "mixed_without_h1"]
    json_filter = ["escaped_characters"]

    for in_path in relevant_paths:
        md_gt_path = root_path / "groundtruth" / "docling_v2" / f"{in_path.name}.md"
        yaml_gt_path = root_path / "groundtruth" / "docling_v2" / f"{in_path.name}.yaml"
        json_gt_path = root_path / "groundtruth" / "docling_v2" / f"{in_path.name}.json"

        in_doc = InputDocument(
            path_or_stream=in_path,
            format=fmt,
            backend=cls,
        )
        backend = cls(
            in_doc=in_doc,
            path_or_stream=in_path,
        )
        assert backend.is_valid()

        act_doc = backend.convert()
        act_data = act_doc.export_to_markdown()

        if in_path.stem in json_filter:
            assert verify_document(act_doc, json_gt_path, GENERATE), "export to json"

        if GEN_TEST_DATA:
            with open(md_gt_path, mode="w", encoding="utf-8") as f:
                f.write(f"{act_data}\n")

            if in_path.stem in yaml_filter:
                act_doc.save_as_yaml(
                    yaml_gt_path,
                    coord_precision=COORD_PREC,
                    confid_precision=CONFID_PREC,
                )
        else:
            with open(md_gt_path, encoding="utf-8") as f:
                exp_data = f.read().rstrip()
            assert act_data == exp_data

            if in_path.stem in yaml_filter:
                exp_doc = DoclingDocument.load_from_yaml(yaml_gt_path)
                assert act_doc == exp_doc, f"export to yaml failed on {in_path}"


def get_md_paths():
    # Define the directory you want to search
    directory = Path("./tests/groundtruth/docling_v2")

    # List all MD files in the directory and its subdirectories
    md_files = sorted(directory.rglob("*.md"))
    return md_files


def get_converter():
    converter = DocumentConverter(allowed_formats=[InputFormat.MD])

    return converter


def test_e2e_md_conversions():
    md_paths = get_md_paths()
    converter = get_converter()

    for md_path in md_paths:
        # print(f"converting {md_path}")

        with open(md_path) as fr:
            true_md = fr.read()

        conv_result: ConversionResult = converter.convert(md_path)

        doc: DoclingDocument = conv_result.document

        pred_md: str = doc.export_to_markdown()
        assert true_md == pred_md

        conv_result_: ConversionResult = converter.convert_string(
            true_md, format=InputFormat.MD
        )

        doc_: DoclingDocument = conv_result_.document

        pred_md_: str = doc_.export_to_markdown()
        assert true_md == pred_md_


def test_table_caption_support():
    """Test that markdown backend correctly handles table captions."""
    
    # Test markdown with table and caption
    markdown_content = """# Test Document

| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Data 1   | Data 2   | Data 3   |
| Data 4   | Data 5   | Data 6   |

<span data-class="table-caption">Table 1: Sample table with caption</span>

Some text after the table.
"""
    
    converter = DocumentConverter(allowed_formats=[InputFormat.MD])
    conv_result: ConversionResult = converter.convert_string(
        markdown_content, format=InputFormat.MD, name="test_table_caption.md"
    )
    
    doc: DoclingDocument = conv_result.document
    
    # Check that we have a table
    assert len(doc.tables) == 1, f"Expected 1 table, found {len(doc.tables)}"
    
    table = doc.tables[0]
    
    # Check that the table has a caption
    assert len(table.captions) == 1, f"Table should have 1 caption, found {len(table.captions)}"
    
    # Get the caption text item
    caption_ref = table.captions[0]
    # Find the text item that the caption refers to
    caption_text_item = None
    for text_item in doc.texts:
        if text_item.self_ref == caption_ref.cref:
            caption_text_item = text_item
            break
    
    assert caption_text_item is not None, "Caption text item should be found"
    assert caption_text_item.text == "Table 1: Sample table with caption", f"Caption text mismatch: {caption_text_item.text}"
    assert caption_text_item.label == DocItemLabel.CAPTION, f"Caption should have CAPTION label, got {caption_text_item.label}"


def test_table_without_caption():
    """Test that markdown backend works correctly with tables that have no captions."""
    
    # Test markdown with table but no caption
    markdown_content = """# Test Document

| Column 1 | Column 2 |
|----------|----------|
| Data 1   | Data 2   |
| Data 3   | Data 4   |

Some text after the table.
"""
    
    converter = DocumentConverter(allowed_formats=[InputFormat.MD])
    conv_result: ConversionResult = converter.convert_string(
        markdown_content, format=InputFormat.MD, name="test_table_no_caption.md"
    )
    
    doc: DoclingDocument = conv_result.document
    
    # Check that we have a table
    assert len(doc.tables) == 1, f"Expected 1 table, found {len(doc.tables)}"
    
    table = doc.tables[0]
    
    # Check that the table has no caption
    assert len(table.captions) == 0, f"Table should not have a caption, got {len(table.captions)} captions"
