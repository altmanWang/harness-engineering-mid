const pendingPermissions = new Map<string, {
  engine: { resolvePermission: (optionId: string) => void }
}>()

export function registerPendingPermission(
  requestId: string,
  engine: { resolvePermission: (optionId: string) => void },
): void {
  pendingPermissions.set(requestId, { engine })
}

export function resolvePermission(requestId: string, optionId: string): boolean {
  const entry = pendingPermissions.get(requestId)
  if (!entry) return false
  entry.engine.resolvePermission(optionId)
  pendingPermissions.delete(requestId)
  return true
}
