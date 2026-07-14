import { tool } from "@opencode-ai/plugin"
import path from "path"

export default tool({
  description: "Find every file that uses a symbol, distinguishing definitions from usages. Run before any refactor to understand blast radius.",
  args: {
    symbol: tool.schema.string().describe("Name of the symbol to find usages of"),
  },
  async execute(args, context) {
    const globalScript = path.join(process.env.HOME || "", ".config/opencode/scripts/impact.py")
    const worktree = context.worktree || "."
    const result = await Bun.$`python3 ${globalScript} ${worktree} ${args.symbol}`.cwd(worktree).text()
    return result.trim()
  },
})
