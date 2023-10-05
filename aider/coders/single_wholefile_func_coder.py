from aider import diffs

from ..dump import dump  # noqa: F401
from .base_coder import Coder
from .single_wholefile_func_prompts import SingleWholeFileFunctionPrompts


class SingleWholeFileFunctionCoder(Coder):
    functions = [
        dict(
            name="write_file",
            description="write new content into the file",
            parameters=dict(
                type="object",
                required=["explanation", "content"],
                properties=dict(
                    explanation=dict(
                        type="string",
                        description=(
                            "Step by step plan for the changes to be made to the code (future"
                            " tense, markdown format)"
                        ),
                    ),
                    content=dict(
                        type="string",
                        description="Content to write to the file",
                    ),
                ),
            ),
        ),
    ]

    def __init__(self, *args, **kwargs):
        raise RuntimeError("Deprecated, needs to be refactored to support get_edits/apply_edits")

    def update_cur_messages(self, edited):
        if edited:
            self.cur_messages += [
                dict(role="assistant", content=self.gpt_prompts.redacted_edit_message)
            ]
        else:
            self.cur_messages += [dict(role="assistant", content=self.partial_response_content)]

    def render_incremental_response(self, final=False):
        if self.partial_response_content:
            return self.partial_response_content

        args = self.parse_partial_args()

        return str(args)

    def live_diffs(self, fname, content, final):
        lines = content.splitlines(keepends=True)

        # ending an existing block
        full_path = self.abs_root_path(fname)

        content = self.io.read_text(full_path)
        orig_lines = [] if content is None else content.splitlines()
        show_diff = diffs.diff_partial_update(
            orig_lines,
            lines,
            final,
            fname=fname,
        ).splitlines()

        return "\n".join(show_diff)

    def _update_files(self):
        name = self.partial_response_function_call.get("name")
        if name and name != "write_file":
            raise ValueError(f'Unknown function_call name="{name}", use name="write_file"')

        args = self.parse_partial_args()
        if not args:
            return

        content = args["content"]
        path = self.get_inchat_relative_files()[0]
        return {path} if self.allowed_to_edit(path, content) else set()
