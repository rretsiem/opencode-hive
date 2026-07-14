import { tool } from "@opencode-ai/plugin"
import path from "path"

export default tool({
  description: "Strip method bodies from a Python file, keeping signatures, docstrings, and type hints. Reduces token usage by ~90% for understanding large files.",
  args: {
    file_path: tool.schema.string().describe("Path to the Python file to skeletonize"),
  },
  async execute(args, context) {
    const globalScript = path.join(process.env.HOME || "", ".config/opencode/scripts/skeleton.py")
    const result = await Bun.$`python3 ${globalScript} ${args.file_path}`.cwd(context.worktree || ".").text()
    return result.trim()
  },
})
