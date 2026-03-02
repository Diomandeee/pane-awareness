import CodeBlock from './code-block'

const installCode = `pip install pane-awareness

# Auto-install Claude Code hooks
pa install --claude-code`

const usageCode = `import pane_awareness as pa

# On each prompt submission
pa.update_pane(
    session_id="my-session",
    cwd="/my/project",
    prompt_text="fix the auth bug"
)

# See what other panes are doing
panes = pa.get_all_panes()
for tty, pane in panes.items():
    print(f"  [{pane.get('quadrant', '?')}] {pane.get('project')}")

# Claim a resource before working on it
pa.claim_resource("file:src/auth.py", reason="fixing login flow")

# Send a message to another pane
pa.send_message(target="top-right", message="I'm done with auth")`

const cliCode = `pa status                    # Show all active panes
pa send <target> <message>   # Send a message
pa claim <resource>          # Claim a resource
pa predictions               # Show convergence predictions
pa pollination               # Full cross-pollination analysis`

export default function QuickStart() {
  return (
    <section className="py-16 px-4">
      <div className="max-w-4xl mx-auto">
        <h2 className="text-3xl font-bold text-center mb-12">Quick Start</h2>

        <div className="space-y-8">
          <div>
            <h3 className="text-lg font-semibold mb-3">Install</h3>
            <CodeBlock code={installCode} language="bash" />
          </div>

          <div>
            <h3 className="text-lg font-semibold mb-3">Python API</h3>
            <CodeBlock code={usageCode} language="python" />
          </div>

          <div>
            <h3 className="text-lg font-semibold mb-3">CLI</h3>
            <CodeBlock code={cliCode} language="bash" />
          </div>
        </div>
      </div>
    </section>
  )
}
