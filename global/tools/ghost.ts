import { tool } from "@opencode-ai/plugin"
import path from "path"

export default tool({
  description: "Scan a Python file for possible dead-code candidates that should be confirmed manually.",
  args: {
    file_path: tool.schema.string().describe("Path to the Python file to check for dead-code candidates"),
  },
  async execute(args, context) {
    const globalScript = path.join(process.env.HOME || "", ".config/opencode/scripts/ghost.py")
    const result = await Bun.$`python3 ${globalScript} ${args.file_path}`.cwd(context.worktree || ".").text()
    return result.trim()
  },
})
