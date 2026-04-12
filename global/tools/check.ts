import { tool } from "@opencode-ai/plugin"
import path from "path"
import { existsSync } from "fs"

export default tool({
  description: "Run ruff lint + format check + pytest in one command. Optionally scope to a directory.",
  args: {
    target: tool.schema.string().optional().describe("Directory or file to check (default: src/)"),
  },
  async execute(args, context) {
    const localScript = path.join(context.worktree || ".", "scripts/check.sh")
    const globalScript = path.join(process.env.HOME || "", ".config/opencode/scripts/check.sh")
    const script = existsSync(localScript) ? localScript : globalScript
    const target = args.target || "src/"
    const result = await Bun.$`bash ${script} ${target}`.cwd(context.worktree || ".").text()
    return result.trim()
  },
})
