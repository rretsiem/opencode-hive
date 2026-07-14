import { tool } from "@opencode-ai/plugin"
import path from "path"

export default tool({
  description: "Run ruff lint + format check + pytest in one command. Optionally scope to a directory.",
  args: {
    target: tool.schema.string().optional().describe("Directory or file to check (default: src/)"),
  },
  async execute(args, context) {
    const globalScript = path.join(process.env.HOME || "", ".config/opencode/scripts/check.sh")
    const target = args.target || "src/"
    const result = await Bun.$`bash ${globalScript} ${target}`.cwd(context.worktree || ".").text()
    return result.trim()
  },
})
