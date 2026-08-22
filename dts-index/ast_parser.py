import ast
from dataclasses import dataclass
from enum import StrEnum
from typing import override
from pathlib import Path

class NodeType(StrEnum):
    CLASS="class"
    METHOD="method"
    FUNCTION="function"

@dataclass
class CodeChunk:
    symbol_name: str
    parent_class: str | None
    node_type: NodeType
    docstring: str | None
    body_code: str | None
    file_path: Path
    line_range: tuple[int, int]

class DTSCodeVisitor(ast.NodeVisitor):

    def __init__(self, file_path: str | Path, source_code: str):
        self.file_path = file_path.relative_to(Path.cwd())
        self.source_code = source_code
        self.curr_class: str | None = None
        self.chunks: list[CodeChunk] = []

    @override
    def visit_ClassDef(self, node: ast.ClassDef):
        prev_class = self.curr_class
        chunk = CodeChunk(
            symbol_name=node.name,
            parent_class=prev_class,
            node_type=NodeType.CLASS,
            docstring=ast.get_docstring(node),
            body_code=ast.get_source_segment(self.source_code, node) or "",
            file_path=self.file_path,
            line_range=(node.lineno, node.end_lineno)
        )
        self.curr_class = node.name
        self.curr_class = prev_class
        self.chunks.append(chunk)
        self.generic_visit(node)

    @override
    def visit_FunctionDef(self, node: ast.FunctionDef):
        if self.curr_class is not None:
            node_type = NodeType.METHOD
            parent_class = self.curr_class

        else:
            node_type = NodeType.FUNCTION
            parent_class = None

        docstring = ast.get_docstring(node)
        body_code = ast.get_source_segment(self.source_code, node)
        chunk = CodeChunk(
            symbol_name=node.name,
            parent_class=parent_class,
            node_type=node_type,
            docstring=docstring,
            body_code=body_code or "",
            file_path=self.file_path,
            line_range=(node.lineno, node.end_lineno)
        )
        self.chunks.append(chunk)
        self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef

def parse_file(file_path: str | Path):
    sanitized_path = Path(file_path)
    source_code = sanitized_path.read_text(encoding="utf-8")
    code_tree = ast.parse(source_code, file_path)
    visitor = DTSCodeVisitor(file_path=file_path, source_code=source_code)
    visitor.visit(code_tree)
    return visitor.chunks
