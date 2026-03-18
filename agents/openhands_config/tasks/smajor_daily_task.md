# Daily smajor.org Maintenance Task

**Agent**: OpenHands (CodeActAgent) on AlienStef — http://10.0.0.97:3001
**Model**: qwen2.5-coder:14b (Ollama local, RTX 3060)
**Schedule**: Daily, any time
**Repo path**: `apps/smajor-command-center/`

---

## Task Description

Review the smajor-command-center Next.js app and fix any issues found.

### Steps

1. **TypeScript audit**
   - Run `npx tsc --noEmit` in `apps/smajor-command-center/`
   - Fix all reported errors
   - Pay attention to missing types, wrong prop shapes, `any` that should be typed

2. **Import verification**
   - Check all `@/lib/*` imports exist and export the referenced symbols
   - Check all `@/components/*` imports match actual file names
   - Verify `@/lib/db` exports: `Client`, `Job`, `Quote`, `JobStatus`, `ClientType`, etc.

3. **API route health check**
   - Verify each route in `app/api/` uses the correct Next.js 15 `params: Promise<{...}>` pattern
   - Confirm GET/POST/PUT/DELETE are properly exported
   - Check error handling returns proper `NextResponse.json()` with status codes

4. **Component review**
   - `components/dashboard.tsx` — check all `useState`, `useEffect` have correct types
   - `components/clients-table.tsx` — verify search + expand logic
   - `components/jobs-list.tsx` — verify filter + status advance logic
   - `components/command-center.tsx` — verify `CommandCenterSnapshot` type compatibility

5. **Dependency check**
   - Confirm `better-sqlite3` and `@types/better-sqlite3` are in `package.json`
   - Confirm `data/` directory exists with `.gitkeep`

6. **Commit fixes**
   ```
   git add apps/smajor-command-center/
   git commit -m "fix(smajor): OpenHands daily maintenance $(date +%Y-%m-%d)"
   ```

---

## Expected outcome

- Zero TypeScript errors
- All API routes respond to test requests
- Dashboard renders without console errors
- Changes committed to repo
