import { tool } from "@opencode-ai/plugin"
import path from "path"

export default tool({
  description: "Find the exact definition of a class or function project-wide. Uses Jedi when available, falls back to AST scan.",
  args: {
    symbol: tool.schema.string().describe("Name of the class or function to find"),
  },
  async execute(args, context) {
    const globalScript = path.join(process.env.HOME || "", ".config/opencode/scripts/seek.py")
    const worktree = context.worktree || "."
    const result = await Bun.$`python3 ${globalScript} ${worktree} ${args.symbol}`.cwd(worktree).text()
    return result.trim()
  },
})
