import fs from 'node:fs'
import path from 'node:path'
import process from 'node:process'

const root = process.cwd()

function read(file) {
  return fs.readFileSync(path.join(root, file), 'utf8')
}

function assert(condition, message) {
  if (!condition) {
    throw new Error(message)
  }
}

const router = read('src/router/index.ts')
const app = read('src/App.vue')
const chatLayout = read('src/components/workflow/ChatLayout.vue')

assert(router.includes("redirect: '/workflow'"), 'root route must redirect to /workflow')
assert(fs.existsSync(path.join(root, 'src/components/layout/AppSidebar.vue')), 'AppSidebar.vue must exist')
assert(app.includes('<AppSidebar />'), 'App.vue must render AppSidebar')
assert(!app.includes('<Navbar />'), 'App.vue must not render Navbar')
assert(!app.includes("@/components/layout/Navbar.vue"), 'App.vue must not import Navbar')
assert(chatLayout.includes('workflow-topbar'), 'ChatLayout must include a Workflow top bar')
assert(!chatLayout.includes('<ChatSidebar'), 'ChatLayout must not render ChatSidebar')
assert(!chatLayout.includes("import ChatSidebar"), 'ChatLayout must not import ChatSidebar')

const sidebar = read('src/components/layout/AppSidebar.vue')
assert(sidebar.includes("index=\"/skills\""), 'AppSidebar must include Skills nav item')
assert(sidebar.includes("index=\"/agents\""), 'AppSidebar must include Agents nav item')
assert(!sidebar.includes("index=\"/workflow\""), 'AppSidebar must not include Workflow as a primary nav item')
assert(sidebar.includes('history-section'), 'AppSidebar must include bottom history section')
assert(sidebar.includes('isCollapsed'), 'AppSidebar must support collapsed state')

console.log('Sidebar layout source checks passed')
