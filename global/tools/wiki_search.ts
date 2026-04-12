import { tool } from "@opencode-ai/plugin"
import path from "path"
import { existsSync, readdirSync, readFileSync } from "fs"

export default tool({
  description: "Search the project wiki for pages matching a keyword or topic. Returns matching page paths and relevant excerpts.",
  args: {
    query: tool.schema.string().describe("Keyword or topic to search for in the wiki"),
  },
  async execute(args, context) {
    const worktree = context.worktree || "."
    const wikiDir = path.join(worktree, ".opencode", "wiki")

    if (!existsSync(wikiDir)) {
      return "No wiki found at .opencode/wiki/ in this project."
    }

    const query = args.query.toLowerCase()
    const results: string[] = []

    function searchDir(dir: string) {
      for (const entry of readdirSync(dir, { withFileTypes: true })) {
        const fullPath = path.join(dir, entry.name)
        if (entry.isDirectory()) {
          searchDir(fullPath)
        } else if (entry.name.endsWith(".md")) {
          try {
            const content = readFileSync(fullPath, "utf-8")
            if (content.toLowerCase().includes(query) || entry.name.toLowerCase().includes(query)) {
              const relPath = path.relative(worktree, fullPath)
              const lines = content.split("\n")
              const matchingLines: string[] = []
              for (let i = 0; i < lines.length && matchingLines.length < 3; i++) {
                if (lines[i].toLowerCase().includes(query)) {
                  matchingLines.push(`  L${i + 1}: ${lines[i].trim()}`)
                }
              }
              results.push(`${relPath}\n${matchingLines.join("\n")}`)
            }
          } catch {
            // Skip unreadable files
          }
        }
      }
    }

    searchDir(wikiDir)

    if (results.length === 0) {
      return `No wiki pages found matching "${args.query}".`
    }

    const limited = results.slice(0, 5)
    return `Found ${results.length} matching wiki page(s):\n\n${limited.join("\n\n")}`
  },
})
