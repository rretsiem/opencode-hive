import { tool } from "@opencode-ai/plugin"
import path from "path"
import { existsSync } from "fs"

export default tool({
  description: "Find the exact definition of a class or function project-wide. Uses Jedi when available, falls back to AST scan.",
  args: {
    symbol: tool.schema.string().describe("Name of the class or function to find"),
  },
  async execute(args, context) {
    const localScript = path.join(context.worktree || ".", "scripts/seek.py")
    const globalScript = path.join(process.env.HOME || "", ".config/opencode/scripts/seek.py")
    const script = existsSync(localScript) ? localScript : globalScript
    const worktree = context.worktree || "."
    const result = await Bun.$`python3 ${script} ${worktree} ${args.symbol}`.cwd(worktree).text()
    return result.trim()
  },
})
