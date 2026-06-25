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
}

export interface StockDiagnosis {
  codes: string[]
  days: number
  skills: string[]
  results: DiagnosisResult[]
  successCount: number
  failedCount: number
}
