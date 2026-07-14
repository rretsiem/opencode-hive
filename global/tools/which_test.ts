import { tool } from "@opencode-ai/plugin"
import path from "path"

export default tool({
  description: "Find all test files that reference or import a specific source module.",
  args: {
    file_path: tool.schema.string().describe("Path to the source file to find tests for"),
  },
  async execute(args, context) {
    const globalScript = path.join(process.env.HOME || "", ".config/opencode/scripts/which_test.py")
    const result = await Bun.$`python3 ${globalScript} ${args.file_path}`.cwd(context.worktree || ".").text()
    return result.trim()
  },
})
