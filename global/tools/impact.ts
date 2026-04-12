import { tool } from "@opencode-ai/plugin"
import path from "path"
import { existsSync } from "fs"

export default tool({
  description: "Find every file that uses a symbol, distinguishing definitions from usages. Run before any refactor to understand blast radius.",
  args: {
    symbol: tool.schema.string().describe("Name of the symbol to find usages of"),
  },
  async execute(args, context) {
    const localScript = path.join(context.worktree || ".", "scripts/impact.py")
    const globalScript = path.join(process.env.HOME || "", ".config/opencode/scripts/impact.py")
    const script = existsSync(localScript) ? localScript : globalScript
    const worktree = context.worktree || "."
    const result = await Bun.$`python3 ${script} ${worktree} ${args.symbol}`.cwd(worktree).text()
    return result.trim()
  },
})
