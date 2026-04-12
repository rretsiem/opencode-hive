import { tool } from "@opencode-ai/plugin"
import path from "path"
import { existsSync } from "fs"

export default tool({
  description: "Find all test files that reference or import a specific source module.",
  args: {
    file_path: tool.schema.string().describe("Path to the source file to find tests for"),
  },
  async execute(args, context) {
    const localScript = path.join(context.worktree || ".", "scripts/which_test.py")
    const globalScript = path.join(process.env.HOME || "", ".config/opencode/scripts/which_test.py")
    const script = existsSync(localScript) ? localScript : globalScript
    const result = await Bun.$`python3 ${script} ${args.file_path}`.cwd(context.worktree || ".").text()
    return result.trim()
  },
})
