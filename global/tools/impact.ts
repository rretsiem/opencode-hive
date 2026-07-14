import { tool } from "@opencode-ai/plugin"
import path from "path"

export default tool({
  description: "Find likely Python definitions and usages of a symbol to estimate refactor blast radius.",
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
