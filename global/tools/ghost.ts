import { tool } from "@opencode-ai/plugin"
import path from "path"
import { existsSync } from "fs"

export default tool({
  description: "Scan a file for functions or classes that are never used anywhere else in the project.",
  args: {
    file_path: tool.schema.string().describe("Path to the Python file to check for dead code"),
  },
  async execute(args, context) {
    const localScript = path.join(context.worktree || ".", "scripts/ghost.py")
    const globalScript = path.join(process.env.HOME || "", ".config/opencode/scripts/ghost.py")
    const script = existsSync(localScript) ? localScript : globalScript
    const result = await Bun.$`python3 ${script} ${args.file_path}`.cwd(context.worktree || ".").text()
    return result.trim()
  },
})
