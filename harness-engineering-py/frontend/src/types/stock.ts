export interface DiagnosisResult {
  code: string
  name: string
  conclusion: "看多" | "看空" | "观望" | null
  reason: string
  close: number | null
  open: number | null
  pct_chg: number | null
  ema20: number | null
  error?: string
  source?: string
  klinePath?: string
}

export interface StockDiagnosis {
  codes: string[]
  sector?: string
  days: number
  skills: string[]
  skillNames: string[]
  initialPrompt: string
  results: DiagnosisResult[]
  successCount: number
  failedCount: number
}

export interface SectorInfo {
  code: string
  name: string
  type?: string  // "行业" | "概念"
}

export interface StockSearchResult {
  code: string
  name: string
  type: string
}
